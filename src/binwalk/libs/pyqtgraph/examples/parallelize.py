# -*- coding: utf-8 -*-
import initExample ## Add path to library (just for examples; you do not need this)
import numpy as np
import pyqtgraph.multiprocess as mp
import pyqtgraph as pg
import time

print( "\n=================\nParallelize")

## Do a simple task: 
##   for x in range(N):
##      sum([x*i for i in range(M)])
##
## We'll do this three times
##   - once without Parallelize
##   - once with Parallelize, but forced to use a single worker
##   - once with Parallelize automatically determining how many workers to use
##

tasks = range(10)
results = [None] * len(tasks)
results2 = results[:]
results3 = results[:]
size = 2000000

pg.mkQApp()

### Purely serial processing
start = time.time()
with pg.ProgressDialog('processing serially..', maximum=len(tasks)) as dlg:
    for i, x in enumerate(tasks):
        tot = 0
        for j in xrange(size):
            tot += j * x
        results[i] = tot
        dlg += 1
        if dlg.wasCanceled():
            raise Exception('processing canceled')
print( "Serial time: %0.2f" % (time.time() - start))

### Use parallelize, but force a single worker
### (this simulates the behavior seen on windows, which lacks os.fork)
start = time.time()
with mp.Parallelize(enumerate(tasks), results=results2, workers=1, progressDialog='processing serially (using Parallelizer)..') as tasker:
    for i, x in tasker:
        tot = 0
        for j in xrange(size):
            tot += j * x
        tasker.results[i] = tot
print( "\nParallel time, 1 worker: %0.2f" % (time.time() - start))
print( "Results match serial:  %s" % str(results2 == results))

### Use parallelize with multiple workers
start = time.time()
with mp.Parallelize(enumerate(tasks), results=results3, progressDialog='processing in parallel..') as tasker:
    for i, x in tasker:
        tot = 0
        for j in xrange(size):
            tot += j * x
        tasker.results[i] = tot
print( "\nParallel time, %d workers: %0.2f" % (mp.Parallelize.suggestedWorkerCount(), time.time() - start))
print( "Results match serial:      %s" % str(results3 == results))

