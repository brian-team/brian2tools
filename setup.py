#! /usr/bin/env python
'''
brian2tools setup script
'''
import sys
from setuptools import setup, find_packages

if sys.version_info < (2, 7):
    raise RuntimeError('Only Python versions >= 2.7 are supported')


def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='brian2tools',
      version='2.0b4+git',
      packages=find_packages(),
      install_requires=['matplotlib>=1.3.1',
                        'brian2>1.9,<2.1'],
      provides=['brian2tools'],
      extras_require={'test': ['nosetests>=1.0'],
                      'docs': ['sphinx>=1.0.1', 'sphinxcontrib-issuetracker']},
      use_2to3=False,
      description='Tools for the Brian 2 simulator',
      long_description=readme(),
      author='Marcel Stimberg, Dan Goodman, Romain Brette',
      author_email='',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: CEA CNRS Inria Logiciel Libre License, version 2.1 (CeCILL-2.1)',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
          'Topic :: Scientific/Engineering :: Bio-Informatics'
      ]
      )
