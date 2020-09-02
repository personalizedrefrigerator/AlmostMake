#!/usr/bin/python3

# See https://danishpraka.sh/2018/09/27/shell-in-python.html (Accessed Aug 22)

import cmd, os, sys, shutil, pathlib

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
Change the current working directory to [directory].""",

    "exit": """Usage: exit [status]
Exit the current script/shell with status [status].
If [status] is not provided, exit with code zero.""",

    "ls": """Usage: ls [options] [directories]
Print the contents of each directory in [directories] 
or the current working directory.
[options] can contain:
 -a, --all                   List all files, including '.' and '..'
 -1, --one-per-line          Each file on its own line.
 -Q, --quote-name            Surround the name of each file with double-quotes.
 -m, --comma-separated-list  List files on a single line, as a comma-separated list.
 -f, --unformatted           No color output, do not sort.
 --color                     Force color output.""",

    "pwd": """Usage: pwd
Print the current working directory's absolute path.""",

    "echo": """Usage: echo [options] [text]
Send [text] to standard output.
[options] can contain:
 -n\t\t Do not print a trailing newline.
 -e\t\t Evaluate escape characters (e.g. echo -ne \\n outputs a single newline).
""",

    "touch": """"Usage: touch [options] [files...]
    Update the access and modification times for each file in files.
Options:
 -c, --no-create  Do not create the file if it does not exist.
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
    "exit": lambda args, flags, stdin, stdout, stderr, state: filterArgs(args, 1, stdout) and sys.exit((len(args) > 1 and args[1]) or 0)
}

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
        'quote-name', 'comma-separated-list'
    })

    if 'default' in args and len(args['default']) > 0:
        dirs = list(map(os.path.abspath, args['default']))
    
    def noteEntry(name, color, isLast = False):
        # If given a file descriptor (not default output),
        # we probably aren't sending output to a terminal. As such,
        # remove coloring. --color overrides this.
        if stdout != None and not 'color' in args:
            color = None

        sep = '  '

        if (not 'all' in args and not 'unformatted' in args) and name.startswith('.'):
            return

        if 'one-per-line' in args:
            sep = not isLast and '\n' or ''

        if 'quote-name' in args:
            name = runner.quote(name, '"')

        if not isLast and 'comma-separated-list' in args:
            sep = ', '

            if 'one-per-line' in args:
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

# Get a set of custom commands that can be used.
def getCustomCommands(macros):
    result = {}
    
    for key in CUSTOM_COMMANDS:
        result[key] = CUSTOM_COMMANDS[key]

    def addCustomCommand(alias, minArgs, fn):
        result[alias] = lambda args, flags, stdin, stdout, stderr, state: filterArgs(args, minArgs, stdout) and fn(args, stdin, stdout, stderr, state)
    
    addCustomCommand("cd", 2, customCd)

    if "_CUSTOM_BASE_COMMANDS" in macros:
        addCustomCommand("ls", 1, customLs)
        result["dir"] = result["ls"]
        addCustomCommand("pwd", 1, customPwd)
        addCustomCommand("echo", 2, customEcho)
        addCustomCommand("touch", 2, customTouch)
    
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

    testDir = os.path.dirname(__file__)

    if testDir != '':
        os.chdir(testDir)

    result, _ = evalScript("ls | grep __init__.py", macroUtil,
    {
        "_CUSTOM_BASE_COMMANDS": True
    },
    defaultFlags=[])
    assertEql(result, 0, "Test ls and grep in current directory for __init__.")

    result, _ = evalScript("ls -f | grep -F ..", macroUtil,
    {
        "_CUSTOM_BASE_COMMANDS": True
    },
    defaultFlags=[])
    assertEql(result, 0, "Test ls with -f flag.")

    result, _ = evalScript("ls -f . | grep -F ..", macroUtil,
    {
        "_CUSTOM_BASE_COMMANDS": True
    },
    defaultFlags=[])
    assertEql(result, 0, "Test ls with provided directory")

    result, _ = evalScript("ls -f ./ ../ | grep -F argsUtil.py", macroUtil,
    {
        "_CUSTOM_BASE_COMMANDS": True
    },
    defaultFlags=[])
    assertEql(result, 0, "Test ls with provided directories (1 of 2)")

    result, _ = evalScript("ls -f ./ ../ | grep -F escapeParser.py", macroUtil,
    {
        "_CUSTOM_BASE_COMMANDS": True
    },
    defaultFlags=[])
    assertEql(result, 0, "Test ls with provided directories (2 of 2)")

    result, _ = evalScript("echo -e 'F\\noo' | grep ^F$", macroUtil,
    {
        "_CUSTOM_BASE_COMMANDS": True
    },
    defaultFlags=[])
    assertEql(result, 0, "Test echo's -e flag.")

