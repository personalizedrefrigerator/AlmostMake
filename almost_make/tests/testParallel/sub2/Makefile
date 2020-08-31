#!make

all: foo bar baz

foo: baz bar
	@echo "This is foo..."
	@echo "Testing..."

bar:
	@echo "Bar does something..."
	ls | grep "Makefile"

baz:
	@echo "Running baz..."