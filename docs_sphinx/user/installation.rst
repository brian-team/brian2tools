Installation instructions
=========================
The ``brian2tools`` package is a pure Python package that should be installable
without problems most of the time, either using the
`Anaconda distribution <https://store.continuum.io/cshop/anaconda/>`_ or using
``pip``. However, it depends on the ``brian2`` package which has more complex
requirements for installation. The recommended approach is therefore to first
install ``brian2`` following the instruction in the
`Brian 2 documentation <https://brian2.readthedocs.org>`_ and then use the same
approach (i.e. either installation with Anaconda or installation with ``pip``)
for ``brian2tools``.

Installation with Anaconda
--------------------------
Since ``brian2tools`` (and ``brian2`` on which it depends) are not part of the
main Anaconda distribution, you have to install it from the
`brian-team channel <https://conda.binstar.org/brian-team>`_. To do so use::

    conda install -c brian-team brian2tools

You can also permanently add the channel to your list of channels::

    conda config --add channels brian-team

This has only to be done once. After that, you can install and update the brian2
packages as any other Anaconda package::

    conda install brian2tools

Installing optional requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The 3D plotting of morphologies (see :ref:`plotting_morphologies`) depends on the
`mayavi package <http://docs.enthought.com/mayavi/mayavi/>`_. You can install
it from anaconda as well::

    conda install mayavi


Installation with pip
---------------------
If you decide not to use Anaconda, you can install `brian2tools` from the Python
package index: https://pypi.python.org/pypi/brian2tools

To do so, use the ``pip`` utility::

    pip install brian2tools

You might want to add the ``--user`` flag, to install Brian 2 for the local user
only, which means that you don't need administrator privileges for the
installation.

If you have an older version of pip, first update pip itself::

    # On Linux/MacOsX:
    pip install -U pip

    # On Windows
    python -m pip install -U pip

If you don't have ``pip`` but you have the ``easy_install`` utility, you can use
it to install ``pip``::

    easy_install pip

If you have neither ``pip`` nor ``easy_install``, use the approach described
here to install ``pip``: https://pip.pypa.io/en/latest/installing.htm

Installing optional requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The 3D plotting of morphologies (see :ref:`plotting_morphologies`) depends on the
`mayavi package <http://docs.enthought.com/mayavi/mayavi/>`_. Follow its
`installation instructions <docs.enthought.com/mayavi/mayavi/installation.html>`_
to install it.