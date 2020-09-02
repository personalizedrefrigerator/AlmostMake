import os, re, shlex

SPACE_CHARS = re.compile('\\s')

# Parse given arguments.
# args: The list of arguments given to the program (e.g. from sys.argv). Note that
# any default arguments (not immediately after  a key) are put into a list under the
# key defaultArgKey. If no default args, the list is empty. For example, 
# ['make'] -> {'default': []}. 
# If a given argument or its single-character representative is in [strictlyFlags], it is
# considered a flag -- non-argument text after it is associated with [defaultArgKey], rather
# than the argument. For example, if foo is in  strictlyFlags, then [ ... --foo thing ...]
# results in { ... 'foo': True, 'default': [... 'thing' ...] ... }.
def parseArgs(args, 
        mappings = 
        {
            'h': 'help'
        }, 
        defaultArgKey = 'default',
        excludeFilename = True,
        strictlyFlags={'help'}):
    result = { }
    singleChars = []
    lastArgText = None
    if excludeFilename:
        args = args[1:] # Omit the filename.
    result[defaultArgKey] = []

    for chunk in args:
        if len(chunk) == 0:
            continue    
        
        if chunk.startswith("--") and len(chunk) > 2:
            if lastArgText:
                result[lastArgText] = True
            lastArgText = chunk[2:]
        elif chunk.startswith("-") and len(chunk) > 1:
            singleChars.extend(chunk[1:])
            
            if lastArgText:
                result[lastArgText] = True
                lastArgText = None
            
            # Permits single-characters mapping to multi-char
            # flags **with values**.
            if chunk[-1] in mappings and not (mappings[chunk[-1]] in result):    
                lastArgText = mappings[chunk[-1]]
        elif lastArgText: # Assign to previous.
            result[lastArgText] = chunk
            lastArgText = None
        else: # Default argument.
            result[defaultArgKey].append(chunk)
        
        # If lastArgText is a flag -- it can't have a value associated with it,
        # clear it so we don't associate a chunk with it.
        if lastArgText and lastArgText in strictlyFlags:
            result[lastArgText] = True
            lastArgText = None
    if lastArgText:
        result[lastArgText] = True

    for char in singleChars:
        if char in mappings and not (mappings[char] in result):
            result[mappings[char]] = True
    
    return result

# Fill in an already-populated argument list
# with arguments defined in an environment variable.
# This variable should have name [envVariable].
# If [givenOverridesNew] is false, then arguments
# found in the variable override those given.
# Returns output as a new argument map. [mappings]
# is used to parse arguments in the environment.
def fillArgsFromEnv(argList, envVariable, mappings, defaultArgKey='default', givenOverridesNew=True):
    if not envVariable in os.environ:
        return argList
    
    # Get the argument mapping from the environment variable...
    envArgList = shlex.split(os.environ[envVariable])
    argsFromEnv = parseArgs(envArgList, mappings, defaultArgKey, excludeFilename = False)

    result = {}
    
    # Single-line ifs... Common in Lua... 
    # I don't think I've seen them in Python... Is this bad style?
    firstMap = not givenOverridesNew and argList or argsFromEnv
    secondMap = givenOverridesNew and argList or argsFromEnv
    
    for key in firstMap:
        result[key] = firstMap[key]
    
    for key in secondMap:
        result[key] = secondMap[key]
    
    return result

# Save the list of arguments specified by [argMap]
# in the environment variable, [envVariable].
# Question: Do we need to clean up after exiting???
def saveArgsInEnv(argMap, envVariable, doNotSave, defaultKey="default"):
    argString = ""
    
    for key in argMap:
        if key in doNotSave:
            continue
    
        prefix = "--"
        defTo = str(argMap[key])
        defTo = shlex.quote(defTo)
        
        if key == defaultKey: # If the default, we have a list...
            prefix = "" # Quote each individually.
            defTo = " ".join([ shlex.quote(val) for val in key ]) # default arg stores a list.
        elif len(key) == 1:
            prefix = "-"
        
        if argMap[key] == True:
            argString += prefix + key
        else:
            argString += prefix + key + " " + defTo
        
        argString += " "
    
    os.environ[envVariable] = argString
