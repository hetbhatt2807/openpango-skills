const fs = require('fs');
const path = require('path');
const os = require('os');
const readline = require('readline');
const { initWorkspace } = require('../shared/workspace');

const OPENCLAW_DIR = path.join(os.homedir(), '.openclaw');
const SKILLS_DIR = path.join(OPENCLAW_DIR, 'skills');
const LOCAL_SKILLS_DIR = path.join(__dirname, '..', 'skills');

const getAvailableSkills = () => {
  return fs.readdirSync(LOCAL_SKILLS_DIR).filter(file => {
    return fs.statSync(path.join(LOCAL_SKILLS_DIR, file)).isDirectory();
  });
};

const getInstalledSkills = () => {
  if (!fs.existsSync(SKILLS_DIR)) return [];
  return fs.readdirSync(SKILLS_DIR).filter(file => {
    return fs.existsSync(path.join(SKILLS_DIR, file, 'SKILL.md'));
  });
};

const installSkills = (skillsToInstall) => {
  if (!fs.existsSync(SKILLS_DIR)) {
    fs.mkdirSync(SKILLS_DIR, { recursive: true });
  }

  skillsToInstall.forEach(skill => {
    const srcDir = path.join(LOCAL_SKILLS_DIR, skill);
    const destDir = path.join(SKILLS_DIR, skill);

    if (!fs.existsSync(srcDir)) {
      console.error(`Skill '${skill}' not found.`);
      return;
    }

    if (!fs.existsSync(destDir)) {
      fs.symlinkSync(srcDir, destDir, 'dir');
      console.log(`Installed ${skill}`);
    } else {
      console.log(`Skill ${skill} is already installed.`);
    }
  });
};

const removeSkills = (skillsToRemove) => {
  skillsToRemove.forEach(skill => {
    const destDir = path.join(SKILLS_DIR, skill);
    if (fs.existsSync(destDir)) {
      fs.unlinkSync(destDir); // Assuming symlinks
      console.log(`Removed ${skill}`);
    } else {
      console.log(`Skill ${skill} is not installed.`);
    }
  });
};

const listSkills = () => {
  const available = getAvailableSkills();
  const installed = getInstalledSkills();

  console.log('Available skills:');
  available.forEach(skill => {
    const isInstalled = installed.includes(skill);
    console.log(`  ${isInstalled ? '[x]' : '[ ]'} ${skill}`);
  });
};

const status = () => {
  const installed = getInstalledSkills();
  console.log('Installed skills status:');
  if (installed.length === 0) {
    console.log('  No skills installed.');
    return;
  }
  installed.forEach(skill => {
    const destDir = path.join(SKILLS_DIR, skill);
    const isValid = fs.existsSync(path.join(destDir, 'SKILL.md'));
    console.log(`  - ${skill}: ${isValid ? 'OK' : 'Broken'}`);
  });
};

const interactiveInstall = async () => {
  const available = getAvailableSkills();
  const installed = getInstalledSkills();
  
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  const promptInstall = () => {
    return new Promise(resolve => {
      console.log('\nSelect skills to install (comma-separated numbers, e.g., 1,3):');
      available.forEach((skill, index) => {
        const isInstalled = installed.includes(skill);
        console.log(`  ${index + 1}. ${isInstalled ? '[Installed]' : '[ ]'} ${skill}`);
      });
      rl.question('\n> ', answer => {
        resolve(answer);
      });
    });
  };

  const answer = await promptInstall();
  rl.close();

  const selectedIndices = answer.split(',').map(s => parseInt(s.trim()) - 1).filter(i => !isNaN(i) && i >= 0 && i < available.length);
  const toInstall = selectedIndices.map(i => available[i]);

  if (toInstall.length > 0) {
    installSkills(toInstall);
  } else {
    console.log('No skills selected.');
  }
};

const run = async () => {
  const args = process.argv.slice(2);
  const command = args[0];

  switch (command) {
    case 'install':
      const skillsToInstall = args.slice(1);
      if (skillsToInstall.length > 0) {
        installSkills(skillsToInstall);
      } else {
        await interactiveInstall();
      }
      break;
    case 'remove':
      const skillsToRemove = args.slice(1);
      if (skillsToRemove.length > 0) {
        removeSkills(skillsToRemove);
      } else {
        console.log('Usage: openpango remove [skill...]');
      }
      break;
    case 'list':
      listSkills();
      break;
    case 'init':
      initWorkspace();
      console.log('Workspace initialized.');
      break;
    case 'status':
      status();
      break;
    default:
      console.log('Usage: openpango <command>\n\nCommands:\n  install [skill...]\n  remove [skill...]\n  list\n  init\n  status');
  }
};

run();