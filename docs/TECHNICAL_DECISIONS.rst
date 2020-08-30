
Technical Decisions
===================


.. contents::  Table of Contents


Why multiprocessing instead of acyncio/threading?
--------------------------------------------------

Processes are also allocated blocks of memory by the OS, that get freed when they are killed/die.
Even when memory is garbage-collected (python-3.7/FreeBSD-12.0), the block of memory 
allocated to the python process does not release this memory while the process lives.

Before multiprocessing, backing up my 10TB fileserver consumed more than 10GB of ram.
There are also other quirks (json parsing in particular), this is my ham-fisted attempt
to keep the memory usage as low as possible.

If you have any suggestions, please create an issue let me know.


Why spawn multiprocessing workers instead of fork?
--------------------------------------------------

Fork copies all of the memory from the parent process. Our worker processes
only need to know about the file that is being passed to them in the queue.
This keeps memory usage down.

