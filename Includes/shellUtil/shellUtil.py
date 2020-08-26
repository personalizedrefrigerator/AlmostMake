#!/usr/bin/python3

# See https://danishpraka.sh/2018/09/27/shell-in-python.html (Accessed Aug 22)

import cmd, os, sys

from Includes.printUtil import *
from Includes.shellUtil.runner import runCommand

SHELL_NAME = "AlmostMake's NotQuiteAShell"

QUICK_HELP = \
{
    "cd": """cd [directory]
Change the current working directory to [directory].
This command is provided by %s.""" % SHELL_NAME,
}

if __name__ == "__main__":
    ps1 = "$ "
    if ps1 in os.environ:
        ps1 = os.environ["PS1"]

    while True:
        command = input(ps1)
        
        if command == "quit":
            sys.exit(0)
        
        runCommand(command)
