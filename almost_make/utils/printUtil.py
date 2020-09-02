#!/usr/bin/python3

import sys, os

FORMAT_COLORS = \
{
    "GREEN": "\033[32m",
    "RED": "\033[31m",
    "YELLOW": "\033[33m",
    "BLUE": "\033[94m",
    "PURPLE": "\033[35m"
}

FORMAT_RESET = "\033[0m"
FORMAT_OUTPUT = sys.stdout.isatty() # Only format if outputting to a terminal.

# Wrap a given value in a file descriptor. Permits calling cprint
# with file=a file descriptor.
class _FDWrap:
    def __init__(self, fd):
        self.fd = fd
    def write(self, txt):
        return os.write(self.fd, bytes(txt, 'utf-8'))
    def read(self):
        result = ''
        part = os.read(self.fd, 1).decode('utf-8')

        while part != '':
            result += part or ''
            part = os.read(self.fd, 1).decode('utf-8')
        
        return result
    def flush(self):
        pass

# If file is None, default to stdout. If a number, 
# wrap it in a file-like object.
def wrapFile(fileOrFd):
    if fileOrFd is None:
        return sys.stdout
    elif type(fileOrFd) == int:
        return _FDWrap(fileOrFd)
    return fileOrFd

def cprint(text, color=None, file=sys.stdout):
    file = wrapFile(file)

    if color in FORMAT_COLORS and FORMAT_OUTPUT:
        print(FORMAT_COLORS[color] + str(text) + FORMAT_RESET, end='', flush=True, file=file)
    elif type(color) == str and FORMAT_OUTPUT:
        print(color + str(text) + FORMAT_RESET, end='', flush=True, file=file)
    else:
        print(text, end='', flush=True, file=file)
