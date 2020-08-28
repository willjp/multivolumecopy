MultiVolumeCopy
===============

Tool to backup a fileserver to multiple smaller hard-drives.


Usage
-----

.. code-block:: bash

    multivolumecopy /mnt/src -o /mnt/usb
    multivolumecopy /mnt/src/{books,ambient,radio} -o /mnt/usb

    # when /mnt/usb is full, you'll be prompted to replace it
    # with another disk

Autocompletion
--------------

Autocompletion is available, but not installed by default.

zsh
...

Copy ``data/autocomplete.zsh/_multivolumecopy`` to a location on your ``$fpath`` .
For example ``/usr/share/zsh/5.8/functions/Unix/_multivolumecopy``


How it Works
------------

1. all files are found, and catalogued with their filesize (in bytes).

2. `--output` is searched for files that do not exist on the src-side.
  these files are deleted.

3. If srcfile timestamp/filesize differs from dstfile, re-copy the file
   to dst. *(see ``df -h file``)*

4. If the next copied file would exceed drive's available-space/requested-padding, 
   then prompt for another hard-drive (or a different medium).


To restore files, simply copy everything from your volumes back onto the source. 
File hierarchy is kept intact.

