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
