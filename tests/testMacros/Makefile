#!make

check: macroTest
clean:

.PHONY: check clean


macroTest:
	echo $(PATH) | grep $(shell echo $PATH)
	echo "$(TEST_MACRO)" | grep "Testing1234=:= := This 'should ' work!"
