
all: $(wildcard *.tx*)
	echo $(strip $(strip a)) | grep -Fx a
	echo $(words a) | grep 1
	echo $(words a b c d    another word) | grep 6
	echo $(sort a b c) | grep "a b c"
	echo $(sort a a b c) | grep -Fx "a b c"
	echo $(sort foo bar baz) | grep -Fx "bar baz foo"
	echo $(words $(sort a a b c)) | grep 3
	echo $(strip       b   ) | grep ^b$$
	echo $(firstword Does it get the first word?) | grep -Fx "Does"
	echo $(lastword Does it get the last word?) | grep -Fx "word?"
	echo $(word 99999, a b c d e f    g) | grep -Fx ""
	echo $(word 3, 1 2 3) | grep -Fx 3
	echo $(word 4, a	thing to test) | grep -Fx "test"
	echo $(word 1,) | grep -Fx ""
	echo $(word 1, firstword) | grep -Fx "firstword"
	echo $(firstword 1,firstword) | grep -Fx "1,firstword"
	echo $(lastword $(strip thing       )) | grep -Fx "thing"

	echo $(dir foo/bar/baz)  | grep -Fx "foo/bar"
	echo $(dir /a/b/c/)  | grep -Fx "/a/b/c"
	echo $(notdir /a/b/c/d.txt)  | grep -Fx "d.txt"
	echo $(notdir d.txt)  | grep -Fx "d.txt"
	echo $(abspath d.txt)  | grep -Fx "$${PWD}/d.txt"
	echo $(realpath d.txt)  | grep -Fx "$${PWD}/d.txt"

	echo $(subst a,b,a) | grep -Fx "b"
	echo $(subst foo,bar,bar) | grep -Fx "bar"
	echo $(subst nope,noChanges,here) | grep -Fx "here"
	echo $(subst and,it,happened to happen, that day. And so it did. And, and, and.) \
		| grep -Fx "happened to happen, that day. And so it did. And, it, it."
	
	echo $(patsubst a,b,c d ) | grep -Fx "c d"
	echo $(patsubst a,,c d ) | grep -Fx "c d"
	echo $(patsubst c,aa,c d ) | grep -Fx "aa d"
	echo $(patsubst c,,c d ) | grep -Fx "d"
	echo a$(patsubst %,,c d )b | grep -Fx "ab"
	echo $(patsubst %.in,%.out, a.in b.in c.out) | grep -Fx "a.out b.out c.out"
	echo $(patsubst \%.%.backup,abc.%.backup,one two.%.backup %.abcdefg.backup) | grep -Fx "one two.%.backup abc.abcdefg.backup"
	echo $(patsubst %%,foo,a% b c% d e% f% g% h) | grep -Fx "foo b foo d foo foo foo h"

%.txt:
	@echo $@