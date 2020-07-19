# Parse given arguments.
# args: The list of arguments
#    given to the program (i.e.
#    from sys.argv). Note that
# any default arguments (come before
# keys) are put into a list under the
# key defaultArgKey. If no default args,
# the list is empty.
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

    # Populate default arguments.
    i = 0
    while i < len(args) and not args[i].startswith('-'):
        result[defaultArgKey].append(args[i])
        i += 1

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
        elif lastArgText:
            result[lastArgText] = chunk
            lastArgText = None
    if lastArgText:
        result[lastArgText] = True

    for char in singleChars:
        if char in mappings and not (mappings[char] in result):
            result[mappings[char]] = True
    
    return result


