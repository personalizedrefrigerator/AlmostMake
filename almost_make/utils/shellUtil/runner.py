#!/usr/bin/python3

# A very simple command-runner.
# See: https://www.gnu.org/software/bash/manual/bash.html#Shell-Expansions

import shlex, os, re
import subprocess

import almost_make.utils.shellUtil.globber as globber

PRECEDENCE_LIST = [ '||', '&&', ";", '|', '>', '2>&1', '&' ]
TWO_ARGUMENTS = { "||", "&&", ";", '|', '>' }
PIPE_OUT_PERMISSIONS = 0o660

SPACE_CHARS = re.compile("\\s")

SYSTEM_SHELL = "system-shell"
USE_SYSTEM_PIPE = "use-system-pipe"

class ShellState:
    def __init__(self):
        self.cwd = os.getcwd()

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

# Return a shallow copy of [array] with 
# all items equal to [eqlTo] removed.
def removeEqual(array, eqlTo):
    result = []

    for val in array:
        if val != eqlTo:
            result.append(val)
    
    return result

# Remove empty strings from a string array.
def removeEmpty(array):
    return removeEqual(array, '')

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
    firstChar = text[0]
    lastChar = text[-1]
    
    if firstChar != lastChar:
        return text
    
    if firstChar in { '"', "'" }:
        return text[1 : len(text) - 1]
    return text

# Surround [text] with quotation marks,
# escaping any internal quotations with a backslash.
# Acts similar to shlex.quote in Python 3.7, but always adds
# quotation marks.
def quote(text, quoteChar="'"):
    result = ""
    escaped = False

    for char in text:
        if char == quoteChar and not escaped:
            result += "\\"
        elif char == '\\' and not escaped:
            escaped = True
        elif escaped:
            escaped = False
        result += char

    return quoteChar + result + quoteChar

# Return whether text begins and ends with the same quoting character,
# **and** the quoting is un-interupted. For example, "a, b, c" -> True,
# "a, b, c' -> False, "a, b," "c" -> False.
def isQuoted(text):
    if len(text) < 2:
        return False
    if text[0] != text[-1]: # Must start and end with the same character.
        return False
    if not text[0] in { '"', "'" }:
        return False
    
    startQuote = text[0]

    escaped = False

    text = text[1:-1] # Remove starting & ending...

    # If something would have broken us out of the quote...
    for char in text:
        if char == startQuote and not escaped:
            return False # ... then it isn't completely quoted.
        elif char == '\\' and not escaped:
            escaped = True
        elif escaped:
            escaped = False
    
    # If the ending quote would have been escaped, it isn't quoted.
    return not escaped

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
            if SPACE_CHARS.search(part.strip()) != None and not isQuoted(part):
                result += " " + quote(part)
            else:
                result += " " + part
        return result.strip()
    
    result = " ".join([ collapse(elem) for elem in clustered ])
    
    return result.strip()

# Glob all arguments in args, excluding the first and 
# quoted arguments.
def globArgs(args, state):
    cwd = os.path.abspath(state.cwd or '.')
    result = []
    isFirst = True
    
    for arg in args:
        if not isQuoted(arg.strip()) and not isFirst:
            result.extend(globber.glob(arg, cwd))
        else:
            result.append(arg)
            isFirst = False
    
    return result

# Returns the exit status of the command specified by args
# (e.g. [ 'ls', '-la' ]). If the command is in [customCommands],
# however, run the custom command, rather than the system command.
# If 'system-shell' is in flags, run this portion of the command in the 
# system's shell. This is useful in systems that support, say,
# the '|' operator, but the file-descriptor piping method fails.
# At the time of this writing, this was the case with iOS's a-Shell.
# If [blocking] is false, do not block and return a Popen object.
def rawRun(args, customCommands={}, flags=[], stdin=None, stdout=None, stderr=None, blocking=True, state=ShellState()):
    if "2>&1" in flags:
        stderr = stdout

    returnOverride = False

    # Force non-blocking.
    if "&" in flags:
        blocking = False
        returnOverride = True
        
    if len(args) == 0:
        return 0
    
    sysShell = SYSTEM_SHELL in flags

    if not sysShell:
        args = globArgs(args, state)
        args = [ stripQuotes(arg) for arg in args ]

    command = args[0].strip()

    if command in customCommands:
        result = customCommands[command](args, flags, stdin, stdout, stderr, state)
        
        if type(result) == bool:
            if result:
                return 0
            return 1
        if result == None:
            return 0
        return result

    if blocking:
        proc = subprocess.run(args, stdin=stdin, stdout=stdout, stderr=stderr, shell=sysShell, close_fds=False, cwd=state.cwd)
        return proc.returncode
    else:
        result = subprocess.Popen(args, stdin=stdin, stdout=stdout, stderr=stderr, shell=sysShell, close_fds=False, cwd=state.cwd)

        if returnOverride:
            return 0
        else:
            return result

def evalCommand(orderedCommand, customCommands={}, flags=[], stdin=None, stdout=None, stderr=None, blocking=True, state=ShellState()):
    if len(orderedCommand) == 0:
        return False
    if type(orderedCommand[0]) == str:
        return rawRun(orderedCommand, customCommands, flags, stdin=stdin, stdout=stdout, stderr=stderr, blocking=blocking, state=state)
    elif len(orderedCommand) == 2:
        recurseFlags = flags.copy()
        flags.append(orderedCommand)

        return evalCommand(orderedCommand[0], customCommands, recurseFlags, stdin=stdin, stdout=stdout, stderr=stderr, state=state)
    elif len(orderedCommand) == 3:
        operator = orderedCommand[1]

        # If we are to use the system's built-in pipe, we need to stop here.
        # Collapse the input and run it.
        if (operator == '|' or operator == '>') and USE_SYSTEM_PIPE in flags:
            runFlags = flags.copy()
            runFlags.append(SYSTEM_SHELL) # Use the system's shell to interpret.
            
            return rawRun(collapse(orderedCommand), customCommands, runFlags, stdin=stdin, stdout=stdout, stderr=stderr, state=state)

        if operator == '|':
            fdIn, fdOut = os.pipe()

            left = evalCommand(orderedCommand[0], customCommands, flags, stdin=stdin, stdout=fdOut, stderr=stderr, blocking = False, state=state)
            os.close(fdOut)

            # Run right with given stdin, stdout.
            right = evalCommand(orderedCommand[2], customCommands, flags, stdin=fdIn, stdout=stdout, stderr=stderr, state=state)
            
            os.close(fdIn)

            if type(left) != int:
                left.communicate()
                left = left.returncode

            if left == 0:
                return right
            
            return left
        elif operator == '>':
            outfd = os.open(os.path.abspath(" ".join(orderedCommand[2])), os.O_WRONLY | os.O_CREAT, mode=PIPE_OUT_PERMISSIONS)

            left = evalCommand(orderedCommand[0], customCommands, flags, stdin=stdin, stdout=outfd, stderr=stderr, state=state)

            os.close(outfd)

            return left
        elif operator == '||' or operator == '&&':
            left = evalCommand(orderedCommand[0], customCommands, flags, stdin=stdin, stdout=stdout, stderr=stderr, state=state)

            if (operator == '||' and left != 0) or (operator == '&&' and left == 0):
                right = evalCommand(orderedCommand[2], customCommands, flags, stdin=stdin, stdout=stdout, stderr=stderr, state=state)

                return right
            return left
        elif operator == ';':
            left = evalCommand(orderedCommand[0], customCommands, flags, stdin=stdin, stdout=stdout, stderr=stderr, state=state)
            right = evalCommand(orderedCommand[2], customCommands, flags, stdin=stdin, stdout=stdout, stderr=stderr, state=state)

            if left != 0:
                return left
            return right
        else:
            raise SyntaxError("Unknown separator, %s." % operator)
    else:
        raise SyntaxError("Too many parts to expression, %s" % str(orderedCommand))

# Like shlex.split but preserves quotation marks. 
# Send output to filterSplitList for punctuation grouping, but groups punctuation intelligently.
def shSplit(text, splitChars={ '(', ')', '|', '&', '>', ';', ' ', '\t', '\n' }, quoteChars = { '"', "'" },
        openingParen='(', closingParen=')'):
    escaped = False
    inQuote = None
    result = []
    buff = ""
    
    # Split by spaces and parentheses (and other punctuation chars...).
    for char in text:
        buff += char
        if char in quoteChars and not escaped:
            if inQuote == char:
                inQuote = None
            elif inQuote == None:
                inQuote = char
        elif char == '\\' and not escaped:
            escaped = True
        elif escaped:
            escaped = False
        elif char in splitChars and inQuote == None:
            result.append(buff[:-1])
            result.append(char)
            buff = ""
    
    result.append(buff)
    
    buff = ''
    filtered = []
    
    
    # Remove spaces, clump parentheses.
    for part in result:
        part = part.strip()
        
        if part != '':
            # If the direction of parentheses switches...
            if part == openingParen and closingParen in buff  or  part == closingParen and openingParen in buff:
                filtered.append(buff)
                buff = ''
        
            if part.startswith(openingParen) or part.endswith(closingParen):
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
def runCommand(commandString, customCommands = {}, flags = [], state=ShellState()):
    # Note: punctuation_chars=True causes shlex to cluster ();&| runs.
    #       For example, a && b -> ['a', '&&', 'b'], instead of ['a', '&', '&', 'b'].
    #       It also, however, clusters runs we don't want, like a &&& b -> ['a', '&&&', 'b'].
    #       This, however, split 'a/b/c' into ['a', '/', 'b', '/', 'c'], which we REALLY DON'T WANT.
    #       As such, we're using 'shSplit' here.
    portions = filterSplitList(shSplit(commandString))
    ordered = cluster(portions) # Convert ['a', '&&', 'b', '||', 'c'] into
                                #       [[['a'], '&&', ['b']], '||', ['c']]
    return evalCommand(ordered, customCommands, flags, state=state)

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
    assertEql(shSplit("'ls -la'"), ["'ls -la'"], "Quoted space-(not)splitting")
    assertEql(shSplit("'ls' '-la'"), ["'ls'", "'-la'"], "Quoted parts splitting")
    assertEql(shSplit("1  \t\n > 2 &\n   & 1>2     "), ["1", ">", "2", "&", "&", "1", ">", "2"], "Lots of spaces!")
    assertEql(shSplit("1;2"), ["1", ";", "2"], "Does it correctly split on semi-colons?")
    assertEql(shSplit("1(2)"), ["1", "(", "2", ")"], "What about parentheses?")
    assertEql(shSplit("ls -la && (echo -ne foo\\n || (ps))"), ["ls", "-la", "&", "&", "(", "echo", "-ne", "foo\\n", "|", "|", "(", "ps", "))"], "Something like sh.")
    assertEql(shSplit("((( )( )))"), ["(((", ")", "(", ")))"], "Almost all parentheses!")

    assertEql(filterSplitList(shSplit("ls || ls")), ["ls", "||", "ls"], "Shlex replacement test 1!")
    assertEql(filterSplitList(shSplit("ls && ps")), ["ls", "&&", "ps"], "Shlex replacement test 2!")
    assertEql(filterSplitList(shSplit("ls; ps")), ["ls", ";", "ps"], "Shlex replacement test 3!")
    assertEql(filterSplitList(shSplit("ls; (ps 2>&1 | grep 'foo && not foo')")), ["ls", ";", "(", "ps", "2>&1", "|", "grep", "'foo && not foo'", ")"], "Shlex replacement test 4!")
    assertEql(filterSplitList(shSplit("\"ls; (ps 2>&1 | grep 'foo && not foo')\"")), ["\"ls; (ps 2>&1 | grep 'foo && not foo')\""], "Shlex replacement test 5!")
    assertEql(filterSplitList(shSplit("make CFLAGS=thing LDFLAGS= CC=cc GCC=g++ A= TEST=33")), 
        [ "make", "CFLAGS=thing", "LDFLAGS=", "CC=cc", "GCC=g++", "A=", "TEST=33" ],
        "Shlex replacement test 6!")
    assertEql(filterSplitList(shSplit('TEST_MACRO="Testing1234=:= := This **should ** work! "')),
        ['TEST_MACRO="Testing1234=:= := This **should ** work! "'], "Quoting that starts in the middle?")
    
    assertEql(collapse([ "1", '&&', '2']), '1 && 2', "Simple collapse test.")
    assertEql(collapse([ "a b", '&&', 'c']), "'a b' && c", "Spaces and quoting.", { "\"a b\" && c" })
    assertEql(collapse([ "a", "2>&1", '|', 'c' ]), "a 2>&1 | c", "Other separators.")
    
    assertEql(globArgs(['a test', 'of some things', 'that should work'], ShellState()), ['a test', 'of some things', 'that should work'], "Test identity globbing")
    
    assertEql(quote("singleWord"), "\'singleWord\'", "Single-word quoting")
    assertEql(quote("two words", '"'), "\"two words\"", "Two-word, double-quoting")
    assertEql(quote("two words"), "\'two words\'", "Two-word, single-quoting")
    assertEql(quote("""assertEql(quote("two words", "'"), "\'two words\'", "Two-word, single-quoting")""", "'"), 
        r''' 'assertEql(quote("two words", "\'"), "\'two words\'", "Two-word, single-quoting")' '''.strip(), 
        "Quoting the single-quoting test.")
    assertEql(quote("[left-[br]][acket[[quoting", '['), "[\\[left-\\[br]]\\[acket\\[\\[quoting[", "Quoting with left-bracket characters!")
