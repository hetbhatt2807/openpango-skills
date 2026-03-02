#!/bin/bash
# Self-Improvement Activator Hook
# Triggers on UserPromptSubmit to remind Claude about learning capture
# Keep output minimal (~50-100 tokens) to minimize overhead

set -e

# Output reminder as system context
# Detect learnings directory (OpenClaw workspace or local project)
if [ -d "${HOME}/.openclaw/workspace/.learnings" ]; then
    LEARNINGS_DIR="~/.openclaw/workspace/.learnings"
elif [ -d ".learnings" ]; then
    LEARNINGS_DIR=".learnings"
else
    LEARNINGS_DIR=".learnings"
fi

cat << EOF
<self-improvement-reminder>
After completing this task, evaluate if extractable knowledge emerged:
- Non-obvious solution discovered through investigation?
- Workaround for unexpected behavior?
- Project-specific pattern learned?
- Error required debugging to resolve?

If yes: Log to ${LEARNINGS_DIR}/ using the self-improvement skill format.
If high-value (recurring, broadly applicable): Consider promotion to SOUL.md, AGENTS.md, or TOOLS.md.
</self-improvement-reminder>
EOF
