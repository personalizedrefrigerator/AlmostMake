#!python

# Macro parsing utilities.

import re, os
from almost_make.utils.printUtil import *
import almost_make.utils.errorUtil as errorUtil

# Regular expressions:
MACRO_NAME_EXP = "[a-zA-Z0-9_\\@\\^\\<]"
MACRO_NAME_CHAR_REGEXP = re.compile(MACRO_NAME_EXP)
MACRO_SET_REGEXP = re.compile("\\s*([:+?]?)\\=\\s*")
IS_MACRO_DEF_REGEXP = re.compile("^%s+\\s*[:+?]?\\=.*" % MACRO_NAME_EXP, re.IGNORECASE)
IS_MACRO_INVOKE_REGEXP = re.compile(".*(?:[\\$])[\\(]?%s+[\\)]?" % MACRO_NAME_EXP)

# Constant(s)
COMMENT_CHAR = '#'

# Filter function lists.
# These are only used by expandAndDefineMacros
# A line must satisfy all of these conditions to
# define a macro.
DEF_CONDITIONS = \
[
    
]

LAZY_EVAL_CONDITIONS = \
[
    
]

# Commands executable as $(COMMAND_NAME Args).
MACRO_COMMANDS = {}

# Option-setting functions
def setStopOnError(stopOnErr):
    errorUtil.setStopOnError(stopOnErr)

def setSilent(silent):
    errorUtil.setSilent(silent)

def setMacroCommands(commands):
    global MACRO_COMMANDS
    MACRO_COMMANDS = commands

# Note that for a line to define a macro,
# it must satisfy the given conditions.
def addMacroDefCondition(condition):
    DEF_CONDITIONS.append(condition)

# Skip expanding macros on a line if condition holds. Only applies to expandAndDefineMacros.
def addLazyEvalCondition(condition):
    LAZY_EVAL_CONDITIONS.append(condition)

# Get if [text] defines a macro.
def isMacroDef(text, defConditions=DEF_CONDITIONS):
    if not defConditions:
        defConditions = DEF_CONDITIONS
    
    if IS_MACRO_DEF_REGEXP.match(text) == None:
        return False
    for condition in defConditions:
        if not condition(text):
            return False
    return True

def isMacroExport(text, defConditions=DEF_CONDITIONS):
    if not text.startswith("export "):
        return False
    return isMacroDef(text[len("export "):].strip(), defConditions)

# Get if [text] syntatically invokes a macro.
def isMacroInvoke(text):
    return IS_MACRO_INVOKE_REGEXP.match(text) != None

# Get whether expandAndDefineMacros should
# evaluate the contents of a line, or allow it to
# be done later. [checkConditions] allows case-by-case
# overriding of the default conditions.
def shouldLazyEval(text, checkConditions=LAZY_EVAL_CONDITIONS):
    if checkConditions == None:
        checkConditions = LAZY_EVAL_CONDITIONS
    
    for condition in checkConditions:
        if condition(text):
            return True
    return False


# Get a list of suggested default macros from the environment
def getDefaultMacros():
    result = { }
    
    for name in os.environ:
        result[name] = os.environ[name]
    
    return result

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
                errorUtil.reportError("Parentheses mismatch on line with content: %s" % line)
            else:
                multiLevelOpen[bracketPairChar] -= 1
        elif c == COMMENT_CHAR and not escaped and not inSomeSingleLevel:
            break
        else:
            escaped = False
        trimToIndex = trimToIndex + 1
    return line[:trimToIndex]

# Expand usages of [macros] in [line].
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
            buff = buff.lstrip()
            words = buff.split(" ")
            if buff in macros:
                buff = macros[buff]
            elif words[0] in MACRO_COMMANDS:
                buff = MACRO_COMMANDS[words[0]](" ".join(words[1:]), macros)
            else:
                errorUtil.reportError("Undefined macro %s. Context: %s." % (buff, line))
            expanded += buff + afterBuff
#            print("Expanded to %s." % (buff + afterBuff))
            buff = ''
            afterBuff = ''
        prev = c
    
    if parenLevel > 0:
        errorUtil.reportError("Unclosed parenthesis: %s" % line)

    # Append buff, but ignore trailing space.
    expanded += buff[:len(buff) - 1] + afterBuff
    return expanded

# Expand and handle macro definitions 
# in [contents].
def expandAndDefineMacros(contents, macros = {}, 
            macroDefConditions=None, lazyEvalConditions=None):
    lines = getLines(contents)
    result = ''

    for line in lines:
        line = stripComments(line)
        exporting = isMacroExport(line, macroDefConditions)
        
        if isMacroDef(line, macroDefConditions) or exporting:
            if exporting:
                line = line[len("export "):]
            
            parts = MACRO_SET_REGEXP.split(line)
            name = parts[0]
            definedTo = line[len(name):]
            definedTo = MACRO_SET_REGEXP.sub("", definedTo, count=1) # Remove the first set character.
            defineType = MACRO_SET_REGEXP.search(line).group(1) # E.g. :,+,? so we can do += or ?=
            name = name.strip()
            
            doNotDefine = False
            concatWith = ''
            deferExpand = False
            
            # ?=, so only define if undefined.
            if defineType == '?' and name in macros:
                doNotDefine = True
            elif defineType == '+' and name in macros:
                concatWith = macros[name]
            elif defineType == '':
                deferExpand = True
            
            if not doNotDefine:
                if not deferExpand:
                    macros[name] = concatWith + expandMacroUsages(definedTo, macros).rstrip('\n')
                else:
#                    print("Expansion defered: %s = %s" % (name, definedTo))
                    macros[name] = concatWith + definedTo.rstrip('\n')
                
                if exporting:
                    os.environ[name] = macros[name]
#            print("%s defined to %s" % (name, macros[name]))
        elif isMacroInvoke(line) and not shouldLazyEval(line, lazyEvalConditions):
            result += expandMacroUsages(line, macros)
        else:
            result += line
        result += '\n'

    return (result, macros)
