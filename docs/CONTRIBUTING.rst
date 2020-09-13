Version Updates
---------------

This project uses semantic versioning.
Update version in ``multivolumecopy.__init__.py`` ,
and add summary of changes to ``VERSION_HIST.yml``


Testing
-------

Run tests using tox. (you'll need to install it with pip, or your os's package manager)

.. code-block:: bash

    tox                        # run tests in all environments
    tox -e py38                # run python-3.8 only
    tox -- {pytest arguments}  # run tests and pass args to pytest


Interactive Testing
-------------------

If you're using linux, I wrote a quick script to generate some dummy data
and interactively test the program.

.. code-block:: bash

    python tests/interactive/test_interactively.py


