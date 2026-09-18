import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const ROOT_DIR = path.resolve(__dirname, '../..');
const DIYA_DATA_DIR = path.join(ROOT_DIR, 'diya', 'data');
const MEMORY_PROGRESS = path.join(ROOT_DIR, 'memory', 'progress.json');
const STRATEGY_FILE = path.join(ROOT_DIR, 'Learner Profile & Strategy.md');
const TARGET_DATA_DIR = path.join(ROOT_DIR, 'frontend', 'public', 'data');

console.log('[sync-data] Synchronizing static data to frontend/public/data...');

function copyDirSync(src, dest) {
  if (!fs.existsSync(src)) return;
  fs.mkdirSync(dest, { recursive: true });
  const entries = fs.readdirSync(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    if (entry.isDirectory()) {
      copyDirSync(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

// 1. Copy all data files
copyDirSync(DIYA_DATA_DIR, TARGET_DATA_DIR);

// 2. Generate profile.json for static consumption
try {
  let student = {};
  let learning_strategy = {};
  if (fs.existsSync(MEMORY_PROGRESS)) {
    const prog = JSON.parse(fs.readFileSync(MEMORY_PROGRESS, 'utf-8'));
    student = prog.student || {};
    learning_strategy = prog.learning_strategy || {};
  }

  let stratContent = '';
  if (fs.existsSync(STRATEGY_FILE)) {
    stratContent = fs.readFileSync(STRATEGY_FILE, 'utf-8');
  }

  const profileData = {
    name: student.name || 'Student',
    pronouns: 'He/Him',
    gender: student.gender || 'Male',
    diya_instructions: learning_strategy.approach || 'Immersion first, grammar consolidation second',
    notes: stratContent,
    target: student.target || 'A0 to A2 Conversational Fluency',
    primary_goal: student.primary_goal || 'Reunion trip with Shivani in Norwich, UK'
  };

  fs.writeFileSync(path.join(TARGET_DATA_DIR, 'profile.json'), JSON.stringify(profileData, null, 2), 'utf-8');
  console.log('[sync-data] Generated profile.json');
} catch (e) {
  console.warn('[sync-data] Warning: Could not generate profile.json', e.message);
}

// 3. Generate static status.json
const statusData = {
  app: 'DIYA Hindi Hub',
  version: '1.0.0',
  anki_connected: false,
  mode: 'cloud',
  time: new Date().toISOString()
};
fs.writeFileSync(path.join(TARGET_DATA_DIR, 'status.json'), JSON.stringify(statusData, null, 2), 'utf-8');

console.log('[sync-data] Successfully synchronized data for static distribution.');
