"""
Multiprocessing utility library
(parallelization done the way I like it)

Luke Campagnola
2012.06.10

This library provides:

  - simple mechanism for starting a new python interpreter process that can be controlled from the original process
    (this allows, for example, displaying and manipulating plots in a remote process
    while the parent process is free to do other work)
  - proxy system that allows objects hosted in the remote process to be used as if they were local
  - Qt signal connection between processes
  - very simple in-line parallelization (fork only; does not work on windows) for number-crunching

TODO:
    allow remote processes to serve as rendering engines that pass pixmaps back to the parent process for display
    (RemoteGraphicsView class)
"""

from .processes import *
from .parallelizer import Parallelize, CanceledError
from .remoteproxy import proxy