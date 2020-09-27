#!/usr/bin/python3

# Parse escape sequences.

# Replace all escape sequences in [text] 
# with their mappings in [escapes] (without the leading '\\', see default argument).
def parseEscapes(text, escapes={ '033': '\033', 't': '\t', 'r': '\r', 'n': '\n', 'b': '\b', 'a': '\a', '\\': '\\' }):
    result = ""
    buff = ""
    escaped = False
    for char in text:
        buff += char
        
        if escaped and buff in escapes:
            result += escapes[buff]
            buff = ''
            escaped = False
        elif char == '\\':
            result += buff[:len(buff) - 1]
            buff = ""
            escaped = True
    result += buff
    return result

# Split [text] by character, only if [splitChar] isn't immediately 
# following [escapeChar]. If [splitInQuotes] is false, do not split
# if a region is surrounded by single or double quotes. Quotes can 
# be escaped.
def escapeSafeSplit(text, splitChar, escapeChar, splitInQuotes=True):
    result = []
    buff = ""
    escaped = False
    inQuotes = None

    if len(text) == 0:
        return []
    
    for char in text:
        if splitInQuotes and char in { "'", '"' } and not escaped:
            if inQuotes == char:
                inQuotes = None
            else:
                inQuotes = char
            
            buff += char
        elif char == splitChar and not escaped and inQuotes == None:
            result.append(buff)
            buff = ''
        elif char == escapeChar and not escaped:
            escaped = True
        elif escaped:
            escaped = False
            buff += char
        else:
            buff += char
    
    result.append(buff)

    return result

# Tests.
if __name__ == "__main__":
    def assertEql(a, b):
        if a != b:
            raise Exception("%s != %s" % (str(a), str(b)))
    assertEql(parseEscapes("a"), "a")
    assertEql(parseEscapes(""), "")
    assertEql(parseEscapes("ab"), "ab")
    assertEql(parseEscapes("a\\n"), "a\n")
    assertEql(parseEscapes("\\n"), "\n")
    assertEql(parseEscapes("a\\nb\\nc"), "a\nb\nc")
    assertEql(parseEscapes("\\\\"), "\\")
    assertEql(parseEscapes("A test of this\\n", {}), "A test of thisn")
    assertEql(parseEscapes("A \\033[32m test! \\033[0m"), "A \033[32m test! \033[0m")
    assertEql(parseEscapes("\\033[32mabc\\033[0m"), "\033[32mabc\033[0m")

    assertEql(escapeSafeSplit("A,test,that,is,simple.", ',', '\\'), ['A', 'test', 'that', 'is', 'simple.'])
    assertEql(escapeSafeSplit("A,test\\n,that,is less,simple.", ',', '\\'), ['A', 'testn', 'that', 'is less', 'simple.'])
    assertEql(escapeSafeSplit("", ',', '\\'), [])
    assertEql(escapeSafeSplit(" ", ',', '\\'), [' '])
    assertEql(escapeSafeSplit(" \\,a", ',', '\\'), [' ,a'])
    assertEql(escapeSafeSplit(" \\,a, b", ',', '\\'), [' ,a', ' b'])
    assertEql(escapeSafeSplit(" \\,a, b", ',', '\\', True), [' ,a', ' b'])
    assertEql(escapeSafeSplit(" \\,'a, b'", ',', '\\', True), [' ,\'a, b\''])
    assertEql(escapeSafeSplit("a,b", ',', '\\', True), ['a', 'b'])
    assertEql(escapeSafeSplit("\\'a,b\\'", ',', '\\', True), ['\'a,b\''])
    assertEql(escapeSafeSplit("\\'a,b\\'", ',', '\\', False), ['\'a', 'b\''])
