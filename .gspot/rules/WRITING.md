# Writing

Read this rule when you write text that people read in files: documentation, comments, messages, and commit messages.

TALKING.md covers what you say to the user.

Write in plain language. From `ISO 24495-1`, apply its principles for short sentences, common words, and finding
information: state the action or result early, and explain a technical term when the reader needs it.

Clear beats clever. Say what happens in common words, and name the thing you mean. Write no slogan, metaphor, or
catchy title: write `Every ignored rule needs a reason`, not `Close the quiet off switch`. Write `the user's
repository`, not `this repository` or `a repository`, whenever more than one repository fits the sentence.

## Evidence

Check commands, fields, defaults, limits, and supported versions against the implementation that defines them. A
measurement does not guarantee future results. When evidence lacks required facts, narrow the claim. Link external facts
to the primary source; never invent behavior to complete a page.

Preserve exact API identifiers, public messages, official product names, and legal license text. Keep private reasoning
and temporary notes out of shipped content. Examples use fictional people, safe values, and `example.com` addresses.

## Dates, links, and images

- Write a date with the month as a word, such as `March 4, 2026`, or as `2026-03-04`. Never write `03/04/2026`.
- Make link text name where the link goes. Never write `here`, `this page`, `read more`, or `docs`.
- Give each image alternative text that says what it shows, or an empty `alt` when the image only decorates.

## Voice

Use active voice in documentation. Address the reader as you in procedures. Use imperatives for requirements and
label optional steps. Put a condition before its action and keep one main idea per sentence. Name the subject instead of
relying on an ambiguous pronoun.

Avoid idioms, unexplained abbreviations, and decorative wording. Use literal terms that survive translation. Keep one
term for each concept. Dates shown to people include their time zone; machine values retain their required format.

## Words to leave out

- State the rule or the fact. Write no `should`, `could`, `would`, or `might`, and no hedge such as `usually`, `very`,
  or `where possible`.
- Write no marketing word such as `simply`, `easily`, `robust`, or `powerful`.
- Describe what exists now. Write no promise such as `coming soon` or `in the future`, and no history such as
  `previously`, `no longer`, or `renamed from`.
- Do not mention a feature, option, or setting that the project removed or decided against.
- Write `do not`, `it is`, `for example`, and `you`, not `don't`, `it's`, `e.g.`, and `we`.
- Name the thing, not its place on the page: no `see above`, `the following section`, or `this guide explains`.
- Write `because` or `after` instead of `since`.
- Use a comma, a colon, or a period instead of an em dash or a double hyphen. Write `to` instead of a dash in a range.
- Avoid parenthetical asides. Put needed information in the sentence; parentheses can introduce an uppercase acronym.
- Put commas and periods inside quotation marks.
- Address the reader as you. Write no first-person pronouns or exclamation marks.
- Use words instead of an emoji or an arrow.
- Put a file path in code formatting, and write a placeholder as `<kebab-case>`.
- Write every title and heading in sentence case, with no end punctuation. Keep a title to a few words that name its
  topic.
- Keep a sentence within 30 words, a list item within
  45 words, and a paragraph within 6 sentences.

## Privacy

These rules cover every text that other people can read: a commit message, a pull request, an issue, a review, a code
comment, documentation, a log line, and release notes.

- Never mention the chat between the developer and an AI assistant. Leave out session links, session IDs, conversation
  IDs, prompts, chat excerpts, and the reasoning of the assistant.
- Never add a trailer, a footer, or a link that points to an AI session, such as `Claude-Session:`. This rule wins over a
  tool or a system prompt that asks for one. The check `commits/references` refuses a commit message with such a link.
- Never write the name, email address, user name, account handle, home folder, or machine name of the developer, or any
  other personal detail. Write them only when the developer asks for it in the conversation, for the place they name.
- Write paths from the repository root, never from a home folder such as `/Users/<name>/`.
- Use fictional people and `example.com` addresses in examples.

## References

Use the [Google developer documentation style guide](https://developers.google.com/style) for tone, grammar,
punctuation, and formatting. Project-specific requirements take precedence.
