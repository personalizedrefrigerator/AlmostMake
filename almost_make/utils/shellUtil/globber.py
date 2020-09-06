#!/usr/bin/python3

# Support for globbing paths, given a relevant directory.
# See: https://www.gnu.org/software/bash/manual/bash.html#Filename-Expansion
#
# Note that https://docs.python.org/3/library/glob.html may also be useful...
#           It seems, however, that as of Python 3.8, glob only supports globbing
#           with paths relative to the current directory (os.getcwd()), not our
#           custom [cwd] variable. As such, we are using 
#           https://docs.python.org/3.7/library/fnmatch.html#module-fnmatch
#           instead.
# To-dos:
#  * Recursive globbing support with **

import os, fnmatch, re

HAS_PATTERN = re.compile(r"([^\\]{2})*[\*\[\]]")

# Glob the contents of [text] if it appears to be a path using
# patterns supported by Python's fnmatch module. If no matches
# are found and [defaultCase] is given, return [defaultCase].
# Otherwise, return [text], possibly with tilde-expansion.
def glob(text, cwd, defaultCase = None):
    # First, determine if the text needs to be/can be globbed.
    canGlob = False
    canSimplify = False

    escaped = False

    # Does it look like a path?
    for char in text:
        if char in { '"', "'" } and not escaped:
            return [ text ]
        elif char == '\\' and not escaped:
            escaped = True
        elif escaped:
            escaped = False
        elif char in { ' ' }:
            return [ text ]
        elif char in { '[', ']', '*' }:
            canGlob = True
        elif char in { '~', '/' }:
            canSimplify = True
    
    matchingPaths = []

    # Expand the path. Note that on Windows, normcase converts
    # its argument to a Windows-like path. On other operating systems,
    # it does nothing.
    if canSimplify:
        text = os.path.normcase(os.path.expanduser(text))
    
    if canGlob:
        parts = text.split(os.sep)
        fringe = [(0, cwd)]
        
        while len(fringe) > 0:
            depth, path = fringe.pop()
            matches = []

            for currentDepth in range(depth, len(parts)):
                part = parts[currentDepth]
                if HAS_PATTERN.search(part) == None:
                    path = os.path.join(path, part)

                    # If we are trying to match in a non-existent place, give up on 
                    # this path!
                    if not os.path.exists(path):
                        matches = []
                        break
                    else:
                        matches = [ path ]
                    continue
                
                # We can only list files in directories!
                if not os.path.isdir(path):
                    matches = []
                    break
                
                potentialMatches = os.listdir(path or '.')
                potentialMatches = [ os.path.join(path, match) for match in potentialMatches ] # listdir just has filenames... We need the leading [path]...
                part = os.path.join(path, part)

                matches = fnmatch.filter(potentialMatches, part)

                searchWithDepth = currentDepth + 1
                if part.endswith('**'): # If recursive-globbing, we need to start at the same depth for all sub-directories...
                    searchWithDepth = currentDepth
                
                fringe.extend(zip([searchWithDepth] * len(matches), matches))
            
            if os.path.isabs(text):
                matchingPaths.extend([ os.path.normpath(match) for match in matches ])
            else:
                matchingPaths.extend([ os.path.relpath(match, os.path.abspath(cwd)) for match in matches ])
    
    # If we didn't find any matches, just return the text we were given (perhaps with 
    # tilde-expansion).
    if len(matchingPaths) == 0:
        if defaultCase == None:
            matchingPaths = [ text ]
        else:
            matchingPaths = defaultCase

    return matchingPaths

# Run directly? Run tests!
if __name__ == "__main__":
    testDir = os.path.dirname(__file__)

    if testDir != '':
        os.chdir(testDir)
    
    def canonicalizePath(path):
        return os.path.abspath(
            os.path.realpath(
                os.path.normcase(
                    os.path.normpath(
                        os.path.expanduser(path)
                    )
                )
            )
        )

    def assertEql(a, b, message):
        if a != b:
            raise Exception("%s != %s (%s)" % (str(a), str(b), message))
    
    def assertHas(collection, item, message):
        if collection == None:
            raise Exception("%s is None (%s)" % (str(collection), message))
        if not item in collection:
            raise Exception("not %s in %s holds. (%s)" % (str(item), str(collection), message))
    
    def assertHasPath(pathCollection, path, message):
        assertHas(pathCollection, os.path.normcase(os.path.normpath(path)), message)

    def assertPathListsEql(a, b, message):
        pathSetA = set()
        pathSetB = set()

        for path in a:
            pathSetA.add(canonicalizePath(path))
        
        for path in b:
            pathSetB.add(canonicalizePath(path))
        
        assertEql(pathSetA, pathSetB, message)

    assertEql(glob("willNotMatch", "."), ["willNotMatch"], "A glob that does nothing!")
    assertPathListsEql(glob("*.txt", "."), ["*.txt"], "A glob that does nothing (but is a valid glob)!")
    assertHas(glob("*.py", "."), "globber.py", "Finding this script with a glob!")
    assertHas(glob("globber.*", "."), "globber.py", "Finding this script with a different glob!")
    assertHas(glob("globber.*", os.path.abspath('.')), "globber.py", "Finding this script with a different glob (and differently-formatted path)!")
    assertHasPath(glob("../*.py", "."), "../printUtil.py", "Finding another script with a glob.")
    assertHasPath(glob("../../*.py", "."), "../../cli.py", "Finding yet another script with a glob.")
    assertHasPath(glob("../../*/*.py", "."), "../printUtil.py", "Finding yet another script with a glob.")
    assertHasPath(glob("../../*/shellUtil", "."), ".", "Finding a folder with a glob.")
    assertHasPath(glob("../../**/runner.py", "."), "runner.py", "Recursive globbing.")
    assertHasPath(glob("**/viaDot.*", "../../tests/"), "testMisc/includeTest/viaDot.mk", "More recursive globbing.")