#!/usr/bin/python3

import shlex, os, re
import subprocess

PRECEDENCE_LIST = [ '||', '&&', ";", '|', '>', '2>&1', '&' ]
TWO_ARGUMENTS = { "||", "&&", ";", '|', '>' }
PIPE_OUT_PERMISSIONS = 0o660

SPACE_CHARS = re.compile("\\s")

SYSTEM_SHELL = "system-shell"
USE_SYSTEM_PIPE = "use-system-pipe"

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

# Remove leading and trailing quotation marks from the given text.
# E.g. "a and b" -> a and b, "a and b' -> "a and b'. Remove at most 1.
def stripQuotes(text):
    if len(text) < 2:
        return text
    result = []
    firstChar = text[0]
    lastChar = text[len(text) - 1]
    
    if firstChar != lastChar:
        return text
    
    if firstChar in { '"', "'" }:
        return text[1 : len(text) - 1]
    return text

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

# Collapse a clustered command back into a string.
def collapse(clustered):
    result = ""
    
    if len(clustered) == 0:
        return result
    elif type(clustered[0]) == str:
        for part in clustered:
            if SPACE_CHARS.search(part.strip()) != None:
                result += " " + shlex.quote(part)
            else:
                result += " " + part
        return result.strip()
    
    result = " ".join([ collapse(elem) for elem in clustered ])
    
    return result.strip()

# Returns the exit status of the command specified by args
# (e.g. [ 'ls', '-la' ]). If the command is in [customCommands],
# however, run the custom command, rather than the system command.
# If 'system-shell' is in flags, run this portion of the command in the 
# system's shell. This is useful in systems that support, say,
# the '|' operator, but the file-descriptor piping method fails.
# At the time of this writing, this was the case with iOS's a-Shell.
def rawRun(args, customCommands={}, flags=[], stdin=None, stdout=None, stderr=None):
    if "2>&1" in flags:
        stderr = stdout

    if "&" in flags:
        print("& flag not implemented!")
        
    if len(args) == 0:
        return 0
    
    sysShell = SYSTEM_SHELL in flags or None
    
    command = args[0].strip()

    if command in customCommands:
        result = customCommands[command](args, flags, stdin, stdout, stderr)
        
        if type(result) == bool:
            if result:
                return 0
            return 1
        if result is None:
            return 0
        return result
    
    proc = subprocess.run(args, stdin=stdin, stdout=stdout, stderr=stderr, shell=sysShell, close_fds=False)
    return proc.returncode

def evalCommand(orderedCommand, customCommands={}, flags=[], stdin=None, stdout=None, stderr=None):
    if len(orderedCommand) == 0:
        return False
    if type(orderedCommand[0]) == str:
        return rawRun(orderedCommand, customCommands, flags, stdin=stdin, stdout=stdout, stderr=stderr)
    elif len(orderedCommand) == 2:
        recurseFlags = flags.copy()
        flags.append(orderedCommand)

        return evalCommand(orderedCommand[0], customCommands, recurseFlags, stdin=stdin, stdout=stdout, stderr=stderr)
    elif len(orderedCommand) == 3:
        operator = orderedCommand[1]

        # If we are to use the system's built-in pipe, we need to stop here.
        # Collapse the input and run it.
        if USE_SYSTEM_PIPE in flags and (operator == '|' or operator == '>'):
            runFlags = flags.copy()
            runFlags.append(SYSTEM_SHELL) # Use the system's shell to interpret.
            
            return rawRun(collapse(orderedCommand), customCommands, runFlags, stdin=stdin, stdout=stdout, stderr=stderr)

        if operator == '|':
            fdIn, fdOut = os.pipe()

            left = evalCommand(orderedCommand[0], customCommands, flags, stdin=stdin, stdout=fdOut, stderr=stderr)
            os.close(fdOut)

            # Run right with given stdin, stdout.
            right = evalCommand(orderedCommand[2], customCommands, flags, stdin=fdIn, stdout=stdout, stderr=stderr)
            
            os.close(fdIn)

            return right
        elif operator == '>':
            outfd = os.open(os.path.abspath(" ".join(orderedCommand[2])), os.O_WRONLY | os.O_CREAT, mode=PIPE_OUT_PERMISSIONS)

            # We need to wait for the process to finish.
            if '&' in flags:
                flags = [ i for i in flags if i != '&' ]

            left = evalCommand(orderedCommand[0], customCommands, flags, stdin=stdin, stdout=outfd, stderr=stderr)

            os.close(outfd)

            return left
        elif operator == '||' or operator == '&&':
            left = evalCommand(orderedCommand[0], customCommands, flags, stdin=stdin, stdout=stdout, stderr=stderr)

            if left and (operator == '||' and left != 0 or operator == '&&' and left == 0):
                right = evalCommand(orderedCommand[2], customCommands, flags, stdin=stdin, stdout=stdout, stderr=stderr)

                return right
            return left
        elif operator == ';':
            left = evalCommand(orderedCommand[0], customCommands, flags, stdin=stdin, stdout=stdout, stderr=stderr)
            right = evalCommand(orderedCommand[2], customCommands, flags, stdin=stdin, stdout=stdout, stderr=stderr)

            if left != 0:
                return left
            return right
        else:
            raise SyntaxError("Unknown separator, %s." % operator)
    else:
        raise SyntaxError("Too many parts to expression, %s" % str(orderedCommand))

def shSplit(text):
    escaped = False
    inQuote = None
    result = []
    buff = ""
    
    # Split by spaces and parentheses (and other punctuation chars...).
    for char in text:
        buff += char
        if char in { '"', "'" }:
            if inQuote == char:
                inQuote = None
            elif inQuote == None:
                inQuote = char
        elif char in [ '(', ')', '|', '&', '>', ';', ' ', '\t', '\n' ] and inQuote == None:
            result.append(stripQuotes(buff[:len(buff)-1]))
            result.append(char)
            buff = ""
    
    result.append(stripQuotes(buff))
    
    buff = ''
    filtered = []
    
    
    # Remove spaces, clump parentheses.
    for part in result:
        part = part.strip()
        
        if part != '':
            # If the direction of parentheses switches...
            if part == '(' and ')' in buff  or  part == ')' and '(' in buff:
                filtered.append(buff)
                buff = ''
        
            if part.startswith('(') or part.endswith(')'):
                buff += part
            elif buff != "":
                filtered.append(buff)
                buff = ''
                filtered.append(part)
            else:
                filtered.append(part)
    if buff != '':
        filtered.append(buff)
    
    return filtered
                

# Run a filter on lex's split output list.
# E.g. Map [ ... '2', '>&', '1', ...] to
# [... '2>&1' ...].
def filterSplitList(splitString):
    result = []
    buff = []
    
    splitString = splitString.copy()
    splitString.reverse()

    for part in splitString:
        buff.append(part)

        if buff == ['|', '|']:
            result.append('||')
            buff = []
        elif buff == ['&', '&']:
            result.append('&&')
            buff = []
        elif buff == ['>', '>']:
            result.append('>>')
            buff = []
        elif part in [ '|', '&', '>' ]:
            result.extend(buff[:len(buff) - 1])
            buff = [ part ]
    
    result.extend(buff)
    result.reverse() # Reverse so that we have ['&', '&', '&'] -> ['&', '&&'], not ['&&', '&']
    
    splitString = result
    result = []
    buff = []
    
    # A second pass for parts that may share characters with those above.
    for part in splitString:
        buff.append(part)
        if buff == ['2', '>', '&', '1']:
            result.append('2>&1')
            buff = []
        elif part == '2':
            result.extend(buff[:len(buff) - 1])
            buff = [ part ]
    result.extend(buff)
    
    return result

# Run the POSIX-like shell command [commandString]. Define
# any additional commands through [customCommands].
def runCommand(commandString, customCommands = {}, flags = []):
    # Note: punctuation_chars=True causes shlex to cluster ();&| runs.
    #       For example, a && b -> ['a', '&&', 'b'], instead of ['a', '&', '&', 'b'].
    #       It also, however, clusters runs we don't want, like a &&& b -> ['a', '&&&', 'b'].
    #       This, however, split 'a/b/c' into ['a', '/', 'b', '/', 'c'], which we REALLY DON'T WANT.
    #       As such, we're using 'shSplit' here.
    portions = filterSplitList(shSplit(commandString))
    ordered = cluster(portions) # Convert ['a', '&&', 'b', '||', 'c'] into
                                #       [[['a'], '&&', ['b']], '||', ['c']]
    return evalCommand(ordered, customCommands, flags)

if __name__ == "__main__":
    # Run directly? Run tests!
    print("Testing runner.py...")
    
    def assertEql(left, right, description, alternates=None):
        if left != right or alternates and left in alternates:
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
    assertEql(filterSplitList([]), [], "Empty split list")
    assertEql(filterSplitList([ '2', '>', '&', '1' ]), [ '2>&1' ], "Split to error re-direction.")
    assertEql(filterSplitList([ '1', '|', '|', '2' ]), ['1', '||', '2'], "Cluster or.")
    assertEql(filterSplitList([ '1', '|', '|', '2', '&', '&', '&', '3', '>', '4' ]), ['1', '||', '2', '&', '&&', '3', '>', '4'], "More complicated clustering")
    assertEql(shSplit("123"), ["123"], "Simple split test")
    assertEql(shSplit("1|2|3"), ["1", "|", "2", "|", "3"], "Splitting on pipes")
    assertEql(shSplit("1||2&&3"), ["1", "|", "|", "2", "&", "&", "3"], "More complicated, no-space splitting.")
    assertEql(shSplit("1 || 2"), ["1", "|", "|", "2"], "Pipe splitting with spaces.")
    assertEql(shSplit("ls -la"), ["ls", "-la"], "Space-splitting")
    assertEql(shSplit("'ls -la'"), ["ls -la"], "Quoted space-(not)splitting")
    assertEql(shSplit("1  \t\n > 2 &\n   & 1>2     "), ["1", ">", "2", "&", "&", "1", ">", "2"], "Lots of spaces!")
    assertEql(shSplit("1;2"), ["1", ";", "2"], "Does it correctly split on semi-colons?")
    assertEql(shSplit("1(2)"), ["1", "(", "2", ")"], "What about parentheses?")
    assertEql(shSplit("ls -la && (echo -ne foo\\n || (ps))"), ["ls", "-la", "&", "&", "(", "echo", "-ne", "foo\\n", "|", "|", "(", "ps", "))"], "Something like sh.")
    assertEql(shSplit("((( )( )))"), ["(((", ")", "(", ")))"], "Almost all parentheses!")
    assertEql(filterSplitList(shSplit("ls || ls")), ["ls", "||", "ls"], "Shlex replacement test 1!")
    assertEql(filterSplitList(shSplit("ls && ps")), ["ls", "&&", "ps"], "Shlex replacement test 2!")
    assertEql(filterSplitList(shSplit("ls; ps")), ["ls", ";", "ps"], "Shlex replacement test 3!")
    assertEql(filterSplitList(shSplit("ls; (ps 2>&1 | grep 'foo && not foo')")), ["ls", ";", "(", "ps", "2>&1", "|", "grep", "foo && not foo", ")"], "Shlex replacement test 4!")
    assertEql(filterSplitList(shSplit("\"ls; (ps 2>&1 | grep 'foo && not foo')\"")), ["ls; (ps 2>&1 | grep 'foo && not foo')"], "Shlex replacement test 5!")
    assertEql(filterSplitList(shSplit("make CFLAGS=thing LDFLAGS= CC=cc GCC=g++ A= TEST=33")), 
        [ "make", "CFLAGS=thing", "LDFLAGS=", "CC=cc", "GCC=g++", "A=", "TEST=33" ],
        "Shlex replacement test 6!")
    assertEql(collapse([ "1", '&&', '2']), '1 && 2', "Simple collapse test.")
    assertEql(collapse([ "a b", '&&', 'c']), "'a b' && c", "Spaces and quoting.", { "\"a b\" && c" })
    assertEql(collapse([ "a", "2>&1", '|', 'c' ]), "a 2>&1 | c", "Other separators.")
    assertEql(filterSplitList(shSplit('TEST_MACRO="Testing1234=:= := This **should ** work! "')),
        ['TEST_MACRO="Testing1234=:= := This **should ** work! "'], "Quoting that starts in the middle?")
    
