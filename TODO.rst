
Safety
======

x [2020/08/29] a commandline tool to (quickly) verify that a 
  backup has actually copied everything it was supposed to.

x [2020/08/28] move reslovers to a multiprocess producer pattern.
  Despite GC, memory is not being freed for OS.

* [2020/08/30] the memory does not spike until files start getting copied.
  I believe the culprit is now the lists that maintain wip copyfiles.
  If we were to always re-assign the variable to a tuple instead,
  that might address our memory issues.

* [2020/08/07] files submitted to srcpaths do not work 
  (either fix, or disallow)

* [2020/08/07] verify and warn if the same disk is mounted
  on disk rollover

* [2020/08/22] Consider emitting a unix signal, writing to a socket or something
  when we are ready to switch the device. It would be good to automate this for tests,
  and also for end-user automation.

* [2020/08/23] add index file, maybe write to it every 50 
  completed copies to keep disk writes to a minimum?

