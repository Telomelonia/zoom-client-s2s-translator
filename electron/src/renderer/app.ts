// electron/src/renderer/app.ts

/**
 * Renderer process main application logic.
 * Handles UI interactions and communication with main process.
 */

if (!window.electronAPI) {
  throw new Error('electronAPI is not available');
}

const { electronAPI } = window;

// DOM Elements
const elements = {
  statusIndicator: document.getElementById('statusIndicator')!,
  statusText: document.querySelector('.status-text')!,
  sourceLang: document.getElementById('sourceLang') as HTMLSelectElement,
  targetLang: document.getElementById('targetLang') as HTMLSelectElement,
  micDevice: document.getElementById('micDevice') as HTMLSelectElement,
  speakerDevice: document.getElementById('speakerDevice') as HTMLSelectElement,
  refreshDevices: document.getElementById('refreshDevices') as HTMLButtonElement,
  incomingStatus: document.getElementById('incomingStatus')!,
  outgoingStatus: document.getElementById('outgoingStatus')!,
  latencyValue: document.getElementById('latencyValue')!,
  startButton: document.getElementById('startButton') as HTMLButtonElement,
  stopButton: document.getElementById('stopButton') as HTMLButtonElement,
};

let isTranslating = false;

// ── Error Banner ──────────────────────────────────────

let errorBanner: HTMLDivElement | null = null;

function showError(message: string): void {
  // Remove existing banner
  if (errorBanner) {
    errorBanner.remove();
  }

  errorBanner = document.createElement('div');
  errorBanner.className = 'error-banner';

  const msgSpan = document.createElement('span');
  msgSpan.textContent = message;
  errorBanner.appendChild(msgSpan);

  const dismissBtn = document.createElement('button');
  dismissBtn.className = 'error-dismiss';
  dismissBtn.textContent = '\u00d7';
  dismissBtn.addEventListener('click', () => {
    errorBanner?.remove();
    errorBanner = null;
  });
  errorBanner.appendChild(dismissBtn);

  // Insert at top of main
  const main = document.querySelector('main')!;
  main.insertBefore(errorBanner, main.firstChild);

  // Auto-dismiss after 8 seconds
  setTimeout(() => {
    errorBanner?.remove();
    errorBanner = null;
  }, 8000);
}

// ── Init ──────────────────────────────────────────────

async function initialize(): Promise<void> {
  try {
    await loadDevices();
    await loadSettings();
    setupEventListeners();
    electronAPI.onStatusUpdate(handleStatusUpdate);
    electronAPI.onError(handleError);
    console.log('Application initialized successfully');
  } catch (error) {
    console.error('Failed to initialize application:', error);
    showError('Failed to initialize application');
  }
}

async function loadDevices(): Promise<void> {
  try {
    const devices = await electronAPI.getDevices();

    elements.micDevice.innerHTML = devices.microphones
      .map((d) => `<option value="${d.id}">${d.name}</option>`)
      .join('');

    elements.speakerDevice.innerHTML = devices.speakers
      .map((d) => `<option value="${d.id}">${d.name}</option>`)
      .join('');

    if (devices.microphones.length === 0) {
      elements.micDevice.innerHTML = '<option value="">No microphones found</option>';
    }
    if (devices.speakers.length === 0) {
      elements.speakerDevice.innerHTML = '<option value="">No speakers found</option>';
    }
  } catch (error) {
    console.error('Failed to load devices:', error);
    elements.micDevice.innerHTML = '<option value="">Error loading devices</option>';
    elements.speakerDevice.innerHTML = '<option value="">Error loading devices</option>';
  }
}

async function loadSettings(): Promise<void> {
  try {
    const settings = await electronAPI.getSettings();
    if (settings.sourceLang) elements.sourceLang.value = settings.sourceLang as string;
    if (settings.targetLang) elements.targetLang.value = settings.targetLang as string;
    if (settings.micDevice) elements.micDevice.value = settings.micDevice as string;
    if (settings.speakerDevice) elements.speakerDevice.value = settings.speakerDevice as string;
  } catch (error) {
    console.error('Failed to load settings:', error);
  }
}

async function saveSettings(): Promise<void> {
  try {
    await electronAPI.setSettings({
      sourceLang: elements.sourceLang.value,
      targetLang: elements.targetLang.value,
      micDevice: elements.micDevice.value,
      speakerDevice: elements.speakerDevice.value,
    });
  } catch (error) {
    console.error('Failed to save settings:', error);
  }
}

function setupEventListeners(): void {
  elements.startButton.addEventListener('click', handleStart);
  elements.stopButton.addEventListener('click', handleStop);
  elements.refreshDevices.addEventListener('click', loadDevices);
  elements.sourceLang.addEventListener('change', saveSettings);
  elements.targetLang.addEventListener('change', saveSettings);
  elements.micDevice.addEventListener('change', saveSettings);
  elements.speakerDevice.addEventListener('change', saveSettings);
}

// ── Translation Controls ──────────────────────────────

async function handleStart(): Promise<void> {
  if (isTranslating) return;

  try {
    if (!elements.micDevice.value || !elements.speakerDevice.value) {
      showError('Please select audio devices');
      return;
    }

    elements.startButton.disabled = true;
    elements.statusText.textContent = 'Starting...';

    await electronAPI.startTranslation({
      mode: 'upstream',
      sourceLang: elements.sourceLang.value,
      targetLang: elements.targetLang.value,
      micDevice: elements.micDevice.value,
      speakerDevice: elements.speakerDevice.value,
    });

    isTranslating = true;
    elements.stopButton.disabled = false;
    elements.statusIndicator.classList.add('active');
    elements.statusText.textContent = 'Translating';
    setConfigEnabled(false);
  } catch (error) {
    console.error('Failed to start translation:', error);
    showError('Failed to start translation');
    elements.startButton.disabled = false;
    elements.statusText.textContent = 'Idle';
  }
}

async function handleStop(): Promise<void> {
  if (!isTranslating) return;

  try {
    elements.stopButton.disabled = true;
    elements.statusText.textContent = 'Stopping...';

    await electronAPI.stopTranslation();

    isTranslating = false;
    elements.startButton.disabled = false;
    elements.statusIndicator.classList.remove('active');
    elements.statusText.textContent = 'Idle';

    elements.incomingStatus.textContent = '--';
    elements.outgoingStatus.textContent = '--';
    elements.latencyValue.textContent = '--';

    setConfigEnabled(true);
  } catch (error) {
    console.error('Failed to stop translation:', error);
    showError('Failed to stop translation');
    elements.stopButton.disabled = false;
  }
}

// ── Status Updates ────────────────────────────────────

function handleStatusUpdate(status: {
  isActive: boolean;
  chunksSent: number;
  chunksReceived: number;
  chunksPlayed: number;
  backlog: number;
}): void {
  if (!status.isActive && isTranslating) {
    // Translation stopped from Python side
    isTranslating = false;
    elements.startButton.disabled = false;
    elements.stopButton.disabled = true;
    elements.statusIndicator.classList.remove('active');
    elements.statusText.textContent = 'Idle';
    setConfigEnabled(true);
  }

  elements.incomingStatus.textContent = `Sent: ${status.chunksSent}`;
  elements.outgoingStatus.textContent = `Recv: ${status.chunksReceived}`;
  elements.latencyValue.textContent = status.backlog > 0
    ? `Backlog: ${status.backlog}`
    : `Played: ${status.chunksPlayed}`;
}

function handleError(error: { code: string; message: string }): void {
  console.error('Application error:', error);
  showError(error.message);
}

function setConfigEnabled(enabled: boolean): void {
  elements.sourceLang.disabled = !enabled;
  elements.targetLang.disabled = !enabled;
  elements.micDevice.disabled = !enabled;
  elements.speakerDevice.disabled = !enabled;
  elements.refreshDevices.disabled = !enabled;
}

// Initialize the application when DOM is ready
initialize();
