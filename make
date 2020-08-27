#!/usr/bin/python3
import sys, os.path
from Includes.printUtil import *
import Includes.makeUtil as makeUtil
import Includes.macroUtil as macroUtil
from Includes.argsUtil import *

ARGUMENT_MAPPINGS = \
{
    'h': "help",
    'k': 'keep-going',
    'p': 'print-expanded',
#   'n': 'just-print', # To-do
    'f': 'file',
    'C': 'directory',
    's': 'silent',
    'b': 'built-in-shell'
}

# Don't save these when we recurse...
NO_SAVE_ARGS = \
{
    'C', 'directory',
    'f', 'file',
    'default'
}

def printHelp():
    cprint("Help: \n", FORMAT_COLORS['YELLOW'])
    cprint(" Summary: ", FORMAT_COLORS['YELLOW'])
    print("Satisfy dependencies of a target in a makefile. This parser is not quite POSIX compliant, but should be able to parse simple makefiles.")
    cprint(" Usage: make [targets...] [options]\n", FORMAT_COLORS['YELLOW'])
    print("  where each target in targets is a valid target and options include:")
    cprint("    -h, --help", FORMAT_COLORS['GREEN'])
    print("\t Print this message.")

    cprint("    --file", FORMAT_COLORS['GREEN'])
    print("\t File to parse (default is Makefile).")
    cprint("    -k", FORMAT_COLORS['GREEN'])
    print("\t\t Keep going if errors are encountered.")
    cprint("    -p", FORMAT_COLORS['GREEN'])
    print("\t\t Rather than finding targets, print the makefile, with top-level targets expanded.")
    cprint("    -C dir", FORMAT_COLORS['GREEN'])
    print("\t Switch to directory, dir, before running make. ")
    cprint("    -s, --silent", FORMAT_COLORS['GREEN'])
    print(" In most cases, don't print output.")
    cprint("    -b", FORMAT_COLORS['GREEN'])
    print("\t\t Use the built-in shell for commands in the makefile. This can also be enabled as follows:")
    cprint("   export ", FORMAT_COLORS['PURPLE'])
    print("_BUILTIN_SHELL ", end='')
    cprint(":= ", FORMAT_COLORS['YELLOW'])
    print("1 \t\t", end='')
    cprint("# Use the built-in shell instead of the system shell.", FORMAT_COLORS['GREEN'])
    print()
    cprint("   export", FORMAT_COLORS['PURPLE'])
    print(" _CUSTOM_BASE_COMMANDS ", end='')
    cprint(":= ", FORMAT_COLORS['YELLOW'])
    print("1 \t", end='')
    cprint("# Enable built-in overrides for several commands like ls, echo, and pwd.", FORMAT_COLORS['GREEN'])
    print()
    cprint("Note: ", FORMAT_COLORS['PURPLE'])
    print("Macro definitions that override those from the environment" +
" can be provided in addition to targets and options. For example,")
    cprint("    make target1 target2 target3 CC=gcc CFLAGS=-O3", FORMAT_COLORS['YELLOW'])
    print()
    print("should make target1, target2, and target3 with the " +
          "macros CC and CFLAGS by default set to gcc and -O3, respectively.")

# On commandline run...
if __name__ == "__main__":
    args = parseArgs(sys.argv, ARGUMENT_MAPPINGS)
    
    # Fill args from MAKEFLAGS (see https://www.gnu.org/software/make/manual/make.html#How-the-MAKE-Variable-Works)
    args = fillArgsFromEnv(args, "MAKEFLAGS", ARGUMENT_MAPPINGS) # Previously-defined args take precedence.
    saveArgsInEnv(args, "MAKEFLAGS", NO_SAVE_ARGS) # For recursive calls to make.
    
    if 'help' in args:
        printHelp()
    else:
        fileName = 'Makefile'
        targets = []
        
        defaultMacros = macroUtil.getDefaultMacros() # Fills with macros from environment, etc.
        overrideMacros = {}
        
        if 'directory' in args:
            try:
                os.chdir(args['directory'])
            except Exception as ex:
                print("Error changing directories: %s" % str(ex))
                sys.exit(1)
        
        # If we know the path to the python interpreter...
        if sys.executable:
            defaultMacros["MAKE"] = sys.executable + " " + os.path.abspath(__file__) 
                                #^ Use ourself, rather than another make implementation.

        if 'keep-going' in args:
            makeUtil.setStopOnError(False)
        
        if 'silent' in args:
            makeUtil.setSilent(True)

        if 'file' in args:
            fileName = args['file']

        if len(args['default']) > 0:
            targets = [ ]
            
            # Split into targets and default macros.
            for arg in args['default']:
                assignmentIndex = arg.find("=")
                if assignmentIndex > 0:
                    key = arg[:assignmentIndex].strip() # e.g. VAR in VAR=33
                    val = arg[assignmentIndex+1:].strip() # e.g. 33 in VAR=33
                    overrideMacros[key] = val
                    defaultMacros[key] = val
                else:
                    targets.append(arg)
	
	    # Were we told to use the built-in shell?
        if 'built-in-shell' in args:
            overrideMacros["_BUILTIN_SHELL"] = "1"
            overrideMacros["_CUSTOM_BASE_COMMANDS"] = "1"
	
        if len(targets) == 0: # Select the default target, if no targets
            targets = ['']
        
        if not os.path.exists(fileName):
            cprint("The file with name \"%s\" was not found!\n" % fileName, FORMAT_COLORS['RED'])
            print("Please check your spelling.")
            sys.exit(1)

        fileObj = open(fileName, 'r')
        fileContents = fileObj.read()
        fileObj.close()
        
        if not 'print-expanded' in args:
            # Run for each target.
            for target in targets:
                makeUtil.runMakefile(fileContents, target, defaultMacros, overrideMacros)
        else:
            contents, macros = macroUtil.expandMacros(fileContents, defaultMacros)
            print(contents)
