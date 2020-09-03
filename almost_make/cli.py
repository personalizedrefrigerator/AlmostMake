#!/usr/bin/python3
import sys, os
from almost_make.utils.printUtil import *
import almost_make.utils.makeUtil as makeUtility
import almost_make.utils.macroUtil as macroUtility
from almost_make.utils.argsUtil import *
from almost_make import version

ARGUMENT_MAPPINGS = \
{
    'h': "help",
    'k': 'keep-going',
    'p': 'print-expanded',
    'n': 'just-print',
    'f': 'file',
    'C': 'directory',
    's': 'silent',
    'b': 'built-in-shell',
    'w': 'print-directory',
    'j': 'jobs'
}

# These are flags, so don't associate values with them...
JUST_FLAGS = \
{
    'help', 'keep-going', 'print-expanded', 'just-print', 'silent', 'built-in-shell',
    'print-directory'
}

# Don't save these when we recurse...
NO_SAVE_ARGS = \
{
    'C', 'directory',
    'f', 'file',
    'default',
    'h', 'help', 
    'version'
}

def printHelp():
    cprint("Help: \n", FORMAT_COLORS['YELLOW'])
    cprint(" Summary: ", FORMAT_COLORS['YELLOW'])
    print("Satisfy dependencies of a target in a makefile. This parser is not quite POSIX-compliant, but should be able to parse simple makefiles.")
    cprint(" Usage: almake [targets...] [options]\n", FORMAT_COLORS['YELLOW'])
    print("  where each target in targets is a valid target and options include:")
    cprint("    -h, --help", FORMAT_COLORS['GREEN'])
    print("\t\t\t Print this message.")
    cprint("    --version", FORMAT_COLORS['GREEN'])
    print("\t\t\t Print version and licensing information.")
    cprint("    --file", FORMAT_COLORS['GREEN'])
    print("\t\t\t File to parse (default is Makefile).")
    cprint("    -k", FORMAT_COLORS['GREEN'])
    print("\t\t\t\t Keep going if errors are encountered.")
    cprint("    -n, --just-print", FORMAT_COLORS['GREEN'])
    cprint("\t\t Just print commands to be run, without evaluating (print commands, don't send them to the shell). ")
    print("Be aware that $(shell ...) macros are still evaluated. This option only applies to individual commands.")
    cprint("    -p", FORMAT_COLORS['GREEN'])
    print("\t\t\t\t Rather than finding targets, print the makefile, with top-level targets expanded.")
    cprint("    -C dir", FORMAT_COLORS['GREEN'])
    print("\t\t\t Switch to directory, dir, before running make. ")
    cprint("    -w, --print-directory", FORMAT_COLORS['GREEN'])
    print("\t Print the current directory before and after running make. ")
    cprint("    -j, --jobs", FORMAT_COLORS['GREEN'])
    print("\t\t\t Maximum number of jobs (e.g. almake -j 8). ")
    cprint("    -s, --silent", FORMAT_COLORS['GREEN'])
    print("\t\t In most cases, don't print output.")
    cprint("    -b, --built-in-shell", FORMAT_COLORS['GREEN'])
    print("\t Use the built-in shell for commands in the makefile. This can also be enabled as follows:")
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
    cprint("# Enable built-in overrides for several commands like ls, echo, cat, grep, and pwd.", FORMAT_COLORS['GREEN'])
    print()
    cprint("   export", FORMAT_COLORS['PURPLE'])
    print(" _SYSTEM_SHELL_PIPES ", end='')
    cprint(":= ", FORMAT_COLORS['YELLOW'])
    print("1 \t", end='')
    cprint("# Send commands that seem related to pipes (e.g. ls | less) directly to the system's shell. ", FORMAT_COLORS['GREEN'])
    print()
    cprint("Note: ", FORMAT_COLORS['PURPLE'])
    print("AlmostMake's built-in shell is currently very limited.")
    print()
    cprint("Note: ", FORMAT_COLORS['PURPLE'])
    print("Macro definitions that override those from the environment" +
" can be provided in addition to targets and options. For example,")
    cprint("    make target1 target2 target3 CC=gcc CFLAGS=-O3", FORMAT_COLORS['YELLOW'])
    print()
    print("should make target1, target2, and target3 with the " +
          "macros CC and CFLAGS by default set to gcc and -O3, respectively.")
    cprint("Note: ", FORMAT_COLORS['PURPLE'])
    print("Options can also be given to almake through the environment. " +
    	  "This is done through the MAKEFLAGS variable. For example, " +
    	  "setting MAKEFLAGS to --built-in-shell causes almake to " +
    	  "always use its built-in shell, rather than the system shell.")

# On commandline run...
def main(args=sys.argv):
    args = parseArgs(args, ARGUMENT_MAPPINGS, strictlyFlags=JUST_FLAGS)
    
    # Fill args from MAKEFLAGS (see https://www.gnu.org/software/make/manual/make.html#How-the-MAKE-Variable-Works)
    args = fillArgsFromEnv(args, "MAKEFLAGS", ARGUMENT_MAPPINGS, JUST_FLAGS) # Previously-defined args take precedence.
    saveArgsInEnv(args, "MAKEFLAGS", NO_SAVE_ARGS) # For recursive calls to make.
    
    if 'help' in args:
        printHelp()
    elif 'version' in args:
        version.printVersion()
    else:
        macroUtil = macroUtility.MacroUtil()
        makeUtil = makeUtility.MakeUtil()

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

        if 'jobs' in args:
            jobs = 1
            try:
                jobs = int(args['jobs'])
            except ValueError as ex:
                makeUtil.errorUtil.reportError("Invalid argument to --jobs. This must be an integer.")
            makeUtil.setMaxJobs(jobs)

        if 'just-print' in args:
            makeUtil.setJustPrint(True)

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

        if 'print-directory' in args:
            cprint("make: ", FORMAT_COLORS['YELLOW'])
            print ('Entering directory %s' % runner.quote(os.getcwd()))
        
        if not 'print-expanded' in args:
            # Run for each target.
            for target in targets:
                makeUtil.runMakefile(fileContents, target, defaultMacros, overrideMacros)
        else:
            contents, macros = macroUtil.expandMacros(fileContents, defaultMacros)
            print(contents)

        if 'print-directory' in args:
            cprint("make: ", FORMAT_COLORS['YELLOW'])
            print ('Leaving directory %s' % runner.quote(os.getcwd()))

if __name__ == "__main__":
    main()
