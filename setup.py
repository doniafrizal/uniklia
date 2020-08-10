# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in uniklia/__init__.py
from uniklia import __version__ as version

setup(
	name='uniklia',
	version=version,
	description='Uniklia App',
	author='Uniklia',
	author_email='unikliadotcom@gmail.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
