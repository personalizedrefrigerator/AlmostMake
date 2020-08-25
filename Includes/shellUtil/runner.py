#!/usr/bin/python3

import shlex, os, re
import subprocess

PRECEDENCE_LIST = [ '||', '&&', ";", '|', '2>&1', '&' ]
TWO_ARGUMENTS = { "||", "&&", ";", '|' }

# Get the number of [char] at the beginning of [text].
def getStartingCount(text, char):
    pos = 0
    
    while pos < len(text) and text[pos] == char:
        pos += 1
    
    return pos

# Get the number of [char] at the end of [text].
def getEndingCount(text, char):
    pos = len(text) - 1
    count = 0

    while pos >= 0 and text[pos] == char:
        pos -= 1
        count += 1

    return count

# Remove empty strings from a string array.
def removeEmpty(array):
    result = []

    for val in array:
        if val != "":
            result.append(val)
    
    return result

# Get the number of pairs of parentheses that
# surround the entirety of [splitText].
def getParenCount(splitText):
    if len(splitText) == 0:
        return 0

    startingParenCount = getStartingCount(splitText[0], '(')
    endingParenCount = getEndingCount(splitText[len(splitText) - 1], ')')
    return min(startingParenCount, endingParenCount)

# Remove parentheses that surround the contents
# of the splitText array, [buff].
def unwrapParens(buff):
    if len(buff) < 2:
        return buff
    result = []
    parenCount = getParenCount(buff)

    result.append(re.sub(r"^[(]{" + str(parenCount) + r"}", "", buff[0]))

    for i in range(1, len(buff) - 1):
        result.append(buff[i])

    result.append(re.sub(r"[)]{" + str(parenCount) + r"}$", "", buff[len(buff) - 1]))

    return removeEmpty(result)

# Cluster elements in [splitText] based on precedence.
# E.g. ['a', '||', 'b', '&&', 'c', '-l'] -> [['a'], '||', [['b'], '&&', ['c', '-l']]].
def cluster(splitText, level=0):
    result = []
    buff = []
    
    if getParenCount(splitText) > 0:
        level = 0

    splitText = unwrapParens(splitText)
    
    if level >= len(PRECEDENCE_LIST):
        return splitText

    searchFor = PRECEDENCE_LIST[level]

    if not searchFor in TWO_ARGUMENTS:
        if len(splitText) == 0:
            return splitText
        
        if splitText[len(splitText) - 1] == searchFor:
            return [ cluster(splitText[:len(splitText) - 1], level + 1), searchFor ]
        return cluster(splitText, level + 1)

    parenLevel = 0
    addedChunks = 0
    part = []

    for chunk in splitText:
        if chunk.startswith("("):
            parenLevel += getStartingCount(chunk, '(')
        elif chunk.startswith(")"):
            parenLevel -= getEndingCount(chunk, ')')

            if parenLevel == 0 and len(buff) > 0:
                buff.append(chunk)
                
                continue
        elif parenLevel == 0:
            if chunk == searchFor and addedChunks == 0:
                result.append(cluster(buff, level + 1))
                buff = []
                addedChunks += 1
                continue
        buff.append(chunk)
    if addedChunks > 0:
        result.append(searchFor)
        result.append(cluster(buff, level))
    else:
        result.extend(cluster(buff, level + 1))
    return result

def evalCommand(orderedCommand, flags=[]):
    if len(orderedCommand) == 0:
        return False
    if type(orderedCommand[0]) == str:
        return rawRun(orderedCommand, flags)
    elif len(orderedCommand) == 2:
        return evalCommand(orderedCommand[0], flags.copy().append(orderedCommand[1]))
    elif len(orderedCommand) == 3:
        operator = orderedCommand[1]

        if operator == '||':
            leftResult = 0 # To-do!!!
    else
        raise SyntaxError("Too many parts to expression, %s" % str(orderedCommand))



def runCommand(commandString):
    # Note: punctuation_chars=True causes shlex to cluster ();&| runs.
    #       For example, a && b -> ['a', '&&', 'b'], instead of ['a', '&', '&', 'b'].
    portions = list(shlex.shlex(commandString, posix=True, punctuation_chars=True))
    ordered = cluster(portions) # Convert ['a', '&&', 'b', '||', 'c'] into
                                #       [[['a'], '&&', ['b']], '||', ['c']]
    evalCommand(ordered)
if __name__ == "__main__":
    # Run directly? Run tests!
    print("Testing runner.py...")
    
    def assertEql(left, right, description):
        if left != right:
            raise Exception("%s != %s (%s)" % (left, right, description)) # We WANT to see this. Don't catch.
    
    assertEql("1", "1", "This should always pass. A test of assertEql.")
    assertEql(['1', ['2', '3']], ['1', ['2', '3']], "We rely on this for our tests.")
    assertEql(cluster([]), [], "Empty cluster")
    assertEql(cluster(['a']), ['a'], "Identity cluster")
    assertEql(cluster([ "a", "||", "b"]), [['a'], '||', ['b']], "Simple cluster test.")
    assertEql(cluster([ "a", "&&", "b" ]), [['a'], '&&', ['b']], "Cluster with ands")
    assertEql(cluster([ "a", "&&", "b", "||", "c" ]), [[['a'], '&&', ['b']], '||', ['c']], "Precedence clustering")
    assertEql(cluster([ "a", "||", "b", "||", "c" ]), [["a"], "||", [["b"], "||", ["c"]]], "Parentheses")
    assertEql(cluster([ "(", "a", "||", "b", ")" ]), [["a"], "||", ["b"]], "Outside parentheses.")
    assertEql(cluster([ "a", "&" ]), [ ['a'], '&' ], "Single argument operator.")
    assertEql(cluster([ "b", "2>&1" ]), [ ['b'], '2>&1' ], "Pipe err to out")
    assertEql(cluster([ 'c', '|', 'd', '||', '(', 'f', '&&', 'g', '||', '(', 'h', '))']), 
            [[ ['c'], '|', ['d'] ], '||', [ [ ['f'], '&&', ['g'] ], '||', ['h'] ] ], "More complicated; nested parentheses")
    assertEql(cluster([ '((((((((((', 'a', '))))))))))' ]), ['a'], "Lots of parentheses")
