import os
import sys

def run():
    try:
        import nose
    except ImportError:
        raise ImportError('Running the test suite requires the nose package.')
    dirname = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    # We write to stderr since nose does all of its output on stderr as well
    sys.stderr.write('Running tests in "%s" ' % dirname)
    argv = ['nosetests', '-c=',  # no config file
            '--exe']
    return nose.run(argv)
