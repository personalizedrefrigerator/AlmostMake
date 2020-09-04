#!/usr/bin/python3

# Macro parsing utilities.

import re, os
import almost_make.utils.shellUtil.runner as runner
import almost_make.utils.errorUtil as errorUtil

# Regular expressions:
MACRO_NAME_EXP = "[a-zA-Z0-9_\\@\\^\\<]"
MACRO_NAME_CHAR_REGEXP = re.compile(MACRO_NAME_EXP)
MACRO_SET_REGEXP = re.compile("\\s*([:+?]?)\\=\\s*")
IS_MACRO_DEF_REGEXP = re.compile("^%s+\\s*[:+?]?\\=.*" % MACRO_NAME_EXP, re.IGNORECASE)
IS_MACRO_INVOKE_REGEXP = re.compile(".*(?:[\\$])[\\(\\{]?%s+[\\)\\}]?" % MACRO_NAME_EXP)
SPACE_CHARS = re.compile("\\s")

CONDITIONAL_START = re.compile(r"^\s*(ifeq|ifneq|ifdef|ifndef)(?:\s|$)")
CONDITIONAL_ELSE = re.compile(r"^\s*(else)(?:\s|$)")
CONDITIONAL_STOP = re.compile(r"^\s*(endif)(?:\s|$)")

# Constant(s)
COMMENT_CHAR = '#'

class MacroUtil:
    macroCommands = {} # All commands executable as $(name arg1, arg2, ...)
    definitionConditions = [] # A list of additional preconditions for the definition of a macro.
    lazyEvalConditions = []   # Don't expand macros on a line when in define & expand mode if any of these conditions are true.
    conditionals = False
    errorLogger = errorUtil.ErrorUtil()
    
    def setStopOnError(self, stopOnErr):
        self.errorLogger.setStopOnError(stopOnErr)
    def setSilent(self, silent):
        self.errorLogger.setSilent(silent)
    def setMacroCommands(self, commands):
        self.macroCommands = commands
    def addMacroDefCondition(self, condition):
        self.definitionConditions.append(condition)

    # Skip expanding macros on a line if condition holds. Applies only to
    # expandAndDefineMacros.
    def addLazyEvalCondition(self, condition):
        self.lazyEvalConditions.append(condition)

    # Turn on conditional support!
    def enableConditionals(self):
        self.conditionals = True

    # Get whether expandAndDefineMacros should
    # evaluate the contents of a line, or allow it to
    # be done later. Add conditions via addLazyEvalCondition.
    def shouldLazyEval(self, text):
        for condition in self.lazyEvalConditions:
            if condition(text):
                return True
        return False
    
    # Get if [text] defines a macro.
    def isMacroDef(self, text):
        if IS_MACRO_DEF_REGEXP.match(text) == None:
            return False
        for condition in self.definitionConditions:
            if not condition(text):
                return False
        return True

    # Get whether [text] defines a macro with value that should be exported to the
    # environment.
    def isMacroExport(self, text):
        if not text.startswith("export "):
            return False
        return self.isMacroDef(text[len("export "):].strip())

    # Get if [text] syntatically invokes a macro.
    def isMacroInvoke(self, text):
        return IS_MACRO_INVOKE_REGEXP.match(text) != None

    # Get if [text] is a conditional statement.
    def isConditional(self, text):
        if self.shouldLazyEval(text): # Lazy evaluation for this line? Skip it.
            return False

        return CONDITIONAL_START.match(text) or CONDITIONAL_STOP.match(text) or CONDITIONAL_ELSE.match(text)

    # Get the name of the conditional in [text], or None, if no conditionals are
    # defined.
    def getConditional(self, text):
        if not self.isConditional(text):
            return None

        startMatch = CONDITIONAL_START.match(text)
        elseMatch  = CONDITIONAL_ELSE.match(text)
        endMatch   = CONDITIONAL_STOP.match(text)
        
        return (startMatch or elseMatch or endMatch).group(1) # If there was a match, there should be at least one group.

    # Return [ifBranch] or [elseBranch] based on the contents of [conditionalContent].
    # CONDITIONAL_START.match([conditionalContent]) should not be None. Do not expand and define 
    # macros in the chosen branch.
    def evaluateIf(self, conditionalContent, ifBranch, elseBranch, macros):
        assert self.isConditional(conditionalContent) # We should always be given a valid starting conditional.
#        print('----------')
#        print(conditionalContent + ";;" + ifBranch + ";;" + str(elseBranch))
#        print('----------')

        conditionalContent = conditionalContent.lstrip()
        conditional = CONDITIONAL_START.match(conditionalContent).group(1)
        argText     = conditionalContent[len(conditional) + 1: ].strip()
        argText     = self.expandMacroUsages(argText, macros).strip()
        choseIfBranch = True

        if conditional == 'ifdef':
            choseIfBranch = (argText.strip() in macros)
        elif conditional == 'ifndef':
            choseIfBranch = not (argText.strip() in macros)
        else: # Binary conditionals.
            args = runner.shSplit(argText, { ',', ' ', '\t', '(', ')' })
            args = runner.removeEqual(runner.unwrapParens(args), ',')

            # shSplit removes empty elements. Add in an empty element if necessary.
            if len(args) == 1:
                args.append('')

            if len(args) != 2:
                self.errorLogger.reportError("""Binary conditional %s has %s arguments!
Context: %s, so,
%s
%s
else
%s
endif
--------
From %s, parsed arguments: %s""" %
    (str(conditional), str(len(args)), 
    str(conditionalContent), str(conditional) + " " + str(argText), 
    str(ifBranch), str(elseBranch),
    str(argText), str(args)))
            
            if conditional == 'ifeq':
                choseIfBranch = args[0] == args[1]
            elif conditional == 'ifneq':
                choseIfBranch = args[0] != args[1]
            else:
                self.errorLogger.reportError("Unknown conditional %s. Context: %s." % (conditional, conditionalContent))

        if choseIfBranch:
            return ifBranch
        return elseBranch or '' # elseBranch can be None...



    # Get a list of suggested default macros from the environment
    def getDefaultMacros(self):
        result = { }
        
        for name in os.environ:
            result[name] = os.environ[name]
        
        return result

    # Split content by lines, but
    # paying attention to escaped newline
    # characters.
    def getLines(self, content):
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
    def stripComments(self, line, force=False):
        singleLevel = { '"': False, "\'": False }
        inSomeSingleLevel = False
        multiLevelOpen = { '(': 0, '{': 0 }
        multiLevelClose = { ')': '(', '}': '{' }
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
                    self.errorLogger.reportError("Parentheses mismatch on line with content: %s" % line)
                else:
                    multiLevelOpen[bracketPairChar] -= 1
            elif c == COMMENT_CHAR and not escaped and not inSomeSingleLevel and (not self.shouldLazyEval(line) or force):
                break
            else:
                escaped = False
            trimToIndex = trimToIndex + 1
        return line[:trimToIndex]

    # Expand usages of [macros] in [line]. Make no definitions and expand
    # regardless of lazyEvalConditions.
    def expandMacroUsages(self, line, macros):
        expanded = ''
        buff = ''
        afterBuff = ''
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
            elif c == '$' and parenLevel == 0 and inMacro and buff == '':
                inMacro = False
                expanded += '$'
            elif (c == '(' or c == '{') and inMacro:
                parenLevel += 1

                if parenLevel > 1:
                    buff += c
            elif (c == ')' or c == '}') and inMacro:
                parenLevel -= 1

                if parenLevel == 0:
                    inMacro = False
                    buffFromMacro = True
                else:
                    buff += c
            elif inMacro and parenLevel == 0 and not MACRO_NAME_CHAR_REGEXP.match(c):
                inMacro = False
                buffFromMacro = True
                afterBuff += c
            else:
                buff += c

            if buffFromMacro:
                buffFromMacro = False
                buff = buff.lstrip()
                words = SPACE_CHARS.split(buff)

                if buff in macros:
                    buff = macros[buff]
                elif words[0] in self.macroCommands:
                    argText = self.expandMacroUsages(" ".join(words[1:]), macros)
                    buff = self.macroCommands[words[0]](argText, macros)
                else:
                    self.errorLogger.reportError("Undefined macro %s. Context: %s." % (buff, line))

                expanded += buff + afterBuff
#               print("Expanded to %s." % (buff + afterBuff))
                buff = ''
                afterBuff = ''
        
        if parenLevel > 0:
            self.errorLogger.reportError("Unclosed parenthesis: %s" % line)

        # Append buff, but ignore trailing space.
        expanded += buff[:len(buff) - 1] + afterBuff
        return expanded

    # Expand and handle macro definitions 
    # in [contents]. This includes removing end-of-line comments.
    def expandAndDefineMacros(self, contents, macros = {}):
        lines = self.getLines(contents)
        result = ''
        conditionalData = None

        for line in lines:
            line = self.stripComments(line)
            exporting = self.isMacroExport(line)
            
            if conditionalData != None:
                if self.isConditional(line):
                    if CONDITIONAL_START.match(line):
                        conditionalData['stack'].append(line)
                        conditionalData['endifWeight'].append(1)
                    # We ignore CONDITIONAL_ELSE unless it applies directly to THIS conditional.
                    elif CONDITIONAL_ELSE.match(line) and len(conditionalData['stack']) == conditionalData['endifWeight'][-1]:
                        elseText = CONDITIONAL_ELSE.match(line).group(1)
#                        print("Else: " + line)
                        line = line.strip()[len(elseText):].strip() # Move anything after 'else' onto the next line (conceptually). Permits else if...

                        if not conditionalData['elseBranch']:
                            conditionalData['elseBranch'] = ''
                        else:
                            conditionalData['elseBranch'] += 'else\n'
                        conditionalData['elseBranch'] += line + '\n' # We can start building-up the else branch...

                        # Is it an else if?
                        if CONDITIONAL_START.match(line):
                            conditionalData['stack'].append(line) # Treat it like an if.
                            conditionalData['endifWeight'].append(conditionalData['endifWeight'][-1] + 1) # The next endif removes two elements from the stack.

                        continue
                    elif CONDITIONAL_STOP.match(line):
#                        print(str(len(conditionalData['stack'])) + "," + line + ",  wt:" + str(conditionalData['endifWeight'][-1]))

                        while conditionalData['endifWeight'][-1] > 1:
                            conditionalData['elseBranch'] += 'endif\n'
                            conditionalData['stack'].pop()
                            conditionalData['endifWeight'][-1] -= 1
                        
                        conditionalData['endifWeight'].pop()

                        if len(conditionalData['stack']) > 1: # The endif applied to a sub-if statement.
                            conditionalData['stack'].pop()
#                            print("   To if. stacklen: " + str(len(conditionalData['stack'])))
                        else:
#                            print("  To else")
                            
                            ifConditional = conditionalData['stack'].pop() # Contents of the if statement.

                            elsePart = conditionalData['elseBranch'] or ''

                            chosenBranch = self.evaluateIf(ifConditional, 
                                conditionalData['ifBranch'], elsePart, macros)
                            
                            # We have reached the end of the branch. Add a version to result.
                            expanded, macros = self.expandAndDefineMacros(chosenBranch, macros)
                            result += expanded + '\n'

                            conditionalData = None # We are done!
                            continue
                if conditionalData['elseBranch'] != None:
                    conditionalData['elseBranch'] += line + '\n'
                else:
                    conditionalData['ifBranch'] += line + '\n'
                continue

            # If either a macro export, or a setting a macro's value, without an export...
            if (self.isMacroDef(line) or exporting):
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
                
                # Depending on the operator, we might not want to define the macro...
                if not doNotDefine:
                    if not deferExpand:
                        macros[name] = concatWith + self.expandMacroUsages(definedTo, macros).rstrip('\n')
                    else:
#                    print("Expansion defered: %s = %s" % (name, definedTo))
                        macros[name] = concatWith + definedTo.rstrip('\n')
                    
                if exporting:
                    os.environ[name] = macros[name]
#            print("%s defined to %s" % (name, macros[name]))
            elif self.conditionals and self.isConditional(line) and not self.shouldLazyEval(line):
#                      Ref:
#                      https://www.gnu.org/software/make/manual/html_node/Conditional-Syntax.html#Conditional-Syntax
                conditional = self.getConditional(line)

                # The conditional must, initially, be some if...
                if not CONDITIONAL_START.match(conditional):
                    self.errorLogger.reportError("%s without a leading if. Context: %s. Buffer: %s" % (conditional, line, result))
                
                conditionalData = { 'ifBranch': '', 'elseBranch': None, 'stack': [], 'endifWeight': [ 1 ] }
                conditionalData['stack'].append(line)
            elif self.isMacroInvoke(line) and not self.shouldLazyEval(line):
                result += self.expandMacroUsages(line, macros)
            else:
                result += line
            result += '\n'

        if not conditionalData is None:
            self.errorLogger.reportError("Un-ending conditional (check your indentation -- leading tabs can mess things up)! Conditional data: %s." % str(conditionalData))
        
        return (result, macros)
