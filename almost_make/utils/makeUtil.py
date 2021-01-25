#!/usr/bin/python3

# Parses very simple Makefiles.
# Useful Resources:
#  - Chris Wellons' "A Tutorial on Portable Makefiles". https://nullprogram.com/blog/2017/08/20/ Accessed August 22, 2020
#  - GNUMake: https://www.gnu.org/software/make/manual/make.html Accessed August 22, 2020
#  - BSDMake:  http://khmere.com/freebsd_book/html/ch01.html Accessed Aug 22 2020 

import re, sys, os, subprocess, time, threading, shlex
# from concurrent.futures import ThreadPoolExecutor # We are **not** using this because adding an 
#                                                   # executor to the queue when in an executed thread can cause deadlock! See 
#                                                   # https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor

from almost_make.utils.printUtil import cprint
import almost_make.utils.macroUtil as macroUtility
import almost_make.utils.shellUtil.shellUtil as shellUtility
import almost_make.utils.shellUtil.runner as runner
import almost_make.utils.shellUtil.globber as globber
import almost_make.utils.shellUtil.escapeParser as escaper
import almost_make.utils.errorUtil as errorUtility

# Regular expressions
SPACE_CHARS = re.compile(r'\s+')
INCLUDE_DIRECTIVE_EXP = re.compile(r"^\s*(include|\.include|-include|sinclude)\s+")

# Targets that are used by this parser/should be ignored.
MAGIC_TARGETS = \
{
    ".POSIX",
    ".SUFFIXES"
}

class MakeUtil:
    recipeStartChar = '\t'
    silent = False
    macroCommands = {}
    maxJobs = 1
    currentJobs = 1 # Number of currently running jobs...
    jobLock = threading.Lock()
    pending = {} # Set of pending jobs.
    justPrint = False # Print commands, without evaluating.

    def __init__(self):
        self.macroCommands["words"] = lambda argstring, macros: str(len(SPACE_CHARS.split(self.macroUtil.expandMacroUsages(argstring, macros))))
        self.macroCommands["sort"] = lambda argstring, macros: " ".join(sorted(list(set(SPACE_CHARS.split(self.macroUtil.expandMacroUsages(argstring, macros))))))
        self.macroCommands["strip"] = lambda argstring, macros: argstring.strip()

        self.macroCommands["shell"] = lambda code, macros: os.popen(self.macroUtil.expandMacroUsages(code, macros)).read().rstrip(' \n\r\t') # To-do: Use the built-in shell if specified...
        self.macroCommands["wildcard"] = lambda argstring, macros: " ".join([ shlex.quote(part) for part in self.glob(self.macroUtil.expandMacroUsages(argstring, macros), macros) ])
        self.macroCommands["dir"] = lambda argstring, macros: " ".join([ os.path.dirname(arg) for arg in SPACE_CHARS.split(self.macroUtil.expandMacroUsages(argstring, macros)) ])
        self.macroCommands["notdir"] = lambda argstring, macros: " ".join([ os.path.basename(arg) for arg in SPACE_CHARS.split(self.macroUtil.expandMacroUsages(argstring, macros)) ])
        self.macroCommands["abspath"] = lambda argstring, macros: " ".join([ os.path.abspath(arg) for arg in SPACE_CHARS.split(self.macroUtil.expandMacroUsages(argstring, macros)) ])
        self.macroCommands["realpath"] = lambda argstring, macros: " ".join([ os.path.realpath(arg) for arg in SPACE_CHARS.split(self.macroUtil.expandMacroUsages(argstring, macros)) ])

        self.macroCommands["subst"] = lambda argstring, macros: self.makeCmdSubst(argstring, macros)
        self.macroCommands["patsubst"] = lambda argstring, macros: self.makeCmdSubst(argstring, macros, True)
        self.macroCommands["firstword"] = lambda argstring, macros: self.getWordOf(argstring, macros, selectWord = 0)
        self.macroCommands["lastword"] = lambda argstring, macros: self.getWordOf(argstring, macros, selectWord = -1)
        self.macroCommands["word"] = lambda argstring, macros: self.getWordOf(argstring, macros)
        # self.macroCommands["filter"] # pattern...,text

        self.errorUtil = errorUtility.ErrorUtil()
        self.macroUtil = macroUtility.MacroUtil()

        self.macroUtil.enableConditionals() # ifeq, ifdef, etc.

        self.macroUtil.setMacroCommands(self.macroCommands)
        self.macroUtil.addMacroDefCondition(lambda line: not line.startswith(self.recipeStartChar))
        self.macroUtil.addLazyEvalCondition(lambda line: line.startswith(self.recipeStartChar))

    def setStopOnError(self, stopOnErr):
        self.macroUtil.setStopOnError(stopOnErr)
        self.errorUtil.setStopOnError(stopOnErr)

    def setSilent(self, silent):
        self.silent = silent
        self.macroUtil.setSilent(silent)
        self.errorUtil.setSilent(silent)
    
    def setJustPrint(self, justPrint):
        self.justPrint = justPrint

    # Set the maximum number of threads used to evaluate targets.
    # Note, however, that use of a recursive build-system may cause more than
    # this number of jobs to be used/created.
    def setMaxJobs(self, maxJobs):
        self.maxJobs = maxJobs

    # Get a tuple.
    # First item: a map from target names
    #   to tuples of (dependencies, action)
    # Second item: A list of the targets
    #   with recipies.
    def getTargetActions(self, content):
        lines = content.split('\n')
        lines.reverse()
        
        result = {}
        currentRecipe = []
        targetNames = []
        specialTargetNames = []

        for line in lines:
            if line.startswith(self.recipeStartChar):
                currentRecipe.append(line[len(self.recipeStartChar) : ]) 
                # Use len() in case we decide to 
                # be less compliant and make it 
                # more than a character.
            elif len(line.strip()) > 0:
                if not ':' in line:
                    if len(currentRecipe) > 0:
                        self.errorUtil.reportError("Pre-recipe line must contain separator! Line: %s" % line)
                    else:
                        continue
                sepIndex = line.index(':')

                # Get what is generated.
                allGenerates = runner.shSplit(line[:sepIndex].strip(), { ' ', '\t', '\n', ';' })
                allGenerates = runner.removeEqual(allGenerates, ';')
                allGenerates = runner.removeEmpty(allGenerates)

                # Get the dependencies.
                preReqs = line[sepIndex + 1 :].strip()
                dependsOn = runner.shSplit(preReqs, { ' ', '\t', '\n', ';' })
                dependsOn = runner.removeEqual(dependsOn, ';')
                dependsOn = runner.removeEmpty(dependsOn)

                for generates in allGenerates:
                    currentDeps = []
                    currentDeps.extend(dependsOn)
                    if generates in result:
                        oldDeps, oldRecipe = result[generates]
                        currentDeps.extend(oldDeps)
                        oldRecipe.reverse()
                        currentRecipe.extend(oldRecipe)
                    
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

    # Get a list of directories (including the current working directory)
    # from macros['VPATH']. Returns an array with one element, the current working
    # directory, if there is no 'VPATH' macro.
    def getSearchPath(self, macros):
        searchPath = [ os.path.abspath('.') ]
        
        if not 'VPATH' in macros:
            return searchPath

        vpath = macros['VPATH']

        # Split first by ';', then by ':', then finally,
        # try to split by space characters.
        splitOrder = [';', ':', ' ']
        split = []
        for char in splitOrder:
            split = escaper.escapeSafeSplit(vpath, char, True)
            split = runner.removeEmpty(split)

            if len(split) > 1:
                break
        
        searchPath.extend([ os.path.normcase(part) for part in split ])

        return searchPath

    # Find a file with relative path [givenPath]. If 
    # VPATH is in macros, search each semi-colon, colon,
    # or space-separated entry for the file. Returns the 
    # path to the file, or None, if the file does not exist.
    def findFile(self, givenPath, macros):
        givenPath = os.path.normcase(givenPath)
        
        searchPath = self.getSearchPath(macros)

        for part in searchPath:
            path = os.path.join(part, givenPath)

            if os.path.exists(path):
                return path
        return None

    # Glob [text], but search [VPATH] for additional matches.
    def glob(self, text, macros):
        if not 'VPATH' in macros:
            return globber.glob(text, '.')
        
        searchPath = self.getSearchPath(macros)
        result = globber.glob(text, '.', [])
        text = os.path.normcase(text)

        for part in searchPath:
            result.extend(globber.glob(os.path.join(part, text), '.', []))
        
        # Act like system glob. If we didn't find anything, 
        # return [ text ] 
        if len(result) == 0:
            result = [ text ]
        
        return result

    # Glob all elements in arr, but not the first.
    def globArgs(self, arr, macros, excludeFirst=True):
        result = []
        isFirst = excludeFirst

        for part in arr:
            if not runner.isQuoted(part.strip()) and not isFirst:
                result.extend(self.glob(part, macros))
            else:
                result.append(part)
                isFirst = False
        
        return result

    # Generate a recipe for [target] and add it to [targets].
    # Returns True if there is now a recipe for [target] in [targets],
    #  False otherwise.
    def generateRecipeFor(self, target, targets, macros):
        if target in targets:
            return True
        
        generatedTarget = False

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
                    generatedTarget = True
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
                
                if not ".SUFFIXES" in targets:
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
                    generatedTarget = True
                    break
        return generatedTarget

    # Return True iff [target] is not a "phony" target
    # (as declared by .PHONY). [targets] is the list of all
    # targets.
    def isPhony(self, target, targets):
        if not ".PHONY" in targets:
            return False
        
        phonyTargets,_ = targets['.PHONY']
        return target in phonyTargets or target in MAGIC_TARGETS

    # Get whether [target] needs to be (re)generated. If necessary,
    # creates a rule for [target] and adds it to [targets].
    def prepareGenerateTarget(self, target, targets, macros, visitedSet=None):
        target = target.strip()
        
        if not target in targets:
            self.generateRecipeFor(target, targets, macros)
        
        if visitedSet is None:
            visitedSet = set()
        
        if not target in visitedSet:
            visitedSet.add(target)
        else: # Circular dependency?
            self.errorUtil.reportError("Circular dependency involving %s!" % target)
            return True
        
        targetPath = self.findFile(target, macros)
        selfExists = targetPath != None
        selfMTime = 0

        if not target in targets:
            if selfExists:
                return False
            else:
                # This is an error! We need to generate the target, but
                # there is no rule for it!
                self.errorUtil.reportError("No rule to make %s." % target)
                return False # If still running, we can't generate this.
        
        deps, _ = targets[target]
        deps = self.globArgs(runner.removeEmpty(deps), macros, False) # Glob the set of dependencies.
        
        if selfExists:
            selfMTime = os.path.getmtime(targetPath)
        else:
            return True
        
        if self.isPhony(target, targets):
            return True
        
        for dep in deps:
            if self.isPhony(dep, targets):
                return True
            
            pathToOther = self.findFile(dep, macros)

            # If it doesn't exist...
            if pathToOther == None:
                return True

            # If we're older than it...
            if selfMTime < os.path.getmtime(pathToOther):
                return True

            if self.prepareGenerateTarget(dep, targets, macros, visitedSet):
                return True
        return False

    # Generate [target] if necessary (i.e. run recipes to create). Returns
    # True if generated, False if not necessary.
    def satisfyDependencies(self, target, targets, macros):
        target = target.strip()

        if not self.prepareGenerateTarget(target, targets, macros):
            return False
        
        targetPath = self.findFile(target, macros)

        deps, commands = targets[target]
        deps = self.globArgs(runner.removeEmpty(deps), macros, False) # Glob the set of dependencies.
        
        depPaths = []
        
        for dep in deps:
            if self.isPhony(dep, targets):
                depPaths.append(dep)
            else:
                depPaths.append(self.findFile(dep, macros) or dep)
        
        pendingJobs = []

        for dep in deps:
    #        print("Checking dep %s; %s" % (dep, str(needGenerate(dep))))
            if dep.strip() != "" and self.prepareGenerateTarget(dep, targets, macros):
                self.jobLock.acquire()
                if self.currentJobs < self.maxJobs and not dep in self.pending:
                    self.currentJobs += 1
                    self.jobLock.release()

                    self.pending[dep] = threading.Thread(target=self.satisfyDependencies, args=(dep, targets, macros))

                    pendingJobs.append(dep)
                else:
                    self.jobLock.release()
                    self.satisfyDependencies(dep, targets, macros)

        for job in pendingJobs:
            self.pending[job].start()

        # Wait for all pending jobs to complete.
        for job in pendingJobs:
            self.pending[job].join()
            self.pending[job] = None

            self.jobLock.acquire()
            self.currentJobs -= 1
            self.jobLock.release()

        # Here, we know that
        # (1) all dependencies are satisfied
        # (2) we need to run each command in recipe.
        # Define several macros the client will expect here:
        macros["@"] = targetPath or target
        macros["^"] = " ".join(depPaths)
        if len(deps) >= 1:
            macros["<"] = depPaths[0]

        for command in commands:
            command = self.macroUtil.expandMacroUsages(command, macros).strip()
            if command.startswith("@"):
                command = command[1:]
            elif not self.silent:
                print(command)
            haltOnFail = not command.startswith("-")
            if command.startswith("-"):
                command = command[1:]
            
            origDir = os.getcwd()

            try:
                status = 0
                
                if self.justPrint:
                    print(command)
                elif not "_BUILTIN_SHELL" in macros:
                    status = subprocess.run(command, shell=True, check=True).returncode
                else:
                    defaultFlags = []
                    
                    if "_SYSTEM_SHELL_PIPES" in macros:
                        defaultFlags.append(runner.USE_SYSTEM_PIPE)
                    
                    status,_ = shellUtility.evalScript(command, self.macroUtil, macros, defaultFlags = defaultFlags)
                
                if status != 0 and haltOnFail:
                    self.errorUtil.reportError("Command %s exited with non-zero exit status, %s." % (command, str(status)))
            except Exception as e:
                if haltOnFail: # e.g. -rm foo should be silent even if it cannot remove foo.
                    self.errorUtil.reportError("Unable to run command:\n    ``%s``. \n\n  Message:\n%s" % (command, str(e)))
            finally:
                # We should not switch directories, regardless of the command's result.
                # Some platforms (e.g. a-Shell) do not reset the cwd after child processes exit.
                if os.getcwd() != origDir:
                    os.chdir(origDir)
        return True
    
    # Handle all .include and include directives, as well as any conditionals.
    def handleIncludes(self, contents, macros):
        lines = self.macroUtil.getLines(contents)
        lines.reverse()

        newLines = []
        inRecipe = False

        for line in lines:
            if line.startswith(self.recipeStartChar):
                inRecipe = True
            elif inRecipe:
                inRecipe = False
            elif INCLUDE_DIRECTIVE_EXP.search(line) != None:
                line = self.macroUtil.expandMacroUsages(line, macros)
                
                parts = runner.shSplit(line)
                command = parts[0].strip()

                parts = self.globArgs(parts, macros) # Glob all, except the first...
                parts = parts[1:] # Remove leading include...
                ignoreError = False

                # Safe including?
                if command.startswith('-') or command.startswith('s'):
                    ignoreError = True

                for fileName in parts:
                    fileName = runner.stripQuotes(fileName)

                    if not os.path.exists(fileName):
                        foundName = self.findFile(fileName, macros)

                        if foundName != None:
                            fileName = foundName

                    if not os.path.exists(fileName):
                        if ignoreError:
                            continue

                        self.errorUtil.reportError("File %s does not exist. Context: %s" % (fileName, line))
                        return (contents, macros)
                    
                    if not os.path.isfile(fileName):
                        if ignoreError:
                            continue
                            
                        self.errorUtil.reportError("%s is not a file! Context: %s" % (fileName, line))
                        return (contents, macros)

                    try:
                        with open(fileName, 'r') as file:
                            contents = file.read().split('\n')
                            contents.reverse() # We're reading in reverse, so write in reverse.

                            newLines.extend(contents)
                        continue
                    except IOError as ex:
                        if ignoreError:
                            continue
                        
                        self.errorUtil.reportError("Unable to open %s: %s. Context: %s" % (fileName, str(ex), line))
                        return (contents, macros)
            newLines.append(line)

        newLines.reverse()

        return self.macroUtil.expandAndDefineMacros("\n".join(newLines), macros)

    ## Macro commands.

    # Example: $(subst foo,bar,foobar baz) -> barbar baz
    # See https://www.gnu.org/software/make/manual/html_node/Syntax-of-Functions.html#Syntax-of-Functions
    #     and https://www.gnu.org/software/make/manual/html_node/Text-Functions.html
    def makeCmdSubst(self, argstring, macros, patternBased=False):
        args = argstring.split(',')

        if len(args) < 3:
            self.errorUtil.reportError("Too few arguments given to subst function. Arguments: %s" % ','.join(args))

        firstThreeArgs = args[:3]
        firstThreeArgs[2] = ','.join(args[2:])
        args = firstThreeArgs

        replaceText = self.macroUtil.expandMacroUsages(args[0], macros)
        replaceWith = self.macroUtil.expandMacroUsages(args[1], macros)
        text        = self.macroUtil.expandMacroUsages(args[2], macros)

        if not patternBased:
            return re.sub(re.escape(replaceText), replaceWith, text)
        else: # Using $(patsubst pattern,replacement,text)
            words = SPACE_CHARS.split(text.strip())
            result = []

            pattern = escaper.escapeSafeSplit(replaceText, '%', '\\')
            replaceWith = escaper.escapeSafeSplit(replaceWith, '%', '\\')

            replaceAll = False
            replaceExact = False
            staticReplace = False

            if len(pattern) == 1:
                replaceAll = pattern == ''
                replaceExact = pattern[0]
            
            if len(replaceWith) <= 1:
                staticReplace = True

            while len(pattern) < 2:
                pattern.append('')
            while len(replaceWith) < 2:
                replaceWith.append('')
            
            pattern[1] = '%'.join(pattern[1:])
            replaceWith[1] = '%'.join(replaceWith[1:])

            for word in words:
                if replaceExact == False and (replaceAll or  word.startswith(pattern[0]) and word.endswith(pattern[1])):
                    if not staticReplace:
                        result.append(replaceWith[0] + word[len(pattern[0]) : -len(pattern[1])] + replaceWith[1])
                    else:
                        result.append(replaceWith[0])
                elif replaceExact == word.strip():
                    result.append('%'.join(runner.removeEmpty(replaceWith)))
                else:
                    result.append(word)
            
            return " ".join(runner.removeEmpty(result))

    # Example: $(word 3, get the third word) -> third
    # If the word with the given index does not exist, return
    # the empty string.
    # Ref: https://www.gnu.org/software/make/manual/html_node/Text-Functions.html#index-word
    # 
    # Note:
    #    If [selectWord] is not None, then attempt to select the specified word.
    #    For example, getWordOf(..., selectWord=-1) selects the last word in argstring.
    #    If selectWord is None, then determine the word to select from the contents of 
    #    [argstring].
    def getWordOf(self, argstring, macros, selectWord=None):
        selectIndex = selectWord
        argText = argstring.strip()

        if selectIndex is None:
            args = argstring.split(',')
            
            if len(args) <= 1:
                self.errorUtil.reportError(
                    "Not enough arguments to word selection macro. Context: %s" % argstring
                )

                return ""
            
            selectIndexText = self.macroUtil.expandMacroUsages(args[0], macros)

            try:
                # From argstring (one-indexed) => string indicies (zero-indicies).
                selectIndex = int(selectIndexText) - 1
                argText = ','.join(args[1:]).strip()
            except ValueError:
                self.errorUtil.reportError(
                    "First argument to word selection macros must be an integer. Context: %s"
                        % argstring
                )
                return ""
        
        argText = self.macroUtil.expandMacroUsages(argText, macros)
        words = SPACE_CHARS.split(argText)

        # TODO: Is there a way to do this with if-statements?
        try:
            return words[selectIndex]
        except IndexError:
            return ""



    ## Intended for use directly by clients:

    # Run commands specified to generate
    # dependencies of target by the contents
    # of the makefile given in contents.
    def runMakefile(self, contents, target = '', defaultMacros={ "MAKE": "almake" }, overrideMacros={}):
        contents, macros = self.macroUtil.expandAndDefineMacros(contents, defaultMacros)
        contents, macros = self.handleIncludes(contents, macros)
        targetRecipes, targets = self.getTargetActions(contents)

        if target == '' and len(targets) > 0:
            target = targets[0]

        # Fill override macros.
        for macroName in overrideMacros:
            macros[macroName] = overrideMacros[macroName]

        satisfied = self.satisfyDependencies(target, targetRecipes, macros)

        if not satisfied and not self.silent:
            print("Nothing to be done for target ``%s``." % target)
        
        return (satisfied, macros)
