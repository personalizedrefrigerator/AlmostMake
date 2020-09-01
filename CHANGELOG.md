
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
