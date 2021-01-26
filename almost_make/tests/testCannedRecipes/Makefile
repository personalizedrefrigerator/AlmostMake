#!make

BUILD_DIR := ./build
OBJS := printPass.o print.o
OBJS_FULLPATH := $(patsubst %.o,$(BUILD_DIR)/%.o,$(OBJS))
IFLAGS := -I./src

VPATH := ./src $(BUILD_DIR)

all:

check: all
	chmod u+x main
	$(EXEC_PROGRAM) ./main | grep PASS

all: main

clean:
	-rm -rf build
	-rm -f main

$(BUILD_DIR):
	mkdir build

main: $(OBJS)
	@echo "Building with objects, $(OBJS_FULLPATH)"
	$(CC) $(IFLAGS) main.c $(OBJS_FULLPATH) -o $(PWD)/main

# This is a test. Just use the C compiler for .cc files.
%.o: %.cc %.h $(BUILD_DIR)
	$(CC) $(CFLAGS) $(IFLAGS) -c $< -o $(BUILD_DIR)/$@

%.o: %.c %.h $(BUILD_DIR)
	$(CC) $(CFLAGS) $(IFLAGS) -c $< -o $(BUILD_DIR)/$@
