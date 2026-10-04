---
trigger: always_on
---

# Agent Rules & Workflow

## Environment
- Local conda environment is located at `./env`.
- If a dependency is missing, run `conda install -p ./env {dependency name}`. **Do not use pip** unless explicitly instructed.
- **Preferred Execution**: Use the dedicated shell scripts in the `./scripts/` directory. They automatically set up the python path, activate the environment, and export required environment variables.

## Git & Branching
- **DO NOT** attempt to push to `master`. It is read-only.
- Branch naming convention: `feature/<short-description>`.
- **Git Operations**: Use standard terminal `git` commands (or `./scripts/` helpers) for all branching, staging, committing, and pushing.
  - Always verify changes against `master` via `./scripts/git_diff.sh` before committing.
- **GitHub Platform Operations**: Use the GitHub MCP server solely for PR and review workflows:
  - Creating Pull Requests (`create_pull_request`).
  - Fetching review threads (`pull_request_read`).
  - Replying to review comments.
- Use the GitHub MCP server to create a Pull Request once tasks are complete.
- **Local Workspace Management**: Use the dedicated shell scripts in the `./scripts/` directory to inspect and manage the local repository state:
  - Check status: `./scripts/git_status.sh`
  - View unstaged diff: `./scripts/git_diff.sh`
  - View staged diff: `./scripts/git_diff_cached.sh`
  - List branches: `./scripts/git_branch.sh`
  - Create/checkout feature branch: `./scripts/git_checkout_branch.sh {branch_name}`
  - Push branch to remote: `./scripts/git_push.sh`
  - View recent commit log: `./scripts/git_log.sh {num_commits}`
  - Discard local unstaged changes: `./scripts/git_restore.sh {path_to_file}`
  - Add local changes to the index: `./scripts/git_add.sh {path_to_file}`
  - Create new commit: `./scripts/git_commit.sh {commit_message}`
- **Database Migrations & i18n Helpers**:
  - Apply database migrations: `./scripts/db_upgrade.sh`
  - Generate database migration: `./scripts/db_migrate.sh {migration_message}`
  - Extract and update translation catalogs: `./scripts/i18n_update.sh`
  - Compile translation catalogs (.mo): `./scripts/i18n_compile.sh`
  - Initialize new translation catalog: `./scripts/i18n_init.sh {lang_code}`
- **PR Review & Communication**:
  - Review comments on pull requests must be addressed by implementing the requested changes, verifying them, and posting an explicit reply to each comment thread upon completion.

## Development Workflow & Code Quality
- **SOLID Principles**:
  - Keep methods and functions focused and single-purpose (Single Responsibility Principle). Decompose complex orchestrators or loop processes (e.g., simulation loop steps) into modular helper functions.
  - Design component interfaces defensively. For example, prepare pipelines for models that might not support specific features like diagnostics or feature importances.
  - It's good to get a working, testable implementation right away, but the work is finished when the code not only works, but is also maintainable in the long term.
  - In case of significant structural changes, update all relevant public interfaces and document any breaking changes.
- **Documentation**:
  - Always include clear docstrings for public APIs (functions and methods) following the Google style guide. Good docstrings should explain what the function does, its arguments, and what it returns.

## Testing & Quality
- **Mandatory check:** Before committing, run the relevant unit tests using `./scripts/run_tests.sh`.
- **Strict Rule on Test Failures**:
  - You are only allowed to self-fix **minor** bugs that you directly introduced during the current task (e.g., syntax errors, typos, incorrect imports, simple test value updates).
  - If the root cause of a test failure is not immediately obvious within 1-2 command runs, do not attempt to debug or investigate extensively. Stop immediately and report the error to the user.
  - If a test fails due to pre-existing bugs, or if fixing the failure requires structural code changes, algorithm redesign, or any non-trivial modifications, you **MUST NOT** proceed with the fix unilaterally. Instead, stop, explain the failure, and consult the user (updating or creating an implementation plan if needed) before writing any code.
- If you modify a file not listed above, check for existing tests in `./tests/` or create a new one.
- If you add new functionality, you must add corresponding unit tests.

## Communication & Action Boundaries
- When the user asks a question, seeks an opinion, or asks "how" to do something, you **MUST** answer the question directly and wait for confirmation. Do **NOT** modify any files (including source code, configurations, or documentation) unless explicitly instructed or approved by the user.
