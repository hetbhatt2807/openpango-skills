# Agent Memory & Lessons Learned

**IMPORTANT: FOR FULL SYSTEM CONTEXT, READ `PROJECT_CONTEXT.md` IN THE ROOT DIRECTORY.**
The project has been restructured into a unified `openpango-skills` NPM package. All standalone Python/Bash skills are now modularly integrated into a single ecosystem managed by the `openpango` CLI. 

---

## Tool Usage and Logic
- **Mistake (Replace tool):** Specified `expected_replacements: 3` when replacing a block of text in `SKILL.md` because there were 3 paths inside the block.
  - **Lesson:** The `expected_replacements` parameter in the `replace` tool corresponds to the number of occurrences of the exact `old_string` block in the entire file, not the number of internal changes or substrings within that block.
- **Mistake (Grep Search):** Used an invalid inline regex flag `(?i)` inside a `grep_search` pattern (e.g., `(?i)openclaw`), resulting in a regex parsing error.
  - **Lesson:** Rely on the `case_sensitive: false` parameter of the `grep_search` tool rather than embedding unsupported inline flags.

## File and Path Management
- **Mistake (Directory handling):** Created the new orchestration files in `project/orchestration` under the workspace root, resulting in a redundant `project/project/orchestration` path.
  - **Lesson:** Always verify the absolute working directory and recognize that relative paths are executed against the workspace root. Avoid duplicating project folder names.
- **Mistake (Moving files):** Had to use generic shell commands (`cp` and `rm`) to move files and delete the mistakenly created directories.
  - **Lesson:** Careful initial planning using the `write_file` paths directly avoids messy manual file operations later.

## Agent Architecture and Efficiency
- **Mistake (Polling):** The initial mock for the Manager Agent's workflow relied on a `check_status` tool to periodically poll the sub-agent until it was finished.
  - **Lesson:** For LLM-based orchestration, blocking tools (like a `wait` command with a configured timeout) are massively more efficient than polling loops. Polling burns through the LLM's context window, increases token cost, and triggers unnecessary tool roundtrips. A single blocking `wait` tool minimizes overhead and simplifies the agent's workflow significantly.
- **Improvement (Sub-Agent Routing):** Integrated `frontend-design` to handle specialized UI tasks instead of relying solely on generic "Coder" agents. 
  - **Lesson:** Specialized sub-agents (Researcher, Planner, Coder, Designer) yield much higher quality results when intent routing is explicitly mapped in the orchestration Manager.

## Code Quality and Python Best Practices
- **Mistake (Resource Leaks):** Opened SQLite connections but failed to properly close them in `sync_read_cache()`.
  - **Lesson:** Always ensure database connections are closed properly to avoid connection leaks and potential file locking issues.
- **Mistake (Deprecated APIs):** Used `datetime.utcnow()` which is deprecated in Python 3.12+.
  - **Lesson:** Keep abreast of modern language features; use timezone-aware date objects like `datetime.now(timezone.utc)`.
- **Mistake (Missing Validations & Safeguards):** Failed to validate if a task exists before attempting to update or link it, and failed to prevent self-dependencies (linking A to A).
  - **Lesson:** Always validate inputs against existing state and implement logical boundary checks (like preventing circular or self dependencies).
- **Mistake (CLI Interface Determinism):** Left argparse `choices` unsorted, which can lead to non-deterministic help output.
  - **Lesson:** Use sorted iterables (e.g., `sorted(VALID_AGENTS)`) for argparse choices to ensure consistent and testable CLI outputs.
- **Mistake (Unused Imports):** Left unused imports (like `os`) in the code.
  - **Lesson:** Clean up unused imports to maintain code hygiene.

## System Observability and Interface Design
- **Mistake (Stdout Pollution):** Printed user-facing progress messages to `stdout` during a wait command, which corrupts the final machine-readable JSON output.
  - **Lesson:** Strictly isolate output streams: write progress or diagnostic messages to `stderr` and reserve `stdout` exclusively for structured, parseable final data (e.g., JSON).
- **Mistake (Lack of State Visibility):** Only built the bare minimum tools for updates and queries, making it hard to see the whole picture.
  - **Lesson:** Proactively build state inspection commands (like `list_tasks`, `get_task`, or `list_sessions`) to improve the system's observability and make debugging easier.
- **Mistake (Documentation Code Snippets):** Provided a shell script example in `SKILL.md` that improperly used shell command substitution `$(...)` against commands outputting raw JSON, which breaks the workflow.
  - **Lesson:** Ensure code and workflow examples reflect the true structural output of the CLI tools (e.g., showing how to handle JSON correctly).

## Development and Verification
- **Mistake (Lack of End-to-End Testing):** Wrote code and skills but only tested them via syntax checks or basic `-h` flags, failing to execute the tools fully to verify their logical correctness and outputs before shipping them.
  - **Lesson:** **Always test before shipping.** You must execute the code and empirically verify its behavior, even if it requires mocking or creating localized testing environments. Never assume code works just because the syntax is valid.
- **Mistake (SPA State Persistence):** Designed a CLI browser controller where each action (`click`, `read`) starts and closes the browser context. Assumed saving the `last_url` was enough to persist state.
  - **Lesson:** Modern Single Page Applications (SPAs) like Twitter use heavy JavaScript to render modals and state changes *without* changing the URL. If the browser context is closed, the SPA resets to the base URL state on the next launch, losing all in-memory UI changes (like an open signup modal). For complex SPAs, a long-running persistent daemon or websocket connection is required rather than isolated atomic CLI scripts.

## Advanced Browser Automation
- **Improvement (Interactive Reading Mode):** Relying on raw DOM selectors (CSS/XPath) for AI agents is brittle and verbose.
  - **Lesson:** Implementing an "Interactive Mode" read script that maps all clickable/typable elements to a simple numerical index (e.g., `[1] Button: "Submit"`) drastically reduces AI hallucination and simplifies the interaction loop. Agents can just use `--index 1` instead of struggling to write complex Playwright selectors.
- **Improvement (Auto-Screenshots on Failure):** When automation fails headlessly, it is often a black box.
  - **Lesson:** Wrapping command handlers in a decorator that automatically captures a screenshot on exceptions (`auto_screenshot_on_error`) provides vital context for debugging broken selectors or unexpected popups.
- **Improvement (Comprehensive Environment Management):** Browsers require managing more than just clicks and reads.
  - **Lesson:** A robust browser agent should natively support `tabs`, `iframes`, `dialogs`, `cookies`, `hover`, and `keyboard` shortcuts to accurately replicate human behavior on complex websites.
