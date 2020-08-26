#!/usr/bin/python3

import shlex, os, re
import subprocess

PRECEDENCE_LIST = [ '||', '&&', ";", '|', '>', '2>&1', '&' ]
TWO_ARGUMENTS = { "||", "&&", ";", '|', '>' }
PIPE_OUT_PERMISSIONS = 0o660

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

# Returns the exit status of the command specified by args
# (e.g. [ 'ls', '-la' ]). If the command is in [customCommands],
# however, run the custom command, rather than the system command.
def rawRun(args, customCommands={}, flags=[]):
    stderrOut = None # Default
    if "2>&1" in flags:
        out = subprocess.STDOUT

    if "&" in flags:
        print("& flag not implemented!")
        
    if len(args) == 0:
        return 0
        
    command = args[0].strip()

    if command in customCommands:
        result = customCommands[command](args, flags)
        
        if type(result) == bool:
            if result:
                return 0
            return 1
        return result
    
    proc = subprocess.run(args, stderr=stderrOut)   
    return proc.returncode

def evalCommand(orderedCommand, customCommands={}, flags=[]):
    if len(orderedCommand) == 0:
        return False
    if type(orderedCommand[0]) == str:
        return rawRun(orderedCommand, customCommands, flags)
    elif len(orderedCommand) == 2:
        recurseFlags = flags.copy()
        flags.append(orderedCommand)

        return evalCommand(orderedCommand[0], customCommands, recurseFlags)
    elif len(orderedCommand) == 3:
        operator = orderedCommand[1]

        if operator == '|':
            # Cache file descriptors that point to stdin and stdout
            stdinSave = os.dup(0)
            stdoutSave = os.dup(1)

            fdIn, fdOut = os.pipe()
            
            # Point stdout to fdIn.
            os.dup2(fdOut, 1)
            os.close(fdOut)

            left = evalCommand(orderedCommand[0], customCommands, flags)

            # Point stdout to stdoutSave.
            os.dup2(stdoutSave, 1)
            os.close(stdoutSave)

            # Make stdin point to fdOut.
            os.dup2(fdIn, 0)
            os.close(fdIn)

            # Run right with given stdin, stdout.
            right = evalCommand(orderedCommand[2], customCommands, flags)
            
            # Restore stdin
            os.dup2(stdinSave, 0)
            os.close(stdinSave)

            return right
        elif operator == '>':
            outfd = os.open(os.path.abspath(" ".join(orderedCommand[2])), os.O_WRONLY | os.O_CREAT, mode=PIPE_OUT_PERMISSIONS)
            stdoutSave = os.dup(1)

            # Point stdout to outfd.
            os.dup2(outfd, 1)
            os.close(outfd)

            # We need to wait for the process to finish.
            if '&' in flags:
                flags = [ i for i in flags if i != '&' ]

            left = evalCommand(orderedCommand[0], customCommands, flags)

            # Point stdout back to our saved file descriptor.
            os.dup2(stdoutSave, 1)
            os.close(stdoutSave)

            return left
        elif operator == '||' or operator == '&&':
            left = evalCommand(orderedCommand[0], customCommands, flags)

            if left and (operator == '||' and left != 0 or operator == '&&' and left == 0):
                right = evalCommand(orderedCommand[2], customCommands, flags)

                return right
            return left
        elif operator == ';':
            left = evalCommand(orderedCommand[0], customCommands, flags)
            right = evalCommand(orderedCommand[2], customCommands, flags)

            if left != 0:
                return left
            return right
        else:
            raise SyntaxError("Unknown separator, %s." % operator)
    else:
        raise SyntaxError("Too many parts to expression, %s" % str(orderedCommand))

# Run a filter on shlex's split output list.
# E.g. Map [ ... '2', '>&', '1', ...] to
# [... '2>&1' ...].
def filterSplitList(splitString):
    result = []
    buff = []

    for part in splitString:
        part = part.strip()
        buff.append(part)

        if part == '2':
            result.extend(buff[:len(buff) - 1])
            buff = [ '2' ]
        elif buff == ['2', '>&', '1']:
            result.append('2>&1')
            buff = []
    result.extend(buff)

    return result

# Run the POSIX-like shell command [commandString]. Define
# any additional commands through [customCommands].
def runCommand(commandString, customCommands = {}):
    # Note: punctuation_chars=True causes shlex to cluster ();&| runs.
    #       For example, a && b -> ['a', '&&', 'b'], instead of ['a', '&', '&', 'b'].
    portions = filterSplitList(list(shlex.shlex(commandString, posix=True, punctuation_chars=True)))
    ordered = cluster(portions) # Convert ['a', '&&', 'b', '||', 'c'] into
                                #       [[['a'], '&&', ['b']], '||', ['c']]
    evalCommand(ordered, customCommands)

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
