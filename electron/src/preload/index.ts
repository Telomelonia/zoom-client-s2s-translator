// electron/src/preload/index.ts

import { contextBridge, ipcRenderer } from 'electron';

/**
 * Preload script that exposes a safe API to the renderer process.
 * Uses contextBridge to isolate the main and renderer processes.
 */

/**
 * IPC channel names for type-safe communication
 */
const IPC_CHANNELS = {
  // Translation control
  START_TRANSLATION: 'translation:start',
  STOP_TRANSLATION: 'translation:stop',
  TRANSLATION_STATUS: 'translation:status',

  // Device management
  GET_DEVICES: 'devices:get',
  DEVICES_RESPONSE: 'devices:response',

  // Settings
  GET_SETTINGS: 'settings:get',
  SET_SETTINGS: 'settings:set',

  // Errors
  ERROR: 'error',
} as const;

/**
 * Type definitions for IPC messages
 */
export interface TranslationConfig {
  sourceLang: string;
  targetLang: string;
  micDevice: string;
  speakerDevice: string;
}

export interface TranslationStatus {
  isActive: boolean;
  incoming: {
    connected: boolean;
    latency: number;
  };
  outgoing: {
    connected: boolean;
    latency: number;
  };
}

export interface AudioDevice {
  id: string;
  name: string;
  kind: 'audioinput' | 'audiooutput';
}

export interface DevicesResponse {
  microphones: AudioDevice[];
  speakers: AudioDevice[];
}

export interface AppError {
  code: string;
  message: string;
  timestamp: number;
}

/**
 * API exposed to renderer process via window.electronAPI
 */
const electronAPI = {
  /**
   * Start translation with the specified configuration
   */
  startTranslation: (config: TranslationConfig): Promise<void> => {
    return ipcRenderer.invoke(IPC_CHANNELS.START_TRANSLATION, config);
  },

  /**
   * Stop the active translation session
   */
  stopTranslation: (): Promise<void> => {
    return ipcRenderer.invoke(IPC_CHANNELS.STOP_TRANSLATION);
  },

  /**
   * Get available audio devices
   */
  getDevices: (): Promise<DevicesResponse> => {
    return ipcRenderer.invoke(IPC_CHANNELS.GET_DEVICES);
  },

  /**
   * Subscribe to translation status updates
   */
  onStatusUpdate: (
    callback: (status: TranslationStatus) => void
  ): (() => void) => {
    const subscription = (_event: unknown, status: TranslationStatus) =>
      callback(status);
    ipcRenderer.on(IPC_CHANNELS.TRANSLATION_STATUS, subscription);

    // Return unsubscribe function
    return () => {
      ipcRenderer.removeListener(IPC_CHANNELS.TRANSLATION_STATUS, subscription);
    };
  },

  /**
   * Subscribe to error events
   */
  onError: (callback: (error: AppError) => void): (() => void) => {
    const subscription = (_event: unknown, error: AppError) => callback(error);
    ipcRenderer.on(IPC_CHANNELS.ERROR, subscription);

    // Return unsubscribe function
    return () => {
      ipcRenderer.removeListener(IPC_CHANNELS.ERROR, subscription);
    };
  },

  /**
   * Get application settings
   */
  getSettings: (): Promise<Record<string, unknown>> => {
    return ipcRenderer.invoke(IPC_CHANNELS.GET_SETTINGS);
  },

  /**
   * Save application settings
   */
  setSettings: (settings: Record<string, unknown>): Promise<void> => {
    return ipcRenderer.invoke(IPC_CHANNELS.SET_SETTINGS, settings);
  },
};

/**
 * Expose the API to the renderer process
 */
contextBridge.exposeInMainWorld('electronAPI', electronAPI);

/**
 * TypeScript declaration for the exposed API
 * This will be used by the renderer process for type checking
 */
declare global {
  interface Window {
    electronAPI: typeof electronAPI;
  }
}
