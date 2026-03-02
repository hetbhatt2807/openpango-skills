const fs = require('fs');
const path = require('path');
const os = require('os');

const OPENCLAW_DIR = path.join(os.homedir(), '.openclaw');
const WORKSPACE_DIR = path.join(OPENCLAW_DIR, 'workspace');
const LEARNINGS_DIR = path.join(WORKSPACE_DIR, '.learnings');

const initWorkspace = () => {
  if (!fs.existsSync(OPENCLAW_DIR)) {
    fs.mkdirSync(OPENCLAW_DIR, { recursive: true });
  }
  if (!fs.existsSync(WORKSPACE_DIR)) {
    fs.mkdirSync(WORKSPACE_DIR, { recursive: true });
  }
  if (!fs.existsSync(LEARNINGS_DIR)) {
    fs.mkdirSync(LEARNINGS_DIR, { recursive: true });
  }

  const agentsFile = path.join(WORKSPACE_DIR, 'AGENTS.md');
  const toolsFile = path.join(WORKSPACE_DIR, 'TOOLS.md');

  if (!fs.existsSync(agentsFile)) {
    fs.writeFileSync(agentsFile, '# Multi-skill coordination rules\n');
  }
  if (!fs.existsSync(toolsFile)) {
    fs.writeFileSync(toolsFile, '# Tool documentation for installed skills\n');
  }
};

module.exports = {
  initWorkspace
};