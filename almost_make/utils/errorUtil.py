#!/usr/bin/python3

from almost_make.utils.printUtil import *

SILENT = False
STOP_ON_ERROR = True

# On error, report [message] depending on [SILENT] and [STOP_ON_ERROR]
def reportError(message):
    if not SILENT or STOP_ON_ERROR:
        cprint(str(message) + "\n", "RED", file=sys.stderr)
    
    if STOP_ON_ERROR:
        print ("Stopping.")
        sys.exit(1)

# Option-setting functions
def setStopOnError(stopOnErr):
    global STOP_ON_ERROR
    STOP_ON_ERROR = stopOnErr

def setSilent(silent):
    global SILENT
    SILENT = silent 
