
all: $(wildcard *.tx*)
	echo $(words a) | grep 1
	echo $(words a b c d    another word) | grep 6
	echo $(sort a b c) | grep "a b c"
	echo $(sort a a b c) | grep -Fx "a b c"
	echo $(sort foo bar baz) | grep -Fx "bar baz foo"

%.txt:
	@echo $@