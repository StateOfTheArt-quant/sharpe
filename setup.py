#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os.path import dirname, join

from setuptools import find_packages, setup


def read_file(file):
    with open(file, "rt") as f:
        return f.read()


with open(join(dirname(__file__), 'sharpe/VERSION.txt'), 'rb') as f:
    version = f.read().decode('ascii').strip()
    

setup(
    name='sharpe',
    version=version,
    description='sharpe',
    packages=find_packages(exclude=[]),
    author='Jiang Yu',
    author_email='yujiangallen@126.com',
    license='Apache License v2',
    package_data={'': ['*.*']},
    url='',
    install_requires=read_file("requirements.txt").strip(),
    zip_safe=False,
    classifiers=[
        'Programming Language :: Python',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)

