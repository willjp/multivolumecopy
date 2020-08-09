
Safety
======


* [2020/08/09] on file copy error because disk is full,
  prompt for disk rollover. (files sizes vary between filesystems,
  especially if they are using compression)

* [2020/08/09] files not being deleted from dst when used
  on fileserver, but seems to be while testing interactively.
  subdirectories maybe? identify and fix.

* [2020/08/07] files submitted to srcpaths do not work 
  (either fix, or disallow)

* [2020/08/07] verify and warn if the same disk is mounted
  on disk rollover

* [2020/08/07] code and tests are really horrible. maybe rewrite?

* [2020/08/07] rewrite as queue/consumer so faster (accept num workers on cli)

