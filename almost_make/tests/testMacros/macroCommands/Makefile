
all: $(wildcard *.tx*)
	echo $(strip $(strip a)) | grep -Fx a
	echo $(words a) | grep 1
	echo $(words a b c d    another word) | grep 6
	echo $(sort a b c) | grep "a b c"
	echo $(sort a a b c) | grep -Fx "a b c"
	echo $(sort foo bar baz) | grep -Fx "bar baz foo"
	echo $(words $(sort a a b c)) | grep 3
	echo $(strip       b   ) | grep ^b$$
	echo $(dir foo/bar/baz)  | grep -Fx "foo/bar"
	echo $(dir /a/b/c/)  | grep -Fx "/a/b/c"
	echo $(notdir /a/b/c/d.txt)  | grep -Fx "d.txt"
	echo $(notdir d.txt)  | grep -Fx "d.txt"
	echo $(abspath d.txt)  | grep -Fx "$${PWD}/d.txt"
	echo $(realpath d.txt)  | grep -Fx "$${PWD}/d.txt"

%.txt:
	@echo $@