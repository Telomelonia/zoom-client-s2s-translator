// electron/src/preload/index.ts

import { contextBridge, ipcRenderer } from 'electron';
import type {
  TranslationConfig,
  TranslationStatus,
  DevicesResponse,
  AppError,
} from '../shared/types.js';

const IPC_CHANNELS = {
  START_TRANSLATION: 'translation:start',
  STOP_TRANSLATION: 'translation:stop',
  TRANSLATION_STATUS: 'translation:status',
  GET_DEVICES: 'devices:get',
  GET_SETTINGS: 'settings:get',
  SET_SETTINGS: 'settings:set',
  ERROR: 'error',
} as const;

const electronAPI = {
  startTranslation: (config: TranslationConfig): Promise<void> => {
    return ipcRenderer.invoke(IPC_CHANNELS.START_TRANSLATION, config);
  },

  stopTranslation: (): Promise<void> => {
    return ipcRenderer.invoke(IPC_CHANNELS.STOP_TRANSLATION);
  },

  getDevices: (): Promise<DevicesResponse> => {
    return ipcRenderer.invoke(IPC_CHANNELS.GET_DEVICES);
  },

  onStatusUpdate: (
    callback: (status: TranslationStatus) => void
  ): (() => void) => {
    const subscription = (_event: unknown, status: TranslationStatus) =>
      callback(status);
    ipcRenderer.on(IPC_CHANNELS.TRANSLATION_STATUS, subscription);
    return () => {
      ipcRenderer.removeListener(IPC_CHANNELS.TRANSLATION_STATUS, subscription);
    };
  },

  onError: (callback: (error: AppError) => void): (() => void) => {
    const subscription = (_event: unknown, error: AppError) => callback(error);
    ipcRenderer.on(IPC_CHANNELS.ERROR, subscription);
    return () => {
      ipcRenderer.removeListener(IPC_CHANNELS.ERROR, subscription);
    };
  },

  getSettings: (): Promise<Record<string, unknown>> => {
    return ipcRenderer.invoke(IPC_CHANNELS.GET_SETTINGS);
  },

  setSettings: (settings: Record<string, unknown>): Promise<void> => {
    return ipcRenderer.invoke(IPC_CHANNELS.SET_SETTINGS, settings);
  },
};

contextBridge.exposeInMainWorld('electronAPI', electronAPI);

declare global {
  interface Window {
    electronAPI: typeof electronAPI;
  }
}
