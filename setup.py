#!/usr/bin/env python3
# coding: utf-8

from setuptools import setup
from setuptools import find_packages

from crawlers import VERSION

with open('crawlers/requirements.txt', 'r', encoding='utf8') as file:
    install_requires = list(map(lambda x: x.strip(), file.readlines()))


setup(
    name='pt-crawler',
    version=VERSION,
    author='kinopico',
    author_email='zqmillet@qq.com',
    url='https://github.com/zqmillet/pt-crawler',
    description='a group of crawlers for private tracker website',
    packages=find_packages(),
    install_requires=install_requires,
)
