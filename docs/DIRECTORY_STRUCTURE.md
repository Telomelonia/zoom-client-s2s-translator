# Project Directory Structure

**Generated:** 2026-01-18
**Phase:** 1 Complete

This document shows the complete directory structure created for the Zoom S2S Translator project.

## Complete Tree

```
zoom-client-s2s-translator/
│
├── .env.example                      # Environment variable template
├── .gitignore                        # Git exclusions (updated)
├── CLAUDE.md                         # Project intelligence
├── README.md                         # Project overview
├── README.dev.md                     # Development guide (new)
│
├── docs/
│   ├── ARCHITECTURE.md               # System architecture
│   ├── DIRECTORY_STRUCTURE.md        # This file
│   ├── PHASE1_COMPLETION.md          # Phase 1 completion report
│   ├── PROJECT_STATUS.md             # Progress tracking (updated)
│   └── SPEC.md                       # Full specification
│
├── electron/                         # Electron frontend (new)
│   ├── .eslintrc.json               # ESLint configuration
│   ├── .prettierrc.json             # Prettier configuration
│   ├── .prettierignore              # Prettier exclusions
│   ├── electron-builder.yml         # Packaging configuration
│   ├── package.json                 # Dependencies and scripts
│   ├── tsconfig.json                # TypeScript configuration
│   ├── vite.config.ts               # Build configuration
│   │
│   └── src/
│       ├── main/                    # Main process
│       │   └── index.ts             # Entry point, window management
│       │
│       ├── preload/                 # Preload script
│       │   └── index.ts             # IPC bridge, security isolation
│       │
│       ├── renderer/                # Renderer process
│       │   ├── index.html           # UI markup
│       │   ├── app.ts               # UI logic
│       │   └── styles.css           # Styling
│       │
│       └── shared/                  # Shared code
│           └── types.ts             # Type definitions
│
├── python/                          # Python backend (new)
│   ├── pyproject.toml              # Build config, linting, formatting
│   ├── requirements.txt            # Dependencies
│   │
│   ├── src/
│   │   ├── __init__.py             # Package init
│   │   ├── main.py                 # Entry point, async event loop
│   │   │
│   │   ├── audio/                  # Audio processing module
│   │   │   └── __init__.py         # Audio constants
│   │   │
│   │   ├── gemini/                 # Gemini API integration
│   │   │   └── __init__.py         # API constants
│   │   │
│   │   └── routing/                # Audio routing
│   │       └── __init__.py         # Routing logic (placeholder)
│   │
│   └── tests/                      # Test suite
│       └── __init__.py             # Test package init
│
└── scripts/                        # Development scripts (new)
    ├── dev.sh                      # Start development environment
    └── install-blackhole.sh        # Install virtual audio driver
```

## Directory Purposes

### Root Level
- **`.env.example`** - Template for environment variables (credentials, configuration)
- **`.gitignore`** - Specifies files to exclude from version control
- **`CLAUDE.md`** - Project standards, conventions, and AI assistant guidelines
- **`README.md`** - High-level project overview and introduction
- **`README.dev.md`** - Comprehensive development setup and workflow guide

### docs/
Contains all project documentation:
- **`ARCHITECTURE.md`** - System design, component relationships, data flow
- **`DIRECTORY_STRUCTURE.md`** - This file, showing project organization
- **`PHASE1_COMPLETION.md`** - Detailed completion report for Phase 1
- **`PROJECT_STATUS.md`** - Current progress, active tasks, decision log
- **`SPEC.md`** - Complete specification with MVP definition and all phases

### electron/
Electron application (desktop UI):
- **Configuration files** - TypeScript, ESLint, Prettier, Vite, electron-builder
- **`src/main/`** - Main process (Node.js), manages windows and app lifecycle
- **`src/preload/`** - Security bridge between main and renderer processes
- **`src/renderer/`** - UI code (HTML, CSS, TypeScript) running in browser context
- **`src/shared/`** - Type definitions and constants used across processes

### python/
Python backend (audio processing and API integration):
- **Configuration files** - pyproject.toml (build, linting), requirements.txt
- **`src/`** - Main source code with modular structure
  - **`main.py`** - Application entry point
  - **`audio/`** - Audio capture, processing, and output
  - **`gemini/`** - Vertex AI Gemini S2ST API client
  - **`routing/`** - Audio routing between devices
- **`tests/`** - pytest test suite

### scripts/
Development automation:
- **`dev.sh`** - One-command development environment setup
- **`install-blackhole.sh`** - macOS virtual audio driver installation

## File Counts by Category

### Source Code
- **TypeScript files:** 5 (main, preload, renderer app, renderer types, vite config)
- **HTML files:** 1 (renderer UI)
- **CSS files:** 1 (renderer styles)
- **Python files:** 7 (main + 3 modules + 3 __init__)
- **Total source:** 14 files

### Configuration
- **TypeScript/JS config:** 5 (package.json, tsconfig, vite, electron-builder, eslint, prettier)
- **Python config:** 2 (requirements.txt, pyproject.toml)
- **Environment:** 1 (.env.example)
- **Git:** 1 (.gitignore)
- **Total config:** 9 files

### Documentation
- **Project docs:** 5 (CLAUDE.md, README.md, README.dev.md, ARCHITECTURE.md, SPEC.md)
- **Phase tracking:** 3 (PROJECT_STATUS.md, PHASE1_COMPLETION.md, DIRECTORY_STRUCTURE.md)
- **Total docs:** 8 files

### Scripts
- **Development scripts:** 2 (dev.sh, install-blackhole.sh)

### Grand Total
**31 files** created or updated in Phase 1

## Notable Patterns

### Separation of Concerns
- **Main process** - Window management, system integration
- **Preload** - Security boundary, IPC API
- **Renderer** - UI logic, user interactions
- **Python modules** - Audio, API, routing clearly separated

### Type Safety
- Shared TypeScript types in `electron/src/shared/types.ts`
- Python type hints in all modules
- Strict configuration in both languages

### Configuration as Code
- All settings in version-controlled files
- No manual setup required beyond `.env`
- Reproducible builds across machines

### Clean Architecture
- Dependencies point inward (shared <- main/preload/renderer)
- No circular dependencies
- Clear module boundaries

## Dependencies Flow

```
electron/src/main/       ─┐
                          ├──> electron/src/shared/
electron/src/preload/    ─┤
                          │
electron/src/renderer/   ─┘

python/src/audio/        ─┐
                          │
python/src/gemini/       ─┼──> (Independent modules)
                          │
python/src/routing/      ─┘
```

## Phase 1 vs Future Phases

### Phase 1 (Complete) ✅
- All directory structure
- All configuration files
- Skeleton source files with TODO markers
- Development scripts
- Documentation

### Phase 2 (Audio Pipeline)
Will add:
- `python/src/audio/capture.py`
- `python/src/audio/playback.py`
- `python/src/audio/devices.py`
- Audio processing utilities

### Phase 3 (UI & Integration)
Will add:
- `electron/src/main/ipc.ts` (IPC handlers)
- `electron/src/main/python-manager.ts` (subprocess)
- `electron/src/renderer/components/` (UI components)
- IPC message handlers

### Phase 4 (Polish & Packaging)
Will add:
- `electron/build/` (app icons, installers)
- `python-dist/` (bundled Python runtime)
- CI/CD configuration
- User documentation

---

**Last Updated:** 2026-01-18
**Phase:** 1 Complete
**Next:** Phase 2 - Audio Pipeline Implementation
