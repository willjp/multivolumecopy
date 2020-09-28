
Todo
====

* [2020/09/13] add option to configure number of workers
  on commandline. Add warning about memory consumption with example.
  (10TB w/ 2x workers, ZFS eats remaining 8GB ram)

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

