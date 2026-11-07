# Engineering guidelines

Only edit this file when explicitly requested.

<!-- >>> gspot managed >>> -->

## Rules

Read `.gspot/rules/WORKING.md` and `.gspot/rules/WRITING.md` first.
Read a rule below when its sentence fits your task.
A more specific rule wins over a general one.

- `.gspot/rules/BASH.md`: when you write or change a shell script.
- `.gspot/rules/CLI.md`: when you change a command-line program that the project ships.
- `.gspot/rules/COMMENTS.md`: when you write or change a comment.
- `.gspot/rules/DEPENDENCIES.md`: before you add, upgrade, or remove a dependency.
- `.gspot/rules/DOCKER.md`: when you change a Dockerfile, a Compose file, or `.dockerignore`.
- `.gspot/rules/DOCS.md`: when you write or change documentation.
- `.gspot/rules/ERRORS.md`: when you write code that raises, catches, or reports an error.
- `.gspot/rules/FASTAPI.md`: when you change a FastAPI application.
- `.gspot/rules/GENERATED.md`: when you change a generated file, or the code that writes one.
- `.gspot/rules/GIT.md`: before you commit, push, tag, or open a pull request.
- `.gspot/rules/HTTP.md`: when you change an HTTP service.
- `.gspot/rules/LOGGING.md`: when you add or change logging.
- `.gspot/rules/NAMING.md`: when you name a file, folder, type, function, or variable.
- `.gspot/rules/OPERATIONS.md`: when you write a deployment, publishing, or remote shell script.
- `.gspot/rules/PLANNING.md`: before you write a plan.
- `.gspot/rules/PYTHON.md`: when you change Python code.
- `.gspot/rules/SAFETY.md`: when a shell script deletes files, downloads, uses `sudo`, starts background jobs, or parses JSON or YAML.
- `.gspot/rules/SECRETS.md`: when code reads, stores, or logs a secret.
- `.gspot/rules/SECURITY.md`: when code takes input from outside the program, or handles authentication, redirects, or downloads.
- `.gspot/rules/SETTINGS.md`: when you change how a program reads its settings or environment.
- `.gspot/rules/SUPPRESSIONS.md`: before you add a suppression comment or run `gspot ignore`.
- `.gspot/rules/TASKS.md`: when you change `mise` tasks, `package.json` scripts, a `Makefile`, or another task runner.
- `.gspot/rules/TESTING.md`: when you write or change a test.
- `.gspot/rules/TYPING.md`: when you write Python type annotations.

### Commands

The rules write `gspot` for `bunx --no-install gspot`.

Before you finish a change, stage it and run `gspot check --staged --only commit`. When you commit, fix what the hook reports.

Change a setting with `gspot set`, `unset`, or `unignore`. Write the other `[[...]]` records by hand, after the user agrees, then run `gspot install`.
When `gspot check` names a new configuration, ask the user, then run the `gspot add` line it prints and `gspot install`.
Run `gspot ignore` or `gspot remove` only after the user agrees, with a reason.
After you edit a package manifest or a tsconfig, run `gspot install`.

Do not edit the files that gspot writes. `gspot/generated-files` reports an edit. Change `gspot.toml`, then run `gspot install`.

<!-- <<< gspot managed <<< -->
