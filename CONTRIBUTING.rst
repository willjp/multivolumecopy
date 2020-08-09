
Testing
-------

Run tests using tox. (you'll need to install it with pip, or your os's package manager)

.. code-block:: bash

    tox                        # run tests in all environments
    tox -e py38                # run python-3.8 only
    tox -- {pytest arguments}  # run tests and pass args to pytest

