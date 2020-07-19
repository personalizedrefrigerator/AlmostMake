#!python

import re, sys, os.path, subprocess

# Options
STOP_ON_ERROR = True

# Regular expressions
MACRO_NAME_EXP = "[a-zA-Z0-9_\\@\\^\\<]"
MACRO_NAME_CHAR_REGEXP = re.compile(MACRO_NAME_EXP)
MACRO_SET_REGEXP = re.compile("\\s*\\:?\\=\\s*")
IS_MACRO_DEF_REGEXP = re.compile("^%s+\\s*\\:?\\=.*" % MACRO_NAME_EXP, re.IGNORECASE)
IS_MACRO_INVOKE_REGEXP = re.compile(".*(?:^|[^\\$])[\\(]?%s+[\\)]?" % MACRO_NAME_EXP)
WHITESPACE = re.compile("\s")

RECIPE_START_CHAR = '\t'
COMMENT_CHAR = '#'

# Commands callable as $(COMMAND_NAME Arguments).
MACRO_COMMANDS = \
{
    "shell": lambda code, macros: subprocess.check_output(code).decode('utf-8').rstrip(' \n\r\t')
}

def reportError(message):
    sys.stderr.write(str(message) + "\n")
    if STOP_ON_ERROR:
        print ("Stopping.")
        sys.exit(1)

# Option-setting functions
def setStopOnError(stopOnErr):
    global STOP_ON_ERROR
    STOP_ON_ERROR = stopOnErr

# Split content by lines, but
# paying attention to escaped newline
# characters.
def getLines(content):
    result = []
    escapeCharLast = False
    buff = ''

    for c in content:
        if c == '\\' and not escapeCharLast:
            escapeCharLast = True
        elif escapeCharLast and c != '\n':
            buff += '\\' + c
            escapeCharLast = False
        elif escapeCharLast and c == '\n':
            buff += ' '
            escapeCharLast = False
        elif c == '\n':
            result.append(buff)
            buff = ''
        else:
            escapeCharLast = False
            buff += c
    result.append(buff)
    return result

# Get if [text] defines a macro.
def isMacroDef(text):
    return IS_MACRO_DEF_REGEXP.match(text) != None

def expandMacroUsages(line, macros):
    expanded = ''
    buff = ''
    afterBuff = ''
    prev = ''
    parenLevel = 0
    inMacro = False
    buffFromMacro = False

    line += ' ' # Force any macros at the
                # end of the line to expand.

    for c in line:
        if c == '$' and not inMacro and parenLevel == 0:
            expanded += buff
            buff = ''
            inMacro = True
        elif c == '$' and parenLevel == 0 and inMacro and buff == '$':
            inMacro = False
            expanded += '$'
        elif c == '(' and inMacro:
            parenLevel += 1
        elif c == ')' and inMacro:
            parenLevel -= 1

            if parenLevel == 0:
                inMacro = False
                buffFromMacro = True
        elif inMacro and parenLevel == 0 and not MACRO_NAME_CHAR_REGEXP.match(c):
            inMacro = False
            buffFromMacro = True
            afterBuff += c
        else:
            buff += c

        if buffFromMacro:
            buffFromMacro = False
            buff = buff.strip()
            words = buff.split(" ")
            if buff in macros:
                buff = macros[buff]
            elif words[0] in MACRO_COMMANDS:
                buff = MACRO_COMMANDS[words[0]](" ".join(words[1:]), macros)
            else:
                reportError("Undefined macro %s" % buff)
            expanded += buff + afterBuff
#            print("Expanded to %s." % (buff + afterBuff))
            buff = ''
            afterBuff = ''
        prev = c
    
    if parenLevel > 0:
        reportError("Unclosed parenthesis: %s" % line)

    # Append buff, but ignore trailing space.
    expanded += buff[:len(buff) - 1] + afterBuff
    return expanded

# Remove comments from line as defined
# by COMMENT_CHAR
def stripComments(line):
    singleLevel = { '"': False, "\'": False }
    inSomeSingleLevel = False
    multiLevelOpen = { '(': 0 }
    multiLevelClose = { ')': '(' }
    escaped = False
    trimToIndex = 0

    for c in line:
        if c in singleLevel and not escaped:
            if not inSomeSingleLevel:
                inSomeSingleLevel = True
                singleLevel[c] = True
            elif singleLevel[c]:
                inSomeSingleLevel = False
                singleLevel[c] = False
        elif c == '\\' and not escaped:
            escaped = True
        elif c == '\\' and escaped:
            escaped = False
        elif c in multiLevelOpen and not escaped and not inSomeSingleLevel:
            multiLevelOpen[c] += 1
        elif c in multiLevelClose and not escaped and not inSomeSingleLevel:
            bracketPairChar = multiLevelClose[c]
            if multiLevelOpen[bracketPairChar] == 0:
                reportError("Parentheses mismatch on line with content: %s" % line)
            else:
                multiLevelOpen[bracketPairChar] -= 1
        elif c == COMMENT_CHAR and not escaped and not inSomeSingleLevel:
            break
        else:
            escaped = False
        trimToIndex = trimToIndex + 1
    return line[:trimToIndex]


# Get if [text] syntatically invokes a macro.
def isMacroInvoke(text):
    return IS_MACRO_INVOKE_REGEXP.match(text) != None

# Expand and handle macro definitions 
# in contents.
def expandMacros(contents, macros = {}):
    lines = getLines(contents)
    result = ''
    preRuleChar = RECIPE_START_CHAR

    for line in lines:
        line = stripComments(line)
        if isMacroDef(line) and not line.startswith(preRuleChar):
            parts = MACRO_SET_REGEXP.split(line)
            name = parts[0].strip()
            definedTo = ":=".join(parts[1:]).strip()
            macros[name] = expandMacroUsages(definedTo, macros).rstrip()
#            print("%s defined to %s" % (name, macros[name]))
        elif isMacroInvoke(line) and not line.startswith(preRuleChar):
            result += expandMacroUsages(line, macros)
        else:
            result += line
        result += '\n'

    return (result, macros)

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
                    reportError("Pre-recipe line must contain separator! Line: %s" % line)
                else:
                    continue
            sepIndex = line.index(':')
            allGenerates = WHITESPACE.split(line[:sepIndex].strip())
            preReqs = line[sepIndex + 1 :].strip()
            
            # Get the dependencies.
            dependsOn = WHITESPACE.split(preReqs)
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
    selfExists = os.path.exists(target)
    selfMTime = 0

    if not target in targets:
        if selfExists:
            return 1
        else:
            reportError("No rule to make %s." % target)
    runRecipe = False
    deps, commands = targets[target]
    
    if selfExists:
        selfMTime = os.path.getmtime(target)

    def isPhony(target):
        return '.PHONY' in targets and target in targets['.PHONY']
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
        command = expandMacroUsages(command, macros).strip()
        if command.startswith("@"):
            command = command[1:]
        else:
            print(command)
        haltOnFail = not command.startswith("-")
        if command.startswith("-"):
            command = command[1:]
        try:
            print(subprocess.check_output(command).decode("UTF-8"))
        except:
            if haltOnFail:
                reportError("Unable to run ``%s``." % command)
    return True

# Run commands specified to generate
# dependencies of target by the contents
# of the makefile given in contents.
def runMakefile(contents, target = ''):
    contents, macros = expandMacros(contents)
    targetRecipes, targets = getTargetActions(contents)
    
    # Define macros, as needed...
    if not "MAKE" in macros:
        macros["MAKE"] = "make"

    if target == '' and len(targets) > 0:
        target = targets[0]

    satisfied = satisfyDependencies(target, targetRecipes, macros)

    if not satisfied:
        print("Nothing to be done for target ``%s``." % target)
