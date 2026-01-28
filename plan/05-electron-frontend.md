# Electron Frontend Architecture

## Project Structure

```
electron-app/
├── src/
│   ├── main/                    # Electron main process
│   │   ├── index.ts            # Main entry point
│   │   ├── window.ts           # Window management
│   │   ├── python-server.ts   # Python subprocess manager
│   │   ├── ipc-handlers.ts    # IPC event handlers
│   │   └── tray.ts            # System tray
│   │
│   ├── renderer/               # React frontend
│   │   ├── src/
│   │   │   ├── components/    # React components
│   │   │   │   ├── ProfileList.tsx
│   │   │   │   ├── ProfileForm.tsx
│   │   │   │   ├── ProxyManager.tsx
│   │   │   │   └── Settings.tsx
│   │   │   │
│   │   │   ├── pages/         # Page views
│   │   │   │   ├── HomePage.tsx
│   │   │   │   ├── ProfilesPage.tsx
│   │   │   │   └── SettingsPage.tsx
│   │   │   │
│   │   │   ├── services/      # API client
│   │   │   │   └── api.ts
│   │   │   │
│   │   │   ├── store/         # State management (Zustand)
│   │   │   │   ├── profileStore.ts
│   │   │   │   └── appStore.ts
│   │   │   │
│   │   │   ├── types/         # TypeScript types
│   │   │   │   └── index.ts
│   │   │   │
│   │   │   ├── App.tsx        # Root component
│   │   │   └── main.tsx       # React entry
│   │   │
│   │   ├── index.html
│   │   └── vite.config.ts
│   │
│   └── preload/               # Preload scripts
│       └── index.ts
│
├── resources/                  # App icons, assets
│   ├── icon.png
│   └── icon.ico
│
├── package.json
├── tsconfig.json
└── electron-builder.yml       # Build configuration
```

---

## Main Process (Electron)

### Main Entry Point

**File: `src/main/index.ts`**

```typescript
import { app, BrowserWindow } from 'electron';
import path from 'path';
import { startPythonServer, stopPythonServer } from './python-server';
import { createMainWindow } from './window';
import { createTray } from './tray';
import './ipc-handlers';

let mainWindow: BrowserWindow | null = null;

// Prevent multiple instances
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(async () => {
    console.log('🚀 Starting Celebium...');

    try {
      // Start Python server
      await startPythonServer();
      console.log('✅ Python server started');

      // Wait 2 seconds for server to initialize
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Create main window
      mainWindow = createMainWindow();

      // Create system tray
      createTray(mainWindow);

      console.log('✅ Celebium ready');

    } catch (error) {
      console.error('❌ Failed to start Celebium:', error);
      app.quit();
    }
  });

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
      app.quit();
    }
  });

  app.on('before-quit', async () => {
    console.log('🛑 Stopping Celebium...');

    // Stop Python server
    await stopPythonServer();
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      mainWindow = createMainWindow();
    }
  });
}
```

---

### Python Server Manager

**File: `src/main/python-server.ts`**

```typescript
import { spawn, ChildProcess } from 'child_process';
import path from 'path';
import axios from 'axios';
import { app } from 'electron';

let pythonProcess: ChildProcess | null = null;
const API_PORT = 25325;
const API_URL = `http://127.0.0.1:${API_PORT}`;

export async function startPythonServer(): Promise<void> {
  return new Promise((resolve, reject) => {
    // Determine Python executable path
    const isDev = !app.isPackaged;

    let pythonPath: string;
    let serverScript: string;

    if (isDev) {
      // Development mode: use python from PATH
      pythonPath = 'python';
      serverScript = path.join(__dirname, '../../../python-server/app/main.py');
    } else {
      // Production mode: use bundled server.exe
      pythonPath = path.join(process.resourcesPath, 'server', 'server.exe');
      serverScript = '';
    }

    // Spawn Python process
    const args = serverScript ? [serverScript] : [];

    pythonProcess = spawn(pythonPath, args, {
      cwd: isDev
        ? path.join(__dirname, '../../../python-server')
        : path.join(process.resourcesPath, 'server'),
      env: {
        ...process.env,
        API_PORT: API_PORT.toString(),
      },
    });

    // Handle stdout
    pythonProcess.stdout?.on('data', (data) => {
      console.log(`[Python] ${data}`);
    });

    // Handle stderr
    pythonProcess.stderr?.on('data', (data) => {
      console.error(`[Python Error] ${data}`);
    });

    // Handle process exit
    pythonProcess.on('close', (code) => {
      console.log(`[Python] Process exited with code ${code}`);
      pythonProcess = null;
    });

    // Wait for server to be ready
    waitForServer().then(resolve).catch(reject);
  });
}

export async function stopPythonServer(): Promise<void> {
  if (!pythonProcess) return;

  try {
    // Try graceful shutdown first
    await axios.get(`${API_URL}/close`, { timeout: 2000 });
  } catch {
    // Force kill if graceful shutdown fails
    pythonProcess.kill();
  }

  pythonProcess = null;
}

async function waitForServer(maxRetries = 30): Promise<void> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await axios.get(`${API_URL}/status`, {
        timeout: 1000,
      });

      if (response.data.code === 0) {
        return; // Server is ready
      }
    } catch {
      // Server not ready yet, wait 1 second
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
  }

  throw new Error('Python server failed to start');
}

export function isPythonServerRunning(): boolean {
  return pythonProcess !== null;
}
```

---

### Window Management

**File: `src/main/window.ts`**

```typescript
import { BrowserWindow, shell } from 'electron';
import path from 'path';

export function createMainWindow(): BrowserWindow {
  const window = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    title: 'Celebium',
    icon: path.join(__dirname, '../../resources/icon.png'),
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    autoHideMenuBar: true,
  });

  // Load app
  if (process.env.NODE_ENV === 'development') {
    window.loadURL('http://localhost:5173');
    window.webContents.openDevTools();
  } else {
    window.loadFile(path.join(__dirname, '../renderer/index.html'));
  }

  // Open external links in browser
  window.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  return window;
}
```

---

### System Tray

**File: `src/main/tray.ts`**

```typescript
import { Tray, Menu, BrowserWindow, app } from 'electron';
import path from 'path';

let tray: Tray | null = null;

export function createTray(mainWindow: BrowserWindow): Tray {
  const iconPath = path.join(__dirname, '../../resources/icon.png');

  tray = new Tray(iconPath);

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show Celebium',
      click: () => {
        mainWindow.show();
      },
    },
    {
      label: 'Hide Celebium',
      click: () => {
        mainWindow.hide();
      },
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        app.quit();
      },
    },
  ]);

  tray.setToolTip('Celebium - Profile Manager');
  tray.setContextMenu(contextMenu);

  tray.on('click', () => {
    if (mainWindow.isVisible()) {
      mainWindow.hide();
    } else {
      mainWindow.show();
    }
  });

  return tray;
}
```

---

## Renderer Process (React)

### API Client

**File: `src/renderer/src/services/api.ts`**

```typescript
import axios from 'axios';

const API_URL = 'http://127.0.0.1:25325';

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
});

export interface Profile {
  id: string;
  name: string;
  folder: string;
  tags: string[];
  os: string;
  browser: string;
  user_agent: string;
  screen_resolution: string;
  language: string;
  status: string;
  debug_port?: number;
  websocket_url?: string;
  created_at: string;
}

export interface ProfileCreate {
  name: string;
  folder?: string;
  tags?: string[];
  os: string;
  browser: string;
  user_agent: string;
  screen_resolution: string;
  language: string;
  cpu_cores?: number;
  memory_gb?: number;
  proxy_string?: string;
}

// System
export const checkStatus = () => api.get('/status');

// Profiles
export const listProfiles = () => api.get<{ code: number; data: Record<string, any> }>('/list');

export const getProfile = (id: string) => api.get(`/profile/getinfo/${id}`);

export const createProfile = (data: ProfileCreate) =>
  api.post('/profile/create', data);

export const updateProfile = (id: string, data: Partial<ProfileCreate>) =>
  api.post(`/profile/update/${id}`, data);

export const deleteProfile = (id: string) => api.get(`/profile/delete/${id}`);

export const startProfile = (id: string) => api.get(`/profile/start/${id}`);

export const stopProfile = (id: string) => api.get(`/profile/stop/${id}`);

// Proxies
export const listProxies = () => api.get('/proxies/list');

export const addProxy = (data: {
  name: string;
  type: string;
  host: string;
  port: number;
  username?: string;
  password?: string;
}) => api.post('/proxies/add', data);

export const deleteProxy = (id: string) => api.get(`/proxies/delete/${id}`);
```

---

### State Management (Zustand)

**File: `src/renderer/src/store/profileStore.ts`**

```typescript
import { create } from 'zustand';
import { Profile } from '../services/api';

interface ProfileState {
  profiles: Profile[];
  selectedProfile: Profile | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setProfiles: (profiles: Profile[]) => void;
  setSelectedProfile: (profile: Profile | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useProfileStore = create<ProfileState>((set) => ({
  profiles: [],
  selectedProfile: null,
  isLoading: false,
  error: null,

  setProfiles: (profiles) => set({ profiles }),
  setSelectedProfile: (profile) => set({ selectedProfile: profile }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
}));
```

---

### Main App Component

**File: `src/renderer/src/App.tsx`**

```tsx
import { useState, useEffect } from 'react';
import { ProfilesPage } from './pages/ProfilesPage';
import { SettingsPage } from './pages/SettingsPage';
import { checkStatus } from './services/api';

export default function App() {
  const [currentPage, setCurrentPage] = useState('profiles');
  const [isServerReady, setIsServerReady] = useState(false);

  useEffect(() => {
    // Check if server is running
    checkStatus()
      .then(() => setIsServerReady(true))
      .catch(() => setIsServerReady(false));
  }, []);

  if (!isServerReady) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900 text-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-lg">Starting Celebium...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-800 border-r border-gray-700">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-blue-400">Celebium</h1>
          <p className="text-sm text-gray-400">Profile Manager</p>
        </div>

        <nav className="mt-6">
          <button
            onClick={() => setCurrentPage('profiles')}
            className={`w-full px-6 py-3 text-left hover:bg-gray-700 transition ${
              currentPage === 'profiles' ? 'bg-gray-700 border-l-4 border-blue-500' : ''
            }`}
          >
            🗂️ Profiles
          </button>

          <button
            onClick={() => setCurrentPage('proxies')}
            className={`w-full px-6 py-3 text-left hover:bg-gray-700 transition ${
              currentPage === 'proxies' ? 'bg-gray-700 border-l-4 border-blue-500' : ''
            }`}
          >
            🌐 Proxies
          </button>

          <button
            onClick={() => setCurrentPage('settings')}
            className={`w-full px-6 py-3 text-left hover:bg-gray-700 transition ${
              currentPage === 'settings' ? 'bg-gray-700 border-l-4 border-blue-500' : ''
            }`}
          >
            ⚙️ Settings
          </button>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {currentPage === 'profiles' && <ProfilesPage />}
        {currentPage === 'settings' && <SettingsPage />}
      </main>
    </div>
  );
}
```

---

### Profile List Component

**File: `src/renderer/src/components/ProfileList.tsx`**

```tsx
import { useEffect, useState } from 'react';
import { listProfiles, startProfile, stopProfile } from '../services/api';
import { useProfileStore } from '../store/profileStore';

export function ProfileList() {
  const { profiles, setProfiles, setLoading } = useProfileStore();
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    loadProfiles();
  }, [refreshKey]);

  const loadProfiles = async () => {
    setLoading(true);
    try {
      const response = await listProfiles();
      const profilesArray = Object.entries(response.data.data).map(([id, data]: [string, any]) => ({
        id,
        ...data,
      }));
      setProfiles(profilesArray);
    } catch (error) {
      console.error('Failed to load profiles:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async (profileId: string) => {
    try {
      await startProfile(profileId);
      setRefreshKey((k) => k + 1); // Refresh list
    } catch (error) {
      console.error('Failed to start profile:', error);
    }
  };

  const handleStop = async (profileId: string) => {
    try {
      await stopProfile(profileId);
      setRefreshKey((k) => k + 1);
    } catch (error) {
      console.error('Failed to stop profile:', error);
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Profiles</h2>
        <button
          onClick={() => setRefreshKey((k) => k + 1)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition"
        >
          🔄 Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {profiles.map((profile) => (
          <div
            key={profile.id}
            className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-blue-500 transition"
          >
            <h3 className="text-lg font-semibold mb-2">{profile.name}</h3>

            <div className="space-y-1 text-sm text-gray-400 mb-4">
              <p>📁 {profile.folder}</p>
              <p>💻 {profile.browser}</p>
              <p>
                Status:{' '}
                <span
                  className={
                    profile.status === 'running'
                      ? 'text-green-400'
                      : 'text-gray-400'
                  }
                >
                  {profile.status}
                </span>
              </p>
            </div>

            <div className="flex gap-2">
              {profile.status !== 'running' ? (
                <button
                  onClick={() => handleStart(profile.id)}
                  className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 rounded transition"
                >
                  ▶️ Start
                </button>
              ) : (
                <button
                  onClick={() => handleStop(profile.id)}
                  className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 rounded transition"
                >
                  ⏹️ Stop
                </button>
              )}

              <button className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded transition">
                ✏️
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## Package.json

```json
{
  "name": "celebium",
  "version": "1.0.0",
  "main": "dist/main/index.js",
  "scripts": {
    "dev": "vite",
    "build": "vite build && electron-builder",
    "start": "electron ."
  },
  "dependencies": {
    "axios": "^1.6.7",
    "zustand": "^4.5.0"
  },
  "devDependencies": {
    "@types/node": "^20.11.16",
    "@vitejs/plugin-react": "^4.2.1",
    "electron": "^28.2.1",
    "electron-builder": "^24.9.1",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "tailwindcss": "^3.4.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.12"
  }
}
```

## Next: See `06-ui-ux-design.md` for component details and styling
