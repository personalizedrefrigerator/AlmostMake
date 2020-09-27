#!/usr/bin/python3

# See https://danishpraka.sh/2018/09/27/shell-in-python.html (Accessed Aug 22)

import cmd, os, sys, shutil, pathlib, re

from almost_make.utils.printUtil import cprint, FORMAT_COLORS
import almost_make.utils.printUtil as printer
from almost_make.utils.argsUtil import parseArgs
from almost_make.version import printVersion
import almost_make.utils.shellUtil.runner as runner
import almost_make.utils.shellUtil.escapeParser as escapeParser

SHELL_NAME = "AlmostMake's built-in shell"

QUICK_HELP = \
{
    "cd": """Usage: cd [directory]
Change the current working directory to [directory].
""",

    "exit": """Usage: exit [status]
Exit the current script/shell with status [status].
If [status] is not provided, exit with code zero.
""",

    "ls": """Usage: ls [options] [directories]
Print the contents of each directory in [directories] 
or the current working directory.
[options] can contain:
 -a, --all                   List all files, including '.' and '..'
 -1, --one-per-line          Each file on its own line. This is assumed when output does not appear to be to a terminal.
 -Q, --quote-name            Surround the name of each file with double-quotes.
 -m, --comma-separated-list  List files on a single line, as a comma-separated list.
 -f, --unformatted           No color output, do not sort.
 --color                     Force color output. Do not assume --one-per-line when output does not seem to be to a terminal.
 """,

    "pwd": """Usage: pwd
Print the current working directory's absolute path.""",

    "echo": """Usage: echo [options] [text]
Send [text] to standard output.
[options] can contain:
 -n\t\t Do not print a trailing newline.
 -e\t\t Evaluate escape characters (e.g. echo -ne \\n outputs a single newline).
""",

    "touch": """Usage: touch [options] [files...]
Update the access and modification times for each file in files.
Options:
 -c, --no-create  Do not create the file if it does not exist.
""",

    "cat": """Usage: cat [options] [files...]
Print the contents of each file in [files]. If a file is -, print standard input, instead.
Options:
 -n, --number    Number each line.
 -T, --show-tabs Replace all tab characters with ^T.
 -E, --show-ends Print a $ at the end of each line.
""",
    "grep": """Usage: grep [options] PATTERN
Search for PATTERN in standard input.
Options:
 -F, --fixed-strings   Treat PATTERN as a fixed string, rather than a regular expression.
 -i, --ignore-case     Do case-insensitive matching.
 -v, --invert-match    Count and print (print depends on other options) lines that do not match PATTERN.
 -c, --count           Print the count of matching lines, rather than the contents of the lines.
 -q, --quiet           Limit output.
 -x, --line-regexp     PATTERN must match each line in its entirety.
 -o, --only-matching   Only output portions of the line that match PATTERN. Ignored if --line-regexp or -x are given.
 -n, --line-number     Prefix each printed-line with a line number.
 --no-color            Force uncolorized output.
""",
    "rm": """Usage: rm [options] files...
Remove all files in [files...]. Note that unlike many implementations of
rm, this implementation never requests confirmation from the user.
Options:
 -f, --force         Ignore nonexistent paths.
 -r, -R, --recursive Recursively remove directories and their contents.
 -d, --dir           Remove empty directories.
""",
    "mkdir": """Usage: mkdir [options] directories...
Make new directories, [directories]. Given directories should not exist.
Options:
 -m, --mode     The mode of the new directory, as an octal number (e.g. 777).
 -p, --parents  Create parent directories as needed. Do not fail if any of [directories] do not exist.
 -v, --verbose  Print a message before creating each directory.
"""
}

def filterArgs(args, minimumLength, stdout):
    if len(args) < minimumLength or "--help" in args:
        cprint(QUICK_HELP[args[0]] + '\n', file=stdout)
        cprint("This command is built into %s.\n" % SHELL_NAME)
        return False
    elif '--version' in args:
        printVersion(printer.wrapFile(stdout))
        return False
    return True

CUSTOM_COMMANDS = \
{
    
}

def customExit(args, stdin, stdout, stderr, state):
    if len(args) == 1:
        sys.exit(0)
    else:
        return int(args[1])

LS_DIRECTORY_COLOR = FORMAT_COLORS['BLUE']
LS_LINK_COLOR = FORMAT_COLORS['BLUE']
LS_FILE_COLOR = None

def customLs(args, stdin, stdout, stderr, state):
    dirs = [ os.path.abspath(state.cwd or '.') ]
    
    args = parseArgs(args, 
    {
        'a': 'all',
        'f': 'unformatted',
        '1': 'one-per-line',
        'Q': 'quote-name',
        'm': 'comma-separated-list'
    },
    strictlyFlags =
    {
        'all', 'unformatted', 'one-per-line',
        'quote-name', 'comma-separated-list',
        'color'
    })

    cwd = state.cwd or '.'

    if len(args['default']) > 0:
        dirs = [ os.path.abspath(os.path.join(cwd, os.path.normcase(arg))) for arg in args['default'] ]
    
    def noteEntry(name, color, isLast = False):
        decolorized = False # If we decolorize, do other formatting...

        # If given a file descriptor (not default output),
        # we probably aren't sending output to a terminal. As such,
        # remove coloring. --color overrides this.
        if stdout != None and not 'color' in args:
            decolorized = True
            color = None

        multiLine = decolorized and not 'comma-separated-list' in args or 'one-per-line' in args

        sep = '  '

        if (not 'all' in args and not 'unformatted' in args) and name.startswith('.'):
            return

        if multiLine:
            sep = not isLast and '\n' or ''

        if 'quote-name' in args:
            name = runner.quote(name, '"')

        if not isLast and 'comma-separated-list' in args:
            sep = ', '

            if multiLine:
                sep = ',\n'

        if 'unformatted' in args:
            cprint(name + sep, file=stdout)
        else:
            cprint(name + sep, color, file=stdout)

    if not 'unformatted' in args:
        dirs.sort()

    isFirst = True

    for directory in dirs:
        if len(dirs) > 1:
            if not isFirst:
                cprint("\n", file=stdout)
            
            isFirst = False
            cprint("%s:\n" % directory, file=stdout)
        
        fileList = []

        with os.scandir(directory) as files:
            if not 'unformatted' in args:
                fileList = sorted(files, key=lambda entry: entry.name)
            else:
                fileList = list(files)

        noteEntry('.', LS_DIRECTORY_COLOR)
        noteEntry('..', LS_DIRECTORY_COLOR, isLast = (len(fileList) == 0))

        if len(fileList) != 0:
            for entry in fileList[:-1]:
                noteEntry(entry.name, entry.is_dir() and LS_DIRECTORY_COLOR or LS_FILE_COLOR)
            noteEntry(fileList[-1].name, fileList[-1].is_dir() and LS_DIRECTORY_COLOR or LS_FILE_COLOR, isLast = True)
        
        cprint("\n", file=stdout)

def customPwd(args, stdin, stdout, stderr, state):
    cprint(os.path.abspath(state.cwd or '.') + '\n', file=stdout)

def customTouch(args, stdin, stdout, stderr, state):
    args = parseArgs(args, 
    {
        'c': 'no-create'
    }, 
    strictlyFlags=
    {
        'no-create'
    })

    cwd = pathlib.Path(state.cwd or '.')
    touchedCount = 0

    for path in args['default']:
        path = cwd.joinpath(path)

        if path.is_file() or not 'no-create' in args:
            path.touch()
            touchedCount += 1
    
    return touchedCount != 0

def customCd(args, stdin, stdout, stderr, state):
    oldCwd = state.cwd

    if not state.cwd:
        state.cwd = os.path.abspath(os.path.expanduser(args[1]))
    else:
        state.cwd = os.path.abspath(os.path.expanduser(os.path.join(state.cwd, os.path.expanduser(args[1]))))
    
    result = True

    if not os.path.exists(state.cwd):
        cprint("cd: " + str(state.cwd) + ": No such file or directory\n", file=stderr)
        state.cwd = oldCwd
        result = False
    
    return result

def customEcho(args, stdin, stdout, stderr, state):
    if len(args) == 1:
        # No arguments? Print a newline.
        cprint('\n', file=stdout)

        return 0
    
    doEscapes = False
    doNewlines = True
    firstArg = args[1].strip()
    
    if firstArg.startswith("-") and len(firstArg) <= 3:
        doEscapes = 'e' in firstArg
        doNewlines = not 'n' in firstArg
        
        args = args[2:]
        
        if len(args) > 0 and args[0].startswith('-') and len(args[0]) <= 2:
            if 'e' in args[0]:
                doEscapes = True
                trimArg = True
            if 'n' in args[0]:
                doNewlines = False
                trimArg = True
            if trimArg:
                args = args[1:]
    else:
        args = args[1:]
    
    
    if len(args) < 1:
        return 0
    
    printEnd = '\n'
    toPrint = " ".join(args)
    
    if not doNewlines:
        printEnd = ''
    
    if doEscapes:
        toPrint = escapeParser.parseEscapes(toPrint)
    
    cprint(toPrint + printEnd, file=stdout)

def customCat(args, stdin, stdout, stderr, state):
    args = parseArgs(args,
    {
        'n': 'number',
        'T': 'show-tabs',
        'E': 'show-ends'
    },
    strictlyFlags=
    {
        'number',
        'show-tabs',
        'show-ends'
    })

    lineNu = 0

    def logLine(line):
        if 'number' in args:
            cprint("%s\t" % str(lineNu), file=stdout)
        
        if 'show-tabs' in args:
            line = re.sub(r'[\t]', '^T', line)
        
        end = 'show-ends' in args and '$' or ''
        cprint(str(line) + end + "\n", file=stdout)

    stdin = printer.wrapFile(stdin)
    success = True
    
    for arg in args['default']:
        if arg == '-':
            lines = stdin.read().split('\n')

            if len(lines) > 0 and lines[-1] == '':
                lines = lines[:-1]

            for line in lines:
                lineNu += 1
                logLine(line)
        else:
            filename = os.path.join(state.cwd or '.', arg)

            if not os.path.exists(filename):
                cprint("File %s does not exist.\n" % filename, color=printer.FORMAT_COLORS["RED"], file=stderr)
                success = False

                continue
            if not os.path.isfile(filename):
                cprint("Path %s is not a file.\n" % filename, color=printer.FORMAT_COLORS["RED"], file=stderr)
                success = False

                continue
            try:
                with open(filename, 'rb') as file:
                    lines = file.read().split(b'\n')

                    if len(lines) > 0 and lines[-1] == '':
                        lines = lines[:-1]

                    for line in lines:
                        lineNu += 1
                        if type(line) == bytes:
                            logLine(line.decode('utf-8', errors='replace'))
                        else:
                            logLine(line)
            except IOError as ex:
                cprint("Unable to read file %s. Message: %s.\n" % (filename, ex), printer.FORMAT_COLORS['RED'], file=stderr)
                success = False
    return success

def customGrep(args, stdin, stdout, stderr, state):
    args = parseArgs(args,
    {
        'F': 'fixed-strings',
        'i': 'ignore-case',
        'v': 'invert-match',
        'c': 'count',
        'q': 'quiet',
        'x': 'line-regexp',
        'o': 'only-matching',
        'n': 'line-number'
    },
    strictlyFlags=
    {
        'fixed-strings', 'ignore-case', 'invert-match',
        'count', 'quiet', 'line-regexp', 'only-matching',
        'line-number', 'no-color'
    })

    if len(args['default']) > 1:
        cprint("[Files...] is currently unsupported. Input should be given via stdin.\n", printer.FORMAT_COLORS['RED'], file=stderr)
        return False
    
    patterns = []

    if len(args['default']) > 0:
        patternList = args['default'][0].split('\n')

        for part in patternList:
            flags = 0

            if 'fixed-strings' in args:
                part = re.escape(part)
            if 'ignore-case' in args:
                flags = flags | re.IGNORECASE

            patterns.append(re.compile(part, flags))
    else:
        # If no default arguments, grep was probably called
        # with an empty pattern. Note this.
        patterns.append(re.compile('')) 
    
    def matchesLine(line):
        matches = []
        for pattern in patterns:
            matchInfo = None

            if not 'line-regexp' in args:
                matchInfo = pattern.search(line)
            else:
                matchInfo = pattern.fullmatch(line)

            if matchInfo != None:
                matches.append(matchInfo.span())
        return matches
    
    stdin = printer.wrapFile(stdin)
    lines = stdin.read().split('\n')

    # Input is from stdin... There is often a trailing newline...
    if len(lines) > 0 and lines[-1] == '':
        lines = lines[:-1]

    lineNumber = 0
    matchCount = 0

    for line in lines:
        lineNumber += 1
        matches = matchesLine(line)

        # Negates (len(matches) > 0) if 'invert-match' in args.
        if (len(matches) > 0) == (not 'invert-match' in args):
            matchCount += 1 # Count the number of **lines**

            if not 'count' in args and not 'quiet' in args:
                if 'line-number' in args:
                    cprint(str(lineNumber) + '\t', file=stdout)

                if not 'only-matching' in args or 'invert-match' in args:
                    if stdout != None or 'no-color' in args: # Don't colorize output when output isn't the default...
                        cprint(line + '\n', file=stdout)
                    else: # Otherwise, colorize output.
                        startIndexes = set()
                        stopIndexes = set()

                        for start,stop in matches:
                            startIndexes.add(start)
                            stopIndexes.add(stop)
                        
                        buff = ''
                        inRange = False

                        for i in range(0, len(line)):
                            if i in startIndexes and not inRange:
                                inRange = True
                            elif i in stopIndexes and inRange:
                                cprint(buff, printer.FORMAT_COLORS['PURPLE'], file=stdout)
                                inRange = False
                                buff = ''
                            if inRange:
                                buff += line[i]
                            else:
                                cprint(line[i], file=stdout)
                        
                        cprint(buff, printer.FORMAT_COLORS['PURPLE'], file=stdout)
                        cprint('\n', file=stdout)
                else:
                    for start,stop in matches:
                        cprint(line[start:stop] + '\n', file=stdout)
    
    if 'count' in args:
        cprint(str(matchCount) + '\n', file=stdout)
    
    return matchCount > 0

def customRm(args, stdin, stdout, stderr, state):
    args = parseArgs(args,
    {
        'r': 'recursive',
        'R': 'recursive',
        'f': 'force',
        'd': 'dir'
    }, 
    strictlyFlags=
    {
        'recursive',
        'force',
        'dir'
    })

    toRemove = [ os.path.join(state.cwd or '.', arg) for arg in args['default'] ]
    success = True

    while len(toRemove) > 0:
        filepath = os.path.abspath(os.path.normcase(os.path.normpath(toRemove.pop())))

        if os.path.isdir(filepath):
            if not 'dir' in args and not 'recursive' in args:
                cprint("Refusing to remove %s because it is a directory.\n" % filepath, FORMAT_COLORS['RED'], stderr)
                success = False
                continue
            
            filesInDir = os.listdir(filepath)

            if len(filesInDir) == 0:
                os.rmdir(filepath)
                continue

            if not 'recursive' in args:
                cprint("Refusing to remove non-empty directory %s.\n" % filepath, FORMAT_COLORS['RED'], stderr)
                success = False
                continue

            # We need to re-consider filepath after removing its contents.
            toRemove.append(filepath)
            toRemove.extend([ os.path.join(filepath, filename) for filename in filesInDir ])
        elif os.path.isfile(filepath):
            os.remove(filepath)
        elif not os.path.exists(filepath) and not 'force' in args:
            cprint("%s does not exist.\n" % filepath, FORMAT_COLORS['RED'], stderr)
            success = False
        elif not 'force' in args:
            cprint('Refusing to remove entity of unknown type: %s.\n' % filepath, FORMAT_COLORS['RED'], stderr)
            success = False
    return success

def customMkdir(args, stdin, stdout, stderr, state):
    args = parseArgs(args,
    {
        'm': 'mode',
        'p': 'parents',
        'v': 'verbose'
    },
    strictlyFlags=
    {
        'parents', 'verbose'
    })

    mode = 0o664
    success = True

    if 'mode' in args:
        try:
            mode = int(mode, 8)
        except ValueError as ex:
            cprint("Unable to parse mode: " + str(ex) + "\n", FORMAT_COLORS['RED'], stderr)
            return False

    for filepath in args['default']:
        filepath = os.path.abspath(os.path.normpath(os.path.normcase(os.path.join(state.cwd or '.', filepath))))

        if 'verbose' in args:
            cprint('Creating %s...\n' % filepath, file=stdout)
        
        try:
            if 'parents' in args:
                os.makedirs(filepath, mode)
            else:
                path = pathlib.Path(filepath)
                if not path.parent.exists():
                    cprint("Parent directory of %s does not exist.\n" % filepath, FORMAT_COLORS['RED'], stderr)
                    success = False
                    continue

                os.mkdir(filepath, mode)
        except FileExistsError as ex:
            if not 'parents' in args:
                cprint("Unable to create directory %s. File exists.\n" % filepath, FORMAT_COLORS['RED'], stderr)
                success = False
            else:
                continue
    
    return success
        
def customChmod(args, stdin, stdout, stderr, state):
    pass

# Get a set of custom commands that can be used.
def getCustomCommands(macros):
    result = {}
    
    for key in CUSTOM_COMMANDS:
        result[key] = CUSTOM_COMMANDS[key]

    def addCustomCommand(alias, minArgs, fn):
        result[alias] = lambda args, flags, stdin, stdout, stderr, state: filterArgs(args, minArgs, stdout) and fn(args, stdin, stdout, stderr, state)
    
    addCustomCommand("cd", 2, customCd)
    addCustomCommand("exit", 1, customExit)

    if "_CUSTOM_BASE_COMMANDS" in macros:
        addCustomCommand("ls", 1, customLs)
        result["dir"] = result["ls"]
        addCustomCommand("pwd", 1, customPwd)
        addCustomCommand("echo", 1, customEcho)
        addCustomCommand("touch", 2, customTouch)
        addCustomCommand("cat", 2, customCat)
        addCustomCommand("grep", 2, customGrep)
        addCustomCommand("rm", 2, customRm)
        addCustomCommand("mkdir", 2, customMkdir)
    
    return result

def evalScript(text, macroUtil, macros={}, defaultFlags = [], state=None):
    if not state:
        state = runner.ShellState()
    
    # Set appropriate macros.
    macros["PWD"] = state.cwd

    text, macros = macroUtil.expandAndDefineMacros(text, macros)
    return (runner.runCommand(text, getCustomCommands(macros), defaultFlags, state), macros)

if __name__ == "__main__":
    import almost_make.utils.macroUtil as macroUtility
    macroUtil = macroUtility.MacroUtil()

    def assertEql(a, b, message):
        if a != b:
            raise Exception("%s != %s (%s)" % (str(a), str(b), message))
    
    def assertNotEql(a, b, message):
        if a == b:
            raise Exception("%s == %s (%s)" % (str(a), str(b), message))

    testDir = os.path.dirname(__file__)

    if testDir != '':
        os.chdir(testDir)

    macros = \
    {
        "_CUSTOM_BASE_COMMANDS": True
    }

    result, _ = evalScript("ls | grep __init__.py", macroUtil, macros, defaultFlags=[])
    assertEql(result, 0, "Test ls and grep in current directory for __init__.")

    result, _ = evalScript("ls -f | grep -F ..", macroUtil, macros, defaultFlags=[])
    assertEql(result, 0, "Test ls with -f flag.")

    result, _ = evalScript("ls -f . | grep -F ..", macroUtil, macros, defaultFlags=[])
    assertEql(result, 0, "Test ls with provided directory")

    result, _ = evalScript("ls -f ./ ../ | grep -F argsUtil.py", macroUtil, macros, defaultFlags=[])
    assertEql(result, 0, "Test ls with provided directories (1 of 2)")

    result, _ = evalScript("ls -f ./ ../ | grep -F escapeParser.py", macroUtil, macros, defaultFlags=[])
    assertEql(result, 0, "Test ls with provided directories (2 of 2)")

    result, _ = evalScript("echo -e 'F\\noo' | grep ^F$", macroUtil, macros, defaultFlags=[])
    assertEql(result, 0, "Test echo's -e flag.")

    result, _ = evalScript("echo test | cat - | grep test", macroUtil, macros, defaultFlags=[])
    assertEql(result, 0, "Test cat from stdin")

    result, _ = evalScript("echo -e 'test\\nfoo' | cat -n - | grep -F 2", macroUtil, macros, defaultFlags=[])
    assertEql(result, 0, "Test -n flag for cat (line numbers)")

    result, _ = evalScript("echo -e 'test\\n\\tfoo' | cat -T - | grep \\^Tfoo", macroUtil, macros, defaultFlags=[])
    assertEql(result, 0, "Test -T flag for cat (tab->^T)")

    result, _ = evalScript("echo -e 'test\\n\\tfoo' | cat -TE - | grep '\\^Tfoo\\$$'", macroUtil, macros, defaultFlags=[])
    assertEql(result, 0, "Test -E flag for cat (ending $)")

    result, _ = evalScript("cat __init__.py | grep '__all__'", macroUtil, macros, defaultFlags=[])
    assertEql(result, 0, "Test cat [filename].")

    result, _ = evalScript("echo nothing | grep 'should not find anything'", macroUtil, macros, defaultFlags=[])
    assertEql(result, 1, "Test grep failure.")

    result, _ = evalScript("echo nothing | grep 'o[th]+ing$'", macroUtil, macros, defaultFlags=[])
    assertEql(result, 0, "Test grep simple regexp.")

    result, _ = evalScript("echo nothing | grep -x noth", macroUtil, macros, defaultFlags=[])
    assertEql(result, 1, "Test grep full-line match failure.")

    result, _ = evalScript("echo '' | grep -x .*", macroUtil, macros, defaultFlags=[])
    assertEql(result, 0, "Test (very simple) grep full-line match success.")

    result, _ = evalScript("echo nothing | grep -Fx nothing", macroUtil, macros, defaultFlags=[])
    assertEql(result, 0, "Test grep full-line match success (with -F).")

    result, _ = evalScript("echo nothing | grep -x nothing", macroUtil, macros, defaultFlags=[])
    assertEql(result, 0, "Test grep full-line match success.")

    result, _ = evalScript("echo -e 'a\\nbcd\\nefg' | grep -Fv 'nothing'", macroUtil, macros, defaultFlags=[])
    assertEql(result, 0, "Test grep invert-match success.")

    result, _ = evalScript("echo textthenfood | grep -o foo | grep -Fx foo", macroUtil, macros, defaultFlags=[])
    assertEql(result, 0, "Test grep only-match success.")

    result, _ = evalScript("echo textthenfood | grep -c foo | grep -Fx 1", macroUtil, macros, defaultFlags=[])
    assertEql(result, 0, "Test grep count (1).")

    result, _ = evalScript("echo -e 'textthenfood\\nfoo' | grep -c foo | grep -Fx 2", macroUtil, macros, defaultFlags=[])
    assertEql(result, 0, "Test grep count (2).")

    result, _ = evalScript("echo -e 'textthenfood\\nfoo' | grep -n foo | cat -T - | grep -Fx 2^Tfoo", macroUtil, macros, defaultFlags=[])
    assertEql(result, 0, "Test grep line number (2).")

    result, _ = evalScript("mkdir foo && rm -d foo && ls -m | grep -v foo", macroUtil, macros, defaultFlags=[])
    assertEql(result, 0, "Test add and remove a directory.")

    result, _ = evalScript("mkdir ./ 2>&1", macroUtil, macros, defaultFlags=[])
    assertNotEql(result, 0, "Test fails on attempt to create existing directory.")

    result, _ = evalScript("mkdir -p testing123/a/b/c/d/e/f && rm -r testing123 && ls -m | grep -v testing123", macroUtil, macros, defaultFlags=[])
    assertEql(result, 0, "Remove recursively, makedir recursively.")