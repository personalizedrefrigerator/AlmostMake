#!make
# To be run with AlmostMake.

CC = clang
CFLAGS =

EXEC_PROGRAM  =  ./
SEND_MACROS   = EXEC_PROGRAM=$(EXEC_PROGRAM) CC=$(CC) CFLAGS=$(CFLAGS)

all: testSimple testClean testRules testRecursion testSuffixes

test%:
	cd $@; \
	$(MAKE) clean check $(SEND_MACROS)

.PHONY: testSimple testClean testRules testRecursion testSuffixes
