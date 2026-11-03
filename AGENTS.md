# AGENTS.md: Rules for AI Coding Agents (any language, any stack)

Read this file fully before writing any code. Follow it for the whole session.
If a rule conflicts with a request, say so and ask before proceeding.
Where a rule names a convention (folder names, test tools), use the equivalent
standard for the language and framework in this project.

---

## 0. How to work with me

- **Plan first.** Before changing code, reply with: what you will change, which files, and the risks. Wait for my "go" on anything bigger than a small fix.
- **One change at a time.** One feature or one fix per step. No bundling unrelated work.
- **No scope creep.** Do not add features, refactor, or "improve" things I did not ask for. If you see a problem, report it and ask.
- **Ask when unsure.** Do not guess requirements. One short question beats a wrong build.
- **Never claim "fixed" or "faster" without evidence.** Show test output or measured before/after numbers. If something was not tested, say so plainly.
- **Be honest about failures.** If a test fails or an approach did not work, say so. Do not hide it or quietly change the test.
- **Summarise at the end of each step:** what changed, what was tested, what is still unverified.

---

## 1. Project structure

Start every project with this layout. Rename folders to match the language's
conventions (for example `src/main/java` in Java, `lib/` in Ruby), but keep the idea:
code, tests, docs, scripts and config are separate.

```
project/
├── README.md              # what it is, how to install, run, test, build
├── AGENTS.md              # this file
├── CHANGELOG.md           # what changed, by version/date
├── .gitignore
├── config/                # settings and an example config (never real secrets)
├── src/                   # all application code
│   ├── app/               # thin entry point: wiring only, no business logic
│   ├── <feature_a>/       # one folder per feature or domain
│   ├── <feature_b>/
│   └── shared/            # small common helpers only
├── tests/                 # ALL tests live here, mirroring src/
│   ├── unit/
│   ├── integration/
│   └── fixtures/          # test data lives here, never in src/
├── docs/
│   ├── architecture.md    # modules and how they connect
│   ├── decisions.md       # why we chose X over Y
│   └── runbook.md         # how to operate, debug, deploy
├── scripts/               # build, packaging, dev tools (not app logic)
└── build/ or dist/        # generated output, git-ignored
```

Rules:
- **Tests go only in the tests folder.** Never put test files, test data or experiments in application code.
- **Generated output** (builds, logs, archives) is git-ignored and never mixed with source.
- **Secrets** (API keys, license files, tokens, passwords) never go in the repo or in shipped builds.

---

## 2. File and function size limits (hard rules)

| Thing | Limit |
|---|---|
| A source file | **300 lines** (over 500 is a bug to fix) |
| A function / method | **40 lines**, does **one** thing |
| Parameters per function | max 5 (otherwise group them into one object) |
| Nesting depth | max 3 levels |

- **Never keep piling code into one file.** When a file nears the limit, split it before adding more.
- The entry point only wires things together. No business logic in it.
- Split by **responsibility**, not by size alone. Example for a data tool:
  - one module fetches data
  - one transforms raw data into rows
  - one writes output
  - one holds shared state
  - one handles logging and diagnostics
- A module should be understandable without reading the others. Depend on small, clear interfaces, not on another module's internals.
- No circular dependencies. If two modules need each other, extract the shared part into a third.
- No dead code, no commented-out code, no unused functions. Delete it (version control keeps history).

---

## 3. Code quality

- **Clear names.** `fetchOptionChain` not `doIt`. Names say what, not how.
- **Use the language's type system** (types, interfaces, annotations) wherever it exists, especially on public functions.
- **Document every module and public function:** what it does, inputs, outputs, errors.
- **No magic numbers or strings.** Put them in config or named constants.
- **Avoid global mutable state.** If unavoidable, document it.
- **Keep pure logic separate from I/O.** Calculations must be testable without network, files or UI.
- **Do not repeat yourself.** If you copy a block twice, make it a function.

### Error handling (important)
- **Never swallow errors.** No empty catch/except blocks, and no "catch everything and return 0/null/empty".
- Catch specific error types. Log with context: what was attempted, inputs, status code, stack trace.
- Distinguish states clearly: `ERROR` vs `EMPTY` vs `LOADING`. A failure must never look like "no data".
- Retry transient failures with backoff. Keep the last good data. Show the problem to the user visibly.
- A successful response status does not mean correct data. Validate what came back (expected fields, expected values).

### Logging
- Use a proper logger, not print statements. Use levels: debug, info, warning, error.
- Logs rotate (size cap) so a long-running process cannot fill the disk.
- Log enough to diagnose a problem remotely. Never log secrets.

---

## 4. Testing

- **Every feature and every bug fix gets a test.** Fixing a bug: write the failing test first, then the fix.
- Tests mirror the source layout and run with **one documented command** (put it in the README).
- **Test the real wiring, not just isolated functions.** A function can pass alone while the code that calls it is wired wrong. Add at least one end-to-end test per feature.
- **Test data is clearly labelled and kept in the fixtures folder.** It must never be written into real user files or shipped output, and never be mistaken for live data.
- Do not edit or delete a failing test to make it pass. If the test is wrong, explain why and ask.
- Run the whole test suite before saying a task is done. Show the result.

### Measuring performance claims
- Measure **before and after** with the same method. When comparing two versions, alternate the runs to avoid warm-cache bias.
- Report numbers, not a verdict. State which data was real and which was synthetic.
- If a "fix" gave no measurable improvement, say so and do not call it a fix.

---

## 5. Documentation

Keep docs current in the same change as the code. A task is not done if docs are stale.

- **README.md:** purpose, requirements, install, run, test, build, troubleshooting.
- **docs/architecture.md:** list of modules, what each does, how data flows, a simple diagram.
- **docs/decisions.md:** short entries: decision, options considered, reason, date.
- **docs/runbook.md:** where logs are, common errors and fixes, how to diagnose.
- **CHANGELOG.md:** every user-visible change, with version and date.
- Comments explain the **why** when it is not obvious from the code.

---

## 6. Version control and change discipline

- Small, focused commits. Message format: `type(scope): what and why` (example: `fix(feed): log request failures instead of returning empty`).
- Keep different kinds of change in separate commits (refactor, feature, fix, packaging).
- **Commit or tag a known-good state before risky work**, so we can go back.
- Never rewrite or force-push shared history without asking.
- Do not commit generated files, secrets or large binaries.

---

## 7. Refactoring a large file (for existing messy code)

When asked to split a big file (for example 3,000+ lines), work in safe steps:

1. **Do not rewrite.** Preserve behaviour exactly.
2. **Map first.** Produce a one-page map: each function, line count, what it does, whether it runs every cycle or once, and whether it is dead or alive. Share it and wait for my approval.
3. **Add safety-net tests** (or a recorded before-output) so we can prove behaviour did not change.
4. **Move code in small slices.** One responsibility at a time into its own module. Run tests after each slice. One commit per slice.
5. **Delete dead code** only after confirming nothing uses it.
6. **Update docs** (the architecture map) at the end.
7. Report: lines before and after, modules created, tests passing.

---

## 8. Packaging and delivery (when shipping software to users)

- Build from a clean checkout, not from a dirty working folder.
- **Leak check** the output: no secrets, license files, test data, source files or stray logs.
- Provide the **full SHA256** (all 64 characters) with every release file.
- Test the packaged build on a clean machine, as a normal (non-admin) user, with antivirus on.
- Record the build ID/version inside the app and in the diagnostics log.
- Release notes must be honest: list what changed and what is still untested. No performance claims without numbers.

---

## 9. Safety rules for the agent

- **Never force-kill** processes, delete files or run destructive commands without asking.
- Do not type into or control windows or apps outside the task.
- Do not touch files outside the project folder.
- Do not install dependencies without saying which and why.
- Do not bypass authentication, tokens or access controls, even for testing.
- Never invent numbers, results or test output. If you did not measure it, say so.

---

## 10. Definition of done (check every item)

- [ ] Does exactly what was asked, nothing more
- [ ] No file over 300 lines, no function over 40 lines
- [ ] Tests added and the full suite passes (output shown)
- [ ] No swallowed errors; failures are logged and visible
- [ ] Docs and CHANGELOG updated
- [ ] No test data, secrets or dead code left behind
- [ ] Committed with a clear message
- [ ] Summary written: changed, tested, still unverified