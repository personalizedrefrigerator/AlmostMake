#!/usr/bin/python3

# See https://danishpraka.sh/2018/09/27/shell-in-python.html (Accessed Aug 22)

import cmd, os, sys

from almost_make.utils.printUtil import *
import almost_make.utils.shellUtil.runner as runner
import almost_make.utils.shellUtil.escapeParser as escapeParser

SHELL_NAME = "AlmostMake's NotQuiteAShell"

QUICK_HELP = \
{
    "cd": """cd [directory]
Change the current working directory to [directory].
This command is provided by %s.""" % SHELL_NAME,
    "exit": """exit [status]
Exit the current script/shell with status [status].
If [status] is not provided, exit with code zero.""",
    "ls": """ls [directory]
Print the contents of [directory] or the current working
directory.""",
    "pwd": """pwd
Print the current working directory's absolute path."""
}

def filterArgs(args, minimumLength):
    if len(args) < minimumLength or "--help" in args:
        print(QUICK_HELP[args[0]])
        return False
    return True

CUSTOM_COMMANDS = \
{
    "cd": lambda args, flags, stdin, stdout, stderr: filterArgs(args, 2) and os.chdir(os.path.abspath(args[1])),
    "exit": lambda args, flags, stdin, stdout, stderr: filterArgs(args, 1) and sys.exit((len(args) > 1 and args[1]) or 0)
}

def customLs(args, stdin, stdout, stderr):
    listInDirectory = os.path.abspath(".")
    
    if len(args) > 1:
        listInDirectory = os.path.abspath(args[1])
    fileList = os.listdir(listInDirectory)
    fileList.sort()
    
    cprint(" \n".join(fileList), file=stdout)

def customPwd(args, stdin, stdout, stderr):
    cprint(os.path.abspath("."), file=stdout)

def customEcho(args, stdin, stdout, stderr):
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
        result[alias] = lambda args, flags, stdin, stdout, stderr: filterArgs(args, minArgs) and fn(args, stdin, stdout, stderr)
    
    if "_CUSTOM_BASE_COMMANDS" in macros:
        addCustomCommand("ls", 1, customLs)
        result["dir"] = result["ls"]
        addCustomCommand("pwd", 1, customPwd)
        addCustomCommand("echo", 2, customEcho)
    
    return result

def evalScript(text, macroUtil, macros={}, resetCwd = True, defaultFlags = []):
    oldCwd = os.path.abspath(os.getcwd())
    
    text, macros = macroUtil.expandAndDefineMacros(text, macros)
    
    result = (runner.runCommand(text, getCustomCommands(macros), defaultFlags), macros)
    
    if resetCwd:
        os.chdir(oldCwd)
    
    return result


