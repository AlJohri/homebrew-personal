#!/usr/bin/env python3

"""
Forked from: https://github.com/zdave/openconnect-gp-okta/blob/master/openconnect-gp-okta
"""

import sys
import json
import signal
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

def okta_auth(s, domain, username, password, token_secret=None):
    r = check(s.post(f'https://{domain}/api/v1/authn', json={'username': username, 'password': password})).json()
    if r['status'] == 'MFA_REQUIRED':
        for factor in r['_embedded']['factors']:
            if factor['factorType'] == 'push':
                url = factor['_links']['verify']['href']
                while True:
                    r = check(s.post(url, json={'stateToken': r['stateToken']})).json()
                    if r['status'] != 'MFA_CHALLENGE':
                        break
                    assert r['factorResult'] == 'WAITING'
                break
            elif factor['factorType'] == 'token:software:totp':
                url = factor['_links']['verify']['href']
                otp_value = onetimepass.get_totp(token_secret)
                r = check(s.post(url, json={'stateToken': r['stateToken'], 'answer': otp_value})).json()
                break
        else:
            assert False
    assert r['status'] == 'SUCCESS'
    return r['sessionToken']

def okta_saml(s, saml_req_url, domain, username, password, token_secret):
    check(s.get(saml_req_url)) # Just to set DT cookie
    token = okta_auth(s, domain, username, password, token_secret)
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
    parser.add_argument('--okta-group', required=False)
    parser.add_argument('--username', required=True)
    parser.add_argument('--password', required=True)
    parser.add_argument('--token-secret', required=True)

    args = parser.parse_args()

    if args.protocol == 'anyconnect': # Cisco AnyConnect SSL VPN, as well as ocserv
        with requests.Session() as s:
            saml_req_url, xml_payload = prelogin(s, args.gateway, args.okta_group)
            saml_resp_url, saml_resp_data = okta_saml(s, saml_req_url, args.okta_domain, args.username, args.password, args.token_secret)
            cookie = complete_saml(s, args.gateway, saml_resp_url, saml_resp_data, xml_payload, args.okta_group)
            print(cookie)
    elif args.protocol == 'nc': # Juniper Network Connect / Pulse Secure SSL VPN
        with requests.Session() as s:
            saml_req_url = s.get(f'https://{args.gateway}').url
            saml_resp_url, saml_resp_data = okta_saml(s, saml_req_url, args.okta_domain, args.username, args.password, args.token_secret)
            r1 = check(s.post(saml_resp_url, data=saml_resp_data))
            action, payload = extract_form(r1, '#DSIDConfirmForm')
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
