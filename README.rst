MultiVolumeCopy
===============

Simple file-backup tool, to facilitate backing up a fileserver to multiple individual hard-drives
(for code-hobos like me).

This script is designed to help you out of the muddy waters of needing to backup a 
file-server, without actually being able to afford a second file-server to back it up onto.


.. note::

    Do not use this script if you can do any of the following:
    
        * your entire backup can fit on a single HDD.             *( use rsync, borg, ...)*
        * you can afford a second file-server with equal capacity *( use rsync, borg, zfs-send, ...)*
        * need data stored as efficiently as possible             *( use bacula, borg, second fileserver, ..)*
        * backups must have snapshots                             *( use bacula, borg, second fileserver, ..)*


Usage
-----

.. code-block:: bash

    # if your filesystem supports snapshots, take a snapshot
    # and backup files from that frozen moment in time.

    sudo zfs snapshot -r zroot/ROOT/default@temp_backup
    mount -t zfs zroot/ROOT/default@temp_backup /mnt/backup

    
    # backup onto HDDs
    multivolumecopy \
      /mnt/backup/{movies,tvshows,music,books} \
      --padding 5G      \
      --output /mnt/usb

    # when /mnt/usb has 5G left, you'll be prompted for the next HDD


How it Works
------------


1. all files are found, and catalogued with their filesize (in bytes).

2. `--output` is searched for files that do not exist on the src-side.
  these files are deleted.

3. If srcfile timestamp/filesize differs from dstfile, re-copy the file
   to dst. *(see ``df -h file``)*

4. If the next copied file would exceed drive's padding, then prompt for
   another hard-drive (or a different medium).


To restore files, simply copy everything from your volumes back onto the source. 
File hierarchy is kept intact.

