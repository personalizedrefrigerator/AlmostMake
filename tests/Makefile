#!make
# To be run with AlmostMake.

CC = clang
CFLAGS =
TEST_MACRO = Testing1234=:= := This 'should ' work! # A comment!

EXEC_PROGRAM  =  ./
SEND_MACROS  := EXEC_PROGRAM=$(EXEC_PROGRAM) CC=$(CC) CFLAGS=$(CFLAGS) TEST_MACRO="$(TEST_MACRO)" # Note: '=' defers expansion. ':=' does not.

# Perhaps not legal in other versions of make, but it
# should work here. As such, it is tested.
all: testSimple testPhony testMacros

test%:
	$(MAKE) -C $@ clean check clean $(SEND_MACROS)

.PHONY: testSimple testPhony testMacros
