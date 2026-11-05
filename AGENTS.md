# Engineering Guidelines

These are detailed engineering guidelines for AI agents. The rules live in
`rules/BASH.md`, `rules/DOCKER.md`, `rules/GENERAL.md`, `rules/NAMING.md`,
`rules/PLANNING.md`, and `rules/PYTHON.md`.

Only edit this file or the files under `rules/` when explicitly requested.

<!-- >>> gspot managed >>> -->

## Rules

Read these rules first:

- `.gspot/rules/WORKING.md`
- `.gspot/rules/WRITING.md`
- `.gspot/rules/TALKING.md`

Read a rule below when its sentence fits your task.
A rule marked `in <folder>/` applies only to files in that folder.
A more specific rule wins over a general one.

### Languages

- `.gspot/rules/BASH.md`: when you write or change a shell script.
- `.gspot/rules/OPERATIONS.md`: when you write a deployment, publishing, or remote shell script.
- `.gspot/rules/PACKAGING.md`: when you change Python dependencies, lockfiles, or package layout.
- `.gspot/rules/PYTHON.md`: when you change Python code.
- `.gspot/rules/SAFETY.md`: when a shell script deletes files, downloads, uses `sudo`, starts background jobs, or parses JSON or YAML.
- `.gspot/rules/TYPING.md`: when you write Python type annotations.

### Frameworks

- `.gspot/rules/FASTAPI.md`: when you change a FastAPI application.

### Testing

- `.gspot/rules/PYTEST.md`: when you write or change a pytest test.

### Infrastructure

- `.gspot/rules/DOCKER.md`: when you change a Dockerfile, a Compose file, or `.dockerignore`.

### General

- `.gspot/rules/CLI.md`: when you change a command-line program that the project ships.
- `.gspot/rules/COMMENTS.md`: when you write or change a comment.
- `.gspot/rules/DEPENDENCIES.md`: before you add, upgrade, or remove a dependency.
- `.gspot/rules/DOCS.md`: when you write or change documentation.
- `.gspot/rules/ERRORS.md`: when you write code that raises, catches, or reports an error.
- `.gspot/rules/GENERATED.md`: when you change a generated file, or the code that writes one.
- `.gspot/rules/GIT.md`: before you commit, push, tag, or open a pull request.
- `.gspot/rules/HTTP.md`: when you change an HTTP service.
- `.gspot/rules/LOGGING.md`: when you add or change logging.
- `.gspot/rules/NAMING.md`: when you name a file, folder, type, function, or variable.
- `.gspot/rules/PLANNING.md`: before you write a plan.
- `.gspot/rules/SECRETS.md`: when code reads, stores, or logs a secret.
- `.gspot/rules/SECURITY.md`: when code handles input, authentication, redirects, or downloads.
- `.gspot/rules/SETTINGS.md`: when you change how a program reads its settings or environment.
- `.gspot/rules/SUPPRESSIONS.md`: before you add a suppression comment or run `gspot ignore`.
- `.gspot/rules/TASKS.md`: when you change `mise` tasks, `package.json` scripts, a `Makefile`, or another task runner.
- `.gspot/rules/TESTING.md`: when you write or change a test.

### Commands

The rules write `gspot` for `bunx --no-install gspot`.

Commit, and fix what the hook reports. Before you push, run `gspot check --changed --stage push`.

To change `gspot.toml`, run `gspot set`, `unset`, or `unignore`.
When `gspot check` or `gspot doctor` names a new configuration, ask the user, then run the `gspot add` line it prints and `gspot install`.
Run `gspot ignore` or `gspot remove` only after the user agrees, with a reason.
After you edit `gspot.toml`, a package manifest, or a tsconfig, run `gspot install`.

### Generated files

`.gitattributes` marks each file that gspot writes `linguist-generated`, in the block between the gspot markers.
Do not edit these files. Change `gspot.toml`, then run `gspot install`.

<!-- <<< gspot managed <<< -->
