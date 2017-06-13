import os
import re
import sys
import shutil

import brian2tools

# require a clean working directory
ret_val = os.system('git diff-index --quiet HEAD --')
if ret_val != 0:
    print('You have uncommited changes, commit them first')
    sys.exit(1)

# Ask for version number
print('Current version is: ' + brian2tools.__version__)
version = raw_input('Enter new Brian2 version number: ').strip()
# update setup.py
setup_py = open('../../setup.py', 'r').read()
setup_py = re.sub("version\s*=\s*'.*?'", "version='" + version + "'", setup_py)
open('../../setup.py', 'w').write(setup_py)

# commit
os.system('git commit -a -v -m "***** Release brian2tools %s *****"' % version)

# add tag
os.system('git tag -a -m "Release brian2tools %s" %s' % (version, version))

# Create universal wheels and source distribution
os.chdir('../..')
if os.path.exists('dist'):
    shutil.rmtree('dist')
os.system('%s setup.py sdist --formats=gztar bdist_wheel' % sys.executable)

# print commands necessary for pushing
print('')
print('*'*60)
print('To push, using the following command:')
print('git push --tags origin master')
