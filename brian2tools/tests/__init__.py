import os
import sys


def run():
    try:
        import pytest
    except ImportError:
        raise ImportError('Running the test suite requires the pytest package.')
    dirname = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    # We write to stderr since nose does all of its output on stderr as well
    sys.stderr.write('Running tests in "%s" ' % dirname)
    argv = ['-c=',  # no config file
            dirname
           ]
    return pytest.main(argv) == 0  # errorcode 0 == all ok
