
Safety
======


* [2020/08/22] `resolved?` numbers are getting lost at the rotation.
  in ineteractive test. 3, 7, 8 should be used in last backup.
  instead we have an extra cycle, and then the last cycle doesn't copy the right files.

* [2020/08/22] `resolved?` Reconciler method should be extracted, handling both identifiaction
  and deletion of files. Optimizations can be made by:

   (reconciliation)
   1. determine total size of all present files not in total list of files
   2. delete them
   3. determine total size of destdir (after delete). This is your volume capacity.
   4. `reduce/sum` over copyfiles until volume capacity reached. This is estimated last index (progress calculated based on this).
   5. delete all files on drive, that come after that last index.

   (other)
   * we must keep a reference to our expected last index.
     if we don't reach it, delete files later on the list (by earliest encountered)
     in each loop until we run out of room.
     (we need to make sure that 2x disks do not have different versions of the same file)

...

* [2020/08/09] `resolved?` on file copy error because disk is full,
  prompt for disk rollover. (files sizes vary between filesystems,
  especially if they are using compression)

* [2020/08/09] `resolved?` files not being deleted from dst when used
  on fileserver, but seems to be while testing interactively.
  subdirectories maybe? identify and fix.

* [2020/08/07] files submitted to srcpaths do not work 
  (either fix, or disallow)

* [2020/08/07] verify and warn if the same disk is mounted
  on disk rollover

* [2020/08/07] `wip` code and tests are really horrible. maybe rewrite?

* [2020/08/07] `resolved?` rewrite as queue/consumer so faster (accept num workers on cli)

* [2020/08/22] `resolved?` _volume_delete_extraneous only deletes files under destdir.
  It ignores files copied elsewhere on the drive. 

  This is good, but volume capacity calculation should be
  run following this operation, and use amount of space left
  on disk at that point.

* [2020/08/22] `resolved?` These methods need to be extracted into classes.
  The whole thing needs to be restrured.

* [2020/08/22] Consider emitting a unix signal, writing to a socket or something
  when we are ready to switch the device. It would be good to automate this for tests,
  and also for end-user automation.

