#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name='ssm',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'ssm=ssm:main'
        ]
    },
)
