# AlmostMake

A pure-python, not-quite-POSIX-compliant implementation of make.

## Usage

AlmostMake installs the `almake` command-line utility. 

Running `almake` in a directory with a file named `Makefile` causes `almake` to satisfy the first target defined in that file.

For example, say `Makefile` contains the following:
```Makefile
# A makefile!

# This is the first target.
# (Pretend `echo 'Hello, world'`
# is indented with a single tab)
firstTarget:
    echo 'Hello, world'

# firstTarget isn't the name of a real file!
# Mark it as PHONY. We need this because if 
# firstTarget were to be a file in the same
# folder as Makefile, its existence (and lack
# of newer dependencies) would cause `almake`
# to do nothing!
.PHONY: firstTarget
```

`almake` then runs the commands associated with firstTarget. Each line is given its own shell.

`almake` also makes available the `almost_make` module! Documentation on this is coming, but for now, check out the source on [GitHub](https://github.com/personalizedrefrigerator/AlmostMake)! 

## Installation

### From PyPI...
AlmostMake is on the Python Package Index! To install it, run:
```sh
$ python3 -m pip install almost-make-personalizedrefrigerator
```

To update it,
```sh
$ python3 -m pip install --upgrade
```

### From GitHub...

As `AlmostMake` is hosted on GitHub, it can be installed by cloning:
```sh
$ git clone https://github.com/personalizedrefrigerator/AlmostMake.git
$ cd AlmostMake
$ make play
```

## Testing

To test AlmostMake, run,
```sh
$ make test
```

At present, it has only been tested on Debian and Ubuntu with Python 3.7 and 3.8. It may work with other operating systems and Python versions, but this is not guaranteed.

If you find that AlmostMake works on a platform not listed here, post an issue or comment on this project's GitHub repository! Pull requests and community feedback are welcome!
