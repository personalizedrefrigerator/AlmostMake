#!/usr/bin/python3

# Support for globbing paths, given a relevant directory.
# See: https://www.gnu.org/software/bash/manual/bash.html#Filename-Expansion
#
# Note that https://docs.python.org/3/library/glob.html may also be useful...
#           It seems, however, that as of Python 3.8, glob only supports globbing
#           with paths relative to the current directory (os.getcwd()), not our
#           custom [cwd] variable.

import os, fnmatch, re

HAS_PATTERN = re.compile(r"([^\\]{2})*[\*\[\]]")

def glob(text, cwd):
    # First, determine if the text needs to be/can be globbed.
    canGlob = False
    canSimplify = False

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
            elif char in { '~', '/' }:
                canSimplify = True
    matchingPaths = []

    # Simplify and expand the path.
    if canSimplify:
        text = os.path.normcase(os.path.normpath(os.path.expanduser(text)))
    
    if canGlob:
        parts = os.sep.split(text)
        fringe = [(0, '')]
        
        while len(fringe) > 0:
            path, depth = fringe.pop()
            matches = []
            for currentDepth in range(depth, len(parts)):
                part = parts[currentDepth]
                if HAS_PATTERN.match(part) == None:
                    path = os.path.join(path, part)

                    if not os.path.exists(path):
                        matches = []
                        break
                    continue
                potentialMatches = os.listdir(path or '.')
                matches = fnmatch.filter(potentialMatches, part)
                fringe.extend(zip([currentDepth + 1] * len(matches), matches))
            matchingPaths.extend(matches)

    
    if len(matchingPaths) == 0:
        matchingPaths = [ text ]

    return matchingPaths