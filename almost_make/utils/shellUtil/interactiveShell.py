#!/usr/bin/python

import cmd, os, sys
import almost_make.utils.shellUtil.shellUtil as shell
import almost_make.utils.macroUtil as macroUtil
import almost_make.utils.shellUtil.escapeParser as escapeParser
from almost_make.utils.printUtil import *

# See https://docs.python.org/3/library/cmd.html
# TODO:
#  * Autocomplete using Cmd.completedefault.

class SimpleShell(cmd.Cmd):
    prompt = '$ '
    command = ''
    
    def __init__(self, useBaseCommands=True, defaultFlags={}):
        self.updatePrompt()
        self.macros = macroUtil.getDefaultMacros()
        self.defaultFlags = defaultFlags
        
        if useBaseCommands:
        	self.macros["_CUSTOM_BASE_COMMANDS"] = True # Use custom base commands for testing.
        
        macroUtil.setStopOnError(False)

        
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
            result, self.macros = shell.evalScript(self.command, self.macros, False, self.defaultFlags)
            
            if result != 0:
                cprint("Warning:", FORMAT_COLORS["YELLOW"])
                print(" Command exited with non-zero exit status, %s." % str(result))
        except Exception as e:
            cprint("Error running %s:\n%s" % (self.command, str(e)), FORMAT_COLORS["RED"])
            print()
        
        self.command = ""
        
        self.updatePrompt()

def main(baseCommands=True, flags=[ 'use-system-pipe' ]):
    SimpleShell(baseCommands, flags).cmdloop()

if __name__ == "__main__":
    main()
