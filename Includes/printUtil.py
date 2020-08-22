#!python

import sys

FORMAT_COLORS = \
{
    "GREEN": "\033[32m",
    "RED": "\033[31m",
    "YELLOW": "\033[33m",
    "PURPLE": "\033[35m"
}

FORMAT_RESET = "\033[0m"
FORMAT_OUTPUT = sys.stdout.isatty() # Only format if outputting to a terminal.

def cprint(text, color, file=sys.stdout):
    if color in FORMAT_COLORS and FORMAT_OUTPUT:
        print(FORMAT_COLORS[color] + str(text) + FORMAT_RESET, end='', flush=True, file=file)
    elif type(color) == str and FORMAT_OUTPUT:
        print(color + str(text) + FORMAT_RESET, end='', flush=True, file=file)
    else:
        print(text, end='', flush=True, file=file)
