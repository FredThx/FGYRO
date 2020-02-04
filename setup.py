#!/usr/bin/env python
# -*- coding: utf-8 -*-
import shutil
import os
from setuptools import setup, find_packages

import FGYRO

setup(
    name='FGYRO',
    version=FGYRO.__version__,
    packages=find_packages(),
    author="FredThx",
    author_email="FredThx@gmail.com",
    description="A python lib for GYRO analyse",
    long_description=open('README.md').read(),
    install_requires=["FUTIL", "picamera", "paho-mqtt"],
    include_package_data=True,
    url='',
    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved",
        "Natural Language :: French",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7"
    ],
    license="WTFPL",
)
try:
	os.mkdir('/opt/FGYRO')
	os.mkdir('/opt/FGYRO/capture') # todo : changer par auto-creation du folder a l utilisation
except OSError:
	pass

#shutil.copy('main.py', '/opt/FGYRO')
#shutil.copy('fgyro.service', '/opt/FGYRO')
#shutil.copy('fgyro.sh', '/opt/FGYRO')
