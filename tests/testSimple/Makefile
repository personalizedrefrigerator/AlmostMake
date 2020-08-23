#!make

.POSIX:

all:

check: all
	chmod u+x main
	$(EXEC_PROGRAM) ./main | grep PASS


all: main

clean:
	-rm -f main.o
	-rm -f main

# We generate main.o because ths is a test makefile.
main: main.o
	$(CC) main.c -o main

.SUFFIXES: .c .o
.c.o:
	$(CC) $(CFLAGS) -c $< -o $@
