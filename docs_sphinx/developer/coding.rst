Coding guidelines
=================

The coding style should mostly follow the
`Brian 2 guidelines <http://brian2.readthedocs.io/en/latest/developer/guidelines/style.html>`_, with one major
exception: for `brian2tools` the code should be both Python 2 (for versions >= 2.7) and Python 3 compatible. This means
for example to use ``range`` and not ``xrange`` for iteration or conversely use ``list(range)`` instead of just
``range`` when a list is required. For now, this works without ``from __future__`` imports or helper modules like
``six`` but the details of this will be fixed when the need arises.