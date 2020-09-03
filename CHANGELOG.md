
## 0.0.17, 0.0.18
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
