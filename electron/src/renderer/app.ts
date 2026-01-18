// electron/src/renderer/app.ts

/**
 * Renderer process main application logic.
 * Handles UI interactions and communication with main process.
 */

// Type guard to ensure electronAPI is available
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
  refreshDevices: document.getElementById('refreshDevices')!,
  incomingStatus: document.getElementById('incomingStatus')!,
  outgoingStatus: document.getElementById('outgoingStatus')!,
  latencyValue: document.getElementById('latencyValue')!,
  startButton: document.getElementById('startButton') as HTMLButtonElement,
  stopButton: document.getElementById('stopButton') as HTMLButtonElement,
};

// Application state
let isTranslating = false;

/**
 * Initialize the application
 */
async function initialize(): Promise<void> {
  try {
    // Load audio devices
    await loadDevices();

    // Load saved settings
    await loadSettings();

    // Set up event listeners
    setupEventListeners();

    // Subscribe to status updates
    electronAPI.onStatusUpdate(handleStatusUpdate);

    // Subscribe to errors
    electronAPI.onError(handleError);

    console.log('Application initialized successfully');
  } catch (error) {
    console.error('Failed to initialize application:', error);
    showError('Failed to initialize application');
  }
}

/**
 * Load available audio devices
 */
async function loadDevices(): Promise<void> {
  try {
    const devices = await electronAPI.getDevices();

    // Populate microphone dropdown
    elements.micDevice.innerHTML = devices.microphones
      .map(
        (device) =>
          `<option value="${device.id}">${device.name}</option>`
      )
      .join('');

    // Populate speaker dropdown
    elements.speakerDevice.innerHTML = devices.speakers
      .map(
        (device) =>
          `<option value="${device.id}">${device.name}</option>`
      )
      .join('');

    if (devices.microphones.length === 0) {
      elements.micDevice.innerHTML =
        '<option value="">No microphones found</option>';
    }

    if (devices.speakers.length === 0) {
      elements.speakerDevice.innerHTML =
        '<option value="">No speakers found</option>';
    }
  } catch (error) {
    console.error('Failed to load devices:', error);
    elements.micDevice.innerHTML = '<option value="">Error loading devices</option>';
    elements.speakerDevice.innerHTML = '<option value="">Error loading devices</option>';
  }
}

/**
 * Load saved settings
 */
async function loadSettings(): Promise<void> {
  try {
    const settings = await electronAPI.getSettings();

    if (settings.sourceLang) {
      elements.sourceLang.value = settings.sourceLang as string;
    }
    if (settings.targetLang) {
      elements.targetLang.value = settings.targetLang as string;
    }
    if (settings.micDevice) {
      elements.micDevice.value = settings.micDevice as string;
    }
    if (settings.speakerDevice) {
      elements.speakerDevice.value = settings.speakerDevice as string;
    }
  } catch (error) {
    console.error('Failed to load settings:', error);
  }
}

/**
 * Save current settings
 */
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

/**
 * Set up UI event listeners
 */
function setupEventListeners(): void {
  // Start translation
  elements.startButton.addEventListener('click', handleStart);

  // Stop translation
  elements.stopButton.addEventListener('click', handleStop);

  // Refresh devices
  elements.refreshDevices.addEventListener('click', loadDevices);

  // Save settings on change
  elements.sourceLang.addEventListener('change', saveSettings);
  elements.targetLang.addEventListener('change', saveSettings);
  elements.micDevice.addEventListener('change', saveSettings);
  elements.speakerDevice.addEventListener('change', saveSettings);
}

/**
 * Handle start translation button click
 */
async function handleStart(): Promise<void> {
  if (isTranslating) {
    return;
  }

  try {
    // Validate configuration
    if (!elements.micDevice.value || !elements.speakerDevice.value) {
      showError('Please select audio devices');
      return;
    }

    // Disable start button
    elements.startButton.disabled = true;
    elements.statusText.textContent = 'Starting...';

    // Start translation
    await electronAPI.startTranslation({
      sourceLang: elements.sourceLang.value,
      targetLang: elements.targetLang.value,
      micDevice: elements.micDevice.value,
      speakerDevice: elements.speakerDevice.value,
    });

    // Update UI state
    isTranslating = true;
    elements.stopButton.disabled = false;
    elements.statusIndicator.classList.add('active');
    elements.statusText.textContent = 'Translating';

    // Disable config changes during translation
    setConfigEnabled(false);
  } catch (error) {
    console.error('Failed to start translation:', error);
    showError('Failed to start translation');
    elements.startButton.disabled = false;
    elements.statusText.textContent = 'Idle';
  }
}

/**
 * Handle stop translation button click
 */
async function handleStop(): Promise<void> {
  if (!isTranslating) {
    return;
  }

  try {
    elements.stopButton.disabled = true;
    elements.statusText.textContent = 'Stopping...';

    await electronAPI.stopTranslation();

    // Update UI state
    isTranslating = false;
    elements.startButton.disabled = false;
    elements.statusIndicator.classList.remove('active');
    elements.statusText.textContent = 'Idle';

    // Reset status displays
    elements.incomingStatus.textContent = '--';
    elements.outgoingStatus.textContent = '--';
    elements.latencyValue.textContent = '-- ms';

    // Re-enable config changes
    setConfigEnabled(true);
  } catch (error) {
    console.error('Failed to stop translation:', error);
    showError('Failed to stop translation');
    elements.stopButton.disabled = false;
  }
}

/**
 * Handle translation status updates
 */
function handleStatusUpdate(status: {
  isActive: boolean;
  incoming: { connected: boolean; latency: number };
  outgoing: { connected: boolean; latency: number };
}): void {
  // Update incoming status
  elements.incomingStatus.textContent = status.incoming.connected
    ? 'Connected'
    : 'Disconnected';

  // Update outgoing status
  elements.outgoingStatus.textContent = status.outgoing.connected
    ? 'Connected'
    : 'Disconnected';

  // Update latency (average of incoming and outgoing)
  const avgLatency = Math.round(
    (status.incoming.latency + status.outgoing.latency) / 2
  );
  elements.latencyValue.textContent = `${avgLatency} ms`;
}

/**
 * Handle error events
 */
function handleError(error: { code: string; message: string }): void {
  console.error('Application error:', error);
  showError(error.message);
}

/**
 * Show error message to user
 */
function showError(message: string): void {
  // TODO: Implement proper error notification UI
  alert(`Error: ${message}`);
}

/**
 * Enable or disable configuration controls
 */
function setConfigEnabled(enabled: boolean): void {
  elements.sourceLang.disabled = !enabled;
  elements.targetLang.disabled = !enabled;
  elements.micDevice.disabled = !enabled;
  elements.speakerDevice.disabled = !enabled;
  elements.refreshDevices.disabled = !enabled;
}

// Initialize the application when DOM is ready
initialize();
