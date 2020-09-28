MultiVolumeCopy
===============

Tool to backup a fileserver to multiple smaller hard-drives.


.. contents:: Table of Contents


Usage
-----

Perform backups, prompting for additional drive as required.

.. code-block:: bash

    multivolumecopy /mnt/src -o /mnt/usb                        # copy from single source
    multivolumecopy /mnt/src/{books,ambient,radio} -o /mnt/usb  # copy from multiple sources

    # when /mnt/usb is full, you'll be prompted to replace it


Verify backup volume using the generated `.mvcopy-jobdata.json` .

.. code-block:: bash

    # verify that /mnt/usb has updated files corresponding
    # to indexes 0-300 in .mvcopy-jobdata.json

    multivolumecopy --verify \
      -f .mvcopy-jobdata.json  \
      -i 0 -si 300 \
      -o /mnt/usb


Install
-------

.. code-block:: bash

    pip install 'git+https://github.com/willjp/multivolumecopy@master'


Configuration
-------------

ZSH Autocompletion
...................

Autocompletion is available, but not installed by default.

Copy ``data/autocomplete.zsh/_multivolumecopy`` to a location on your ``$fpath`` .
(ex: ``/usr/share/zsh/5.8/functions/Unix/_multivolumecopy`` )


Misc
----

* contributing_
* technical_decisions_
* helpful_suggestions_

.. _contributing: ./docs/CONTRIBUTING.rst
.. _technical_decisions: ./docs/TECHNICAL_DECISIONS.rst
.. _helpful_suggestions: ./docs/HELPFUL_SUGGESTIONS.rst
