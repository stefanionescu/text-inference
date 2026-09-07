# Working on Python

These rules apply to Python source files, Python test files, Python data
modules, local linting tools, quantization code, engine code, runtime code, CLI
modules, generated Python examples, and Python snippets committed to this
repository.

Use this file together with [`GENERAL.md`](GENERAL.md), [`NAMING.md`](NAMING.md),
and the local tooling configured in `pyproject.toml` and `quality/`.

## Contents

- [Core Python Philosophy](#core-python-philosophy)
- [Source Material Decisions](#source-material-decisions)
- [Local Tooling Authority](#local-tooling-authority)
- [Runtime, Encoding, and Files](#runtime-encoding-and-files)
- [Environment and Configuration](#environment-and-configuration)
- [Package Installation Security](#package-installation-security)
- [Module Structure](#module-structure)
- [Imports](#imports)
- [Public and Internal Interfaces](#public-and-internal-interfaces)
- [Formatting](#formatting)
    - [Indentation](#indentation)
    - [Line Length and Wrapping](#line-length-and-wrapping)
    - [Blank Lines](#blank-lines)
    - [Whitespace](#whitespace)
    - [Trailing Commas](#trailing-commas)
    - [Parentheses](#parentheses)
    - [String Quotes](#string-quotes)
- [Naming](#naming)
- [Comments and Docstrings](#comments-and-docstrings)
    - [Comments](#comments)
    - [Docstrings](#docstrings)
    - [Module Docstrings](#module-docstrings)
    - [Function and Method Docstrings](#function-and-method-docstrings)
    - [Class Docstrings](#class-docstrings)
    - [Property Docstrings](#property-docstrings)
    - [Override Docstrings](#override-docstrings)
    - [TODO Comments](#todo-comments)
- [Type Annotations](#type-annotations)
    - [Annotation Scope](#annotation-scope)
    - [Annotated Metadata](#annotated-metadata)
    - [Using Any and Object](#using-any-and-object)
    - [Input and Return Types](#input-and-return-types)
    - [Typing Imports](#typing-imports)
    - [None and Optional Values](#none-and-optional-values)
    - [Generic Types](#generic-types)
    - [Type Aliases](#type-aliases)
    - [Type Variables](#type-variables)
    - [Forward References](#forward-references)
    - [Protocols and Interfaces](#protocols-and-interfaces)
    - [Variable Annotations](#variable-annotations)
    - [Ignoring Type Errors](#ignoring-type-errors)
- [Constants, Globals, and Mutable State](#constants-globals-and-mutable-state)
- [Functions and Methods](#functions-and-methods)
    - [Function Size](#function-size)
    - [Default Arguments](#default-arguments)
    - [Return Statements](#return-statements)
    - [Nested Functions and Classes](#nested-functions-and-classes)
    - [Lambda Functions](#lambda-functions)
    - [Conditional Expressions](#conditional-expressions)
    - [Comprehensions and Generator Expressions](#comprehensions-and-generator-expressions)
    - [Generators](#generators)
- [Classes](#classes)
    - [Class Design](#class-design)
    - [Initialization and Named Constructors](#initialization-and-named-constructors)
    - [Dataclasses](#dataclasses)
    - [Properties](#properties)
    - [Inheritance](#inheritance)
    - [Decorators](#decorators)
    - [Exceptions as Classes](#exceptions-as-classes)
- [Exceptions and Error Handling](#exceptions-and-error-handling)
- [Assertions](#assertions)
- [Boolean Logic and Comparisons](#boolean-logic-and-comparisons)
- [Control Flow Simplification](#control-flow-simplification)
- [Iteration and Collections](#iteration-and-collections)
- [Strings, Logging, and Error Messages](#strings-logging-and-error-messages)
- [Files and Stateful Resources](#files-and-stateful-resources)
- [Main Programs and Top-Level Code](#main-programs-and-top-level-code)
- [Packages and Architecture](#packages-and-architecture)
    - [src Layout and Import Path](#src-layout-and-import-path)
- [FastAPI](#fastapi)
    - [FastAPI Source Decisions](#fastapi-source-decisions)
    - [FastAPI Application Structure](#fastapi-application-structure)
    - [FastAPI Routers](#fastapi-routers)
    - [FastAPI Path Operations](#fastapi-path-operations)
    - [FastAPI Parameters and Validation](#fastapi-parameters-and-validation)
    - [FastAPI Request and Response Schemas](#fastapi-request-and-response-schemas)
    - [FastAPI Schema Fields and Examples](#fastapi-schema-fields-and-examples)
    - [FastAPI Nested and Special Types](#fastapi-nested-and-special-types)
    - [FastAPI Headers and Cookies](#fastapi-headers-and-cookies)
    - [FastAPI Response Models](#fastapi-response-models)
    - [FastAPI Status Codes and Errors](#fastapi-status-codes-and-errors)
    - [FastAPI Forms and Files](#fastapi-forms-and-files)
    - [FastAPI JSON Encoding and Updates](#fastapi-json-encoding-and-updates)
    - [FastAPI Async and Blocking Work](#fastapi-async-and-blocking-work)
    - [FastAPI Dependencies](#fastapi-dependencies)
    - [FastAPI Dependencies with Yield](#fastapi-dependencies-with-yield)
    - [FastAPI Security](#fastapi-security)
    - [FastAPI Streaming](#fastapi-streaming)
    - [FastAPI Background Tasks](#fastapi-background-tasks)
    - [FastAPI Middleware](#fastapi-middleware)
    - [FastAPI Metadata and Docs](#fastapi-metadata-and-docs)
    - [FastAPI Testing](#fastapi-testing)
    - [FastAPI Anti-Patterns](#fastapi-anti-patterns)
- [Power Features](#power-features)
- [Threading and Concurrency](#threading-and-concurrency)
- [Tests](#tests)
- [Verification Commands](#verification-commands)
- [Review Checklist](#review-checklist)
- [Anti-Patterns](#anti-patterns)

## Core Python Philosophy

Rules:

- Write readable Python before clever Python.
- Prefer explicit data flow, clear names, and small functions.
- Keep code import-stable. Importing a module must not load models, initialize
  engines, touch external services, start background work, parse CLI arguments, or mutate
  runtime state.
- Prefer project-specific rules over generic style guides when they conflict.
- Prefer consistency with the surrounding module when a source guide allows more
  than one style.
- Do not make style-only churn outside the requested scope.
- Do not preserve obsolete Python APIs, wrappers, re-exports, or alternate code
  paths. Follow [`GENERAL.md`](GENERAL.md) for replacement work.
- Make public behavior clear through names, type annotations, docstrings, and
  tests when tests are requested.
- Use exceptions for exceptional conditions, not for ordinary branch logic.
- Use built-in language features directly when they express the operation
  clearly.

Good Python is easy to scan:

```python
"""Yield request text from chat messages."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PromptMessage:
    """One request message."""

    content: str


def iter_message_text(messages: Iterable[PromptMessage]) -> Iterable[str]:
    """Yield text content from request messages."""
    for message in messages:
        yield message.content


__all__ = [
    "PromptMessage",
    "iter_message_text",
]
```

Bad Python hides behavior and ownership:

```python
from examples import *

STATE = {"instance": None}


def get_instance():
    import importlib

    return importlib.import_module("loader").build_examples()
```

## Source Material Decisions

These rules adapt PEP 8, PEP 257, and the Google Python Style Guide into one
local standard for this repository.

| Topic                        | Local decision                                                                                                                                                                                                           |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Style authority              | Project rules and local tooling win over generic source guides.                                                                                                                                                          |
| Formatter line length        | Ruff is configured with `line-length = 120`; use that local limit for Python code.                                                                                                                                       |
| Standard-library line length | PEP 8's 79-character code limit and 72-character comment/docstring limit describe the Python standard library, not this repo.                                                                                            |
| Google line length           | Google's 80-character default is useful guidance for docstring summaries and comments, but local Ruff formatting is authoritative.                                                                                       |
| Formatter                    | Ruff format is the local formatter. Do not hand-format against a different style.                                                                                                                                        |
| Linter                       | Ruff lint, BasedPyright, import-linter, and custom `quality/` scripts are local policy. Pylint guidance from Google maps to these local tools.                                                                           |
| Runtime                      | The project requires Python 3.12. Use Python 3.12 syntax when it improves clarity.                                                                                                                                       |
| Future imports               | Prefer `from __future__ import annotations` in Python modules.                                                                                                                                                           |
| Quotes                       | Ruff format uses double quotes. Use double quotes for ordinary strings unless another quote avoids escaping. Docstrings always use triple double quotes.                                                                 |
| Imports                      | Use absolute imports for cross-package imports. Explicit relative sibling imports are allowed inside a package when that is the local pattern.                                                                           |
| Class/function imports       | Direct imports of public classes, functions, and constants are allowed when they keep call sites readable. Import typing and `collections.abc` symbols directly.                                                         |
| `__all__`                    | Keep `__all__` at the bottom of modules. This local rule overrides PEP 8's normal module-dunder placement for `__all__`.                                                                                                 |
| Other module dunders         | Put dunders such as `__version__` after the module docstring and future imports, before ordinary imports.                                                                                                                |
| License boilerplate          | Do not invent license boilerplate. Add it only if the project defines the exact boilerplate.                                                                                                                             |
| Function length              | Custom lint limits functions to 60 counted code lines by default. Keep functions smaller when practical.                                                                                                                 |
| File length                  | Custom lint limits runtime Python files to 300 counted code lines by default, except barrel `__init__.py` files.                                                                                                         |
| Public typing                | Public APIs should be annotated. The repo does not require every private helper to be annotated, but annotations are encouraged where they clarify contracts.                                                            |
| Typing style                 | Use modern union syntax, built-in generics, `type` statements or `TypeAlias` for real type aliases, `Annotated` for typed metadata, `object` for values that can be any object, and protocols for structural interfaces. |
| Argument and return types    | Prefer abstract input types and concrete return types for concrete implementations. Avoid union return types that force caller-side type branching.                                                                      |
| Logging                      | Modules create `logging.getLogger(__name__)`; application entrypoints configure handlers and levels. Library modules do not configure handlers except `NullHandler`.                                                     |
| Project layout               | Keep importable project code under `src/`; do not patch `sys.path` to make package imports work.                                                                                                                         |
| Inheritance                  | Prefer composition for code sharing, protocols for interfaces, and subclassing only for true specialization.                                                                                                             |
| FastAPI                      | Keep FastAPI framework rules in the FastAPI section. They apply only to FastAPI apps and must not override general Python, security, or local architecture rules.                                                        |
| Package installs             | Deployment installs should use pinned, hashed, binary-only requirements where practical. Do not use direct setuptools install commands.                                                                                  |
| Verification                 | Do not run tests, linting, type checks, or format checks unless the user asks.                                                                                                                                           |

When editing an existing file, follow the surrounding style where the source
guides allow a choice. When creating new code, use the decisions in this table.

## Local Tooling Authority

The local Python quality stack is:

- Ruff format.
- Ruff lint.
- BasedPyright.
- import-linter.
- Custom structural linters in `quality/`.
- Naming checks described in [`NAMING.md`](NAMING.md).

Rules:

- Treat local lint failures as policy failures.
- Do not add per-file ignores, inline ignores, or broad config exceptions unless
  the user explicitly asks for a tooling change or the violation is unavoidable.
- Do not copy an existing per-file ignore into new files.
- Do not broaden an existing exception to make unrelated code pass.
- Do not disable a rule when a clear code change can satisfy it.
- Do not run verification commands unless the user asks. When asked, run only
  the requested or necessary scoped command.

Current local tooling constraints include:

- Python source under configured directories uses snake_case `.py` filenames.
- Runtime files should stay under 300 counted code lines.
- Functions and methods should stay under 60 counted code lines.
- Runtime modules must not use local imports inside function, method, or class
  bodies.
- Runtime modules must not use lazy module loading, module-level lazy export
  hooks, or dynamic imports.
- Runtime modules must not use lazy singleton patterns.
- Runtime modules must not create import cycles.
- Packages with `__init__.py` and exactly one non-init module should be flattened
  to a single module.
- Directories should not contain multiple `.py` files with the same
  underscore-delimited prefix.
- `__all__` must appear at the bottom of each module.
- Python logic must live in Python modules. Shell scripts must call it with
  `python -m`; do not embed inline Python in shell scripts.

## Runtime, Encoding, and Files

Rules:

- Use Python 3.12 syntax.
- Store source files as UTF-8.
- Do not add an encoding declaration unless a tool or runtime requires it.
- Use LF line endings.
- Keep identifiers ASCII-only.
- Use English words for identifiers, comments, and docstrings unless an external
  identifier must keep another language or spelling.
- Use non-ASCII characters sparingly in string data.
- Do not use byte-order marks.
- Python filenames must use `.py`.
- Python filenames must be snake_case, except `__init__.py` and `__main__.py`.
- Python filenames must not contain dashes.
- Keep modules importable by pydoc, tests, linting tools, and type checkers.

Bad:

```text
ModelConfig.py
model-config.py
model config.py
```

Good:

```text
model_config.py
modeling.py
__main__.py
```

## Environment and Configuration

Rules:

- Treat environment variables as external text input.
- Read environment variables at a configuration or application boundary, not
  throughout business logic.
- Parse and validate environment-derived values once before passing them inward.
- Store secrets in environment variables or a secret manager, never in source
  code, docs examples, tests, or checked-in config.
- Do not use a real-looking default for a secret. Missing required secrets
  should fail at startup or command initialization.
- Do not make importable modules depend on an active shell, virtual
  environment, current working directory, or globally installed package.
- Use project configuration, editable installs, `python -m`, or the configured
  environment to resolve imports.
- Do not commit virtual environment directories or generated package caches.

Good:

```python
@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration loaded from the environment."""

    max_items: int


def load_config(environ: Mapping[str, str]) -> AppConfig:
    """Load runtime configuration from environment variables."""
    raw_max_items = environ.get("MAX_ITEMS", "100")
    return AppConfig(max_items=int(raw_max_items))
```

Bad:

```python
def list_items() -> list[Item]:
    limit = int(os.getenv("MAX_ITEMS", "100"))
    return query_items(limit=limit)
```

## Package Installation Security

These rules apply to deployment scripts, release images, CI release installs,
production environment bootstraps, and any committed install command meant to
create a repeatable runtime environment.

Rules:

- Prefer a generated lock or requirements file with every direct and transitive
  dependency pinned.
- For pip-based deployment installs, use hash-checking mode with
  `--require-hashes`.
- Use `sha256` hashes for package artifacts.
- Hashes must cover every requirement and every transitive dependency in the
  requirements file.
- Requirements used with `--require-hashes` must be pinned with `==`, a direct
  URL, or a filesystem path.
- Use multiple hashes for a package when deployments may install different
  wheels for different supported platforms.
- Disallow source distributions for deployment installs with
  `--only-binary :all:` when all required packages publish compatible wheels.
- If a package must be installed from source, treat that as a deliberate
  supply-chain exception. Keep the build environment explicit and reviewed.
- Do not rely on hashes embedded in package-index download URLs as the integrity
  control for deployment installs. The hash must be local to the requirements or
  lock material used by the install.
- Do not use `--extra-index-url` for private packages in deployment installs.
  Prefer a single controlled `--index-url`, or `--no-index` with reviewed
  `--find-links` wheel artifacts.
- Use `--no-deps` only when the requirements file already contains the complete
  resolved dependency tree.
- Install the local project through pip, not direct setuptools commands.
- When project dependencies are already installed from a pinned and hashed
  requirements file, install the local project with `python -m pip install
--no-deps .` or the editable equivalent for development workflows.
- Do not call `python setup.py install`, `python setup.py develop`, or
  `easy_install`.
- Do not weaken install security in a deploy script just to make an install pass.
  Fix the requirements or document the supply-chain exception.
- Do not add or regenerate dependency locks, hashes, or requirements files unless
  the requested task includes dependency maintenance.

Good deployment install:

```bash
python -m pip install \
  --require-hashes \
  --only-binary :all: \
  --no-deps \
  -r requirements.lock
```

Good local project install after dependency install:

```bash
python -m pip install --no-deps .
```

Good editable install for development:

```bash
python -m pip install --no-deps -e .
```

Good hashed requirement:

```text
example-package==1.2.3 \
  --hash=sha256:1111111111111111111111111111111111111111111111111111111111111111 \
  --hash=sha256:2222222222222222222222222222222222222222222222222222222222222222
```

Bad deployment installs:

```bash
python -m pip install -r loose-requirements.lock
python -m pip install --extra-index-url https://packages.example.com/simple private-package
python setup.py install
python setup.py develop
easy_install example-package
```

## Module Structure

Order module contents this way:

1. Module docstring.
2. `from __future__ import annotations`, when used.
3. Other module dunders, except `__all__`.
4. Imports.
5. Module constants.
6. Type aliases.
7. Dataclasses and classes.
8. Functions.
9. `if __name__ == "__main__":` guard, when the module is executable.
10. `__all__` at the bottom.

Rules:

- Every runtime module should have a module docstring that describes its present
  purpose.
- Keep top-level code limited to declarations, constants, imports, and cheap
  initialization.
- Do not perform I/O, network calls, quantization, model loading, CLI parsing, or
  long computations at import time.
- Do not mutate global runtime state at import time except for declared
  constants and deliberate local configuration.
- Keep `__all__` explicit for modules with a public API.
- Use `__all__ = []` when a module intentionally exports no public names.

Good:

```python
"""Configuration constants for runtime settings."""

from __future__ import annotations

from pathlib import Path

MODELS_DIR = Path("/models")
DEFAULT_ENGINE = "trt"


def resolve_model_dir(name: str) -> Path:
    """Return the model directory for a model name."""
    return MODELS_DIR / name


__all__ = [
    "DEFAULT_ENGINE",
    "MODELS_DIR",
    "resolve_model_dir",
]
```

Bad:

```python
from pathlib import Path

settings = read_runtime_settings()
model = AutoModel.from_pretrained("some-model")

__all__ = ["model"]
```

## Imports

Rules:

- Put imports at the top of the file, after the module docstring and future
  imports.
- Keep ordinary imports in one flat block. Do not separate standard-library,
  third-party, first-party, or sibling imports with blank lines.
- Put one-line imports before multiline or explicitly parenthesized imports.
- Sort one-line imports by the total rendered statement length. Break equal
  lengths by case-insensitive statement text and then exact statement text.
- Sort multiline or explicitly parenthesized imports by the rendered import
  header length using the same text tie-breakers.
- Sort names inside grouped imports by rendered name length using the same text
  tie-breakers.
- Apply the same ordering and spacing rules inside a top-level bare
  `if TYPE_CHECKING:` body.
- Put a blank line after each completed import block.
- Use one import per line for ordinary imports.
- Import typing and `collections.abc` symbols directly.
- Use absolute imports for cross-package repository imports.
- Use explicit relative imports for sibling modules inside the same package when
  surrounding code already does that.
- Never use implicit relative imports.
- Never use wildcard imports.
- Never import inside function, method, or class bodies in runtime code.
- Never use dynamic imports through `importlib.import_module`, `__import__`, or
  `builtins.__import__` in runtime code.
- Do not rely on the main script directory being present on `sys.path`.
- Avoid circular imports by moving shared data or contracts into a lower-level
  owner.

Good:

```python
from __future__ import annotations

import torch
import logging
from pathlib import Path
from .runtime import RuntimeConfig
from transformers import AutoTokenizer
from src.config.model.selection import MODEL
from src.runtime.config import ModelSettings
from collections.abc import Iterable, Sequence
```

Bad:

```python
import os, sys
from examples import *


def build():
    import src.runtime.settings
```

Direct symbol imports are acceptable for public classes, functions, constants,
and typing symbols when they make the call site clearer:

```python
from pathlib import Path
from typing import Literal
from dataclasses import dataclass
from src.runtime.config import ModelSettings
```

Use module imports when the module prefix makes ownership clearer:

```python
import random
import logging

logger = logging.getLogger(__name__)
rng = random.Random(seed)  # noqa: S311
```

Do not import a module only to hide a vague name:

```python
from storage.file_system import options as fs_options
```

Use aliases only when:

- two imported modules have the same final name;
- an imported module conflicts with a local top-level name;
- the original module name is inconveniently long;
- the alias is a standard abbreviation, such as `np` for NumPy;
- the alias disambiguates a generic module name.

## Public and Internal Interfaces

Rules:

- Public names are names intended for callers outside the module.
- Internal names use one leading underscore.
- Do not use double-leading underscores unless avoiding subclass collisions in a
  class designed for inheritance.
- Do not invent double-leading and double-trailing dunder names.
- Use `__all__` to declare public module exports.
- Imported names are implementation details unless explicitly exported through
  `__all__` or documented as module API.
- Do not rely on indirect access to names imported by another module.
- Public attributes should not have leading underscores.
- Internal modules, functions, constants, and attributes should have one leading
  underscore.

Good:

```python
_DEFAULT_TIMEOUT_SECONDS = 30


def _normalize_quantization(value: str) -> str:
    return value.strip().lower()


def build_model_settings(model: str, quantization: str) -> ModelSettings:
    """Build model settings for one runtime."""
    return ModelSettings(model=model, quantization=_normalize_quantization(quantization))


__all__ = [
    "build_model_settings",
]
```

Bad:

```python
def __normalize_label__(value):
    return int(value)
```

## Formatting

Use Ruff format as the source of truth for mechanical formatting.

Rules:

- Do not fight the formatter.
- Do not hand-align code in ways the formatter will undo.
- Do not use semicolons.
- Do not put multiple statements on one line.
- Keep formatting consistent with the surrounding file when the formatter allows
  more than one readable option.

### Indentation

Rules:

- Use 4 spaces per indentation level.
- Never use tabs.
- Use implicit continuation inside parentheses, brackets, and braces.
- Prefer hanging indents with one argument or item per line when a call or
  literal is too long.
- When using a hanging indent, put no arguments on the first line.
- Align closing delimiters with the construct start when the values are split
  across lines.

Good:

```python
result = long_function_name(
    first_argument,
    second_argument,
    third_argument,
)
```

Good:

```python
result = long_function_name(first_argument, second_argument, third_argument)
```

Bad:

```python
result = long_function_name(first_argument,
    second_argument,
    third_argument)
```

Long conditionals may use extra indentation to distinguish the condition from
the body:

```python
if (
    config is None
    or "editor.language" not in config
    or config["editor.language"].use_spaces is False
):
    use_tabs()
```

### Line Length and Wrapping

Rules:

- Local Python code uses the Ruff limit of 120 characters.
- Prefer shorter lines when they are naturally readable.
- Keep docstring summary lines concise and on one physical line.
- Wrap long expressions with implicit continuation inside parentheses, brackets,
  and braces.
- Do not use backslashes for line continuation.
- Break before binary operators in new multiline arithmetic or boolean
  expressions when that improves readability.
- Prefer breaking at the highest syntactic level.
- Do not split a name from its type annotation unless the name and type together
  cannot fit readably.
- Put long URLs on their own comment line instead of splitting them.

Good:

```python
income = (
    gross_wages
    + taxable_interest
    + (dividends - qualified_dividends)
    - ira_deduction
    - student_loan_interest
)
```

Bad:

```python
income = (gross_wages +
          taxable_interest +
          (dividends - qualified_dividends) -
          ira_deduction -
          student_loan_interest)
```

Good:

```python
message = (
    "This long string is split through implicit literal concatenation "
    "inside parentheses."
)
```

Bad:

```python
message = "This long string is split with an explicit continuation " \
    "character."
```

### Blank Lines

Rules:

- Use two blank lines between top-level function and class definitions.
- Use one blank line between methods inside a class.
- Use one blank line between a class docstring and the first method.
- Use blank lines inside functions sparingly to separate logical sections.
- Do not add blank lines immediately after a `def` line.
- Do not use large blank-line blocks as visual decoration.

Good:

```python
def build_examples() -> list[PromptExample]:
    """Build examples."""
    return []


def count_examples(examples: list[PromptExample]) -> int:
    """Return the number of examples."""
    return len(examples)
```

Bad:

```python
def build_examples() -> list[PromptExample]:

    return []
```

### Whitespace

Rules:

- Do not use extra whitespace inside parentheses, brackets, or braces.
- Do not use whitespace before commas, semicolons, or colons.
- Use one space after commas and colons, except at the end of a line.
- Do not use whitespace before the opening parenthesis of a function call.
- Do not use whitespace before indexing or slicing brackets.
- Surround assignment, augmented assignment, comparisons, identity checks,
  membership checks, and boolean operators with one space on each side.
- Use judgment around arithmetic operators, but never use more than one space on
  either side.
- Do not vertically align assignments, comments, dictionary colons, or other
  tokens with extra spaces.
- Do not leave trailing whitespace.

Good:

```python
spam(ham[1], {"eggs": 2})
x = 1
long_name = 2
if value is not None:
    return value
```

Bad:

```python
spam( ham[ 1 ], { "eggs" : 2 } )
x         = 1
long_name = 2
if value == None:
    return value
```

For slices, treat the colon like a low-priority binary operator when both sides
are complex. Omit spaces when an endpoint is omitted.

Good:

```python
items[1:9]
items[:9]
items[lower + offset : upper + offset]
items[: upper_fn(x) : step_fn(x)]
```

Bad:

```python
items[1: 9]
items[lower + offset:upper + offset]
items[ : upper]
```

### Trailing Commas

Rules:

- Use a trailing comma in multiline literals, argument lists, imports, and
  `__all__`.
- Do not use a redundant trailing comma when the closing delimiter is on the
  same line.
- Use a trailing comma for a one-item tuple, preferably inside parentheses.

Good:

```python
FILES = ("setup.cfg",)

VARIANTS = [
    "trt",
    "vllm",
    "awq",
]
```

Bad:

```python
FILES = "setup.cfg",
VARIANTS = ["trt", "vllm",]
```

### Parentheses

Rules:

- Use parentheses for grouping, tuples, and implicit line continuation.
- Do not wrap simple conditions in unnecessary parentheses.
- Do not wrap simple return values in unnecessary parentheses.
- Parenthesize one-item tuples for clarity.
- Returning a tuple may use parentheses when it improves readability.

Good:

```python
if is_ready:
    return value

singleton = (value,)
return first, second
```

Bad:

```python
if (is_ready):
    return (value)
```

### String Quotes

Rules:

- Use double quotes for ordinary strings in new code.
- Use single quotes only when it avoids escaping or matches surrounding code the
  formatter preserves.
- Use triple double quotes for docstrings.
- Prefer triple double quotes for multiline strings.
- Do not create string literals with significant trailing whitespace.
- Use `textwrap.dedent()` when a multiline string should not include indentation.

Good:

```python
name = "ModernBERT"
message = "It's ready."
doc = """One multiline string."""
```

Bad:

```python
name = 'ModernBERT'
doc = '''A docstring-like string.'''
```

## Naming

Follow [`NAMING.md`](NAMING.md) for all naming choices.

Python-specific rules from the source guides:

- Packages and modules use short, lowercase names. Use underscores when they
  improve readability.
- Classes use CapWords.
- Exceptions use CapWords and end with `Error` when they represent errors.
- Functions, methods, parameters, local variables, and instance variables use
  lowercase words separated by underscores.
- Constants use uppercase words separated by underscores.
- Type aliases use CapWords, with one leading underscore for internal aliases.
- Private unconstrained type variables may use `_T` and `_P`.
- Avoid single-character names except for narrow counters, iterators, exception
  aliases such as `e`, file handles such as `f`, private unconstrained type
  variables, and established mathematical notation.
- Never use `l`, `O`, or `I` as single-character names.
- Use `self` for instance methods and `cls` for class methods.
- If a parameter would conflict with a keyword, append one trailing underscore.

Good:

```python
class TrainingConfig:
    """Training configuration."""


def build_examples(source_items: list[object]) -> list[PromptExample]:
    """Build examples from raw items."""
    ...


MAX_EXAMPLES = 1000
class_: str
```

Bad:

```python
class runtime_config:
    ...


def buildExamples(data):
    ...


maxExamples = 1000
clss = "value"
```

## Comments and Docstrings

Comments and docstrings must match [`GENERAL.md`](GENERAL.md).

Rules:

- Describe present behavior only.
- Do not include change history.
- Do not mention removed, replaced, renamed, or previous code.
- Do not reference specific file paths unless the reference is essential and
  stable.
- Keep comments and docstrings accurate when behavior changes.
- Use clear English.
- Use complete sentences for block comments and docstrings.
- Keep punctuation, spelling, and grammar clean.

### Comments

Rules:

- Use comments to explain intent, invariants, edge cases, and non-obvious
  choices.
- Do not narrate obvious code.
- Block comments apply to the code that follows and use `#` plus one space on each line.
- Inline comments are separated from code by at least two spaces and start with
  `#` plus one space.
- Use inline comments sparingly.
- Keep comments up to date when code changes.

Good:

```python
# Longformer uses the first token for global attention in classification.
global_attention_mask[:, 0] = 1
```

Bad:

```python
global_attention_mask[:, 0] = 1  # Set item to one
```

When suppressing a linter warning, keep the suppression narrow and explain it
when the symbolic name is not enough:

```python
rng = random.Random(seed)  # noqa: S311
```

Do not add broad suppressions:

```python
# noqa
```

### Docstrings

Rules:

- Use triple double quotes for all docstrings.
- Write docstrings for public modules, functions, classes, and methods.
- Write docstrings for nontrivial private functions and methods.
- Do not write noisy docstrings for obvious private helpers.
- One-line docstrings stay on one line and end with punctuation.
- Multiline docstrings start with a one-line summary, then a blank line, then
  details.
- Put the closing triple quotes of a multiline docstring on their own line.
- Do not restate the signature in a docstring.
- Document arguments, return values, yielded values, side effects, and raised
  exceptions when they are part of the interface.
- Do not document exceptions raised only when callers violate the documented
  contract.
- Keep docstring style consistent within a file. Descriptive style and
  imperative style are both allowed by the source material.

Good one-line docstring:

```python
def build_token_budget(prompt_tokens: int, output_tokens: int) -> int:
    """Return the total token budget."""
    return prompt_tokens + output_tokens
```

Bad one-line docstring:

```python
def build_token_budget(prompt_tokens: int, output_tokens: int) -> int:
    """build_token_budget(prompt_tokens, output_tokens) -> int"""
    return prompt_tokens + output_tokens
```

Good multiline docstring:

```python
def fetch_rows(keys: Sequence[str]) -> Mapping[str, tuple[str, ...]]:
    """Fetch rows for the requested keys.

    Retrieves one row for each key that exists in the backing table.

    Args:
        keys: Keys to fetch.

    Returns:
        A mapping from key to row values.

    Raises:
        OSError: The backing table could not be read.
    """
```

### Module Docstrings

Rules:

- Runtime modules should start with a docstring describing the module's purpose.
- A module docstring may include a short usage example when it helps callers.
- Test modules do not need a module docstring unless they need unusual setup,
  environment, or update instructions.
- Do not write a test module docstring that only repeats the file name or module
  name.

Good:

```python
"""Runtime settings assembly for the inference server."""
```

Bad:

```python
"""Tests for loader."""
```

### Function and Method Docstrings

Rules:

- Public functions and methods require docstrings.
- Nontrivial private helpers require docstrings.
- Functions with non-obvious logic require docstrings.
- Functions that mutate an argument must say so.
- Generator functions use `Yields:` instead of `Returns:`.
- `Returns:` may be omitted when the one-line summary already fully describes
  the returned value.
- Do not document `None` returns unless it clarifies control flow.
- Use `Args:`, `Returns:`, `Yields:`, and `Raises:` sections when needed.
- Keep section indentation consistent within a file.

Good:

```python
def build_engine_settings(
    inference_engine: str | None,
    trt_engine_dir: str,
    default_max_batched_tokens: int,
) -> EngineSettings:
    """Build inference engine settings from validated inputs.

    Args:
        inference_engine: Runtime backend name.
        trt_engine_dir: TensorRT engine directory.
        default_max_batched_tokens: vLLM token batch limit.

    Returns:
        Resolved engine settings.
    """
```

Bad:

```python
def build_engine_settings(engine, path, tokens):
    """build_engine_settings(engine, path, tokens)."""
```

### Class Docstrings

Rules:

- Public classes require docstrings.
- A class docstring starts with a one-line summary describing what an instance
  represents.
- Public attributes, excluding properties, are documented in an `Attributes:`
  section.
- Exception class docstrings describe the condition represented by the
  exception, not the raising site.
- Do not write "Class that..." as the summary.

Good:

```python
@dataclass
class RuntimePrompt:
    """Single runtime prompt example.

    Attributes:
        prompt: Normalized prompt text.
        expected_status: Expected response status.
        group: Group identifier for related prompts.
    """

    prompt: str
    expected_status: str
    group: str
```

Bad:

```python
class RuntimePrompt:
    """Class that stores a runtime prompt."""
```

Good exception docstring:

```python
class MissingModelError(Exception):
    """The requested model artifact is unavailable."""
```

Bad exception docstring:

```python
class MissingModelError(Exception):
    """Raised when model loading fails."""
```

### Property Docstrings

Rules:

- Property docstrings describe the attribute, not the method action.
- Use attribute-style wording.
- Do not write "Returns..." for a property unless the surrounding file already
  uses that style.

Good:

```python
@property
def num_labels(self) -> int:
    """The number of supported runtime labels."""
    return len(self.labels)
```

Bad:

```python
@property
def num_labels(self) -> int:
    """Returns the number of supported runtime labels."""
    return len(self.labels)
```

### Override Docstrings

Rules:

- An overridden method may omit a docstring when it is decorated with
  `@override` and does not materially change the base contract.
- Add a docstring when an override changes behavior, side effects, constraints,
  or return semantics.
- Use `typing.override` when available in the target runtime. Use
  `typing_extensions.override` when needed.

Good:

```python
from typing_extensions import override


class Child(Parent):
    @override
    def build(self) -> Result:
        return super().build()
```

### TODO Comments

Rules:

- Use TODO comments only for temporary, tracked work.
- A TODO starts with `TODO:`, then a link or issue reference, then `-`, then an
  explanation.
- Do not use individual names or team names as TODO ownership.
- Do not add TODOs for vague future improvements.
- Include a specific event or date when the TODO depends on time or an external
  milestone.

Good:

```python
# TODO: https://example.com/issues/123 - Remove this branch when all exports use JSONL.
```

Bad:

```python
# TODO: clean this up later
# TODO(alex): fix this
```

## Type Annotations

Type annotations improve readability and catch type-related errors. They are
especially important for public APIs, stable code, complex data shapes, and
model or data boundaries.

### Annotation Scope

Rules:

- Annotate public APIs.
- Annotate functions whose types are hard to infer.
- Annotate data structures crossing module boundaries.
- Annotate code that is prone to type-related errors.
- Annotate code when it becomes stable from a type perspective.
- Do not annotate `self` or `cls` unless needed for precise typing.
- Do not annotate `__init__` as returning `None` unless local tooling or
  surrounding style requires it.
- Use `Any` only when the type should genuinely be unconstrained or cannot be
  expressed clearly.
- Do not add obsolete `# type:` comments.
- Prefer modern Python 3.12 shorthand syntax over older `typing.Union`,
  `typing.Optional`, `typing.List`, `typing.Dict`, and `typing.Type` aliases.

Good:

```python
def build_examples(source: Literal["warmup", "test"] = "warmup") -> list[PromptExample]:
    """Build examples for a data source."""
```

Acceptable for a private helper when the body is obvious and local:

```python
def _token_count(value):
    return int(value)
```

Better when the helper is part of a typed flow:

```python
def _token_count(value: int) -> int:
    return int(value)
```

### Annotated Metadata

Rules:

- Use `typing.Annotated` when a framework or validation library needs metadata
  attached to a normal Python type.
- Put the real type first. Put framework or validation metadata after it.
- Keep defaults as ordinary Python parameter defaults when using
  `Annotated`.
- Do not put conflicting defaults in both the metadata object and the function
  signature.
- Do not use arbitrary string metadata as a substitute for clear domain types,
  validators, or documented framework metadata.
- Prefer `Annotated` over older framework styles that replace the Python
  default value with a metadata object.

Good:

```python
def read_items(q: Annotated[str | None, Query(max_length=50)] = None) -> list[Item]:
    return find_items(query=q)
```

Bad:

```python
def read_items(q: str | None = Query(default=None, max_length=50)) -> list[Item]:
    return find_items(query=q)
```

Bad conflicting defaults:

```python
def read_items(q: Annotated[str, Query(default="recent")] = "popular") -> list[Item]:
    return find_items(query=q)
```

### Using Any and Object

Rules:

- Use `object` when a value can be literally any Python object and the function
  only uses operations available on all objects, such as passing the value to
  `str()`.
- Use `object` for callback return values when the callback return value is
  ignored.
- Use `Any` when the type cannot be expressed accurately, the correct type would
  make the API unreasonably hard to use, or the value intentionally escapes type
  checking.
- Do not use `Any` just to avoid writing a precise type.
- Prefer a protocol, type variable, overload, or small value object over `Any`
  when that models the contract clearly.

Good:

```python
def format_for_display(value: object) -> str:
    """Format any object for display."""
    if isinstance(value, int):
        return f"{value:02}"
    return str(value)


def call_callback(callback: Callable[[int], object]) -> None:
    """Call a callback and ignore its return value."""
    callback(42)
```

Bad:

```python
def format_for_display(value: Any) -> str:
    return str(value)


def call_callback(callback: Callable[[int], None]) -> None:
    callback(42)
```

### Input and Return Types

Rules:

- For arguments, prefer protocols and abstract collection types such as
  `Iterable`, `Sequence`, `Mapping`, and `Callable`.
- For arguments that accept any value, use `object`, not `Any`.
- For concrete implementations, return concrete types such as `list`, `dict`,
  and concrete dataclasses.
- For protocols and abstract base classes, choose return types case by case
  based on the promised interface.
- Avoid union return types when callers must immediately branch with
  `isinstance()` to use the result.
- If different result shapes require different caller behavior, prefer separate
  functions, a tagged dataclass, a protocol, or a small hierarchy with a clear
  common contract.
- Use `float` instead of `int | float` for numeric APIs where integers are valid
  float inputs.
- Use `None`, not `Literal[None]`.

Good:

```python
def map_lengths(values: Iterable[str]) -> list[int]:
    return [len(value) for value in values]


def create_label_map() -> dict[str, int]:
    return {"reject": 0, "accept": 1}


def to_display_text(value: object) -> str:
    return str(value)
```

Bad:

```python
def map_lengths(values: list[str]) -> list[int]:
    return [len(value) for value in values]


def create_label_map() -> MutableMapping[str, int]:
    return {"reject": 0, "accept": 1}


def to_display_text(value: Any) -> str:
    return str(value)
```

### Typing Imports

Rules:

- Import symbols from `typing` and `collections.abc` directly.
- Prefer `collections.abc` abstract containers for input types.
- Prefer built-in generic types such as `list[str]`, `dict[str, int]`, and
  `tuple[str, ...]`.
- Do not use `typing.List`, `typing.Dict`, or `typing.Tuple` in new Python 3.12
  code.
- Do not use `typing.Type`; use built-in `type`.
- Do not use `typing.Union` or `typing.Optional`; use `|`.
- Do not use `typing.Text` in new code.
- Use `str` for text and `bytes` for binary data.
- Use `AnyStr` only when multiple string annotations must all be the same text
  or binary type.

Good:

```python
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Literal, TypeAlias


def transform(rows: Sequence[tuple[str, int]]) -> Mapping[str, int]:
    ...
```

Bad:

```python
from typing import Dict, List, Tuple, Type


def transform(rows: List[Tuple[str, int]]) -> Dict[str, int]:
    ...


def build(cls: Type[ModelConfig]) -> ModelConfig:
    ...
```

### None and Optional Values

Rules:

- Use explicit `X | None` for nullable values.
- Put `None` last in union annotations.
- Do not rely on implicit optional inference from a default of `None`.
- Use `is None` and `is not None` for None checks.
- When a parameter is nullable and has a default, annotate it as nullable.

Good:

```python
def read_examples(path: Path | None = None) -> list[PromptExample]:
    if path is None:
        path = DEFAULT_DATA_PATH
    ...
```

Bad:

```python
def normalize(value: None | str) -> str:
    ...


def read_examples(path: Path = None) -> list[PromptExample]:
    path = path or DEFAULT_DATA_PATH
```

### Generic Types

Rules:

- Specify type parameters for generic types.
- Do not write bare `Sequence`, `Mapping`, `list`, or `dict` unless the element
  type is intentionally unconstrained and made explicit with `Any`.
- Prefer `TypeVar` when a relationship between input and output types matters.

Good:

```python
def get_names(employee_ids: Sequence[int]) -> Mapping[int, str]:
    ...
```

Bad:

```python
def get_names(employee_ids: Sequence) -> Mapping:
    ...
```

Good when the key type should be preserved:

```python
_T = TypeVar("_T")


def get_names(employee_ids: Sequence[_T]) -> Mapping[_T, str]:
    ...
```

### Type Aliases

Rules:

- Use type aliases for complex repeated types.
- Type alias names use CapWords.
- Internal type aliases use one leading underscore.
- Use Python 3.12 `type` statements for new type aliases when they improve
  clarity and the surrounding module already uses Python 3.12 syntax.
- Keep `TypeAlias` for existing aliases when changing syntax would create
  unrelated churn.
- Do not use `TypeAlias` for ordinary value, module, class, function, constant,
  or path aliases.

Good:

```python
from typing import TypeAlias

_LossAndGradient: TypeAlias = tuple[torch.Tensor, torch.Tensor]
MetricMap: TypeAlias = Mapping[str, float]
Path = pathlib.Path
ERROR_EXISTS = errno.EEXIST
```

Bad:

```python
_LossAndGradient = tuple[torch.Tensor, torch.Tensor]
Path: TypeAlias = pathlib.Path
ERROR_EXISTS: TypeAlias = errno.EEXIST
```

### Type Variables

Rules:

- Private unconstrained type variables may use `_T`, `_P`, and similar short
  names.
- Public or constrained type variables must have descriptive names.
- Use `_co` and `_contra` suffixes for covariant and contravariant variables.
- Do not use public single-letter `T` or `P` for type variables.

Good:

```python
from collections.abc import Callable
from typing import ParamSpec, TypeVar

_P = ParamSpec("_P")
_T = TypeVar("_T")
AddableType = TypeVar("AddableType", int, float, str)
AnyFunction = TypeVar("AnyFunction", bound=Callable)
```

Bad:

```python
T = TypeVar("T")
_F = TypeVar("_F", bound=Callable)
_T = TypeVar("_T", int, float, str)
```

### Forward References

Rules:

- Prefer `from __future__ import annotations` for forward references.
- Do not remove `from __future__ import annotations` only because newer Python
  versions defer annotation evaluation. This repository still targets Python
  3.12 and keeps future annotations as the local convention.
- Use string annotations only when future annotations are not available or when
  needed for a type-checking-only import pattern.
- Avoid type-only circular imports. They are design pressure to move shared
  contracts.

Good:

```python
from __future__ import annotations


class Node:
    def __init__(self, parent: Node | None = None) -> None:
        self.parent = parent
```

Acceptable when avoiding a runtime import strictly for typing:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from external_package import ExternalType


def build(value: "ExternalType") -> str:
    ...
```

### Protocols and Interfaces

Rules:

- Prefer `typing.Protocol` for structural interfaces used by a consumer.
- Keep protocols narrow. Define only the attributes and methods the consumer
  needs.
- Place a protocol near the consumer when it describes what that consumer needs,
  not what an implementation happens to provide.
- Use `@runtime_checkable` only when runtime `isinstance()` checks are truly
  needed.
- Use abstract base classes when nominal identity, runtime instantiation checks,
  or a standard-library ABC contract is the real requirement.
- Do not use an abstract base class to share implementation code.
- Do not mix interface definition with subclass-based code sharing.
- Implementations do not need to import or subclass a protocol for type checkers
  to recognize that they satisfy it.

Good:

```python
class Reader(Protocol):
    def read(self) -> str:
        ...


def print_reader(reader: Reader) -> None:
    print(reader.read())
```

Good implementation:

```python
class FileReader:
    def read(self) -> str:
        return "contents"
```

Bad:

```python
class BaseReader(abc.ABC):
    def read_and_print(self) -> None:
        print(self.read())

    @abc.abstractmethod
    def read(self) -> str:
        ...
```

### Variable Annotations

Rules:

- Use variable annotations when the inferred type is unclear or impossible.
- Use one space after the colon.
- Do not use a space before the colon.
- If assigning a value, use one space around `=`.

Good:

```python
examples: list[PromptExample] = []
label_by_name: dict[str, int] = {}
```

Bad:

```python
examples:list[PromptExample] = []
label_by_name : dict[str, int]={}
```

### Ignoring Type Errors

Rules:

- Avoid `# type: ignore`.
- If an ignore is necessary, keep it line-scoped.
- Include the specific error code when the type checker supports it.
- Do not keep unused ignores.
- Prefer refactoring or a clearer annotation over suppressing a type error.

Good:

```python
value = untyped_api()  # type: ignore[no-any-return]
```

Bad:

```python
# type: ignore
```

## Constants, Globals, and Mutable State

Rules:

- Module constants are allowed and encouraged.
- Constants use uppercase names with underscores.
- Internal constants use one leading underscore.
- Avoid mutable global state.
- Do not use lazy singleton state.
- Do not create module-level `STATE`, `_STATE`, `INSTANCE`, `_INSTANCE`, or
  `_instance` holders.
- Do not expose mutable globals directly as public API.
- If mutable global state is genuinely required, keep it internal and document
  the design reason.
- Do not mutate module globals as a hidden side effect of ordinary function
  calls.

Good:

```python
DEFAULT_MODEL_NAME = "answerdotai/ModernBERT-base"
_MAX_RETRIES = 3
```

Bad:

```python
STATE = {"instance": None}
_INSTANCE = None
```

Prefer passing state explicitly:

```python
def build_client(config: ClientConfig) -> Client:
    return Client(config)
```

Do not hide process-wide state behind lifecycle helpers:

```python
def get_instance() -> Client:
    ...
```

## Functions and Methods

Rules:

- Keep functions focused on one responsibility.
- Prefer plain functions and explicit data flow before classes.
- Name functions by action and domain concept.
- Do not use `process`, `handle`, `run`, `execute`, or `do_work` when a more
  precise action exists.
- Use `handle` only for callbacks, framework boundaries, event handlers, or
  signal handlers.
- Keep side effects explicit in the name or docstring.
- Do not hide I/O in helpers that look like pure transformations.

### Function Size

Rules:

- Keep functions small and focused.
- Custom lint limits functions and methods to 60 counted code lines by default.
- If a function approaches the limit, consider extracting real sub-operations.
- Do not split a function into meaningless helpers only to satisfy the count.
- Extract helpers when the extracted operation has a clear name and contract.

Good extraction:

```python
def _trim_history_messages(
    messages: Sequence[HistoryMessage],
    max_messages: int,
) -> list[HistoryMessage]:
    if len(messages) <= max_messages:
        return list(messages)
    return list(messages[-max_messages:])
```

Bad extraction:

```python
def _part_one(data):
    ...


def _part_two(data):
    ...
```

### Default Arguments

Rules:

- Do not use mutable objects as default argument values.
- Use `None` as the default and create the mutable value inside the function.
- Immutable defaults such as `None`, strings, numbers, booleans, and tuples are
  allowed.
- Do not use dynamic values such as `time.time()` as defaults.
- Do not use parsed flag values, environment-dependent values, or mutable global
  values as defaults.
- When an annotated parameter has a default, put spaces around `=`.
- When an unannotated parameter has a default, do not put spaces around `=`.

Good:

```python
def collect_labels(labels: Sequence[str] | None = None) -> list[str]:
    if labels is None:
        labels = []
    return list(labels)
```

Bad:

```python
def collect_labels(labels: list[str] = []) -> list[str]:
    return labels
```

Good formatting:

```python
def resize(width: int = 0, height: int = 0) -> None:
    ...
```

Bad formatting:

```python
def resize(width: int=0, height: int=0) -> None:
    ...
```

### Return Statements

Rules:

- Be consistent in return statements.
- If any return statement returns a value, every no-value path should explicitly
  return `None` or end in a clear final return.
- Do not mix `return` and `return value` in the same function.
- Do not rely on implicit `None` when an explicit no-result path is meaningful.

Good:

```python
def safe_sqrt(value: float) -> float | None:
    if value < 0:
        return None
    return math.sqrt(value)
```

Bad:

```python
def safe_sqrt(value: float) -> float | None:
    if value >= 0:
        return math.sqrt(value)
```

### Nested Functions and Classes

Rules:

- Nested functions are allowed when they close over a local value and make the
  outer function clearer.
- Nested classes are allowed for narrowly scoped helper types.
- Do not nest a function only to hide it from users.
- Prefer a module-level private helper when tests or reuse need direct access.
- Avoid nested functions that make the outer function long or hard to scan.

Good:

```python
def get_adder(summand: float) -> Callable[[float], float]:
    """Return a function that adds a fixed summand."""

    def add(value: float) -> float:
        return summand + value

    return add
```

Bad:

```python
def build_examples(data: list[object]) -> list[PromptExample]:
    def normalize_prompt(value: object) -> str:
        return str(value).strip()

    ...
```

Use a module helper instead:

```python
def _normalize_prompt(value: object) -> str:
    return str(value).strip()
```

### Lambda Functions

Rules:

- Lambdas are allowed for simple one-line expressions.
- Do not bind a lambda directly to a name. Use `def`.
- Prefer generator expressions over `map()` or `filter()` with a lambda.
- Use functions from `operator` for common operations when they are clearer.
- If a lambda spans multiple lines or becomes hard to read, use a named
  function.

Good:

```python
def double(value: int) -> int:
    return value * 2


sorted_items = sorted(items, key=lambda item: item.name)
```

Bad:

```python
double = lambda value: value * 2
```

### Conditional Expressions

Rules:

- Conditional expressions are allowed for simple cases.
- Each portion should be easy to read: true expression, condition, false
  expression.
- Use a full `if` statement when the expression becomes long or nested.

Good:

```python
mode = "stream" if is_streaming else "batch"
```

Bad:

```python
mode = (
    choose_streaming_mode(request, config)
    if complicated_condition(request, config, metadata)
    else choose_batch_mode(request, config, metadata)
)
```

### Comprehensions and Generator Expressions

Rules:

- Use comprehensions for simple mapping or filtering.
- Do not use multiple `for` clauses or multiple filter expressions in one
  comprehension.
- Optimize for readability, not compactness.
- Use ordinary loops for nested logic, multiple conditions, mutation, or
  non-obvious transformations.
- Generator expressions are preferred when a list is not needed.

Good:

```python
names = [user.name for user in users if user is not None]
```

Good with a long expression:

```python
valid_examples = [
    transform_example(example)
    for example in examples
    if is_valid_example(example)
]
```

Bad:

```python
pairs = [(x, y) for x in range(10) for y in range(5) if x * y > 10]
```

Use a loop:

```python
pairs: list[tuple[int, int]] = []
for x in range(10):
    for y in range(5):
        if x * y > 10:
            pairs.append((x, y))
```

### Generators

Rules:

- Use generators when values can be produced lazily.
- A generator docstring uses `Yields:`.
- If a generator manages an expensive resource, make cleanup explicit.
- Do not keep resource lifetime implicit in a partially consumed generator.

Good:

```python
def iter_prompt_text(examples: Iterable[PromptExample]) -> Iterable[str]:
    """Yield prompt text values.

    Yields:
        Prompt text values.
    """
    for example in examples:
        yield example.prompt
```

## Classes

### Class Design

Rules:

- Prefer functions and data structures unless a class owns real state,
  invariants, or behavior.
- Keep related classes together when they form one cohesive contract, including
  schemas, exceptions, protocols, and their input/output records.
- Split modules by independent responsibilities, not by class count.
- Treat size limits as review prompts: document a justified limit adjustment
  rather than extracting forwarding wrappers only to reduce line counts.
- Do not create classes only to group static functions.
- Avoid `Manager`, `Processor`, `Helper`, and similar vague class names.
- Decide deliberately which attributes are public and which are internal.
- Use public attributes for simple data.
- Use one leading underscore for internal attributes.
- Avoid double-leading underscores unless protecting a base class from subclass
  name collisions.
- Focus on the shape of data before adding behavior.
- If a function coordinates work between multiple classes and no polymorphism is
  involved, keep it a function unless one class clearly owns the behavior.

Good:

```python
class RuntimeBatch:
    """Tokenized prompts prepared for inference."""
```

Bad:

```python
class RuntimeManager:
    """Class that manages runtime work."""
```

### Initialization and Named Constructors

Rules:

- Keep `__init__` small.
- `__init__` should accept the values the class needs, not complex external
  objects that happen to contain those values.
- Do not couple a class constructor to database rows, ORM objects, API payloads,
  CLI namespaces, or provider SDK response objects.
- Use classmethod named constructors for external representations, such as
  `from_row`, `from_payload`, `from_token`, or `from_path`.
- Do not construct business objects with `ClassName(**external_attributes)` when
  that couples the class to an external storage or wire format.
- Validation of class invariants belongs in initialization.
- Complex loading, serialization, deserialization, and validation systems should
  stay outside the business object.
- Derived attributes should be cheap, deterministic, and based on already
  initialized fields. Prefer a named constructor when deriving them requires I/O,
  external services, or complex parsing.

Good:

```python
@dataclass
class Point:
    """Two-dimensional point."""

    x: float
    y: float

    @classmethod
    def from_row(cls, row: PointRow) -> Point:
        """Build a point from a database row."""
        return cls(x=row.x, y=row.y)
```

Bad:

```python
class Point:
    def __init__(self, database_row):
        self.x = database_row.x
        self.y = database_row.y


point = Point(**row.attributes)
```

### Dataclasses

Rules:

- Use dataclasses for plain data records.
- Keep dataclass fields typed.
- Document public fields in the class docstring `Attributes:` section when the
  class is public.
- Do not add methods to a dataclass unless they are part of the data contract.
- Do not use a dataclass as a disguised mutable global configuration object.
- Use `field(default_factory=...)` for mutable defaults.
- Use `__post_init__` for simple invariant checks or cheap derived fields.
- Prefer a named constructor over `__post_init__` when construction needs
  parsing, I/O, external objects, or multiple alternate sources.
- If a project already uses `attrs`, apply the same principles: use factories
  for mutable defaults, validators for invariants, converters for simple input
  normalization, and named constructors for complex creation paths.
- Do not introduce `attrs` solely to avoid writing a small dataclass or ordinary
  function.

Good:

```python
@dataclass(frozen=True)
class ModelVariant:
    """Supported model variant.

    Attributes:
        name: Stable variant name.
        base_model: Hugging Face base model identifier.
    """

    name: str
    base_model: str
```

Good mutable default:

```python
@dataclass
class Batch:
    """Batch of prompts."""

    prompts: list[PromptExample] = field(default_factory=list)
```

Bad mutable default:

```python
@dataclass
class Batch:
    prompts: list[PromptExample] = []
```

### Properties

Rules:

- Use properties only for cheap, straightforward, unsurprising attribute access.
- Do not use a property to simply get and set an internal attribute.
- Do not hide expensive work behind attribute syntax.
- Do not hide side effects behind properties.
- Use `@property`; do not manually implement descriptors unless the power
  feature is necessary.
- Avoid properties for computations subclasses may need to override and extend.

Good:

```python
@property
def num_examples(self) -> int:
    """The number of examples."""
    return len(self.examples)
```

Bad:

```python
@property
def model(self) -> AutoModel:
    return AutoModel.from_pretrained(self.model_name)
```

### Inheritance

Rules:

- Design explicitly for inheritance or avoid inheritance.
- Prefer composition over inheritance for code sharing.
- Do not subclass only to reuse methods or state.
- Do not use the template method pattern as a default design. A base class that
  defines control flow and calls subclass hooks is harder to read and easier to
  break than a wrapper with explicit delegation.
- Do not mix three different inheritance purposes in one hierarchy: code
  sharing, interface definition, and specialization.
- Use protocols or small ABCs for interfaces.
- Use specialization only when the subclass truly is the base class plus more
  and can be used anywhere the base class is expected.
- Follow the Liskov substitution principle: callers that accept the base class
  must be able to interact correctly with the subclass.
- Keep strict specialization hierarchies shallow and physically close together
  when practical.
- Do not model variants as one class with a type field and many optional fields
  that only apply for some type values.
- Make invalid states unrepresentable where practical.
- Use composition when behavior varies across more than one axis.
- Use a wrapper when you need one behavior plus cross-cutting behavior such as
  tracking, caching, timing, or logging.
- Consider `functools.singledispatch` when an operation varies by type but does
  not clearly belong to one class.
- Public attributes have no leading underscore.
- Internal attributes use one leading underscore.
- Double-leading underscores are only for avoiding accidental subclass name
  collisions.
- If a class is intended for subclassing, document the public API and subclass
  API separately when that distinction matters.

Good specialization:

```python
@dataclass
class EmailAddress:
    """Email address shared by all address types."""

    id: UUID
    address: str


@dataclass
class Mailbox(EmailAddress):
    """Email address that stores mail."""

    password_hash: str
```

Bad optional-field variant:

```python
@dataclass
class EmailAddress:
    kind: str
    id: UUID
    address: str
    password_hash: str | None
    forwarding_targets: list[str] | None
```

Good wrapper:

```python
class TrackingRepository:
    """Repository wrapper that records retrieved products."""

    def __init__(self, repository: Repository) -> None:
        self._repository = repository
        self.seen: set[Product] = set()

    def add_product(self, product: Product) -> None:
        self._repository.add_product(product)
        self.seen.add(product)
```

Bad subclass-based code sharing:

```python
class BaseRepository(abc.ABC):
    def add_product(self, product: Product) -> None:
        self._add_product(product)
        self.seen.add(product)

    @abc.abstractmethod
    def _add_product(self, product: Product) -> None:
        ...
```

### Decorators

Rules:

- Use decorators when they remove real repetition or express a clear framework
  contract.
- Decorator behavior must be unsurprising.
- Decorators run at definition time, usually import time. Do not let them depend
  on files, sockets, databases, network calls, or other unavailable resources.
- Decorators should preserve function metadata when wrapping functions.
- Write tests for decorators when tests are requested for decorated behavior.
- Avoid `staticmethod`. Use a module-level function instead.
- Use `classmethod` for named constructors or class-specific routines.
- Use `@property` only under the property rules above.

Good:

```python
class ModelConfig:
    @classmethod
    def from_name(cls, name: str) -> ModelConfig:
        """Build a model config from a variant name."""
        return cls(name=name)
```

Bad:

```python
class ModelConfig:
    @staticmethod
    def normalize_name(name: str) -> str:
        return name.strip().lower()
```

Use a module function:

```python
def normalize_model_name(name: str) -> str:
    return name.strip().lower()
```

### Exceptions as Classes

Rules:

- Custom exceptions inherit from `Exception`.
- Do not inherit directly from `BaseException`.
- Exception class names use CapWords.
- Error exception names end with `Error`.
- Exception names should not repeat the module name.
- Exception docstrings describe the represented condition.

Good:

```python
class InvalidVariantError(Exception):
    """The requested model variant is not supported."""
```

Bad:

```python
class VariantsInvalidVariantError(BaseException):
    """Raised in variants.py when the variant is invalid."""
```

## Exceptions and Error Handling

Rules:

- Use built-in exception classes when they fit the error.
- Raise `ValueError` for invalid argument values.
- Raise `TypeError` for invalid argument types when type validation is needed.
- Keep `try` blocks as small as possible.
- Catch specific exceptions.
- Do not use bare `except:`.
- Do not catch `Exception` unless re-raising or creating a deliberate isolation
  boundary that records and suppresses failures.
- Use `else` when code should run only if the `try` block succeeds.
- Use `finally` for cleanup that must run regardless of success or failure.
- Do not use `return`, `break`, or `continue` in a `finally` block when an
  exception could be active.
- Use `raise NewError(...) from error` when replacing an exception but preserving
  the cause.
- Use `raise NewError(...) from None` only when deliberately suppressing an
  irrelevant implementation exception, and preserve relevant details in the new
  message.
- When catching operating-system errors, prefer Python's explicit OSError
  subclass hierarchy over checking `errno` manually.

Good:

```python
try:
    value = collection[key]
except KeyError:
    return key_not_found(key)
else:
    return handle_value(value)
```

Bad:

```python
try:
    return handle_value(collection[key])
except KeyError:
    return key_not_found(key)
```

Good exception replacement:

```python
try:
    raw_value = payload["label"]
except KeyError as error:
    raise ValueError("Missing required field: label") from error
```

Bad catch-all:

```python
try:
    start_server()
except Exception:
    return None
```

## Assertions

Rules:

- Do not use `assert` for application logic, input validation, permission
  checks, or required preconditions.
- Do not rely on `assert` to satisfy type checking or runtime correctness.
- `assert` is acceptable in pytest tests.
- `assert` is acceptable for non-critical internal consistency checks where
  removing it would not change application behavior.
- Use explicit `if` checks and raise exceptions for real validation.

Good:

```python
def connect_to_port(minimum: int) -> int:
    """Connect to the next available port."""
    if minimum < 1024:
        raise ValueError(f"Minimum port must be at least 1024: {minimum=}")
    port = find_next_open_port(minimum)
    if port is None:
        raise ConnectionError(f"Could not connect on or above port: {minimum=}")
    assert port >= minimum
    return port
```

Bad:

```python
def connect_to_port(minimum: int) -> int:
    assert minimum >= 1024
    port = find_next_open_port(minimum)
    assert port is not None
    return port
```

## Boolean Logic and Comparisons

Rules:

- Compare to `None` with `is None` or `is not None`.
- Do not compare booleans to `True` or `False`.
- Use truthiness for sequences and containers.
- When handling integers, compare to `0` when zero has domain meaning.
- Do not write `if not value` when `None`, `0`, `False`, and empty containers
  have different meanings.
- Use `is not` instead of `not ... is`.
- Use `isinstance()` for type checks.
- Use `startswith()` and `endswith()` for prefix and suffix checks.
- Do not compare types directly unless exact type identity is the real contract.
- For rich ordering, implement all relevant comparison operations or use
  `functools.total_ordering()`.

Good:

```python
if value is not None:
    ...

if not examples:
    ...

if count == 0:
    ...

if isinstance(obj, int):
    ...

if filename.endswith(".json"):
    ...
```

Bad:

```python
if value != None:
    ...

if greeting == True:
    ...

if len(examples) == 0:
    ...

if type(obj) is int:
    ...

if filename[-5:] == ".json":
    ...
```

NumPy arrays may reject implicit boolean evaluation. Use `.size` or another
explicit property when checking array emptiness.

## Control Flow Simplification

Rules:

- Reduce nesting when a condition can be merged without changing behavior.
- Merge adjacent `if` statements when the inner condition has no intervening
  work and no `else` branch that changes the result.
- Prefer guard clauses when they remove a level of nesting and keep the main
  path easy to scan.
- Hoist repeated code out of conditional branches when it runs in every branch.
- Hoist loop-invariant statements out of `for` and `while` loops when they do
  not depend on the loop variable and have no required repeated side effect.
- Do not combine conditions when separate conditions communicate distinct
  domain decisions more clearly.
- Do not hoist code when execution order, exceptions, logging, timing, database
  calls, or mutation would change.

Good merged condition:

```python
if is_enabled and has_examples:
    return build_examples()
```

Bad nested condition:

```python
if is_enabled:
    if has_examples:
        return build_examples()
```

Good hoisted branch code:

```python
if sold > DISCOUNT_AMOUNT:
    total = sold * DISCOUNT_PRICE
else:
    total = sold * PRICE
label = f"Total: {total}"
```

Bad repeated branch code:

```python
if sold > DISCOUNT_AMOUNT:
    total = sold * DISCOUNT_PRICE
    label = f"Total: {total}"
else:
    total = sold * PRICE
    label = f"Total: {total}"
```

Good loop-invariant hoist:

```python
city = "London"
for building in buildings:
    addresses.append((building.street_address, city))
```

Bad loop-invariant assignment:

```python
for building in buildings:
    city = "London"
    addresses.append((building.street_address, city))
```

Do not merge conditions when it hides separate decisions:

```python
if not request.user:
    raise PermissionError("Authentication is required")
if not request.user.can_export:
    raise PermissionError("Export permission is required")
```

## Iteration and Collections

Rules:

- Use default iterators and membership operators for containers that support
  them.
- Iterate dictionaries directly for keys.
- Use `.items()` when both keys and values are needed.
- Do not call `.keys()` only to iterate keys.
- Do not call `.readlines()` only to iterate file lines.
- Do not mutate a container while iterating over it.
- Prefer clear loops over dense collection transformations.
- Use `yield from iterable` instead of a loop that only yields every item from
  another iterable.
- Use `any()` and `all()` for simple existence or universal predicate checks.
- Use `[]` for an empty list and `{}` for an empty dictionary.
- Use `list()` or `dict()` when converting an iterable or mapping, not for empty
  literals.

Good:

```python
for key in values:
    ...

for key, value in values.items():
    ...

for line in file_obj:
    ...

if item in values:
    ...
```

Bad:

```python
for key in values.keys():
    ...

for line in file_obj.readlines():
    ...
```

Good delegated yield:

```python
def get_content(entry: Entry) -> Iterable[Block]:
    yield from entry.get_blocks()
```

Bad delegated yield:

```python
def get_content(entry: Entry) -> Iterable[Block]:
    for block in entry.get_blocks():
        yield block
```

Good predicate check:

```python
found = any(thing == expected for thing in things)
all_valid = all(is_valid(thing) for thing in things)
```

Bad predicate loop:

```python
found = False
for thing in things:
    if thing == expected:
        found = True
        break
```

Good empty containers:

```python
items = []
metadata = {}
```

Bad empty containers:

```python
items = list()
metadata = dict()
```

## Strings, Logging, and Error Messages

### String Formatting

Rules:

- Use f-strings, `%` formatting, or `.format()` for formatting.
- Prefer f-strings for ordinary string interpolation.
- Do not use `+` to format strings with values.
- A single `a + b` concatenation is allowed when both values are already strings
  and this is not formatting.
- Do not accumulate strings with `+` or `+=` in a loop.
- Accumulate parts in a list and `"".join(parts)`, or use `io.StringIO`.
- Use implicit literal concatenation inside parentheses for long string
  literals.

Good:

```python
message = f"name: {name}; score: {score}"

rows = ["<table>"]
for last_name, first_name in employees:
    rows.append("<tr><td>%s, %s</td></tr>" % (last_name, first_name))
rows.append("</table>")
employee_table = "".join(rows)
```

Bad:

```python
message = "name: " + name + "; score: " + str(score)

employee_table = "<table>"
for last_name, first_name in employees:
    employee_table += "<tr><td>%s, %s</td></tr>" % (last_name, first_name)
employee_table += "</table>"
```

### Logging

Rules:

- Create loggers with `logging.getLogger(__name__)`.
- Use module-level loggers. Logger names should track the package and module
  hierarchy through `__name__`.
- Do not log through the root logger from application or library modules.
- Use `print()` for ordinary CLI output intended for the user.
- Use `logger.debug()` for detailed diagnostic information.
- Use `logger.info()` for normal operational events and status.
- Use `logger.warning()` when something unexpected happened but the software can
  still continue as expected.
- Use `warnings.warn()` in library code when client code should change to avoid
  the issue.
- Raise an exception to report an error that prevents the requested operation.
- Use `logger.error()`, `logger.exception()`, or `logger.critical()` when an
  error is deliberately suppressed at an isolation boundary and must be recorded.
- Use `logger.exception()` only inside an exception handler.
- Logging calls that accept pattern strings must use a string literal first
  argument and pass values as later arguments.
- Do not use f-strings in logging pattern calls.
- Do not call logging once for the static text and once for the value.
- Do not eagerly compute expensive logging arguments unless the log level is
  enabled. Use `logger.isEnabledFor(...)` around expensive diagnostic work.
- Configure handlers, formatters, and levels at the application entrypoint or
  deployment boundary, not in importable library modules.
- Call `logging.basicConfig()` before logger methods are called when an
  entrypoint uses basic configuration.
- If dictionary or file logging configuration is used, set
  `disable_existing_loggers` deliberately.
- Library modules must not add handlers other than `logging.NullHandler()` to
  their own top-level logger.
- Do not define custom logging levels unless there is a documented application
  need.
- Do not log secrets, tokens, passwords, PII, or full authenticated request
  bodies.
- Keep log messages precise and searchable.

Good:

```python
logger.info("Warmup prompts: %d", num_prompts)
logger.warning("Requested max_length=%d exceeds model limit; clamping to %d", requested, effective)
```

Good expensive debug logging:

```python
if logger.isEnabledFor(logging.DEBUG):
    logger.debug(
        "Tokenization details: %s",
        build_expensive_tokenization_summary(batch),
    )
```

Good exception logging:

```python
try:
    upload_model(model_dir)
except UploadError:
    logger.exception("Model upload failed")
    raise
```

Bad:

```python
logging.info("Warmup prompts: %d", num_prompts)
logger.info(f"Warmup prompts: {num_prompts}")
logger.info("Warmup prompts:")
logger.info(num_prompts)
```

Bad exception logging:

```python
logger.exception("Model upload failed")
```

### Error Messages

Rules:

- Error messages must match the actual error condition.
- Interpolated values must be clearly identifiable.
- Prefer `name=value` formatting for values that aid debugging.
- Keep messages easy to grep.
- Start user-visible messages with an uppercase letter.
- Do not leak schema names, table names, file paths, internal IDs, stack traces,
  trigger names, policy names, secrets, or implementation details.
- Use generic messages for configuration and infrastructure failures unless the
  details are part of the public contract.

Good:

```python
if not 0 <= probability <= 1:
    raise ValueError(f"Not a probability: {probability=}")
```

Bad:

```python
if probability < 0 or probability > 1:
    raise ValueError(f"The probability was bad: {probability}")
```

Good logging around OS errors:

```python
try:
    workdir.rmdir()
except OSError as error:
    logger.warning("Could not remove directory (reason: %r): %r", error, workdir)
```

Bad logging:

```python
try:
    workdir.rmdir()
except OSError:
    logger.warning("Directory already was deleted: %s", workdir)
```

## Files and Stateful Resources

Rules:

- Explicitly close files, sockets, database connections, mmap mappings, h5py
  files, matplotlib figures, and similar stateful resources.
- Prefer `with` statements for resources that support context management.
- Use `contextlib.closing()` for closeable resources without context-manager
  support.
- Do not rely on finalizers or garbage collection for resource cleanup.
- Keep resource scope as small as practical.
- Do not return open resources from helpers unless resource ownership is part of
  the documented contract.
- Document resource lifetime when context-based management is infeasible.

Good:

```python
with path.open(encoding="utf-8") as file_obj:
    for line in file_obj:
        handle_line(line)
```

Bad:

```python
file_obj = path.open()
for line in file_obj:
    handle_line(line)
```

Good for closeable objects without context-manager support:

```python
import contextlib

with contextlib.closing(open_remote_resource(url)) as resource:
    consume(resource)
```

## Main Programs and Top-Level Code

Rules:

- Executable modules put main behavior in a `main()` function.
- Use `if __name__ == "__main__":` before executing program behavior.
- Prefer `raise SystemExit(main())` when `main()` returns an exit code.
- Do not parse CLI arguments at import time.
- Do not run quantization, model loading, tests, network calls, or file
  mutations at import time.
- Use `python -m package.module` for repository Python entrypoints.
- Shell scripts must call Python modules, not inline Python snippets.
- Files that are not intended to execute directly do not need a shebang.
- Directly executable Python files may use `#!/usr/bin/env python3` when a
  shebang is needed.

Good:

```python
def main() -> int:
    """Run the command."""
    ...
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Bad:

```python
args = parser.parse_args()
start_server(args)
```

## Packages and Architecture

Rules:

- Keep packages shallow and purposeful.
- Flatten packages that contain only `__init__.py` and one other module.
- Do not create single-file packages.
- Do not create import cycles.
- Do not create lazy module export hooks such as module-level `__getattr__`,
  `__dir__`, or `__getattribute__`.
- Do not use dynamic imports for lazy loading.
- Do not use package `__init__.py` files to hide expensive imports.
- Keep `__init__.py` files small and import-stable.
- Barrel `__init__.py` files may contain imports and `__all__`.
- Respect import-linter contracts configured in `pyproject.toml`.
- Keep lower-level packages independent of higher-level workflow packages.

### src Layout and Import Path

Rules:

- Keep importable repository code under `src/`.
- Do not create top-level import packages beside repository configuration files.
- Treat the repository root as project configuration and tooling space, not as
  the import package root.
- Run Python entrypoints through the configured environment, editable install,
  project scripts, or `python -m` with the intended import path.
- Do not mutate `sys.path` in package code to make imports work.
- Do not rely on the current working directory being first on Python's import
  path.
- Do not make root-level modules importable only in development. Code that works
  only because the process starts from the repository root is not packaged
  correctly.
- Keep helper scripts that are not meant to be imported outside the package
  import path.

Good layout:

```text
.
  pyproject.toml
  README.md
  src/
    config/
      __init__.py
      runtime/
        __init__.py
        engine.py
    runtime/
      __init__.py
      settings.py
```

Bad layout:

```text
.
  pyproject.toml
  config/
    __init__.py
  runtime/
    __init__.py
```

Bad import-path patch:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
```

Current import-linter contracts include:

- `config` must not import `state`.
- `config` must not import runtime orchestration packages.
- `state` must not import Hugging Face push modules.
- session handlers must not import websocket or runtime orchestration.
- runtime bootstrap code must not import the websocket stack.
- engines must not import handlers.
- scripts must not import engines directly.

Good package shape:

```text
src/
  config/
    __init__.py
    runtime/
      __init__.py
      engine.py
  runtime/
    __init__.py
    settings.py
    server_start.py
```

Bad single-file package:

```text
src/
  metrics/
    __init__.py
    accuracy.py
```

Use a module instead:

```text
src/
  metrics.py
```

## FastAPI

These rules apply when a Python project uses FastAPI for an HTTP API, web
service, internal service, webhook receiver, streaming endpoint, or API gateway.
They do not apply to non-FastAPI Python modules except where the general Python
rules already say the same thing.

### FastAPI Source Decisions

Rules:

- Keep FastAPI framework code organized by application boundaries: app creation,
  routers, dependencies, schemas, security, middleware, and infrastructure.
- Prefer `Annotated[..., Query(...)]`, `Annotated[..., Path(...)]`,
  `Annotated[..., Body(...)]`, `Annotated[..., Depends(...)]`,
  `Annotated[..., Header()]`, `Annotated[..., Cookie()]`, and similar metadata
  annotations for FastAPI parameters.
- Use Pydantic models for request bodies, response bodies, and documented
  structured data.
- Return concrete Pydantic models, dataclasses, dictionaries, lists, or
  iterables that match the declared return type.
- Use FastAPI and Starlette primitives directly when they own the HTTP behavior.
- Keep business logic outside path operation functions. Path operations adapt
  HTTP input to application calls and adapt application results to HTTP output.
- Keep database, SDK, and service clients out of module-level import-time work.
- Keep security-specific rules stricter than general examples. Documentation
  examples with fake secrets, fake hashes, fake users, or fake tokens are not
  acceptable production patterns.
- Do not add a FastAPI dependency, middleware, background task, or router when a
  plain Python function is enough.

### FastAPI Application Structure

Rules:

- Split nontrivial FastAPI apps across multiple modules.
- Use one main application module to create the `FastAPI` object and include
  routers.
- Put related path operations in router modules.
- Put shared dependencies in a dependencies module or a domain-owned dependency
  module.
- Put internal-only routers or admin routers in clearly named internal packages.
- Every package and subpackage that should be importable has an `__init__.py`.
- Keep the main app module small. It wires routers, global dependencies,
  middleware, exception handlers, metadata, and startup configuration.
- Configure the FastAPI entrypoint in project configuration when the deployment
  tool supports it.
- Do not depend on running the app from the repository root.
- Do not patch `sys.path` to make a FastAPI app importable from source.

Good shape:

```text
src/
  app/
    __init__.py
    main.py
    dependencies.py
    routers/
      __init__.py
      items.py
      users.py
    internal/
      __init__.py
      admin.py
```

Good main module:

```python
from fastapi import Depends, FastAPI

from .dependencies import get_query_token, get_token_header
from .internal import admin
from .routers import items, users

app = FastAPI(dependencies=[Depends(get_query_token)])

app.include_router(users.router)
app.include_router(items.router)
app.include_router(
    admin.router,
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_token_header)],
)
```

Bad main module:

```python
app = FastAPI()


@app.get("/users/")
async def read_users():
    ...


@app.get("/items/")
async def read_items():
    ...


@app.get("/admin/")
async def read_admin():
    ...
```

### FastAPI Routers

Rules:

- Use `APIRouter` to group related path operations.
- Name the router object `router` unless a local framework convention requires
  a more specific name.
- Import router modules when multiple modules expose a `router` object, so names
  do not collide.
- Put shared router prefix, tags, dependencies, and default responses on the
  `APIRouter`.
- Router prefixes do not end with `/`.
- Path operation paths start with `/`.
- Add path-operation-specific tags, dependencies, status codes, and responses
  only when they differ from the router default.
- Include routers in the main app module or a higher-level router module.
- Include a router in another router before including the parent router in the
  app.
- Reusing the same router under multiple prefixes is an advanced pattern. Use it
  only when the same API must intentionally be exposed under multiple route
  groups.

Good router module:

```python
from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_token_header

router = APIRouter(
    prefix="/items",
    tags=["items"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
async def read_items() -> list[Item]:
    return list_items()
```

Bad router prefix:

```python
router = APIRouter(prefix="/items/")


@router.get("latest")
async def read_latest():
    ...
```

Good router imports:

```python
from .routers import items, users

app.include_router(items.router)
app.include_router(users.router)
```

Bad router imports:

```python
from .routers.items import router
from .routers.users import router
```

### FastAPI Path Operations

Rules:

- Keep path operation functions thin.
- Annotate path operation parameters and return values.
- Use response models or return type annotations so FastAPI can validate,
  filter, document, and serialize responses.
- Use `HTTPException` for HTTP errors that are part of the API contract.
- Use precise status codes.
- Do not leak internal error details in `HTTPException.detail`.
- Use `status` constants when they make intent clearer.
- Use `Annotated` for headers, cookies, dependencies, form fields, and other
  parameter metadata.
- Do not use path operation functions as dumping grounds for database access,
  authorization logic, external API calls, and response formatting.
- Put repeated path operation policy at the router or app level.
- Use relative OpenAPI security URLs such as `tokenUrl="token"` so deployments
  behind a proxy can keep working.

Good:

```python
@router.get("/{item_id}")
async def read_item(item_id: str) -> Item:
    item = get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
```

Bad:

```python
@router.get("/{item_id}")
async def read_item(item_id):
    row = db.execute(f"select * from items where id = {item_id}")
    if not row:
        raise Exception("missing item in item table")
    return row
```

### FastAPI Parameters and Validation

Rules:

- Use standard Python type annotations on path operation parameters so FastAPI
  can parse, validate, document, and serialize consistently.
- Treat a missing default value as required.
- Treat a default value, including `None`, as optional.
- When a parameter can be `None`, include `None` in the type annotation.
- Use `Query`, `Path`, `Body`, `Header`, `Cookie`, and `Form` inside
  `Annotated` for framework metadata and validation.
- Keep `Annotated` defaults in the function signature, not inside `Query`,
  `Path`, `Body`, or other metadata objects.
- Use `min_length`, `max_length`, and `pattern` for string constraints at the
  HTTP boundary when those constraints are part of the API contract.
- Use `gt`, `ge`, `lt`, and `le` for numeric constraints at the HTTP boundary.
- Use Pydantic validators for pure request-value validation that only depends
  on the request data.
- Use dependencies, not validators, for validation that needs a database,
  service call, filesystem access, authorization state, or other external I/O.
- Declare fixed routes before parameterized routes that could otherwise match
  the same path.
- Do not define two path operations for the same method and path.
- Use `str, Enum` path parameter types for documented string choices.
- Use the `{name:path}` path convertor only when a path parameter is genuinely
  allowed to contain slashes.
- Use aliases only to preserve external API names that are not valid or desired
  Python identifiers. Translate to domain names before moving inward.
- For query parameters that can appear multiple times, use an explicit
  `Query()` annotation with a collection type such as `list[str]`.
- Use Pydantic query parameter models for cohesive groups such as pagination,
  filtering, sorting, or search options.
- Set `model_config = {"extra": "forbid"}` on a query parameter model when
  unknown query parameters are invalid for that endpoint.

Good validated parameters:

```python
@router.get("/items/{item_id}")
async def read_item(
    item_id: Annotated[int, Path(ge=1)],
    q: Annotated[str | None, Query(max_length=50)] = None,
) -> Item:
    return get_item(item_id=item_id, query=q)
```

Good query parameter model:

```python
class FilterParams(BaseModel):
    """Query parameters for item filtering."""

    model_config = {"extra": "forbid"}

    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = Field(default_factory=list)


@router.get("/items/")
async def read_items(filters: Annotated[FilterParams, Query()]) -> list[Item]:
    return list_items(filters=filters)
```

Good route order:

```python
@router.get("/users/me")
async def read_current_user() -> User:
    return get_current_user()


@router.get("/users/{user_id}")
async def read_user(user_id: str) -> User:
    return get_user(user_id)
```

Bad route order:

```python
@router.get("/users/{user_id}")
async def read_user(user_id: str) -> User:
    return get_user(user_id)


@router.get("/users/me")
async def read_current_user() -> User:
    return get_current_user()
```

Bad old-style metadata default:

```python
@router.get("/items/")
async def read_items(q: str | None = Query(default=None, max_length=50)) -> list[Item]:
    return list_items(query=q)
```

### FastAPI Request and Response Schemas

Rules:

- Use Pydantic `BaseModel` classes for JSON request bodies and response bodies.
- Use Pydantic models as boundary schemas. Keep business workflows and
  persistence behavior outside schema classes.
- Declare required body fields without defaults.
- Declare optional or nullable body fields with explicit defaults and `None`
  annotations where applicable.
- Prefer `Field(default_factory=...)` for mutable defaults, even when Pydantic
  would copy mutable defaults.
- Use `Field` constraints on model attributes when the constraint belongs to the
  schema contract.
- Use separate schema classes for create, read, and update shapes when their
  required fields, nullable fields, or public fields differ.
- Do not send request bodies with `GET` endpoints.
- Use `Body()` for singular values that must come from the request body instead
  of the query string.
- Use `Body(embed=True)` only when the wire contract intentionally wraps a
  single body model under its parameter name.
- When multiple body parameters are declared, document and preserve the keyed
  body shape clients must send.
- Use `.model_dump()` for Pydantic v2 model-to-dict conversion.
- Use `.model_dump(exclude_unset=True)` for partial-update input where omitted
  values must not overwrite stored values.
- Use `.model_copy(update=...)` to create updated model values without mutating
  the original model.
- Use `jsonable_encoder()` when converting Pydantic models or datetimes to
  values that must be JSON-compatible for storage or transport.
- Use `response_model` or a return type annotation when response filtering,
  validation, serialization, or documentation matters.

Good schema defaults:

```python
class ItemCreate(BaseModel):
    """Request body for creating an item."""

    name: str
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
```

Good body embedding when the API contract requires an envelope:

```python
@router.put("/items/{item_id}")
async def update_item(
    item_id: int,
    item: Annotated[ItemCreate, Body(embed=True)],
) -> Item:
    return save_item(item_id=item_id, item=item)
```

Good partial update:

```python
@router.patch("/items/{item_id}")
async def patch_item(item_id: str, item: ItemUpdate) -> Item:
    stored_item = get_item(item_id)
    update_data = item.model_dump(exclude_unset=True)
    return stored_item.model_copy(update=update_data)
```

Bad mutable schema default:

```python
class ItemCreate(BaseModel):
    tags: list[str] = []
```

Bad GET body:

```python
@router.get("/items/search")
async def search_items(filters: FilterParams) -> list[Item]:
    return list_items(filters=filters)
```

### FastAPI Schema Fields and Examples

Rules:

- Import `Field` from `pydantic`, not from `fastapi`.
- Use `Field` for Pydantic model attribute validation, defaults, and schema
  metadata.
- Use `Query`, `Path`, `Body`, `Header`, `Cookie`, `Form`, and `File` for
  FastAPI parameter metadata.
- Keep model field defaults in `Field(default=...)` or ordinary assignment
  syntax, consistently with surrounding schema code.
- Use `Field(default_factory=...)` for mutable field defaults.
- Use `Field` constraints when the constraint belongs to the JSON schema, not
  only to one handler implementation.
- Use `title`, `description`, `deprecated`, `examples`, and validation
  arguments deliberately. They become part of generated JSON Schema and
  OpenAPI.
- Do not add arbitrary extra keyword arguments to `Field`, `Query`, `Body`, or
  similar helpers unless the generated schema extension is intentional and
  compatible with the OpenAPI tools that consume it.
- Put whole-model request examples in `model_config["json_schema_extra"]`.
- Put field-level examples in `Field(examples=[...])`.
- Put body or parameter examples in the relevant FastAPI helper, such as
  `Body(examples=[...])`.
- Prefer the JSON Schema `examples` field over older singular `example`
  metadata.
- Use `openapi_examples` only when the API docs need named examples with
  summaries, descriptions, values, or external example URLs.
- Keep examples sanitized. Do not include real secrets, tokens, credentials,
  internal IDs, production hostnames, personal data, or customer data.
- Make examples valid by default. Include invalid examples only when the docs
  intentionally demonstrate validation failure.
- Keep examples aligned with current schema fields. Remove examples when they
  become stale.

Good model field metadata:

```python
class PromptRequest(BaseModel):
    """Request body for a prompt."""

    prompt: str = Field(examples=["Warm up the selected model."])
    session_id: str | None = Field(default=None, max_length=128)
    max_tokens: int = Field(gt=0, le=4096)
    stop: list[str] = Field(default_factory=list)
```

Good model example:

```python
class PromptRequest(BaseModel):
    """Request body for a prompt."""

    prompt: str
    max_tokens: int

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "prompt": "Warm up the selected model.",
                    "max_tokens": 128,
                }
            ],
        },
    }
```

Good OpenAPI examples:

```python
@router.put("/prompts/{session_id}")
async def update_prompt(
    session_id: str,
    prompt: Annotated[
        PromptRequest,
        Body(
            openapi_examples={
                "normal": {
                    "summary": "Valid prompt",
                    "value": {"prompt": "Warm up the selected model.", "max_tokens": 128},
                },
            },
        ),
    ],
) -> PromptRequest:
    return save_prompt(session_id=session_id, prompt=prompt)
```

Bad `Field` import:

```python
from fastapi import Field
```

Bad schema metadata:

```python
class ItemCreate(BaseModel):
    name: str = Field(ui_widget="secret-internal-control")
    api_key: str = Field(examples=["sk-live-real-token"])
    tags: list[str] = []
```

### FastAPI Nested and Special Types

Rules:

- Use nested Pydantic models for structured JSON objects with known fields.
- Do not model known JSON object shapes as `dict[str, object]`.
- Specify type parameters for `list`, `set`, `frozenset`, `tuple`, and `dict`
  fields.
- Use `list[Model]` for arrays of structured objects.
- Use top-level `list[Model]` body parameters only when the external API
  contract is a JSON array.
- Use `set[T]` or `frozenset[T]` when uniqueness is part of the domain
  contract. Remember that JSON responses still serialize these values as
  arrays.
- Use `dict[KeyType, ValueType]` bodies only when valid field names are not
  known ahead of time.
- Remember that JSON object keys are strings. If a body is typed as
  `dict[int, float]`, clients still send string keys and Pydantic validates and
  converts them.
- Use precise Pydantic and standard-library types at API boundaries when they
  express the domain better than plain strings.
- Use `UUID` for UUID identifiers.
- Use timezone-aware `datetime` values for instants that cross process or
  service boundaries.
- Use `date`, `time`, and `timedelta` when those are the actual domain values.
- Use `Decimal` for exact decimal quantities such as money or prices when
  binary floating-point behavior is not acceptable.
- Use Pydantic string-like types such as `HttpUrl` and `EmailStr` when URL or
  email validation is part of the schema contract.
- Use `bytes` only for small binary values represented in JSON. Use FastAPI
  file handling for uploaded files.
- Avoid deeply nested request bodies when the domain can be expressed as
  smaller endpoints or named resources.

Good nested schema:

```python
class Image(BaseModel):
    """Image metadata."""

    url: HttpUrl
    name: str


class ItemCreate(BaseModel):
    """Request body for creating an item."""

    name: str
    tags: set[str] = Field(default_factory=set)
    images: list[Image] = Field(default_factory=list)
```

Good arbitrary-key body:

```python
@router.post("/index-weights/")
async def create_index_weights(weights: dict[int, float]) -> dict[int, float]:
    return weights
```

Bad untyped collection fields:

```python
class ItemCreate(BaseModel):
    tags: list = []
    image: dict[str, object]
```

### FastAPI Headers and Cookies

Rules:

- Use `Header()` for values that must come from HTTP headers.
- Use `Cookie()` for values that must come from cookies.
- Do not rely on plain scalar parameters for headers or cookies. FastAPI treats
  plain non-path scalar parameters as query parameters.
- Use `Annotated[..., Header()]` and `Annotated[..., Cookie()]` for new code.
- Keep Python parameter and field names in snake_case.
- Let `Header()` convert underscores to hyphens by default.
- Set `Header(convert_underscores=False)` only when an external protocol
  requires underscores in header names and the deployment path supports them.
- Remember that HTTP header names are case-insensitive.
- Use `list[str] | None` with `Header()` for duplicate headers that can appear
  more than once.
- Use Pydantic header parameter models for cohesive groups of related headers.
- Use Pydantic cookie parameter models for cohesive groups of related cookies.
- Use `model_config = {"extra": "forbid"}` on header or cookie models when
  unknown headers or cookies are invalid for that endpoint.
- Prefer `Field(default_factory=list)` for repeated header fields in models.
- Do not log cookies, authorization headers, session IDs, CSRF tokens, or other
  sensitive header values.
- Do not use ad hoc header parameters for authentication when FastAPI security
  utilities can express the authentication scheme.
- Do not rely on Swagger UI execution to prove cookie behavior. Browser cookie
  handling can prevent JavaScript-driven docs requests from sending the cookie
  value entered in the UI.

Good header parameter:

```python
@router.get("/items/")
async def read_items(user_agent: Annotated[str | None, Header()] = None) -> list[Item]:
    return list_items(user_agent=user_agent)
```

Good duplicate header:

```python
@router.get("/items/")
async def read_items(x_token: Annotated[list[str] | None, Header()] = None) -> list[Item]:
    return list_items(tokens=x_token or [])
```

Good header model:

```python
class CommonHeaders(BaseModel):
    """Headers shared by item endpoints."""

    model_config = {"extra": "forbid"}

    host: str
    save_data: bool
    if_modified_since: str | None = None
    x_tag: list[str] = Field(default_factory=list)


@router.get("/items/")
async def read_items(headers: Annotated[CommonHeaders, Header()]) -> list[Item]:
    return list_items(headers=headers)
```

Good cookie model:

```python
class SessionCookies(BaseModel):
    """Cookies required for session-aware endpoints."""

    model_config = {"extra": "forbid"}

    session_id: str


@router.get("/items/")
async def read_items(cookies: Annotated[SessionCookies, Cookie()]) -> list[Item]:
    return list_items(session_id=cookies.session_id)
```

Bad header or cookie source:

```python
@router.get("/items/")
async def read_items(user_agent: str | None = None, session_id: str | None = None):
    return list_items(user_agent=user_agent, session_id=session_id)
```

Bad underscore header override:

```python
@router.get("/items/")
async def read_items(x_custom_header: Annotated[str, Header(convert_underscores=False)]):
    return list_items(header=x_custom_header)
```

### FastAPI Response Models

Rules:

- Prefer return type annotations when the function returns the same public
  schema shape it declares.
- Use the path operation decorator's `response_model` when the returned Python
  object differs from the public response schema.
- Remember that `response_model` takes priority over the return type annotation
  for FastAPI validation, serialization, documentation, and filtering.
- Prefer returning an instance of the public response model when that is simple
  and keeps type checking precise.
- Use `-> Any` with `response_model=...` only at a FastAPI boundary where the
  returned object intentionally differs from the response schema and adapting it
  first would add noise without improving safety.
- Never reuse an input schema containing passwords, tokens, secrets, or private
  fields as the response schema.
- Use separate input and output models when request and response fields differ.
- Schema inheritance is acceptable for response filtering only when the subclass
  is a true specialization of the public base schema.
- Use direct `Response` or `Response` subclass return annotations when returning
  a Starlette/FastAPI response object directly.
- Do not annotate a path operation with a return type that FastAPI cannot turn
  into a Pydantic response model unless the path operation sets
  `response_model=None`.
- Use `response_model=None` only when response model generation is deliberately
  disabled and the route's response contract is documented another way.
- Use `response_model_exclude_unset=True` when omitted default-valued fields
  should be omitted from responses.
- Use `response_model_exclude_defaults=True` or
  `response_model_exclude_none=True` only when that omission is part of the
  public response contract.
- Prefer dedicated output models over `response_model_include` and
  `response_model_exclude`.
- Do not rely on `response_model_include` or `response_model_exclude` for
  security filtering. The generated OpenAPI schema still describes the full
  response model.
- Treat response validation failures as server bugs. Fix the returned data or
  response schema rather than weakening validation.

Good return type:

```python
@router.get("/items/{item_id}")
async def read_item(item_id: str) -> ItemOut:
    return get_item_out(item_id)
```

Good response model for a different internal return shape:

```python
@router.post("/users/", response_model=UserOut)
async def create_user(user: UserIn) -> Any:
    return save_user(user)
```

Good direct response:

```python
@router.get("/download")
async def download_report() -> Response:
    return FileResponse(path=REPORT_PATH)
```

Good explicit response-model disable:

```python
@router.get("/portal", response_model=None)
async def get_portal(teleport: bool = False) -> Response | dict[str, str]:
    if teleport:
        return RedirectResponse(url="/elsewhere")
    return {"message": "Portal ready"}
```

Bad secret leakage:

```python
class UserIn(BaseModel):
    username: str
    password: str


@router.post("/users/")
async def create_user(user: UserIn) -> UserIn:
    return user
```

Bad response filtering shortcut:

```python
@router.get("/users/{user_id}", response_model=User, response_model_exclude={"password_hash"})
async def read_user(user_id: str):
    return get_user(user_id)
```

### FastAPI Status Codes and Errors

Rules:

- Declare successful non-default HTTP status codes with the path operation
  decorator's `status_code` parameter.
- Do not model status codes as path operation function parameters.
- Prefer `fastapi.status` constants for readability, such as
  `status.HTTP_201_CREATED`.
- Python's `http.HTTPStatus` is acceptable when surrounding code already uses
  it.
- Use the default 200 only when it is the correct success response.
- Use 201 for successful resource creation.
- Use 202 only when the request was accepted but the work is not complete.
- Use 204 only when the response intentionally has no body.
- Do not return a body with status codes that must not have one, including 204
  and 304.
- Do not manually return 500-range status codes for ordinary application
  failures. Raise or let unexpected exceptions surface at the server boundary.
- Use `HTTPException` for HTTP errors that are part of the API contract.
- Raise `HTTPException`; do not return it.
- Keep `HTTPException.detail` sanitized and user-facing.
- Do not include stack traces, file paths, table names, internal IDs, request
  bodies, secrets, or implementation details in error responses.
- Use custom `HTTPException` headers only for public protocol requirements,
  such as authentication challenges, rate limits, or documented client
  behavior.
- Put global exception handlers in the FastAPI application setup boundary.
- Register HTTP exception handlers for Starlette's `HTTPException` when the
  handler must catch FastAPI, Starlette, and extension-raised HTTP errors.
- Custom exception handlers must return the API's standard error shape and
  status code policy.
- Do not expose `RequestValidationError.body` to clients.
- Do not stringify validation exceptions into client responses. Validation
  errors can include internal context that is safe for logs only after review.
- Reuse FastAPI's default exception handlers when adding logging or metrics
  around the default behavior.
- Log validation and HTTP errors carefully. Do not log full authenticated
  request bodies or sensitive headers.

Good created status:

```python
@router.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate) -> ItemOut:
    return save_item(item)
```

Good no-content status:

```python
@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: str) -> None:
    delete_existing_item(item_id)
```

Good API error:

```python
@router.get("/items/{item_id}")
async def read_item(item_id: str) -> ItemOut:
    item = find_item(item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item
```

Good exception handler boundary:

```python
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": "Request failed"},
    )
```

Bad status code parameter:

```python
@router.post("/items/")
async def create_item(item: ItemCreate, status_code: int = 201) -> ItemOut:
    return save_item(item)
```

Bad no-content body:

```python
@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: str) -> dict[str, str]:
    delete_existing_item(item_id)
    return {"status": "deleted"}
```

Bad leaked validation response:

```python
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )
```

### FastAPI Forms and Files

Rules:

- Use `Form()` for values that must be read from form fields.
- Use `File()` and `UploadFile` for uploaded files.
- Do not rely on plain scalar parameters for form fields. FastAPI treats plain
  non-path scalar parameters as query parameters.
- Use `Annotated[..., Form()]` and `Annotated[..., File()]` for new code.
- Declare `python-multipart` as a project dependency when any endpoint accepts
  form data or file uploads.
- Remember that form bodies use `application/x-www-form-urlencoded` unless they
  include files.
- Remember that file uploads use `multipart/form-data`.
- Do not combine JSON `Body` fields with `Form` or `File` parameters in one path
  operation. A single request body cannot be both JSON and multipart form data.
- Use Pydantic form models for cohesive groups of related form fields.
- Use `model_config = {"extra": "forbid"}` on form models when unknown form
  fields are invalid for that endpoint.
- Use exact form field names required by external protocols. OAuth2 password
  flow login receives `username` and `password` form fields, not JSON.
- Use aliases in `Form()` only when the external form field name cannot be a
  good Python identifier.
- Use `bytes` file parameters only for small uploads that are safe to load
  fully into memory.
- Use `UploadFile` for images, videos, archives, model artifacts, large binary
  files, or any upload whose size is not tightly bounded.
- Use `Annotated[UploadFile, File(...)]` when an uploaded file needs FastAPI
  metadata such as description or validation metadata.
- Use `UploadFile | None = None` or `Annotated[bytes | None, File()] = None`
  for optional uploads.
- Use `list[UploadFile]` or `Annotated[list[UploadFile], File()]` for multiple
  uploads from the same form field.
- Await `UploadFile.read()`, `write()`, `seek()`, and `close()` inside
  `async def`.
- In normal `def` path operations, use `upload.file` directly when a library
  expects a file-like object.
- Close uploaded files when ownership extends beyond FastAPI's request
  lifecycle.
- Do not trust `UploadFile.filename` for filesystem paths. Sanitize or replace
  client-provided filenames before storage.
- Do not trust `UploadFile.content_type` as proof of file safety. Validate file
  content at the application boundary when it matters.
- Do not log uploaded file contents, full filenames containing user data, or
  sensitive form fields.

Good form fields:

```python
@router.post("/login/")
async def login(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
) -> Token:
    return authenticate_form_user(username=username, password=password)
```

Good form model:

```python
class LoginForm(BaseModel):
    """Login form fields."""

    model_config = {"extra": "forbid"}

    username: str
    password: str


@router.post("/login/")
async def login(data: Annotated[LoginForm, Form()]) -> Token:
    return authenticate_form_user(username=data.username, password=data.password)
```

Good upload:

```python
@router.post("/images/")
async def upload_image(
    image: Annotated[UploadFile, File(description="Image file.")],
) -> ImageUploadResult:
    return await store_image(image)
```

Good multiple uploads:

```python
@router.post("/images/batch")
async def upload_images(files: Annotated[list[UploadFile], File()]) -> BatchUploadResult:
    return await store_images(files)
```

Bad form source:

```python
@router.post("/login/")
async def login(username: str, password: str) -> Token:
    return authenticate_form_user(username=username, password=password)
```

Bad upload for unbounded files:

```python
@router.post("/videos/")
async def upload_video(video: Annotated[bytes, File()]) -> VideoUploadResult:
    return store_video(video)
```

Bad mixed body encoding:

```python
@router.post("/items/import")
async def import_items(file: UploadFile, metadata: ItemImportMetadata) -> ImportResult:
    return import_file(file=file, metadata=metadata)
```

### FastAPI JSON Encoding and Updates

Rules:

- Use `jsonable_encoder()` when data must be converted to JSON-compatible
  Python structures before storage or transport outside FastAPI's response
  handling.
- Do not use `jsonable_encoder()` only to return ordinary responses. FastAPI
  already uses it internally for response serialization.
- Remember that `jsonable_encoder()` returns Python data structures such as
  dictionaries, lists, strings, numbers, booleans, and `None`. It does not
  return a JSON string.
- Use `jsonable_encoder()` before writing Pydantic models, `datetime`,
  `date`, `time`, `timedelta`, `UUID`, `Decimal`, sets, or nested models to
  storage layers that only accept JSON-compatible data.
- Use `PUT` for full replacement semantics.
- Be explicit that a `PUT` body can replace omitted stored values with schema
  defaults.
- Use `PATCH` for partial-update semantics when clients may send only fields
  they want to change.
- Partial-update schemas should make every patchable field optional.
- For partial updates, use `.model_dump(exclude_unset=True)` to distinguish
  omitted fields from fields explicitly set to defaults or `None`.
- Use `.model_copy(update=...)` to produce an updated Pydantic model without
  mutating the stored model instance.
- Convert the updated model with `jsonable_encoder()` before saving it to a
  JSON-only store.
- Do not apply `model_dump()` without `exclude_unset=True` for partial updates.
  That can overwrite stored values with model defaults.
- Do not use one schema for create, replace, patch, and read operations when
  those operations have different required fields or visibility rules.

Good JSON-compatible storage:

```python
def save_item(item_id: str, item: ItemOut) -> None:
    item_store[item_id] = jsonable_encoder(item)
```

Good replacement:

```python
@router.put("/items/{item_id}", response_model=ItemOut)
async def replace_item(item_id: str, item: ItemReplace) -> ItemOut:
    encoded_item = jsonable_encoder(item)
    item_store[item_id] = encoded_item
    return ItemOut.model_validate(encoded_item)
```

Good partial update:

```python
@router.patch("/items/{item_id}", response_model=ItemOut)
async def patch_item(item_id: str, item: ItemPatch) -> ItemOut:
    stored_item = ItemOut.model_validate(item_store[item_id])
    update_data = item.model_dump(exclude_unset=True)
    updated_item = stored_item.model_copy(update=update_data)
    item_store[item_id] = jsonable_encoder(updated_item)
    return updated_item
```

Bad partial update:

```python
@router.patch("/items/{item_id}")
async def patch_item(item_id: str, item: ItemPatch) -> ItemOut:
    stored_item = ItemOut.model_validate(item_store[item_id])
    updated_item = stored_item.model_copy(update=item.model_dump())
    item_store[item_id] = jsonable_encoder(updated_item)
    return updated_item
```

### FastAPI Async and Blocking Work

Rules:

- Use `async def` for path operations and dependencies that await async
  libraries.
- Use normal `def` for path operations and dependencies that call blocking
  synchronous libraries for database, API, filesystem, or SDK work.
- Do not call blocking I/O directly inside an `async def` path operation.
- If the blocking call must stay in async code, isolate it behind an explicit
  thread offload or move it to a normal `def` dependency or path operation.
- Lightweight compute-only path operations may use `async def`.
- When unsure whether a third-party call blocks, treat it as blocking until the
  library documents an awaitable API.
- Mix `def` and `async def` path operations and dependencies as needed.
- Remember that ordinary utility functions are called exactly as written.
  FastAPI only manages `def` versus `async def` behavior for callables it
  invokes as path operations or dependencies.
- Do not make CPU-bound model loading, quantization, image processing, or batch inference
  asynchronous by only adding `async def`. Use a worker, process pool, task
  queue, or other explicit execution boundary.

Good async path operation:

```python
@router.get("/items/{item_id}")
async def read_item(item_id: str) -> Item:
    return await item_client.fetch_item(item_id)
```

Good blocking path operation:

```python
@router.get("/items/{item_id}")
def read_item(item_id: str) -> Item:
    return item_repository.fetch_item(item_id)
```

Bad blocking call inside async path operation:

```python
@router.get("/items/{item_id}")
async def read_item(item_id: str) -> Item:
    return item_repository.fetch_item(item_id)
```

### FastAPI Dependencies

Rules:

- Use dependencies for request-scoped concerns such as authentication,
  authorization, pagination parameters, database sessions, current user lookup,
  request metadata, and reusable request validation.
- A dependency is any callable FastAPI can call and inspect.
- Prefer function dependencies for simple reusable values or validation.
- Use class dependencies when the dependency returns a structured object that
  improves type checking and editor support.
- When using a class dependency, prefer
  `Annotated[CommonQueryParams, Depends()]` when the shortcut is clear.
- Use a dependency parameter when the path operation needs the returned value.
- Use `dependencies=[Depends(...)]` on a path operation, router, or app when the
  dependency must run but its value is not used.
- Put dependencies shared by a router on the `APIRouter`.
- Put dependencies that apply to every path operation on the `FastAPI` app.
- Keep dependency graphs understandable. Deep sub-dependency trees need a clear
  ownership reason.
- FastAPI caches dependency results per request by default. Use
  `use_cache=False` only when the same dependency must intentionally run more
  than once in one request.
- Dependencies may raise `HTTPException`.
- Do not add unused dependency parameters to path operation functions just to
  force execution. Use decorator, router, or app dependencies instead.
- Do not hide business workflows in dependencies.

Good value dependency:

```python
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    return decode_user_token(token)


@router.get("/users/me")
async def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user
```

Good execution-only dependency:

```python
async def verify_token(x_token: Annotated[str, Header()]) -> None:
    if x_token != EXPECTED_TOKEN:
        raise HTTPException(status_code=400, detail="Invalid token header")


@router.get("/items/", dependencies=[Depends(verify_token)])
async def read_items() -> list[Item]:
    return list_items()
```

Good class dependency:

```python
class CommonQueryParams:
    """Common pagination and search parameters."""

    def __init__(self, q: str | None = None, skip: int = 0, limit: int = 100):
        self.q = q
        self.skip = skip
        self.limit = limit


@router.get("/items/")
async def read_items(
    params: Annotated[CommonQueryParams, Depends()],
) -> list[Item]:
    return list_items(q=params.q, skip=params.skip, limit=params.limit)
```

Bad unused dependency parameter:

```python
@router.get("/items/")
async def read_items(_: Annotated[None, Depends(verify_token)]) -> list[Item]:
    return list_items()
```

### FastAPI Dependencies with Yield

Rules:

- Use `yield` dependencies for request-scoped resource lifetime, such as
  database sessions, transactions, temporary files, and client sessions.
- A dependency with `yield` uses exactly one `yield`.
- Put setup before `yield`.
- Put cleanup in `finally`.
- The yielded value is injected into path operations and dependent dependencies.
- A dependency with `yield` may be `def` or `async def`.
- If a `yield` dependency catches an exception, it must re-raise the same
  exception or raise a deliberate replacement such as `HTTPException`.
- Do not swallow exceptions in `yield` dependencies.
- Prefer ordinary `with` or `async with` inside a `yield` dependency when a
  resource is already a context manager.
- Do not decorate FastAPI dependencies with `@contextlib.contextmanager` or
  `@contextlib.asynccontextmanager`; FastAPI handles that internally.
- Use `Depends(scope="function")` only when cleanup must happen after the path
  operation returns but before the response is sent.
- A request-scoped dependency cannot depend on a function-scoped dependency if
  it needs that dependency during cleanup.

Good:

```python
async def get_db() -> AsyncIterable[DBSession]:
    db = DBSession()
    try:
        yield db
    finally:
        db.close()
```

Good exception handling:

```python
def get_username() -> Iterable[str]:
    try:
        yield "Rick"
    except OwnerError as error:
        raise HTTPException(status_code=400, detail="Owner error") from error
```

Bad swallowed exception:

```python
def get_username() -> Iterable[str]:
    try:
        yield "Rick"
    except OwnerError:
        logger.error("Owner error")
```

Good context manager usage:

```python
async def get_db() -> AsyncIterable[DBSession]:
    with create_db_session() as db:
        yield db
```

### FastAPI Security

Rules:

- Use FastAPI security utilities for authentication and authorization that
  should appear in OpenAPI.
- Use `OAuth2PasswordBearer` for bearer-token dependencies when that is the
  chosen security scheme.
- Use a relative `tokenUrl`, such as `tokenUrl="token"`.
- Use `OAuth2PasswordRequestForm` for OAuth2 password-flow login forms.
- Use `OAuth2PasswordRequestFormStrict` when `grant_type=password` must be
  enforced.
- Login endpoints for OAuth2 password flow receive username and password as form
  data, not JSON.
- Token endpoints return JSON with `access_token` and `token_type`.
- Bearer token responses use `token_type="bearer"`.
- Unauthorized bearer-token responses use HTTP 401 and include
  `WWW-Authenticate: Bearer`.
- Never store plaintext passwords.
- Hash passwords with a current password-hashing library and a recommended
  algorithm.
- Verify passwords through the password-hashing library.
- When authentication fails, use the same public error message for unknown user
  and wrong password.
- Reduce username enumeration risk by keeping failure timing consistent where
  practical, such as verifying against a dummy hash for unknown users.
- JWT tokens are signed, not encrypted. Do not put secrets or sensitive data in
  JWT payloads.
- JWT access tokens include an expiration.
- Use timezone-aware UTC datetimes when creating expirations.
- Use the JWT `sub` claim for a unique application-wide subject string when JWTs
  identify users or entities.
- Store signing secrets outside source code.
- Do not use documentation example secret keys, fake hashes, fake users, or fake
  token logic in real code.
- Catch token verification errors from the JWT library and convert them to a
  generic credentials error.
- Use scopes for fine-grained permissions when the API needs them.
- Prefer integrated security dependencies over custom header checks for real
  authentication.

Good security dependency:

```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except InvalidTokenError as error:
        raise credentials_error from error

    subject = payload.get("sub")
    if subject is None:
        raise credentials_error
    user = get_user_by_subject(subject)
    if user is None:
        raise credentials_error
    return user
```

Good token response:

```python
class Token(BaseModel):
    """OAuth2 bearer token response."""

    access_token: str
    token_type: str


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(subject=user.username)
    return Token(access_token=access_token, token_type="bearer")
```

Bad security:

```python
SECRET_KEY = "example-secret"


def fake_decode_token(token: str) -> User:
    return get_user(token)
```

### FastAPI Streaming

Rules:

- Use streaming when the client should receive items before the whole sequence
  is available.
- Use JSON Lines for streams of JSON objects.
- Annotate async streaming path operations as `AsyncIterable[T]`.
- Annotate sync streaming path operations as `Iterable[T]`.
- Use Pydantic models for streamed JSON items when possible.
- Prefer a declared return type so FastAPI can validate, filter, serialize, and
  document streamed items.
- Use Server-Sent Events when clients need event names, event IDs, retry values,
  comments, or browser EventSource semantics.
- Use `EventSourceResponse` for SSE endpoints.
- Yield `ServerSentEvent(data=...)` for JSON-encoded SSE data.
- Yield `ServerSentEvent(raw_data=...)` for preformatted text, log lines, or
  sentinel values.
- Do not set both `data` and `raw_data` on the same SSE event.
- Include event IDs when clients need to resume after reconnecting.
- Read `Last-Event-ID` when resumable streams are required.
- SSE can use methods other than GET when the protocol requires it.
- Keep streamed item generation cancellable and resource-safe.

Good JSON Lines stream:

```python
@router.get("/items/stream")
async def stream_items() -> AsyncIterable[Item]:
    for item in iter_items():
        yield item
```

Good sync stream:

```python
@router.get("/items/stream-sync")
def stream_items_sync() -> Iterable[Item]:
    yield from iter_items()
```

Good SSE stream:

```python
@router.get("/items/events", response_class=EventSourceResponse)
async def stream_item_events() -> AsyncIterable[ServerSentEvent]:
    yield ServerSentEvent(comment="item updates")
    for index, item in enumerate(iter_items()):
        yield ServerSentEvent(data=item, event="item_update", id=str(index))
```

Good raw SSE data:

```python
@router.get("/logs/stream", response_class=EventSourceResponse)
async def stream_logs() -> AsyncIterable[ServerSentEvent]:
    for line in iter_log_lines():
        yield ServerSentEvent(raw_data=line)
```

Bad SSE event:

```python
yield ServerSentEvent(data=item, raw_data="[DONE]")
```

### FastAPI Background Tasks

Rules:

- Use `BackgroundTasks` for small follow-up work that can run after the response
  is sent and should stay in the same process.
- Typical uses include recording a warmup marker, writing a small audit event,
  or doing short local cleanup.
- Do not use `BackgroundTasks` for heavy computation, durable jobs, distributed
  work, long-running tasks, or work that must survive process restarts.
- Use a real job queue or worker system for heavy or durable background work.
- Import `BackgroundTasks` from `fastapi`.
- Use `BackgroundTasks`, not Starlette's singular `BackgroundTask`, for
  dependency-injected path operation parameters.
- Do not put required user-visible work in a background task if the response
  should depend on its success.
- Background task failures happen after the response. Log and monitor them at
  the worker boundary.

Good:

```python
@router.post("/warmup-events/{session_id}")
async def record_warmup(
    session_id: str,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    background_tasks.add_task(record_warmup_event, session_id)
    return {"message": "Warmup event queued"}
```

Bad:

```python
@router.post("/warmup")
async def warmup_model(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_full_warmup)
    return {"message": "Warmup started"}
```

### FastAPI Middleware

Rules:

- Use middleware for cross-cutting HTTP request and response behavior.
- Middleware receives the request and a `call_next` function.
- Code before `await call_next(request)` runs before the path operation.
- Code after `await call_next(request)` runs after the path operation and before
  returning the response.
- Use `time.perf_counter()` for elapsed-time measurements.
- Add custom response headers deliberately.
- If browser clients must read a custom header, expose it in CORS settings.
- Middleware order matters. The last middleware added is the outermost.
- On the request path, the outermost middleware runs first.
- On the response path, the outermost middleware runs last.
- Dependencies with `yield` run their exit code after middleware.
- Background tasks run after middleware.
- Keep middleware small. Do not put business logic in middleware.
- Do not use middleware when a router dependency or path operation dependency is
  the narrower correct boundary.

Good:

```python
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

Bad:

```python
@app.middleware("http")
async def authorize_and_run_business_logic(request: Request, call_next):
    update_user_records(request)
    return await call_next(request)
```

### FastAPI Metadata and Docs

Rules:

- Disable OpenAPI schema output and interactive documentation by default.
- Expose OpenAPI, Swagger UI, or ReDoc only when the product or deployment
  explicitly requires it.
- Gate schema and docs exposure behind a typed configuration value loaded at
  the application boundary, such as an environment-derived `enable_api_docs`
  flag.
- Default that flag to `False`.
- Do not expose docs or schema only because FastAPI enables them by default.
- When docs are disabled, set `openapi_url=None`, `docs_url=None`, and
  `redoc_url=None`.
- When docs are enabled, enable all schema and docs URLs deliberately and keep
  the exposed paths stable.
- Do not expose internal-only endpoints, hidden admin routes, security schemes,
  example payloads, or environment-specific metadata in a public OpenAPI schema.
- Do not rely on obscurity of docs URLs as the control. The schema endpoint is
  the contract exposure that must be explicitly enabled or disabled.
- Configure API metadata on the `FastAPI` object when the API is user-facing or
  published.
- Metadata may include title, summary, description, version, terms of service,
  contact, and license information.
- Keep the metadata accurate. Do not describe endpoints or features that do not
  exist.
- Use tag metadata to group path operations in generated docs.
- The order of tag metadata controls docs display order.
- Use `openapi_url`, `docs_url`, and `redoc_url` deliberately when versioning,
  relocating, exposing, or disabling documentation surfaces.
- Prefer configuring the FastAPI entrypoint in project configuration when the
  tool supports it.

Good:

```python
tags_metadata = [
    {
        "name": "sessions",
        "description": "Operations with inference sessions.",
    },
    {
        "name": "warmup",
        "description": "Operations with model warmup.",
    },
]

app = FastAPI(
    title="Text Inference API",
    summary="Text inference service API.",
    version="1.0.0",
    openapi_tags=tags_metadata,
    openapi_url="/openapi.json" if config.enable_api_docs else None,
    docs_url="/docs" if config.enable_api_docs else None,
    redoc_url="/redoc" if config.enable_api_docs else None,
)
```

Bad default exposure:

```python
app = FastAPI(title="Text Inference API")
```

Good project configuration:

```toml
[tool.fastapi]
entrypoint = "app.main:app"
```

### FastAPI Testing

Follow the repository testing rules. Do not add or run tests unless requested.

Rules when FastAPI tests are requested:

- Test the HTTP contract, not FastAPI internals.
- Use the framework test client or async HTTP client appropriate for the app.
- Assert status codes, response bodies, headers, and auth behavior.
- Override dependencies at the app boundary for external systems.
- Test router-level, decorator-level, and app-level dependencies where they
  control security or request validation.
- Test streaming endpoints by consuming enough items to prove the stream
  contract.
- Test background tasks only when their observable side effect matters.
- Do not test that FastAPI itself routes requests correctly.

### FastAPI Anti-Patterns

Do not write:

```python
app = FastAPI()


@app.get("/users/")
async def read_users():
    ...


@app.get("/items/")
async def read_items():
    ...
```

```python
router = APIRouter(prefix="/items/")
```

```python
@router.get("latest")
async def read_latest():
    ...
```

```python
@router.get("/items/")
async def read_items(unused: Annotated[None, Depends(verify_token)]):
    ...
```

```python
@router.get("/items/")
async def read_items(q: str | None = Query(default=None, max_length=50)):
    ...
```

```python
@router.get("/users/{user_id}")
async def read_user(user_id: str):
    ...


@router.get("/users/me")
async def read_current_user():
    ...
```

```python
@router.get("/items/search")
async def search_items(filters: FilterParams):
    ...
```

```python
@router.get("/items/{item_id}")
async def read_item(item_id: str):
    return blocking_repository.fetch_item(item_id)
```

```python
from fastapi import Field
```

```python
class ItemCreate(BaseModel):
    name: str = Field(ui_widget="private-admin-control")
    tags: list[str] = []
```

```python
class ItemCreate(BaseModel):
    image: dict[str, object]
    tags: list = []
```

```python
@router.get("/items/")
async def read_items(user_agent: str | None = None, session_id: str | None = None):
    ...
```

```python
@router.get("/items/")
async def read_items(x_custom_header: Annotated[str, Header(convert_underscores=False)]):
    ...
```

```python
class UserIn(BaseModel):
    username: str
    password: str


@router.post("/users/")
async def create_user(user: UserIn) -> UserIn:
    return user
```

```python
@router.get("/users/{user_id}", response_model=User, response_model_exclude={"password_hash"})
async def read_user(user_id: str):
    return get_user(user_id)
```

```python
@router.post("/items/")
async def create_item(item: ItemCreate, status_code: int = 201):
    ...
```

```python
@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: str):
    return {"status": "deleted"}
```

```python
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(content={"detail": exc.errors(), "body": exc.body})
```

```python
@router.post("/login/")
async def login(username: str, password: str):
    ...
```

```python
@router.post("/videos/")
async def upload_video(video: Annotated[bytes, File()]):
    ...
```

```python
@router.post("/items/import")
async def import_items(file: UploadFile, metadata: ItemImportMetadata):
    ...
```

```python
@router.patch("/items/{item_id}")
async def patch_item(item_id: str, item: ItemPatch):
    update_data = item.model_dump()
    ...
```

```python
async def get_db():
    db = DBSession()
    yield db
    db.close()
```

```python
def get_username():
    try:
        yield "Rick"
    except OwnerError:
        logger.error("Owner error")
```

```python
SECRET_KEY = "example-secret"
```

```python
@router.post("/token")
async def login(credentials: LoginJson):
    ...
```

```python
@router.get("/logs", response_class=EventSourceResponse)
async def stream_logs():
    yield ServerSentEvent(data="line", raw_data="line")
```

```python
@app.middleware("http")
async def run_domain_work(request: Request, call_next):
    sync_customer_records()
    return await call_next(request)
```

## Power Features

Avoid power features unless the project already has a clear local pattern and
the feature is necessary.

Avoid:

- custom metaclasses;
- bytecode manipulation;
- dynamic inheritance;
- object reparenting;
- import hooks and import hacks;
- runtime monkeypatching;
- reflection-heavy designs;
- modifying interpreter internals;
- `__del__` cleanup logic;
- manual descriptor implementations;
- dynamic code generation.

Allowed standard-library uses include `dataclasses`, `enum`, and `abc` when they
fit the problem.

Rules:

- Do not use a power feature to make code shorter.
- Do not use a power feature to hide a dependency cycle or ownership problem.
- Prefer ordinary functions, dataclasses, explicit imports, and explicit data
  structures.

## Threading and Concurrency

Rules:

- Do not rely on atomicity of built-in types.
- Do not rely on atomic variable assignment for synchronization.
- Use `queue.Queue` for thread communication when appropriate.
- Use `threading` locks, conditions, or higher-level primitives for shared
  state.
- Prefer `threading.Condition` over low-level polling loops.
- Keep shared mutable state small and explicit.
- Document concurrency, cancellation, and isolation behavior when present.

## Tests

Follow [`GENERAL.md`](GENERAL.md) for when tests may be added or changed.

Rules when Python tests are requested:

- Test behavior, not implementation details.
- Use pytest-style `assert` in tests.
- Keep tests focused on the behavior under change.
- Do not add module docstrings to test files unless they explain unusual setup,
  environment requirements, or update commands.
- Test names follow [`NAMING.md`](NAMING.md).
- Do not assert hardcoded configuration values that can change freely.
- Use mocks only at external boundaries.
- Do not test that mocks return the values assigned inside the test.
- Cover meaningful edge cases, failure paths, and state transitions.

Good:

```python
def test_parse_prompt_rejects_unexpected_entry() -> None:
    with pytest.raises(TypeError, match="Unexpected prompt entry"):
        parse_prompt(value=object())
```

Bad:

```python
def test_default_temperature() -> None:
    assert CONFIG.temperature == 0.7
```

## Verification Commands

Do not run verification commands unless the user asks.

When verification is requested, the local Python verification stack is:

```bash
mise run lint:python
```

For narrower verification, use the specific requested tool or file scope when
available:

```bash
uv run ruff format --config pyproject.toml --check src
uv run ruff check --config pyproject.toml src
uv run --extra local basedpyright
PYTHONPATH="${PWD}" uv run --extra local lint-imports --cache-dir .artifacts/import-linter
uv run python -m quality.python.runner --root "${PWD}"
```

Rules:

- Do not run Python formatting, linting, type checking, import checks, tests, or
  security scans unless requested.
- If the user asks for linting, prefer the project command unless a narrower
  command is clearly requested.
- If a verification command fails, report the command and the relevant failure.
- Do not broaden verification into unrelated areas.

## Review Checklist

Before finishing Python changes, review the diff for these points:

- Does the code follow local project rules over generic style preferences?
- Are imports top-level, grouped, sorted, and free of cycles?
- Is the module import-stable, with no import-time work?
- Are public APIs typed and documented?
- Do argument types accept the broadest useful protocol or abstract collection?
- Do concrete implementations return concrete types?
- Is `Any` avoided where `object`, a protocol, or a type variable would express
  the contract?
- Are names consistent with [`NAMING.md`](NAMING.md)?
- Are functions small, focused, and under the local length limit?
- Are defaults immutable or initialized inside the function?
- Are None checks explicit?
- Are constructors free of external row, payload, SDK, or CLI object coupling?
- Is subclassing used only for interfaces or true specialization, not code
  sharing?
- Are exceptions specific, with narrow `try` blocks?
- Are resources managed with `with` or documented ownership?
- Are logging calls using literal pattern strings and argument parameters?
- Is logging configured only at the application boundary?
- Are error messages precise, actionable, and free of internal details?
- Are environment variables read, parsed, and validated at a boundary instead
  of inside business logic?
- When changing deployment install commands, are pip requirements pinned,
  locally hashed, binary-only where practical, and free of direct setuptools
  install commands?
- Are comments present where behavior is non-obvious and absent where they only
  narrate code?
- Is `__all__` explicit and at the bottom when public exports exist?
- Are package boundaries and import-linter contracts respected?
- Is importable code under `src/` without `sys.path` mutation?
- For FastAPI code, are path operations thin and grouped behind routers?
- For FastAPI code, are parameter defaults, `Annotated` metadata, and
  validation constraints declared consistently?
- For FastAPI code, are route declarations ordered so fixed paths are not
  shadowed by parameterized paths?
- For FastAPI code, are request and response schemas using Pydantic v2 APIs and
  avoiding mutable defaults?
- For FastAPI code, are `Field` constraints, schema metadata, and examples
  accurate, sanitized, and imported from the right package?
- For FastAPI code, do nested models use precise typed fields instead of
  untyped collections or arbitrary dictionaries?
- For FastAPI code, are special boundary types such as `UUID`, `datetime`,
  `Decimal`, `HttpUrl`, and `EmailStr` used where they express real domain
  constraints?
- For FastAPI code, are headers and cookies declared with `Header()` and
  `Cookie()`, including grouped parameter models where that improves the
  contract?
- For FastAPI code, do response models filter private fields through dedicated
  output schemas rather than include/exclude shortcuts?
- For FastAPI code, are success status codes declared on decorators, error
  status codes raised with sanitized `HTTPException`, and no-body statuses free
  of response bodies?
- For FastAPI code, are custom exception handlers registered at the app boundary
  and free of leaked request bodies, internal paths, and implementation details?
- For FastAPI code, are forms and files declared with `Form()`, `File()`, and
  `UploadFile`, with JSON bodies kept separate from multipart form bodies?
- For FastAPI code, do file uploads use `UploadFile` unless the file is small
  and intentionally read fully into memory?
- For FastAPI code, are replacement and partial-update routes using clear
  `PUT`/`PATCH` semantics, `exclude_unset=True`, `.model_copy()`, and
  `jsonable_encoder()` where storage needs JSON-compatible data?
- For FastAPI code, are OpenAPI, Swagger UI, and ReDoc disabled by default and
  enabled only through explicit boundary configuration?
- For FastAPI code, is blocking I/O kept out of `async def` path operations?
- For FastAPI code, are dependencies placed at the narrowest correct boundary:
  parameter, decorator, router, or app?
- For FastAPI code, are secrets externalized, credentials errors generic, and
  bearer-token responses standards-compliant?
- For FastAPI code, are background tasks, middleware, and streaming endpoints
  used only for their intended boundaries?
- Did you avoid tests, linting, and formatting commands unless requested?

## Anti-Patterns

Do not write:

```python
from module import *
```

```python
from typing import Dict, List, Optional, Type, Union
```

```python
type Rows = list[dict[str, object]]
```

```python
def format_value(value: Any) -> str:
    return str(value)
```

```python
def load(path: None | Path) -> list[str]:
    ...
```

```python
_Rows = list[dict[str, object]]
```

```python
Path: TypeAlias = pathlib.Path
```

```python
def f(value=[]):
    ...
```

```python
if value == None:
    ...
```

```python
if flag == True:
    ...
```

```python
try:
    ...
except:
    ...
```

```python
try:
    return transform(collection[key])
except KeyError:
    return fallback()
```

```python
logger.info(f"Loaded {count} prompts")
```

```python
logging.info("Loaded %d prompts", count)
```

```python
logger.exception("Upload failed")
```

```python
STATE = {"instance": None}
```

```python
def get_instance():
    ...
```

```python
def build():
    import examples
```

```python
def build_client() -> Client:
    token = os.getenv("API_TOKEN", "example-token")
    return Client(token=token)
```

```python
import importlib

module = importlib.import_module("examples")
```

```python
import sys

sys.path.insert(0, "src")
```

```bash
python -m pip install -r loose-requirements.lock
python -m pip install --extra-index-url https://packages.example.com/simple private-package
python setup.py install
python setup.py develop
easy_install example-package
```

```python
def __getattr__(name: str) -> object:
    ...
```

```python
class TrainingManager:
    ...
```

```python
class Point:
    def __init__(self, row):
        self.x = row.x
        self.y = row.y
```

```python
class BaseRepository(abc.ABC):
    def add_product(self, product: Product) -> None:
        self._add_product(product)
        self.seen.add(product)
```

```python
double = lambda value: value * 2
```

```python
employee_table = ""
for row in rows:
    employee_table += render_row(row)
```

```python
if len(examples):
    ...
```

```python
if type(value) is str:
    ...
```

```python
if name[:4] == "test":
    ...
```

```python
def main():
    ...


main()
```
