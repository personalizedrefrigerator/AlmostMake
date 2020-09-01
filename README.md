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

In addition to the `almake` command, the `almake_shell` command is available. This command gives access to an interactive version of the (very limited) shell built into AlmostMake. See `almake --help` and `almake_shell --help` for more information.

## Installation

### From PyPI...
AlmostMake is on the Python Package Index! To install it, run:
```sh
$ python3 -m pip install almost-make
```

To update it,
```sh
$ python3 -m pip install --upgrade almost-make
```

### From GitHub...

As `AlmostMake` is hosted on GitHub, it can be installed by cloning:
```sh
$ git clone https://github.com/personalizedrefrigerator/AlmostMake.git
$ cd AlmostMake
$ make install
```

You may also need to install `setuptools`, `wheel`, and `twine`. [See Packaging Python Projects](https://packaging.python.org/tutorials/packaging-projects/) for a brief overview of these packages. They can be installed as follows:
```sh
$ python3 -m pip install --user --upgrade setuptools wheel twine
```

## Testing

To test AlmostMake, run,
```sh
$ make test
```

Note, however, that `make test` depends on `make install`!

At present, it has only been tested on Debian and Ubuntu with Python 3.7 and 3.8. It may work with other operating systems and Python versions, but this is not guaranteed.

If you find that AlmostMake works on a platform not listed here, post an issue or comment on this project's GitHub repository! Pull requests and feedback are welcome!
