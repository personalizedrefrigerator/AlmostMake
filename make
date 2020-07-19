#!python
import sys, os.path
from Includes.printUtil import *
from Includes.makeUtil import *
from Includes.argsUtil import *

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

# On commandline run...
if __name__ == "__main__":
    args = parseArgs(sys.argv,
    {
        'h': "help",
        'k': 'keep-going',
        'p': 'print-expanded'
    })
    
    if 'help' in args:
        printHelp()
    else:
        fileName = 'Makefile'
        targets = ['']

        if 'keep-going' in args:
            setStopOnError(False)

        if 'file' in args:
            fileName = args['file']

        if len(args['default']) > 0:
            targets = args['default']

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
                runMakefile(fileContents, target)
        else:
            contents, macros = expandMacros(fileContents)
            print(contents)
