#!make
# To be run with AlmostMake.

CC = clang
CFLAGS =

EXEC_PROGRAM  =  ./
SEND_MACROS   = EXEC_PROGRAM=$(EXEC_PROGRAM) CC=$(CC) CFLAGS=$(CFLAGS)

all: testSimple testPhony
# testRules testRecursion testSuffixes

test%:
	cd $@; \
	$(MAKE) clean check clean $(SEND_MACROS)

.PHONY: testSimple testPhony testRules testRecursion testSuffixes
