#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name='openconnect_okta_helper',
    install_requires=['requests', 'lxml', 'cssselect', 'xmltodict', 'onetimepass'],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'openconnect-okta-helper=openconnect_okta_helper:main'
        ]
    },
)
