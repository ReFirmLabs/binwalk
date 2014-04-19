# Python distutils build script for magic extension
from distutils.core import setup

setup(name = 'Magic file extensions',
    version = '0.2',
    author = 'Reuben Thomas',
    author_email = 'rrt@sc3d.org',
    license = 'BSD',
    description = 'libmagic Python bindings',
    py_modules = ['magic'])
