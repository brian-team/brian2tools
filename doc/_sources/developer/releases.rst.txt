Release procedure
=================

In `brian2tools` we use the `setuptools_scm package <https://pypi.python.org/pypi/setuptools_scm>`_ to set the package
version information, the basic release procedure therefore consists of setting a git tag and pushing that tag to github.
The test builds on `travis <https://travis-ci.org/brian-team/brian2tools>`_ will then automatically push the conda
packages to `anaconda.org <https://anaconda.org/brian-team/brian2tools>`_.

The ``dev/release/prepare_release.py`` script automates the tag creation and makes sure that no uncommited changes
exist when doing do.

In the future, we will probably also push the pypi packages automatically from the test builds; for now this has to
be done manually. The ``prepare_release.py`` script mentioned above will already create the source distribution and
universal wheel files, they can then be uploaded with ``twine upload dist/*`` or using the
``dev/release/upload_to_pypi.py`` script.