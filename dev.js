const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const FRONTEND_PORT = 3005;
const BACKEND_PORT = 8011;
const args = process.argv.slice(2);
const isProd = args.includes('--prod');
const allowKill = args.includes('--kill');

if (args.includes('--help')) {
  console.log('Usage: bun dev [-- --prod] [-- --kill] [-- --check]\n\nStarts the backend API and frontend. --prod starts frontend production server. --kill stops processes already listening on ports 3005 and 8011 first. --check verifies local prerequisites without starting servers.');
  process.exit(0);
}
const checkOnly = args.includes('--check');

function runPowerShell(command) {
  return execSync(`powershell -NoProfile -Command "${command}"`, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
}

function portPids(port) {
  try {
    const output = runPowerShell(`Get-NetTCPConnection -LocalPort ${port} -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -gt 0 } | Select-Object -ExpandProperty OwningProcess -Unique`);
    return output.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  } catch {
    return [];
  }
}

function assertPortAvailable(port) {
  const pids = portPids(port);
  if (!pids.length) return;
  if (!allowKill) {
    console.error(`Port ${port} is already in use by PID(s): ${pids.join(', ')}. Close them, or rerun with --kill to stop those local processes.`);
    process.exit(1);
  }
  for (const pid of pids) {
    try {
      runPowerShell(`Stop-Process -Id ${pid} -Force`);
      console.log(`Stopped PID ${pid} on port ${port}`);
    } catch (error) {
      console.error(`Failed to stop PID ${pid} on port ${port}: ${error.message}`);
      process.exit(1);
    }
  }
}

function hasBun() {
  try {
    execSync('bun --version', { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
}

function frontendCommand() {
  if (hasBun()) return { command: 'bun', args: ['run', isProd ? 'start' : 'dev'] };
  return { command: 'npm', args: ['run', isProd ? 'start' : 'dev'] };
}

function pythonCommand() {
  const venv = path.join('.', '.venv', 'Scripts', 'python.exe');
  return fs.existsSync(venv) ? venv : 'python';
}

function prefixStream(stream, label) {
  let buffer = '';
  stream.on('data', (chunk) => {
    buffer += chunk.toString();
    const lines = buffer.split(/\r?\n/);
    buffer = lines.pop() ?? '';
    for (const line of lines) console.log(`[${label}] ${line}`);
  });
  stream.on('end', () => {
    if (buffer) console.log(`[${label}] ${buffer}`);
  });
}

const frontendPkg = path.join('frontend', 'package.json');
const frontendModules = path.join('frontend', 'node_modules');
if (!fs.existsSync(frontendPkg)) {
  console.error('Missing frontend/package.json. Run this from the repository root.');
  process.exit(1);
}
if (!fs.existsSync(frontendModules)) {
  console.error("Frontend dependencies are not installed. Run: Set-Location frontend; bun install; Set-Location ..");
  process.exit(1);
}

if (checkOnly) {
  const frontend = frontendCommand();
  const python = pythonCommand();
  console.log(`frontend command: ${frontend.command} ${frontend.args.join(' ')}`);
  console.log(`backend command: ${python} -m uvicorn supplyndemand.main:app --app-dir backend/src --host 127.0.0.1 --port ${BACKEND_PORT}`);
  for (const port of [BACKEND_PORT, FRONTEND_PORT]) {
    const pids = portPids(port);
    console.log(pids.length ? `port ${port} busy: PID(s) ${pids.join(', ')}` : `port ${port} available`);
  }
  process.exit(0);
}

assertPortAvailable(BACKEND_PORT);
assertPortAvailable(FRONTEND_PORT);

const frontend = frontendCommand();
const python = pythonCommand();
const children = [];

children.push(spawn(frontend.command, frontend.args, { cwd: 'frontend', env: process.env, stdio: ['inherit', 'pipe', 'pipe'] }));
children.push(spawn(python, ['-m', 'uvicorn', 'supplyndemand.main:app', '--app-dir', 'backend/src', '--host', '127.0.0.1', '--port', String(BACKEND_PORT)], {
  cwd: '.',
  env: { ...process.env, PYTHONUNBUFFERED: '1' },
  stdio: ['inherit', 'pipe', 'pipe'],
}));

prefixStream(children[0].stdout, 'frontend');
prefixStream(children[0].stderr, 'frontend');
prefixStream(children[1].stdout, 'backend');
prefixStream(children[1].stderr, 'backend');

let shuttingDown = false;
function shutdown(code) {
  if (shuttingDown) return;
  shuttingDown = true;
  for (const child of children) {
    if (!child.killed) child.kill();
  }
  setTimeout(() => process.exit(code), 1000).unref();
}

process.on('SIGINT', () => shutdown(0));
process.on('SIGTERM', () => shutdown(0));

for (const [index, child] of children.entries()) {
  child.on('exit', (code, signal) => {
    if (shuttingDown) return;
    const label = index === 0 ? 'frontend' : 'backend';
    console.error(`[${label}] exited with code ${code ?? 'null'} signal ${signal ?? 'null'}`);
    shutdown(code || 1);
  });
}
