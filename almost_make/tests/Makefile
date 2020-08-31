#!make
# To be run with AlmostMake.

# Use the mini-shell built into AlmostMake
export _BUILTIN_SHELL := 1
export _CUSTOM_BASE_COMMANDS := 1

CC = clang
CFLAGS =
TEST_MACRO = Testing1234=:= := This **should ** work! # A comment!
### Note: The above line was changed such that it DOES NOT contain 
### single-quote characters! Some shells were breaking "foo 'bar' baz"
### into something similar to ["foo", "bar", "baz"].

EXEC_PROGRAM  = 
SEND_MACROS  := EXEC_PROGRAM=$(EXEC_PROGRAM) CC=$(CC) CFLAGS=$(CFLAGS) TEST_MACRO="$(TEST_MACRO)" # Note: '=' defers expansion. ':=' does not.

# Perhaps not legal in other versions of make, but it
# should work here. As such, it is tested.
all: testSimple testPhony testMacros testRecursion testParallel

test%:
	$(MAKE) -C $@ clean check clean $(SEND_MACROS)

.PHONY: testSimple testPhony testMacros testRecursion
