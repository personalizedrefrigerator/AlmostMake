# Parse given arguments.
# args: The list of arguments
#    given to the program (i.e.
#    from sys.argv). Note that
# any default arguments (not immediately after 
# a key) are put into a list under the
# key defaultArgKey. If no default args,
# the list is empty.
# For example, 
#    make 
def parseArgs(args, 
        mappings = 
        {
            'h': 'help'
        }, 
        defaultArgKey = 'default'):
    result = { }
    singleChars = []
    lastArgText = None
    args = args[1:] # Omit the filename.
    result[defaultArgKey] = []

    for chunk in args:
        if chunk.startswith("--"):
            if lastArgText:
                result[lastArgText] = True
            lastArgText = chunk[2:]
        elif chunk.startswith("-"):
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
    if lastArgText:
        result[lastArgText] = True

    for char in singleChars:
        if char in mappings and not (mappings[char] in result):
            result[mappings[char]] = True
    
    return result


