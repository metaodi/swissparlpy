# -*- coding: utf-8 -*-

from codecs import open
from setuptools import setup, find_packages
import re

with open('swissparlpy/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')

with open('README.md', 'r', encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='swissparlpy',
    packages=find_packages(),
    version=version,
    install_requires=['requests', 'pyodata'],
    description='Client for Swiss parliament API',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Stefan Oderbolz',
    author_email='odi@metaodi.ch',
    maintainer='Stefan Oderbolz',
    maintainer_email='odi@metaodi.ch',
    url='https://github.com/metaodi/swissparlpy',
    download_url='https://github.com/metaodi/swissparlpy/archive/v%s.zip' % version,
    keywords=['api', 'swiss', 'switzerland', 'parliament', 'odata', 'swissparl'],
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    python_requires='>=3.6'
)
