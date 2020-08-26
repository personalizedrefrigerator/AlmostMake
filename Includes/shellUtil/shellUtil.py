#!/usr/bin/python3

# See https://danishpraka.sh/2018/09/27/shell-in-python.html (Accessed Aug 22)

import cmd, os, sys

from Includes.printUtil import *
import Includes.macroUtil as macroUtil
import Includes.shellUtil.runner as runner

SHELL_NAME = "AlmostMake's NotQuiteAShell"

QUICK_HELP = \
{
    "cd": """cd [directory]
Change the current working directory to [directory].
This command is provided by %s.""" % SHELL_NAME,
    "exit": """exit [status]
Exit the current script/shell with status [status].
If [status] is not provided, exit with code zero."""
}

def filterArgs(args, minimumLength):
    if len(args) < minimumLength or "--help" in args:
        print(QUICK_HELP[args[0]])
        return False
    return True

CUSTOM_COMMANDS = \
{
    "cd": lambda args: filterArgs(args, 2) and os.chdir(args[1]),
    "exit": lambda args: filterArgs(args, 1) and sys.exit((len(args) > 1 and args[1]) or 0)
}

def evalScript(text, macros={}):
    text, macros = macroUtil.expandAndDefineMacros(text, macros, {}, {})
    return (runner.runCommand(text, CUSTOM_COMMANDS), macros)

# If run directly, open a small test-shell.
if __name__ == "__main__":
    ps1 = "$ "
    if "PS1" in os.environ:
        ps1 = os.environ["PS1"]
    
    macros = macroUtil.getDefaultMacros()

    while True:
        command = input(ps1)
        
        result, macros = evalScript(command, macros)
