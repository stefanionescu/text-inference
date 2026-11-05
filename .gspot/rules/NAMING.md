# Naming

Read this rule when you name a file, folder, type, function, or variable.

## Casing across languages

`naming.cases` sets the case of each kind of name in each language. These decisions hold across languages, so one
concept reads alike throughout the program.

- Acronyms: follow the language. TypeScript and JavaScript treat them as words, such as `parseHttpUrl` and `userId`.
  Swift keeps uppercase initialisms, such as `avatarURL` and `userID`, and writes `apiClient` at the start of a name.
  Python, SQL, and Bash lowercase them inside snake_case, such as `http_url` and `user_id`.
- Folders: kebab-case for TypeScript, JavaScript, HTML, CSS, and static sites; kebab-case or snake_case for Bash;
  snake_case for Python packages; PascalCase for Swift folders, which mirror type names.
- On the wire: camelCase JSON fields and kebab-case URL segments. Log event names and fields follow the property case of the
  language, unless an existing logging interface defines their spelling.
- Environment variables: `UPPER_SNAKE_CASE`. An application's own variables take no prefix; a variable that a tool writes
  into another project's environment takes the tool's prefix.
- Constants: a module-level constant bound to a literal or a frozen object uses `UPPER_SNAKE_CASE` in TypeScript,
  JavaScript, Python, and Bash, and camelCase in Swift.

## Authority

`naming/identifiers` and `naming/paths` check banned words, case, length, and word count. Fix a finding by renaming.
Never hide a bad name in a string key, an alias, or a file name. When no file uses a name of `allowed_names` in a
`[[naming.exception]]` record, remove it.

## Principles

A name lets a reader understand the concept, scope, role, and expected value without reading the implementation. Name by
role, responsibility, and domain meaning, never by storage type, UI framework type, collection shape, or implementation
accident. Use English unless an external identifier keeps another spelling. Prefer the shortest name that keeps its
meaning at the use site. Add a qualifier only when the bare name has more than one meaning there. Never invent private
shorthand or drop letters from a word.

Do not repeat context the enclosing type, module, folder, or package already supplies, or encode every implementation
detail.

Give each concept one word across the repository, and each word one meaning. Before you give a word to a new concept,
search the code for it. When the word already names another concept, choose a different one. Add the synonyms you reject
to `naming.banned_words`, so the naming check reports them. Use singular names for single values and plural ones for
collections. Name a collection by what it holds.

The same holds for the words that people read in messages, help, and documentation. Pick one word for each concept the
program shows, and use it everywhere. For example, a command-line tool that writes config files uses these words:

| Mixed words                 | One word             | Concept                                                       |
| --------------------------- | -------------------- | ------------------------------------------------------------- |
| config file, generated file | generated file       | A file that the tool writes from its settings.                |
| key, field, setting         | setting              | A value that the user writes in the settings file.            |
| delete, remove              | remove               | Take a configuration out of the settings file.                |
| clear, unset                | unset                | Take a value out of a setting.                                |
| program, tool               | tool                 | A program that the tool installs and runs.                    |
| rule, for two concepts      | lint rule, rule file | A rule of a linter; a file of instructions for coding agents. |

Add each word you reject to `naming.terms` with its replacement, such as `"config file" = "generated file"`. The naming
check then reports the word in identifiers, and the prose check in documentation, code comments, and commit messages.

A role word carries meaning where a primitive or weak type does not.

| Avoid               | Prefer                        | Why                              |
| ------------------- | ----------------------------- | -------------------------------- |
| `string`, `dict`    | `welcomeMessage`, `usersById` | The role, not the type.          |
| `u`, `tmp`, `cfg`   | `user`, `accountSummary`      | Whole words a stranger can read. |
| `userArray`         | `users`                       | The type already says array.     |
| `Car.carMake`       | `Car.make`                    | The type supplies the context.   |
| `optionalAvatarURL` | `avatarURL`                   | Optionality lives in the type.   |
| `DataProcessor`     | `ProfileImageClient`          | An external API.                 |

## Role words

A suffix names the role of a type. Use each suffix for one meaning. Name a type with no such role for its concrete
domain concept.

| Role word    | Use when                                                             |
| ------------ | -------------------------------------------------------------------- |
| `UseCase`    | Application operation or business workflow.                          |
| `Repository` | Domain-facing access to persisted, cached, or remote domain data.    |
| `Client`     | External API, SDK, HTTP, storage, or platform protocol.              |
| `Factory`    | Type that constructs instances and assembles dependencies.           |
| `Formatter`  | Converts a value into a display or wire representation.              |
| `Parser`     | Converts raw input into structured data.                             |
| `Validator`  | Checks a value and returns or throws validation failure.             |
| `Mapper`     | Converts between explicit layers, such as record to domain.          |
| `Store`      | Holds local mutable state or persistence mechanics.                  |
| `Provider`   | Supplies a capability or value, especially when the source may vary. |
| `Adapter`    | Bridges one interface or framework shape to another.                 |

Use `Route`, `Callback`, `Observer`, and `Listener` only for the framework shapes they name. In Swift, keep the UI role
words `View`, `ViewModel`, `ViewController`, and `Coordinator` for those roles. Never use `Manager`. Keep `Service` for
framework roles, such as a NestJS provider.

## Functions and methods

A function name starts with the action and carries enough domain context to read at the call site without repeating the
enclosing type or module. A generic verb such as `process`, `handle`, `execute`, `manage`, `perform`, or `ensure` never
stands where the name can state the action. `handle` exists only in a framework callback such as a React `handleSubmit`
or a UIKit `@objc handleConfirmButtonTapped`. Never use `Handler` as a type suffix. A name that needs `and`, `or`,
`with`, or an umbrella verb marks a function that combines too many concepts. A preposition cannot replace a verb:
`toPosix`, `fromRow`, and `withTimeout` need one.

Each act has one verb. Use the table verb for each act, never a synonym:

| Verb                          | Act                                                                                                                                     |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `get`                         | Take a value already in memory: a variable, a map entry, a cache, or a parsed structure. The return type says if it may be absent.      |
| `read`                        | Take data from outside memory: a file, Git, the environment, a child process, or the network. The return type says if it may be absent. |
| `find`                        | Search for one item. Return nothing when it is absent.                                                                                  |
| `list`                        | Return every item of a kind, such as the orders of a customer.                                                                          |
| `select`                      | Choose among known options.                                                                                                             |
| `detect`                      | Infer a fact from evidence, such as the language of a file.                                                                             |
| `build`                       | Construct a value in memory from other values, such as a message, a plan, or the text of a file.                                        |
| `create`                      | Make a new file, folder, or other resource on disk.                                                                                     |
| `parse`, `decode`             | Raw text to structured data; encoded bytes or payloads to typed values.                                                                 |
| `encode`, `serialize`         | Typed values to bytes; values to the text of a file format.                                                                             |
| `format`                      | Return the text that people read for a value: terminal lines, Markdown, or a message.                                                   |
| `print`                       | Write text that people read to a terminal or a log stream.                                                                              |
| `write`                       | Put data into a file or another store outside memory.                                                                                   |
| `validate`                    | Return what makes one value invalid.                                                                                                    |
| `assert`                      | Throw an error on an invalid value.                                                                                                     |
| `check`                       | Run a check that reports findings, such as a lint check. Use `validate` or `assert` for one value.                                      |
| `run`                         | Start a named program, command, or step, such as `runMigrations`. Never a bare `run`.                                                   |
| `spawn`                       | Start a child process.                                                                                                                  |
| `set`                         | Assign a key or a field of a value in memory.                                                                                           |
| `add`, `remove`               | Put an item into a collection in memory, or take it out.                                                                                |
| `insert`, `update`, `delete`  | Add, change, or destroy a row or item in persisted data, or a file on disk.                                                             |
| `prepare`, `refresh`, `reset` | Set up local state before a workflow; replace presentation state from a source; return to an initial state.                             |
| `is`, `has`, `can`            | Predicates only: `is` for state, `has` for presence, and `can` for capability.                                                          |

When no table verb fits, pick another plain one that names the act. Plain verbs include `count`, `compare`, `merge`,
`split`, `sort`, `filter`, `group`, `match`, `replace`, `normalize`, `convert`, `extract`, `strip`, `copy`, `move`,
`stop`, and `wait`. Name your own retrieval functions `get`, `read`, or `find`; `load`, `fetch`, and `resolve` stay for
platform APIs such as `fetch`.

The noun and the return type carry multiplicity and optionality, such as `getSession` and `getSessions`. Give an
operation that combines create, read, update, and delete (CRUD) acts its precise domain verb.

| Avoid                    | Prefer                   | Meaning                        |
| ------------------------ | ------------------------ | ------------------------------ |
| `saveCall`               | `insertCall`             | Insert a new call.             |
| `handleData`             | `decodeAccountResponse`  | Decode account response bytes. |
| `process`                | `validateEmailAddress`   | Validate an email address.     |
| `update`                 | `updateDraftMessageText` | Replace draft message text.    |
| `mapUserRowToUserDomain` | `mapUser`                | The parameter type says row.   |

Where external data enters, name the conversion for the operation and the concept, `decodeUserResponse` rather than
`transform`. DTO means data transfer object. Shape suffixes such as `Row`, `DTO`, `Request`, and `Response` stay on the
type that declares it. Never put those suffixes on domain entities, view models, or functions that accept the shape.

## Booleans and predicates

Name stored boolean columns and direct domain mappings as concise positive states without a prefix: `enabled`, `active`,
`retryable`, and `webSearchEnabled`. Predicates, including computed ones, and presentation-state assertions start with
`is`, `has`, or `can`. Name an action for what it does even when it returns a boolean, such as `sendInvite`. Name a
proposed answer or control parameter for its role, such as `defaultCountry`; a boolean type does not make a function a
predicate.

Replace negative names such as `isNotReady` and `isEmailNotUsed` with the positive form that matches the branch without
double negation. A boolean never reads like a noun value.

| Avoid                    | Prefer                 | Meaning                                           |
| ------------------------ | ---------------------- | ------------------------------------------------- |
| `SearchPolicy.isEnabled` | `SearchPolicy.enabled` | Stored policy state.                              |
| `email`                  | `hasEmailAddress`      | Presence of an email address.                     |
| `textFile`               | `isTextFile`           | Whether a file meets the text-file definition.    |
| `isEmailNotUsed`         | `isEmailUsed`          | Whether an account already uses an email address. |
| `ready`                  | `is_ready`             | A computed readiness predicate in Bash.           |

## Files and folders

Name files and folders for the behavior or entity they contain, not for reuse.

- Name a file that holds one primary type after it, where the language does so. Name a module after the capability it
  implements. Prefer feature folders to top-level type buckets.
- Move code to a shared place only for a repeated concept with one module that implements it, never for a caller that
  does not exist yet.
- File names and identifiers avoid the same banned words. Only a generated artifact or a migration may carry a timestamp
  in its name.

| Avoid              | Prefer                        | Meaning                |
| ------------------ | ----------------------------- | ---------------------- |
| `Helpers.swift`    | `DateRangeFormatter.swift`    | Date range formatting. |
| `LoginStuff.swift` | `LoginView.swift`             | Login presentation.    |
| `common-utils.ts`  | `email-address-validation.ts` | Email validation.      |
| `src/helpers/`     | `src/accounts/`               | Account behavior.      |

## External names

External systems use names that do not match the domain language, such as `XMLHttpRequest`, Apple's `FileManager`, or
`AWS_REGION`. Keep those names in code that reads or writes external data.

DTOs, SQL rows, generated types, wire payloads, and validation schemas keep the external field names. Renaming one
changes the public interface. Translate them into domain names through explicit mappings before the values reach domain
or presentation code. Keep provider, database, and HTTP mechanics out of domain names.

A wire shape such as `MessageAttachmentDTO` keeps `storage_object_path`. The validated `MessageAttachment` uses
`attachmentPath`, and the module that implements the storage protocol converts one into the other.
