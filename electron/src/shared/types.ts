// electron/src/shared/types.ts

/**
 * Shared type definitions used across main, renderer, and preload processes.
 */

/**
 * Translation configuration passed from renderer to main
 */
export interface TranslationConfig {
  sourceLang: string;
  targetLang: string;
  micDevice: string;
  speakerDevice: string;
}

/**
 * Translation status information sent from main to renderer
 */
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

/**
 * Audio device information
 */
export interface AudioDevice {
  id: string;
  name: string;
  kind: 'audioinput' | 'audiooutput';
}

/**
 * Device list response
 */
export interface DevicesResponse {
  microphones: AudioDevice[];
  speakers: AudioDevice[];
}

/**
 * Application error
 */
export interface AppError {
  code: string;
  message: string;
  timestamp: number;
}

/**
 * Application settings
 */
export interface AppSettings {
  sourceLang?: string;
  targetLang?: string;
  micDevice?: string;
  speakerDevice?: string;
  windowBounds?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

/**
 * Supported language codes
 */
export const SUPPORTED_LANGUAGES = [
  'en', // English
  'ja', // Japanese
  'es', // Spanish
  'fr', // French
  'de', // German
  'cmn', // Mandarin Chinese
  'ko', // Korean
  'hi', // Hindi
  'ar', // Arabic
  'pt', // Portuguese
] as const;

export type LanguageCode = (typeof SUPPORTED_LANGUAGES)[number];

/**
 * Language metadata
 */
export interface Language {
  code: LanguageCode;
  name: string;
  nativeName: string;
}

/**
 * Full language list with metadata
 */
export const LANGUAGES: readonly Language[] = [
  { code: 'en', name: 'English', nativeName: 'English' },
  { code: 'ja', name: 'Japanese', nativeName: '日本語' },
  { code: 'es', name: 'Spanish', nativeName: 'Español' },
  { code: 'fr', name: 'French', nativeName: 'Français' },
  { code: 'de', name: 'German', nativeName: 'Deutsch' },
  { code: 'cmn', name: 'Mandarin Chinese', nativeName: '中文' },
  { code: 'ko', name: 'Korean', nativeName: '한국어' },
  { code: 'hi', name: 'Hindi', nativeName: 'हिन्दी' },
  { code: 'ar', name: 'Arabic', nativeName: 'العربية' },
  { code: 'pt', name: 'Portuguese', nativeName: 'Português' },
] as const;
