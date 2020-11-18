
Helpful Suggestions
===================

This is mostly a collection of traps I personally ran into.
If you try this script and find some gotchas, let me know and I'll add them to the list.


du and df report different disk usage
-------------------------------------

Small differences are to be expected here.
If you're seeing large differences between your backup-size and your reported HDD size, 
try running fsck on your device (ex: `fsck -y /dev/da0p1` ).
No, Seriously - I freed up 4TB on a 6TB ufs2 partition this way.

memory consumption is high with ZFS
-----------------------------------

Firstly, if running FreeBSD, check `ARC` memory consumption within top (under memory).
By default, zfs is configured to use the larger of all-but 1GB/5/8 of available ram.
You can adjust this by configuring `vfs.zfs.arc_max` . See https://www.freebsd.org/doc/handbook/zfs-advanced.html .

If you're on a server with limited resources, reduce the number of workers (ex: `multivolumecopy --workers 1 ...`).
