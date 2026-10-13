# OTCBot

Discord bot for the OTC server, built with Python and Pycord.

This repository contains the bot's source code, configuration, tests, and deployment-related files.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Issue Rules](#issue-rules)
- [Branch Rules](#branch-rules)
- [Commit Rules](#commit-rules)
- [Workflow Rules](#workflow-rules)
- [Server Rules](#server-rules)
- [File Architecture](#file-architecture)
- [Testing](#testing)
- [Pull Requests](#pull-requests)

---

## Project Overview

OTCBot is a Discord bot designed to provide utility and moderation features for the OTC server.

Its features are organized into independent cogs and supporting services to keep the codebase maintainable and easy to extend.

### Main technologies

- **Python** — Main programming language.
- **Pycord** — Discord API wrapper.
- **pytest** — Automated testing.
- **GitHub Actions** — Automation and CI/CD.
- **Waifly** — Bot hosting.

---

## Getting Started

### Requirements

- Python version compatible with the project's dependencies.
- Git.
- A Discord bot application and token for local execution.
- Access to the repository's required configuration values.

### Installation

Clone the repository:

```bash
git clone <repository-url>
cd OTCBot
```

Set up the virtual environment:

**Linux:**

```bash
bin/setup_linux.sh
```

or

```bash
make setup
```

**Windows:**

```powershell
bin\setup_linux.ps1
```

---

## Configuration

OTCBot uses environment variables for configuration.

Copy the .`env.example` as `.env`, and fill it with your own values

### Rules

- Never commit .env, bot tokens, passwords, or other secrets.
- Use GitHub Secrets for sensitive values in automated workflows.
- Use GitHub Actions Variables for non-sensitive deployment configuration.
- Keep local configuration out of version control.
- Validate required environment variables during startup.

---

## Issue Rules

Issues are used to report bugs, propose features, and track improvements.

### Creating an issue

Every issue should:

- Have a clear, descriptive title.
- Explain the problem or requested change.
- Include reproduction steps when reporting a bug.
- Include expected and actual behavior when relevant.
- Include logs or screenshots when useful, without exposing secrets.
- Identify relevant components or files when possible.

### Issue categories

Use labels consistently to identify the type of work.

Suggested labels:

| Label           | Purpose                                              |
|-----------------|------------------------------------------------------|
| `bug`           | Something is broken or behaves incorrectly.          |
| `feature`       | A new capability is requested.                       |
| `enhancement`   | An existing feature should be improved.              |
| `documentation` | Documentation needs to be added or updated.          |
| `tests`         | Test coverage or test infrastructure needs work.     |
| `maintenance`   | Refactoring, dependencies, or internal improvements. |
| `help wanted`   | The issue is open for contributions.                 |

### Issue assignment

- Check for an existing issue before opening a duplicate.
- Discuss substantial changes before implementing them.
- Assign an issue to yourself before beginning work when assignments are used.
- Keep the issue updated if the scope or implementation changes.

---

## Branch Rules

Branches isolate changes and make collaboration safer.

### Branch naming

Use descriptive names with a category prefix:

```text
feature/#<issue number>-<description>
fix/#<issue number>-<description>
task/#<issue number>-<description>
docs/#<issue number>-<description>
refactor/#<issue number>-<description>
test/#<issue number>-<description>
```

Examples:

```text
feature/#3-voice-channel-limits
fix/#12-purge-permissions
task/#12-clean-voice-channel-service
```

Use lowercase words separated by hyphens.

### Branch guidelines

- Never develop directly on `main`.
- Create branches from the agreed base branch.
- Keep branches focused on one issue or closely related change.
- Avoid including unrelated changes in the same branch.
- Update your branch when necessary to resolve conflicts.
- Do not force-push shared branches without coordinating with affected teammates.
- Delete merged branches when they are no longer needed.

### Protected branches

The default branch should contain working, reviewed code.

Direct pushes should be restricted when repository settings permit it. Changes should go through pull requests and the agreed review process.

---

## Commit Rules

Commit messages should make the purpose of each change immediately understandable.

### Commit format

Use a consistent, imperative format:

```text
<type>(#<issue number>): <short description>
```

Suggested types:

| Type       | Purpose                                              |
|------------|------------------------------------------------------|
| `feature`  | Add a feature.                                       |
| `fix`      | Fix a bug.                                           |
| `task`     | Perform general maintenance.                         |
| `docs`     | Update documentation.                                |
| `test`     | Add or modify tests.                                 |
| `refactor` | Restructure code without changing intended behavior. |

Examples:

```text
feature(#31): add engineer announcement commands
fix(#43): validate purge permissions
test(#103): cover announcement failures
```

### Commit guidelines

- Write messages in English.
- Use the imperative mood: `add`, `fix`, `update`, not `added`, `fixed`, `updated`.
- Keep the subject short and specific.
- Make each commit represent a logical change.
- Avoid vague messages such as `update`, `changes`, or `fix stuff`.
- Never commit credentials, generated files that should be ignored, or unrelated local changes.
- Do not rewrite shared history without coordinating with the team.

---

## Workflow Rules

Every contribution should follow a predictable development workflow.

### Standard workflow

1. Find or create an issue.
2. Agree on the intended behavior when necessary.
3. Create a dedicated branch.
4. Implement the change.
5. Add or update tests.
6. Run the relevant tests and checks.
7. Commit the changes using the commit rules.
8. Push the branch.
9. Open a pull request.
10. Address review feedback and merge according to repository policy.

### Code guidelines

- Keep responsibilities separated between cogs, services, and core modules.
- Avoid duplicating existing functionality.
- Prefer small, readable functions with clear responsibilities.
- Handle expected Discord API errors explicitly.
- Use the existing logging system instead of adding ad hoc logging.
- Validate user input and permissions before performing privileged actions.
- Keep configuration outside business logic where practical.
- Update tests whenever behavior changes.

### Dependencies

- Add dependencies only when they are justified.
- Update `requirements.txt` when dependencies change.
- Avoid committing virtual environments or machine-specific files.
- Communicate changes that affect the required Python version or deployment environment.

### Generated files

Do not commit temporary files, caches, local logs, coverage output, or other generated artifacts unless the project explicitly requires them.

---

## Server Rules

These rules apply to changes and operations involving the Discord server and the bot's hosting environment.

### Discord server

- Do not test destructive commands on real users or production channels.
- Use a test server for development and permission checks whenever possible.
- Never grant the bot permissions it does not need.
- Verify role and channel permissions before deploying permission-sensitive features.
- Avoid unnecessary mentions, mass notifications, or disruptive messages.
- Do not expose private server information in logs, issues, commits, or screenshots.

### Bot hosting

- Production credentials must remain secret.
- Do not restart, stop, or reconfigure the production bot without authorization of the OTC owner.
- Coordinate deployments that could interrupt service.
- Check logs after deployment to confirm that the bot started correctly.
- Keep deployment configuration consistent with the repository's expected environment variables.
- Do not manually modify production files when the same change should be made and tracked in Git.

### Maintenance and incidents

For a production incident:

1. Identify the affected feature or service.
2. Check the available logs.
3. Notify the responsible teammate when intervention is required.
4. Apply an approved fix or rollback.
5. Verify recovery.
6. Document the cause and any follow-up work.

---

## File Architecture

The repository is organized by responsibility.

```text
OTCBot/
├── bin/
│   ├── setup_windows.ps1
│   └── setup_linux.sh
├── otc_bot/
│   ├── cogs/
│   ├── core/
│   ├── services/
│   └── __main__.py
├── tests/
│   ├── cogs/
│   ├── core/
│   ├── services/
│   └── test_main.py
├── .env
├── LICENSE
├── requirements.txt
├── Makefile
└── README.md
```

### `bin/`

Contains scripts used for setup and operational tasks.

### `otc_bot/cogs/`

Contains Discord cogs: commands, listeners, and Discord-facing behavior.

- `general.py` — General-purpose commands and message listeners.
- `voice_channels.py` — Commands and behavior for voice channels.
- `engineer_only.py` — Engineer-oriented commands.
- `mod_only.py` — Moderator-oriented commands.

### `otc_bot/core/`

Contains shared application infrastructure.

- `bot.py` — Bot initialization and lifecycle behavior.
- `constants.py` — Shared constants and identifiers.
- `logging.py` — Logging utilities.
- `models.py` — Shared data models.

### `otc_bot/services/`

Contains reusable business logic that should not be tied directly to Discord command callbacks.

- `env.py` — Environment variable handling.
- `voice_channel.py` — Voice channel operations and related logic.

### `otc_bot/__main__.py`

Provides the application entry point, allowing the bot to be launched with:

```bash
python -m otc_bot
```

### `tests/`

Contains automated tests organized around the application modules.

- `tests/cogs/` — Tests for Discord cogs.
- `tests/core/` — Tests for core infrastructure.
- `tests/services/` — Tests for services.
- `tests/test_main.py` — Tests for application startup.

### Architecture guidelines

- Put Discord command and event handling in cogs.
- Put reusable business logic in services.
- Put shared infrastructure in core.
- Keep tests close to the module categories they validate.
- Avoid circular imports.
- Keep secrets and deployment-only files outside the tracked source code.

---

## Testing

Tests are required for new behavior and bug fixes.

### Run the test suite

**Linux:**

```bash
make tests
```

**Windows:**

```bash
.venv\bin\pytest tests\ --cov=otc_bot --cov-report=term-missing --cov-report=html
```

### Testing guidelines

- Test successful behavior and expected failure cases.
- Mock Discord API interactions rather than making real requests.
- Test permission checks for privileged commands.
- Test error handling for expected Discord exceptions.
- Keep tests deterministic and independent.
- Never require a production token to run ordinary unit tests.
- Fix warnings caused by the application or tests rather than suppressing them without investigation.
- Tests may be generated by IA, BUT must be reviewed and validated by a team member.

---

## Pull Requests

Pull requests are the review point before changes are integrated.

### Requirements

A pull request should:

- Reference the relevant issue when one exists.
- Explain what changed and why.
- Describe any behavior changes.
- Include tests for new or modified behavior.
- Pass the required automated checks.
- Update documentation when necessary.
- Contain only relevant changes.

### Review process

- Review the implementation, not just whether it works locally.
- Check permission handling, error handling, logging, and security implications.
- Request changes when behavior is unclear or unsafe.
- Resolve review comments before merging.
- Do not merge your own changes if repository policy requires another reviewer.

### Suggested pull request template

```markdown
## Summary

Describe the changes.

## Related issue

Closes #

## Changes

- Change 1
- Change 2

## Testing

- [ ] Tests added or updated
- [ ] Test suite passes
- [ ] Documentation updated if necessary

## Notes

Mention risks, deployment considerations, or known limitations.
```

---

## Security

- Never commit `.env` files, tokens, passwords, or private keys.
- Never paste secrets into issues, pull requests, logs, chat, or in the code.
- Use the minimum permissions required for each bot feature.
- Report exposed credentials immediately and rotate them.
- Keep dependencies updated when necessary.
- Treat external input and Discord interaction data as untrusted.

---

## Contributing

If you are unsure how a feature should behave, ask before implementing a large change.

Small, focused, tested contributions are easier to review, merge, and maintain.

**When in doubt, prioritize security, clarity, and consistency with the existing architecture.**
