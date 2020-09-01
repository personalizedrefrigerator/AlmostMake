#!/usr/bin/python3

# Support for globbing paths, given a relevant directory.
# See: https://www.gnu.org/software/bash/manual/bash.html#Filename-Expansion
#
# Note that https://docs.python.org/3/library/glob.html may also be useful...
#           It seems, however, that as of Python 3.8, glob only supports globbing
#           with paths relative to the current directory (os.getcwd()), not our
#           custom [cwd] variable.

import os, glob

def glob(text, cwd):
    # First, determine if the text needs to be/can be globbed.
    canGlob = False

    inQuote = None
    escaped = False
    for char in text:
        if char in { '"', "'" } and not escaped:
            if inQuote == char:
                inQuote = None
            elif inQuote == None:
                inQuote = char
        elif char == '\\' and not escaped:
            escaped = True
        elif escaped:
            escaped = False
        elif not inQuote:
            if char in { ' ' }:
                return [ text ]
            elif char in { '[', ']', '*' }:
                canGlob = True
    
    text = os.path.expanduser(text)
    return [ text ]