#!/usr/bin/python3

# See https://danishpraka.sh/2018/09/27/shell-in-python.html (Accessed Aug 22)

import cmd

from Includes.cprint import *
from Includes.shellUtil.runner import runCommand

SHELL_NAME = "AlmostMake's NotQuiteAShell"

QUICK_HELP = \
{
    "cd": """cd [directory]
Change the current working directory to [directory].
This command is provided by %s.""" % SHELL_NAME,
}

class SimpleShell(cmd.Cmd):
    intro = 'Welcome to SimpleShell, an extremely simple shell.'
    def __init__(self):
        cmd.Cmd.__init__(self)



