#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name='webvpn',
    install_requires=['requests', 'lxml', 'cssselect', 'xmltodict', 'onetimepass'],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'webvpn=webvpn.webvpn:main'
        ]
    },
)
