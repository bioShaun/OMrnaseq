#!/usr/bin/env python

from setuptools import setup, find_packages

version = '0.1dev'

print '''------------------------------
Installing RNAseq version {}
------------------------------
'''.format(version)

setup(
    name='rnaseq',
    version=version,
    author='lx Gui',
    author_email='guilixuan@gmail.com',
    keywords=['bioinformatics', 'NGS', 'RNAseq'],
    license='GPLv3',
    packages=find_packages(),
    include_package_data=True,
    scripts=['scripts/mrna',
             'scripts/mrna_fastqc'],
    install_requires=[
        'luigi',
        'pyyaml',
        'envoy',
        'xlsxwriter'],
)

print '''------------------------------
RNAseq installation complete!
------------------------------
'''
