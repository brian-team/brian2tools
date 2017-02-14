import sys
import os
import glob
import subprocess
import time
import yaml

try:
    from conda_build.config import config
except ImportError:
    from conda_build.config import Config
    config = Config()

from binstar_client.scripts.cli import main
from binstar_client.errors import BinstarError

with open(os.path.join('dev', 'conda-recipe', 'meta.yaml')) as f:
    name = yaml.load(f)['package']['name']

#### Convert linux-64 package to all other platforms
binary_package_glob = os.path.join(config.bldpkgs_dir, '{0}*.tar.bz2'.format(name))
binary_package = glob.glob(binary_package_glob)[0]

release = 'dev' not in binary_package
# We only upload release packages to conda
if not release:
    sys.exit(0)

# Call convert via command line

args = ['conda-convert', binary_package, '-p', 'all',
        '-o', os.path.join(config.bldpkgs_dir, '..')]
subprocess.check_call(args)

### Upload packages for all platforms
token = os.environ['BINSTAR_TOKEN']
options = ['-t', token, 'upload',
           '-u', 'brian-team']

for target in ['linux-32', 'linux-64', 'win-32', 'win-64', 'osx-64']:
    filename = os.path.abspath(os.path.join(config.bldpkgs_dir, '..', target,
                                            os.path.basename(binary_package)))
    # Uploading sometimes fails due to server or network errors -- we try it five
    # times before giving up
    attempts = 5
    for attempt in range(attempts):
        try:
            main(args=options+[filename])
            break  # all good
        except BinstarError as ex:
            print('Something did not work (%s).' % str(ex))
            if attempt < attempts - 1:
                print('Trying again in 10 seconds...')
                time.sleep(10)
            else:
                print('Giving up...')
                raise ex
