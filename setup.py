#! /usr/bin/env python
'''
brian2tools setup script
'''
import os
import sys

from setuptools import setup, find_packages

if sys.version_info < (2, 7):
    raise RuntimeError('Only Python versions >= 2.7 are supported')

def readme():
    with open('README.rst') as f:
        return f.read()

# Note that this does not set a version number explicitly, but automatically
# figures out a version based on git tags
setup(name='brian2tools',
      url='https://github.com/brian-team/brian2tools',
      version='0.2.1.1',
      packages=find_packages(),
      package_data={'brian2tools.nmlexport': ['LEMSUnitsConstants.xml',
                                              'NeuroMLCoreDimensions.xml']},
      install_requires=['matplotlib>=1.3.1',
                        'brian2>=2.0',
                        'setuptools',
                        'setuptools_scm',
                        'pylems>=0.4.9'],
      provides=['brian2tools'],
      extras_require={'test': ['pytest'],
                      'docs': ['sphinx>=1.0.1', 'sphinxcontrib-issuetracker',
                               'mock']},
      use_2to3=False,
      description='Tools for the Brian 2 simulator',
      long_description=readme(),
      author='Marcel Stimberg, Dan Goodman, Romain Brette',
      author_email='team@briansimulator.org',
      license='CeCILL-2.1',
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
      ],
      keywords='visualization neuroscience'
      )
