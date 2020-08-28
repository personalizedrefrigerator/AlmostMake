#!python

# Parses very simple Makefiles.
# Useful Resources:
#  - Chris Wellons' "A Tutorial on Portable Makefiles". https://nullprogram.com/blog/2017/08/20/ Accessed August 22, 2020
#  - GNUMake: https://www.gnu.org/software/make/manual/make.html Accessed August 22, 2020
#  - BSDMake:  http://khmere.com/freebsd_book/html/ch01.html Accessed Aug 22 2020 

import re, sys, os, subprocess, time
from almost_make.utils.printUtil import *
import almost_make.utils.macroUtil as macroUtil
import almost_make.utils.shellUtil.shellUtil as shellUtil
import almost_make.utils.shellUtil.runner as runner
import almost_make.utils.errorUtil as errorUtil

# Regular expressions
SPACE_CHARS = re.compile("\\s")

# Constants.
RECIPE_START_CHAR = '\t'

# Options
SILENT = False

# Commands callable as $(COMMAND_NAME Arguments).
MACRO_COMMANDS = \
{   # See https://linuxhandbook.com/execute-shell-command-python/
    "shell": lambda code, macros: os.popen(code).read().rstrip(' \n\r\t')
}

# Send commands to macroUtil.py
macroUtil.setMacroCommands(MACRO_COMMANDS)
macroUtil.addMacroDefCondition(lambda line: not line.startswith(RECIPE_START_CHAR))
macroUtil.addLazyEvalCondition(lambda line: line.startswith(RECIPE_START_CHAR))

# Targets that are used by this parser/should be ignored.
MAGIC_TARGETS = \
{
    ".POSIX",
    ".SUFFIXES"
}

# Option-setting functions
def setStopOnError(stopOnErr):
    macroUtil.setStopOnError(stopOnErr)
    errorUtil.setStopOnError(stopOnErr)

def setSilent(silent):
    global SILENT
    SILENT = silent
    macroUtil.setSilent(silent)
    errorUtil.setSilent(silent)

# Get a tuple.
# First item: a map from target names
#   to tuples of (dependencies, action)
# Second item: A list of the targets
#   with recipies.
def getTargetActions(content):
    lines = content.split('\n')
    lines.reverse()
    
    result = {}
    currentRecipe = []
    targetNames = []
    specialTargetNames = []

    for line in lines:
        if line.startswith(RECIPE_START_CHAR):
            currentRecipe.append(line[len(RECIPE_START_CHAR) : ]) 
            # Use len() in case we decide to 
            # be less compliant and make it 
            # more than a character.
        elif len(line.strip()) > 0:
            if not ':' in line:
                if len(currentRecipe) > 0:
                    errorUtil.reportError("Pre-recipe line must contain separator! Line: %s" % line)
                else:
                    continue
            sepIndex = line.index(':')
            allGenerates = SPACE_CHARS.split(line[:sepIndex].strip())
            preReqs = line[sepIndex + 1 :].strip()
            
            # Get the dependencies.
            dependsOn = SPACE_CHARS.split(preReqs)
            for generates in allGenerates:
                currentDeps = []
                currentDeps.extend(dependsOn)
                if generates in result:
                    oldDeps, oldRecipe = result[generates]
                    currentDeps.extend(oldDeps)
                    oldRecipe.reverse()
                    currentRecipe.extend(oldRecipe)
# reportError("Multiple definitions for target %s. Line: %s" % (generates, line))
                # Clean up & add to output.
                outRecipe = [] + currentRecipe
                outRecipe.reverse()
                result[generates] = (currentDeps, outRecipe)

                if generates.startswith('.'):
                    specialTargetNames.append(generates)
                else:
                    targetNames.append(generates)
            currentRecipe = []
    # Move targets that start with a '.' to
    # the end...
    targetNames.reverse()
    targetNames.extend(specialTargetNames)
    return (result, targetNames)

# Generate [target] if necessary. Returns
# True if generated, False if not necessary.
def satisfyDependencies(target, targets, macros):
    target = target.strip()
    if not target in targets:
        # Can we generate a recipe?
        for key in targets.keys():
#            print("Checking target %s..." % key)
            if "%" in key:
                sepIndex = key.index("%")
                beforeContent = key[:sepIndex]
                afterContent = key[sepIndex + 1 :]
                if target.startswith(beforeContent) and target.endswith(afterContent):
                    deps, rules = targets[key]
                    newKey = target
                    newReplacement = newKey[sepIndex : len(newKey) - len(afterContent)]
                    deps = " ".join(deps)
                    deps = deps.split("%")
                    deps = newReplacement.join(deps)
                    deps = deps.split(" ")

                    targets[newKey] = (deps, rules)
                    break
            elif key.startswith(".") and "." in key[1:]:
                shortKey = key[1:] # Remove the first '.'
                parts = shortKey.split('.') # NOT a regex.
                requires = '.' + parts[0].strip()
                creates = '.' + parts[1].strip()
                
                # Don't evaluate... The user probably didn't intend for us to
                # make a recipe from this.
                if len(parts) > 2:
                    continue
                
                if not targets[".SUFFIXES"]:
                    continue
                
                validSuffixes,_ = targets[".SUFFIXES"]
                
                # Are these valid suffixes?
                if not creates in validSuffixes \
                        or not requires in validSuffixes:
                    continue
                
                # Does it fit the current target?
                if target.endswith(creates):
                    deps,rules = targets[key]
                    
                    newDeps = [ dep for dep in deps if dep != '' ]
                    withoutExtension = target[: - len(creates)]
                    
                    newDeps.append(withoutExtension + requires)
                    
                    targets[target] = (newDeps, rules)
                    break
    selfExists = os.path.exists(target)
    selfMTime = 0

    if not target in targets:
        if selfExists:
            return False
        else:
            errorUtil.reportError("No rule to make %s." % target)
            return True # If still running, the user wants us to exit successfully.
    runRecipe = False
    deps, commands = targets[target]
    
    if selfExists:
        selfMTime = os.path.getmtime(target)

    def isPhony(target):
        if not ".PHONY" in targets:
            return False
        
        phonyTargets,_ = targets['.PHONY']
        return target in phonyTargets or target in MAGIC_TARGETS
    selfPhony = isPhony(target)
    
    def needGenerate(other):
        return isPhony(other) \
            or not os.path.exists(other) \
            or selfMTime > os.path.getmtime(other) \
            or not selfExists \
            or selfPhony

    if isPhony(target):
        runRecipe = True

    if not runRecipe:
        if not selfExists:
            runRecipe = True
        else:
            for dep in deps:
                if isPhony(dep) or \
                    not os.path.exists(dep) \
                    or os.path.getmtime(dep) >= selfMTime:
                        runRecipe = True
                        break
    # Generate each dependency, if necessary.
    if not runRecipe:
        return False
    
    for dep in deps:
#        print("Checking dep %s; %s" % (dep, str(needGenerate(dep))))
        if dep.strip() != "" and needGenerate(dep):
            satisfyDependencies(dep, targets, macros)
    # Here, we know that
    # (1) all dependencies are satisfied
    # (2) we need to run each command in recipe.
    # Define several macros the client will expect here:
    macros["@"] = target
    macros["^"] = " ".join(deps)
    if len(deps) >= 1:
        macros["<"] = deps[0]

    for command in commands:
        command = macroUtil.expandMacroUsages(command, macros).strip()
        if command.startswith("@"):
            command = command[1:]
        elif not SILENT:
            print(command)
        haltOnFail = not command.startswith("-")
        if command.startswith("-"):
            command = command[1:]
        try:
            status = 0
            
            if not "_BUILTIN_SHELL" in macros:
            	status = subprocess.run(command, shell=True, check=True).returncode
            else:
            	defaultFlags = []
            	
            	if "_SYSTEM_SHELL_PIPES" in macros:
            	    defaultFlags.append(runner.USE_SYSTEM_PIPE)
            	
            	status,_ = shellUtil.evalScript(command, macros, defaultFlags = defaultFlags)
            
            if status != 0 and haltOnFail:
            	errorUtil.reportError("Command %s exited with non-zero exit status, %s." % (command, str(status)))
        except Exception as e:
            if haltOnFail: # e.g. -rm foo should be silent even if it cannot remove foo.
                errorUtil.reportError("Unable to run command:\n    ``%s``. \n\n  Message:\n%s" % (command, str(e)))
    return True

# Run commands specified to generate
# dependencies of target by the contents
# of the makefile given in contents.
def runMakefile(contents, target = '', defaultMacros={ "MAKE": "make" }, overrideMacros={}):
    contents, macros = macroUtil.expandAndDefineMacros(contents, defaultMacros)
    targetRecipes, targets = getTargetActions(contents)

    if target == '' and len(targets) > 0:
        target = targets[0]

    # Fill override macros.
    for macroName in overrideMacros:
        macros[macroName] = overrideMacros[macroName]

    satisfied = satisfyDependencies(target, targetRecipes, macros)

    if not satisfied and not SILENT:
        print("Not hing to be done for target ``%s``." % target)
