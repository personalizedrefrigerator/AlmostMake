#!/usr/bin/python

import cmd, os, sys
import almost_make.utils.shellUtil.shellUtil as shell
import almost_make.utils.shellUtil.runner as runner
import almost_make.utils.macroUtil as macroUtility
import almost_make.utils.shellUtil.escapeParser as escapeParser
from almost_make.utils.printUtil import *

from almost_make.utils.argsUtil import parseArgs
from almost_make.version import printVersion

# See https://docs.python.org/3/library/cmd.html
# TODO:
#  * Autocomplete using Cmd.completedefault.

class SimpleShell(cmd.Cmd):
    prompt = '$ '
    command = ''
    macroUtil = macroUtility.MacroUtil()
    
    def __init__(self, useBaseCommands=True, defaultFlags={}):
        self.updatePrompt()
        self.macros = self.macroUtil.getDefaultMacros()
        self.defaultFlags = defaultFlags
        
        if useBaseCommands:
        	self.macros["_CUSTOM_BASE_COMMANDS"] = True # Use custom base commands for testing.
        
        self.macroUtil.setStopOnError(False)

        
        cmd.Cmd.__init__(self)
    
    def updatePrompt(self):
        if "PS1" in os.environ:
            self.prompt = escapeParser.parseEscapes(os.environ["PS1"])
        else:
            self.prompt = '$ '
        
        if self.command != "":
            if "PS2" in os.environ:
                self.prompt = escapeParser.parseEscapes(os.environ["PS2"])
            else:
                self.prompt = ". "
    
    def precmd(self, line):
        return line
    
    def default(self, line):
        if line == "EOF":
            sys.exit(0)
    
        if line.strip().endswith('\\'):
            line = line.strip()
            
            self.command += line[0:len(line) - 1]
            self.updatePrompt()
            
            return
        else:
            self.command += line
        
        try:
            result, self.macros = shell.evalScript(self.command, self.macroUtil, self.macros, False, self.defaultFlags)
            
            if result != 0:
                cprint("Warning:", FORMAT_COLORS["YELLOW"])
                print(" Command exited with non-zero exit status, %s." % str(result))
        except Exception as e:
            cprint("Error running %s:\n%s" % (self.command, str(e)), FORMAT_COLORS["RED"])
            print()
        
        self.command = ""
        
        self.updatePrompt()

ARG_MAPPINGS = \
{
    'h': 'help',
    'v': 'version',
    'B': 'without-builtins',
    'p': 'system-pipe'
}

def printHelp():
    cprint("Help: \n", FORMAT_COLORS['YELLOW'])
    cprint(" Summary: ", FORMAT_COLORS['YELLOW'])
    print("Run an interactive version of the shell built into almake. This is a POSIX-like shell. It is not POSIX-compliant.")
    cprint(" Usage: almake_shell [options]\n", FORMAT_COLORS['YELLOW'])
    print("  ...where options include:")
    cprint("    -h, --help", FORMAT_COLORS['GREEN'])
    print("\t Print this message.")
    cprint("    --version", FORMAT_COLORS['GREEN'])
    print("\t Print version and licensing information.")
    cprint("    -B, --without-builtins", FORMAT_COLORS['GREEN'])
    print("\t Do not (re)define built-in commands (like echo). By default, echo, ls, dir, pwd, and perhaps other commands," +
    " are defined and override any commands with the same name already present in the system.")
    cprint("    -p, --system-pipe", FORMAT_COLORS['GREEN'])
    print("\t Rather than attempting to pipe output between commands (e.g. in ls | grep foo), send piped portions of the input " +
        "to the system's shell.")

def main():
    args = parseArgs(sys.argv, ARG_MAPPINGS)
    
    if 'help' in args:
        printHelp()
        sys.exit(1)
    elif 'version' in args:
        printVersion()
        sys.exit(1)
    else:
        builtins = True
        flags = []

        if 'without-builtins' in args:
            builtins = False

        if 'system-pipe' in args:
            flags.append(runner.USE_SYSTEM_PIPE)

        SimpleShell(builtins, flags).cmdloop()



if __name__ == "__main__":
    main()
