#!python

import sys, os

FORMAT_COLORS = \
{
    "GREEN": "\033[32m",
    "RED": "\033[31m",
    "YELLOW": "\033[33m",
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
    def flush(self):
        pass

def cprint(text, color=None, file=sys.stdout):
    # If file is None, default to stdout. If a number, 
    # wrap it in a file-like object.
    if file is None:
        file = sys.stdout
    elif type(file) == int:
        file = _FDWrap(file)

    if color in FORMAT_COLORS and FORMAT_OUTPUT:
        print(FORMAT_COLORS[color] + str(text) + FORMAT_RESET, end='', flush=True, file=file)
    elif type(color) == str and FORMAT_OUTPUT:
        print(color + str(text) + FORMAT_RESET, end='', flush=True, file=file)
    else:
        print(text, end='', flush=True, file=file)
