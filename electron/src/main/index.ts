// electron/src/main/index.ts

import { app, BrowserWindow } from 'electron';
import { join } from 'path';

/**
 * Main process entry point for the Zoom S2S Translator application.
 * Handles window creation and lifecycle management.
 */

let mainWindow: BrowserWindow | null = null;

const isDev = process.env.NODE_ENV === 'development';

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
    show: false, // Don't show until ready-to-show event
  });

  // Show window when ready to prevent visual flash
  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();
  });

  // Load the renderer
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'));
  }

  // Cleanup on window close
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

/**
 * App lifecycle: ready
 */
app.whenReady().then(() => {
  createWindow();

  // macOS: Re-create window when dock icon is clicked
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

/**
 * App lifecycle: all windows closed
 */
app.on('window-all-closed', () => {
  // macOS: Keep app running until explicit quit
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

/**
 * App lifecycle: before quit
 */
app.on('before-quit', () => {
  // TODO: Cleanup Python subprocess
  // TODO: Stop any active translation sessions
});

/**
 * Security: Prevent navigation to external URLs
 */
app.on('web-contents-created', (_, contents) => {
  contents.on('will-navigate', (event, navigationUrl) => {
    const parsedUrl = new URL(navigationUrl);

    // Only allow localhost in development
    if (isDev && parsedUrl.origin === 'http://localhost:5173') {
      return;
    }

    // Prevent all other navigation
    event.preventDefault();
  });
});
