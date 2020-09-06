# AlmostMake

A pure-python, not-quite-POSIX-compliant implementation of make.

## Sample Supported Makefile(s)

This example consists of a lightly-edited set of files from AlmostMake's tests.

**macroDefinitions.mk**
```Makefile
# Use the mini-shell built into AlmostMake
export _BUILTIN_SHELL := 1
export _CUSTOM_BASE_COMMANDS := 1

CC = clang
CFLAGS =
TEST_MACRO = Testing1234=:= := This **should ** work! # A comment!

EXEC_PROGRAM         = 
SEND_MACROS         := EXEC_PROGRAM=$(EXEC_PROGRAM) CC=$(CC) CFLAGS=$(CFLAGS) TEST_MACRO="$(TEST_MACRO)" # Note: '=' defers expansion. ':=' does not.
export MAKEFLAGS    := $(MAKEFLAGS) $(SEND_MACROS)
```

**Makefile**
```Makefile
# To be run with AlmostMake.
include *.mk

all: testSimple testPhony testMacros testRecursion testParallel testMisc

test%:
	$(MAKE) -C $@ clean
	$(MAKE) -C $@ check
	$(MAKE) -C $@ clean

.PHONY: testSimple testPhony testMacros testRecursion testParallel testMisc
```

**testSimple/Makefile**
```Makefile
.POSIX:

all:

# Note: As of v0.0.19, chmod is not built-in.
check: all
	chmod u+x main
	$(EXEC_PROGRAM) ./main | grep PASS

all: main

clean:
	-rm -f main.o
	-rm -f main

main: main.o
	$(CC) main.c -o main

.SUFFIXES: .c .o
.c.o:
	$(CC) $(CFLAGS) -c $< -o $@
```

## Usage

AlmostMake comes with the `almake` and `almake_shell` command-line utilities. Let's see how to use them!

### `almake`

Running `almake` in a directory with a file named `Makefile` causes `almake` to satisfy the first target defined in that file.

For example, say `Makefile` contains the following:
```Makefile
# A makefile!

# This is the first target.
# (Pretend `echo 'Hello, world'`
# is indented with a single tab)
firstTarget:
    echo 'Hello, world'

# firstTarget isn't the name of a real file!
# Mark it as PHONY. We need this because if 
# firstTarget were to be a file in the same
# folder as Makefile, its existence (and lack
# of newer dependencies) would cause `almake`
# to do nothing!
.PHONY: firstTarget
```

`almake` then runs the commands associated with firstTarget. Each line is given its own shell.

Additional options are documented through `almake`'s helptext:
```sh
$ almake --help
Help: 
 Summary: Satisfy dependencies of a target in a makefile. This parser is not quite POSIX-compliant, but should be able to parse simple makefiles.
 Usage: almake [targets...] [options]
  where each target in targets is a valid target and options include:
    -h, --help                   Print this message.
    --version                    Print version and licensing information.
    --file                       File to parse (default is Makefile).
    -k                           Keep going if errors are encountered.
    -n, --just-print             Just print commands to be run, without evaluating (print commands, don't send them to the shell). Be aware that $(shell ...) macros are still evaluated. This option only applies to individual commands.
    -p                           Rather than finding targets, print the makefile, with top-level targets expanded.
    -C dir                       Switch to directory, dir, before running make. 
    -w, --print-directory        Print the current directory before and after running make. 
    -j, --jobs                   Maximum number of jobs (e.g. almake -j 8). 
    -s, --silent                 In most cases, don't print output.
    -b, --built-in-shell         Use the built-in shell for commands in the makefile. This can also be enabled as follows:
   export _BUILTIN_SHELL := 1           # Use the built-in shell instead of the system shell.
   export _CUSTOM_BASE_COMMANDS := 1    # Enable built-in overrides for several commands like ls, echo, cat, grep, and pwd.
   export _SYSTEM_SHELL_PIPES := 1      # Send commands that seem related to pipes (e.g. ls | less) directly to the system's shell. 
Note: AlmostMake's built-in shell is currently very limited.

Note: Macro definitions that override those from the environment can be provided in addition to targets and options. For example,
    make target1 target2 target3 CC=gcc CFLAGS=-O3
should make target1, target2, and target3 with the macros CC and CFLAGS by default set to gcc and -O3, respectively.
Note: Options can also be given to almake through the environment. This is done through the MAKEFLAGS variable. For example, setting MAKEFLAGS to --built-in-shell causes almake to always use its built-in shell, rather than the system shell.
```

### `almake_shell`

In addition to the `almake` command, the `almake_shell` command is available. This command gives access to an interactive version of the (very limited) shell built into AlmostMake. 

Like `almake`, we get usage information as follows:
```sh
$ almake_shell --help
Help: 
 Summary: Run an interactive version of the shell built into almake. This is a POSIX-like shell. It is not POSIX-compliant.
 Usage: almake_shell [options] [files...]
  ...where each filename in [files...] is an optional file to interpret. If files are given, interpret them before opening the shell.
Options include:
    -h, --help   Print this message.
    --version    Print version and licensing information.
    -B, --without-builtins       Do not (re)define built-in commands (like echo). By default, echo, ls, dir, pwd, and perhaps other commands, are defined and override any commands with the same name already present in the system.
    -p, --system-pipe    Rather than attempting to pipe output between commands (e.g. in ls | grep foo), send piped portions of the input to the system's shell.
```

### The `almost_make` Python module

AlmostMake also makes available the `almost_make` module! Documentation on this is coming, but for now, check out the source on [GitHub](https://github.com/personalizedrefrigerator/AlmostMake)! 

## Installation

### From PyPI...
AlmostMake is on the Python Package Index! To install it, run:
```sh
$ python3 -m pip install almost-make
```

To update it,
```sh
$ python3 -m pip install --upgrade almost-make
```

### From GitHub...

As `AlmostMake` is hosted on GitHub, it can be installed by cloning:
```sh
$ git clone https://github.com/personalizedrefrigerator/AlmostMake.git
$ cd AlmostMake
$ make install
```

You may also need to install `setuptools`, `wheel`, and `twine`. [See Packaging Python Projects](https://packaging.python.org/tutorials/packaging-projects/) for a brief overview of these packages. They can be installed as follows:
```sh
$ python3 -m pip install --user --upgrade setuptools wheel twine
```

## Notable Missing Features

At present, `AlmostMake` **does not support** the following, notable features.

In `almake`:
 * `$(shell ...)` that can use `almake_shell`
 * BSDMake-style conditionals
 * BSDMake-style `.include < ... >` includes
 * Defining recipes via `a:: b` and `a! b`.
 * Pre-defined recipes (e.g. `.o` from `.c`)

In `almake_shell`/built-in shell:
 * `if` statements, loops, functions.
 * Built-in `chmod`

## Testing

To test AlmostMake, run,
```sh
$ make test
```

Note, however, that `make test` depends on `make install`.

## Supported Platforms

At present, it has been tested on the following platforms:
 - Ubuntu with Python 3.8, AlmostMake v0.2.0. All tests pass.
 - Debian with Python 3.7, older AlmostMake. All tests pass.
 - iOS via [a-Shell](https://github.com/holzschu/a-shell), AlmostMake v0.19.0. Failing tests.

If you find that AlmostMake works on a platform not listed here, please consider [creating an issue and/or submitting a pull request to update the list of supported platforms and versions of Python](https://github.com/personalizedrefrigerator/AlmostMake/issues/new)!

If AlmostMake doesn't work for you, you may wish to try [PyMake](https://pypi.org/project/py-make/). This package appears to support a wider range of Python versions and platforms, but may have fewer features.