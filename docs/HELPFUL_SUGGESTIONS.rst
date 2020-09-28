
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

Decrease the number of workers for this program (ex: `multivolumecopy --workers 1 ...`).
For example, on a 10T server with 32G ram and 2x workers ZFS consumes about 28G of ram for me.
This will get freed up as required by the OS.

