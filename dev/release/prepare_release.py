import os
import sys

import brian2tools

# require a clean working directory
ret_val = os.system('git diff-index --quiet HEAD --')
if ret_val != 0:
    print('You have uncommited changes, commit them first')
    sys.exit(1)

# Ask for version number
print('Current version is: ' + brian2tools.__version__)
version = raw_input('Enter new Brian2 version number: ').strip()


# add tag
os.system('git tag -a -m "Release brian2tools %s" %s' % (version, version))

# print commands necessary for pushing
print('Review the last commit: ')
os.system('git show %s' % version)
print('')
print('To push, using the following command:')
print('git push --tags origin master')