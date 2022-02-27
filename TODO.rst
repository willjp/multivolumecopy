
Todo
====

* [2020/09/13] large backups use an unecessary amount of ram to
  hold serialized json jobfile. Instead, store one copyfile per line
  and refer to the indexes. (10MB json file serialized is ~400MB in ram!)

* [2020/08/07] files submitted to srcpaths do not work
  (either fix, or disallow)

* [2020/08/07] verify and warn if the same disk is mounted
  on disk rollover

* [2020/08/22] Consider emitting a unix signal, writing to a socket or something
  when we are ready to switch the device. It would be good to automate this for tests,
  and also for end-user automation.

* [2020/08/23] add index file, maybe write to it every 50
  completed copies to keep disk writes to a minimum?

* [2020/09/13] use of -i with -si breaks reconciler
  (deletes files that it should not before copy starts)
  (do I know this? or was it just the 2TB limit because fsck was needed?)

* [2022/02/26] Additional reports or logging would be useful.
  Before deleting/copying, consider printing out est-deletes and est-copied.
  After filling a volume, print what was removed/unchanged/written.

* [2022/02/26] Dump the jobfile, start-index, last-index on each volume once it's full.
  (so that any disk can be used to determine if the file exists in the backup)
  The jobfile/start-stop-indexfile should be the first files copied to a disk (to ensure it is present).
  The stop-index should then be able to be appended to the `start-stop-indexfile` safely,
  independently of any set padding.

* [2022/02/26] CopyOptions can compare on modified-time, bytes, or checksums.
  This should be configurable on the cli.

* [2022/02/26] on SIGINFO, print the current progress (then can check progress via ssh)

* [2022/02/27] Since the goal of --device-padding is gracefully handling a new backup HDD
  without causing deletes across all backup drives (with a slightly different number of bytes).
  It would be better to set a fixed-size of the backup in bytes than an offset.

