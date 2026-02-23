// electron/src/main/index.ts

import { app, BrowserWindow, ipcMain } from 'electron';
import { join } from 'path';
import Store from 'electron-store';
import { PythonBridge } from './python-bridge.js';
import type { PythonMessage, DevicesResponse } from '../shared/types.js';

let mainWindow: BrowserWindow | null = null;
const isDev = process.env.NODE_ENV === 'development';
const store = new Store();
const pythonBridge = new PythonBridge();

/**
 * Create the main application window.
 */
function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 600,
    height: 700,
    minWidth: 500,
    minHeight: 600,
    title: 'Zoom S2S Translator',
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
    show: false,
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// ── IPC Handlers ─────────────────────────────────────

async function ensurePython(): Promise<void> {
  if (!pythonBridge.isRunning) {
    await pythonBridge.start();
  }
}

ipcMain.handle('devices:get', async (): Promise<DevicesResponse> => {
  await ensurePython();
  const resp = await pythonBridge.sendAndWait({ cmd: 'list_devices' }, 'devices');
  return {
    microphones: resp.inputs.map((d) => ({ id: String(d.index), name: d.name, kind: 'audioinput' as const })),
    speakers: resp.outputs.map((d) => ({ id: String(d.index), name: d.name, kind: 'audiooutput' as const })),
  };
});

ipcMain.handle('translation:start', async (_event, config) => {
  await ensurePython();
  // Wait for Python to confirm Gemini connection before returning to renderer
  await pythonBridge.sendAndWait({
    cmd: 'start',
    mode: config.mode ?? 'upstream',
    target: config.targetLang,
    mic_index: config.micDevice ? Number(config.micDevice) : null,
    speaker_index: config.speakerDevice ? Number(config.speakerDevice) : null,
    blackhole_index: null,
    segment: 5,
  }, 'started', 15_000);
});

ipcMain.handle('translation:stop', async () => {
  try {
    if (pythonBridge.isRunning) {
      pythonBridge.send({ cmd: 'stop' });
    }
  } catch {
    // Process may have exited between isRunning check and send
  }
});

ipcMain.handle('settings:get', () => {
  return store.store;
});

ipcMain.handle('settings:set', (_event, settings) => {
  for (const [key, value] of Object.entries(settings)) {
    store.set(key, value);
  }
});

// Forward Python status/error messages to the renderer
pythonBridge.on('message', (msg: PythonMessage) => {
  if (!mainWindow) return;

  if (msg.type === 'status') {
    mainWindow.webContents.send('translation:status', {
      isActive: true,
      chunksSent: msg.chunks_sent,
      chunksReceived: msg.chunks_received,
      chunksPlayed: msg.chunks_played,
      backlog: msg.backlog,
    });
  } else if (msg.type === 'stopped') {
    mainWindow.webContents.send('translation:status', {
      isActive: false,
      chunksSent: msg.chunks_sent,
      chunksReceived: msg.chunks_received,
      chunksPlayed: msg.chunks_played,
      backlog: 0,
    });
  } else if (msg.type === 'error') {
    mainWindow.webContents.send('error', {
      code: 'PYTHON_ERROR',
      message: msg.message,
      timestamp: Date.now(),
    });
  }
});

// ── App Lifecycle ─────────────────────────────────────

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Properly await async cleanup before quitting
let isQuitting = false;
app.on('before-quit', (event) => {
  if (isQuitting || !pythonBridge.isRunning) return;
  event.preventDefault();
  isQuitting = true;
  pythonBridge.stop().finally(() => {
    app.quit();
  });
});

/**
 * Security: Prevent navigation to external URLs
 */
app.on('web-contents-created', (_, contents) => {
  contents.on('will-navigate', (event, navigationUrl) => {
    const parsedUrl = new URL(navigationUrl);
    if (isDev && parsedUrl.origin === 'http://localhost:5173') {
      return;
    }
    event.preventDefault();
  });
});
