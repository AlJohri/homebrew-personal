#!/usr/bin/env python3

"""
Forked from: https://github.com/zdave/openconnect-gp-okta/blob/master/openconnect-gp-okta
"""

import sys
import json
import signal
import getpass
import textwrap
import argparse
import subprocess
import urllib.parse

import requests
import lxml.html
import xmltodict
import onetimepass

def check(r):
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print('ERROR', e, file=sys.stderr)
        print(r.headers, file=sys.stderr)
        print(r.status_code, file=sys.stderr)
        print(r.text, file=sys.stderr)
        raise
    return r

def extract_form(response, form_id):
    doc = lxml.html.fromstring(response.content)
    form = doc.cssselect(form_id)[0]
    action = form.get('action')
    if action.startswith('http'):
        pass
    elif action.startswith('/'):
        o = urllib.parse.urlparse(response.url)
        action = f'{o.scheme}://{o.netloc}{action}'
    else:
        action = response.url.rsplit('/', 1)[0] + '/' + action
    inputs = {x.get('name'):x.get('value') for x in form.cssselect('input')}
    return action, inputs

def prelogin(s, gateway, vpn_group):
    payload = textwrap.dedent("""
    <config-auth client="vpn" type="init" aggregate-auth-version="2">
        <version who="vpn">4.6.03049</version>
        <device-id>mac-intel</device-id>
        <group-select>{}</group-select>
        <group-access>{}</group-access>
        <capabilities>
            <auth-method>multiple-cert</auth-method>
            <auth-method>single-sign-on</auth-method>
            <auth-method>single-sign-on-v2</auth-method>
        </capabilities>
    </config-auth>
    """).strip().format(vpn_group, f'https://{gateway}')
    r1 = check(s.post(f"https://{gateway}/", data=payload, headers={'X-Aggregate-Auth': '1'}))
    data = xmltodict.parse(r1.text)
    url = data['config-auth']['auth']['sso-v2-login']
    r2 = check(s.get(url, allow_redirects=False))
    saml_req_url = r2.headers['Location']
    return saml_req_url, data

def okta_auth(s, domain, username, password, totp_secret, okta_mfa_default_factor_type):
    """
    Factors https://developer.okta.com/docs/api/resources/factor_admin/#factor-model
    """

    r = check(s.post(f'https://{domain}/api/v1/authn', json={'username': username, 'password': password})).json()

    if r['status'] == 'MFA_ENROLL':
        print('Please enroll in multi-factor authentication before using this tool')
        exit(1)

    if r['status'] == 'MFA_REQUIRED':
        factors = r['_embedded']['factors']

        # if only one factor enabled, use it
        if len(factors) == 1:
            factor = factors[0]
        else:
            # if multiple, use the "okta_mfa_default_factor_type"
            try:
                factor = [x for x in factors in x['factorType'] == okta_mfa_default_factor_type][0]
            except IndexError:
                factor_types = set([x['factorType'] for x in okta_mfa_default_factor_type])
                print(f"You have {len(factor_types)} factors enabled in Okta: {factor_types}.\n"
                      f"Please set the --okta-mfa-default-factor-type flag. "
                      f"Currently set or defaulted to: {okta_mfa_default_factor_type}")
                exit(1)

        if factor['factorType'] == 'push':
            url = factor['_links']['verify']['href']
            while True:
                r = check(s.post(url, json={'stateToken': r['stateToken']})).json()
                print('Push notification sent; waiting for your response', file=sys.stderr)
                if r['status'] != 'MFA_CHALLENGE':
                    break
                assert r['factorResult'] == 'WAITING'
                time.sleep(3)
            assert r['status'] == 'SUCCESS'
            return r['sessionToken']
        elif factor['factorType'] == 'token:software:totp':
            url = factor['_links']['verify']['href']
            if totp_secret:
                otp_value = onetimepass.get_totp(totp_secret)
            else:
                print('Enter your multifactor authentication token: ', file=sys.stderr, end='')
                otp_value = input()
            r = check(s.post(url, json={'stateToken': r['stateToken'], 'answer': otp_value})).json()
            assert r['status'] == 'SUCCESS'
            return r['sessionToken']
        elif factor['factorType'] in ['sms', 'question', 'call', 'token']:
            factor_type = factor['factorType']
            raise NotImplementedError(' factor not implemented')

def okta_saml(s, saml_req_url, domain, username, password, totp_secret, okta_default_mfa_factor_type):
    check(s.get(saml_req_url)) # Just to set DT cookie
    token = okta_auth(s, domain, username, password, totp_secret, okta_default_mfa_factor_type)
    params = {'token': token, 'redirectUrl': saml_req_url}
    r = check(s.get(f'https://{domain}/login/sessionCookieRedirect', params=params))
    saml_resp_url, saml_resp_data = extract_form(r, '#appForm')
    assert 'SAMLResponse' in saml_resp_data
    return saml_resp_url, saml_resp_data

def complete_saml(s, gateway, saml_resp_url, saml_resp_data, xml_payload, vpn_group):
    r1 = check(s.post(saml_resp_url, data=saml_resp_data))
    action, payload = extract_form(r1, '#samlform')
    check(s.post(action, data=payload))
    assert 'Authentication successful' in s.get(f'https://{gateway}/+CSCOE+/logon.html?a0=0&a1=&a2=&a3=1').text
    payload_dict = {
        'config-auth': {
            '@client': 'vpn',
            '@type': 'auth-reply',
            '@aggregate-auth-version': '2',
            'version': {'@who':'vpn', '#text': '4.6.03049'},
            'device-id': 'mac-intel',
            'group-select': vpn_group,
            'opaque': xml_payload['config-auth']['opaque'],
            'auth': {'sso-token': s.cookies['acSamlv2Token']},
            'session-id': None,
            'session-token': None
        }
    }
    payload = xmltodict.unparse(payload_dict)
    r4 = check(s.post(f'https://{gateway}', data=payload, headers={'X-Aggregate-Auth': '1'}))
    ret = xmltodict.parse(r4.text)
    return ret['config-auth']['session-token']

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--protocol', choices=['anyconnect', 'nc'], required=True)
    parser.add_argument('--gateway', required=True)
    parser.add_argument('--okta-domain', required=True)
    parser.add_argument('--username', required=True)
    parser.add_argument('--password')
    parser.add_argument('--totp-secret')
    parser.add_argument('--okta-group')
    parser.add_argument('--okta-mfa-default-factor-type', default='token:software:totp',
        choices=('token:software:totp', 'push', 'sms', 'token', 'question', 'call'),
        help='default okta mfa factor type to use if multiple are found')
    parser.add_argument('--verbose', action='store_true', default=False)

    args = parser.parse_args()

    if not args.password:
        args.password = getpass.getpass('Okta Password: ')

    if args.protocol == 'anyconnect': # Cisco AnyConnect SSL VPN, as well as ocserv
        with requests.Session() as s:
            saml_req_url, xml_payload = prelogin(s, args.gateway, args.okta_group)
            saml_resp_url, saml_resp_data = okta_saml(s, saml_req_url, args.okta_domain, args.username, args.password, args.totp_secret, args.okta_mfa_default_factor_type)
            cookie = complete_saml(s, args.gateway, saml_resp_url, saml_resp_data, xml_payload, args.okta_group)
            print(cookie)
    elif args.protocol == 'nc': # Juniper Network Connect / Pulse Secure SSL VPN
        with requests.Session() as s:
            saml_req_url = s.get(f'https://{args.gateway}', timeout=2).url
            saml_resp_url, saml_resp_data = okta_saml(s, saml_req_url, args.okta_domain, args.username, args.password, args.totp_secret, args.okta_mfa_default_factor_type)
            r = check(s.post(saml_resp_url, data=saml_resp_data))
            if 'DSIDConfirmForm' in r.text:
                action, payload = extract_form(r, '#DSIDConfirmForm')
                del payload['btnCancel']
                check(s.post(action, data=payload))
            cookies = {
                'DSID': s.cookies['DSID'],
                'DSFirst': s.cookies['DSFirstAccess'],
                'DSLast': s.cookies['DSLastAccess'],
                'DSSignInUrl': s.cookies['DSSignInURL']
            }
            print('; '.join([f'{k}={v}' for k, v in cookies.items()]))

if __name__ == "__main__":
    main()
