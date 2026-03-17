import os
import shutil
import sys

import brian2tools

# require a clean working directory
ret_val = os.system('git diff-index --quiet HEAD --')
if ret_val != 0:
    print('You have uncommited changes, commit them first')
    sys.exit(1)

# Ask for version number
print('Current version is: ' + brian2tools.__version__)
version = input('Enter new Brian2 version number: ').strip()

# commit
os.system('git commit -a -v -m "***** Release brian2tools %s *****"' % version)

# add tag
os.system('git tag -a -m "Release brian2tools %s" %s' % (version, version))

# Create wheel and source distribution via PEP 517 build backend
os.chdir('../..')
if os.path.exists('dist'):
    shutil.rmtree('dist')
os.system('%s -m build' % sys.executable)

# print commands necessary for pushing
print('')
print('*'*60)
print('To push, using the following command:')
print('git push --tags origin master')
