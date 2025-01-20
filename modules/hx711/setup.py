import setuptools
from distutils.core import setup
from codecs import open
from os import path

setup(
    name='JoyIT_hx711py',
    version='0.1.1',
    packages=setuptools.find_packages(),
    install_requires=[

    ],
    author='j-dohnalek',
    author_email='service@joy-it.net',
    description='Updated Python library for the HX711 load cell amplifier and Raspberry Pi 5',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/joy-it/JoyIT_hx711py',  
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
    ],
    python_requires='>=3.6',
    zip_safe=False,
)
