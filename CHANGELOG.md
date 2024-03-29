## 0.5.2
 * Flush `stdout` so that commands aren't out-of-order when there's no TTY (added by [PR #21](https://github.com/personalizedrefrigerator/AlmostMake/pull/21)).

## 0.5.1
 * Fix circular dependency warnings shown when there are no circular dependencies.
 * `\u` expands to the username in `almake_shell`.

## 0.5.0
 * Multiple template recipes with the same target format (e.g. %.o: %.c and %.o: %.cc)
   are no longer merged into a single target.
 * Hide `\[` and `\]` characters in `almake_shell`'s interactive prompt.
   * Define `\h` and `\w` escape sequences for `PS1` and `PS2` in `almake_shell`'s prompt.
 * By default, expand undefined macros to nothing, rather than stopping the build and displaying an error.

## 0.4.1
 * If running `make a`, for files `a`, `b`, and `c`, if `a` depends on `b` and 
      `b` depends on `c`, previously, a change to `c` would not remake `a`! This has been fixed!
 * Python 3.6.8 is (mostly) supported! Allow package distribution for it on PyPI.

## 0.4.0
 * Calling custom `echo` with no arguments now produces a single newline.
 * `grep` can accept an empty pattern.
 * Added macro functions `$(firstword some words here)`, `$(lastword more words)`, and `$(word 3,1 2 3)`.

## 0.3.3
 * Fix `exit` command.

## 0.3.2
 * Support GNUMake-style `generates: ;` empty recipes.

## 0.3.1
 * Fix include directive bug: `include: dependency1 ...` is not an include directive.

## 0.3.0
 * Support for finding files relative to `VPATH`

## 0.2.1
 * Fix a bug: `if not targets['.SUFFIXES']: ...` should have been `if not '.SUFFIXES' in targets: ...` 

## 0.2.0
 * Built-in `cat` does not stop early on failure to decode/open one or more arguments.
 * GNUMake-style conditionals!
    * You can now use `ifeq`, `ifneq`, `ifdef`, and `ifndef`.
 * Added macro functions `$(subst from,to,text)` and `$(patsubst pattern,replacement,text)`

## 0.1.3
 * `$(dir ...)`, `$(notdir ...)`, `$(abspath ...)`, and `$(realpath ...)` functions.
 * Macro usage bug-fixes.
    * `$(words $(sort foo bar baz))` now works as expected! Nested macro-expansions were not working!

## 0.1.2
 * Support for `-w, --print-directory` flags.
 * Flags imported from `MAKEFLAGS` no longer attempt to claim following values that are really default arguments.

## 0.1.1
 * Built-in pipe interface: If the first argument has a non-zero return code, return that, rather than the return code of the right!
 * Add `$(words ...)` and `$(sort ...)` macro functions. `$(words a b c)` returns 3, the number of words it is given. `$(sort ...)` sorts the  list of words it is given and removes duplicates.
 * Fix `$(wildcard ...)`!

## 0.1.0
 * Improved `README`.

## 0.0.19
 * Built-in `mkdir` and `rm` commands.
 * `$(wildcard ...)` function available in `almake`.
 * Misc. bug fixes 

## 0.0.18
 * Oops! `FORMAT_COLORS['red']` is bad! Use `FORMAT_COLORS['RED']` instead!
    * In some places, output was colorized using `FORMAT_COLORS['red']`. There is no key, `red` in `FORMAT_COLORS`. As such, when logging was to occur, a very-confusing error message was displayed when caught, namely, `'red'`!

## 0.0.17
 * Shell-related bug fixes.

## 0.0.16
 * Built-in `grep` and `cat` commands.
 * Globbing bug-fixes.
 * `.include`, `include`, `sinclude`, and `-include` directives.
    * `.include` is not fully compatible with BSDMake.

## 0.0.15
 * Built-in `ls`
    * Doesn't use color when piped (assuming pipes not sent to system)
    * Additional flags
    * Documented flags (in output of `ls --help`).
 * Added built-in `touch` command.
 * Globbing expansions can be relative.
 * Recursive globbing via `**`.

## 0.0.14
 * Stop using `os.chdir` to keep track of `cwd` in `almake_shell`.

## 0.0.13
 * Partial globbing support in `almake_shell`.
    * No recursive (e.g. `./**/*.txt`) globbing support yet...
 * Tilde expansion.
 * `almake_shell` has a file option!
 * Flags do not remove arguments from the pool of default arguments.
 * Better built-in `ls` implementation.

## 0.0.12
 * Built-in shell can now be run via `almake_shell`
    * Make and shell bug-fixes.
