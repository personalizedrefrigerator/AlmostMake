#!make

check: macroTest
clean:

.PHONY: check clean macroTest


macroTest: testMacroConcat testMacroConditionalSet testMacroCommands testConditionals
	echo $(PATH) | grep $(shell echo ${PATH})
	echo $(TEST_MACRO) | grep "Testing1234=:= := This \*\*should \*\* work!"
	$(MAKE) -C overrideMacrosTest DOES_IT_OVERRIDE=YesItDoes

A  = 123
A += 4

C := $(A)
C += 56789

testMacroConcat:
	echo $(A) | grep 1234
	echo $(C) | grep 123456789

CONDITIONALLY_SET ?= I am set!
CONDITIONALLY_SET ?= Really?

testMacroConditionalSet:
	echo $(CONDITIONALLY_SET) | grep "I am set!"

testMacroCommands:
	@echo "---- Testing macro commands ----"
	$(MAKE) -C macroCommands
	OUT=$(MAKE) -C macroCommands;\
	echo $$(OUT) | grep -F 'a.txt';\
	echo $$(OUT) | grep -F 'b.txt';\
	echo $$(OUT) | grep -F 'c.txt';

testConditionals:
	@echo "---- Testing macro conditionals!!! ----"
	$(MAKE) -C macroConditionals