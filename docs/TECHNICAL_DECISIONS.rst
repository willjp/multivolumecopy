
Technical Decisions
===================


.. contents::  Table of Contents


Why multiprocessing instead of acyncio/threading?
--------------------------------------------------

TL;DR - To keep memory consumption low.

Processes are assigned a chunk of usable memory (the heap).
When that chunk of memory is filled, the OS expands the memory allocated to the heap.
Python does not release this memory until the process that owns it is terminated.


Why spawn multiprocessing workers instead of fork?
--------------------------------------------------

Fork copies all of the memory from the parent process. Our worker processes
only need to know about the file that is being passed to them in the queue.
This keeps memory usage down.

