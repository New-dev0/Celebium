# Build & Packaging

## Distribution Architecture

```
Celebium-Setup.exe (Windows Installer)
  │
  ├── Electron App
  │   ├── celebium.exe (Main executable)
  │   ├── resources/
  │   │   ├── app.asar (Bundled frontend)
  │   │   └── server/ (Python server)
  │   │       ├── server.exe (PyInstaller bundle)
  │   │       └── _internal/ (Dependencies)
  │   └── node_modules/ (If needed)
  │
  ├── Database
  │   └── celebium.db (Created on first run)
  │
  └── Profiles
      └── (Created dynamically)
```

---

## Python Backend Packaging

### PyInstaller Configuration

**File: `python-server/celebium.spec`**

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include SeleniumBase drivers
        ('venv/Lib/site-packages/seleniumbase/drivers', 'seleniumbase/drivers'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'seleniumbase',
        'selenium',
        'psutil',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Set to False to hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # Optional
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='server',
)
```

### Build Python Server

```bash
cd python-server

# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller celebium.spec

# Output: dist/server/server.exe + dependencies
```

**Result:**
```
dist/server/
├── server.exe         (30MB)
└── _internal/         (150MB - all dependencies)
    ├── python3.dll
    ├── seleniumbase/
    ├── fastapi/
    └── ...
```

---

## Electron Frontend Packaging

### Electron Builder Configuration

**File: `electron-app/electron-builder.yml`**

```yaml
appId: com.celebium.app
productName: Celebium
copyright: Copyright © 2024 Celebium

directories:
  output: dist
  buildResources: resources

files:
  - dist/**/*
  - node_modules/**/*
  - package.json

extraResources:
  - from: ../../python-server/dist/server
    to: server
    filter:
      - "**/*"

win:
  target:
    - target: nsis
      arch:
        - x64
  icon: resources/icon.ico
  artifactName: ${productName}-Setup-${version}.${ext}

nsis:
  oneClick: false
  allowToChangeInstallationDirectory: true
  createDesktopShortcut: true
  createStartMenuShortcut: true
  shortcutName: Celebium
  installerIcon: resources/icon.ico
  uninstallerIcon: resources/icon.ico
  license: LICENSE.txt

mac:
  target:
    - dmg
  icon: resources/icon.icns
  category: public.app-category.developer-tools

linux:
  target:
    - AppImage
  icon: resources/icon.png
  category: Development
```

### Package.json Scripts

```json
{
  "name": "celebium",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "vite build && tsc -p tsconfig.main.json",
    "package": "npm run build && electron-builder",
    "package:win": "npm run build && electron-builder --win",
    "package:mac": "npm run build && electron-builder --mac",
    "package:linux": "npm run build && electron-builder --linux"
  }
}
```

---

## Complete Build Process

### 1. Build Python Server

```bash
cd python-server

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build
pyinstaller celebium.spec

# Output: dist/server/
```

### 2. Build Electron App

```bash
cd electron-app

# Install dependencies
npm install

# Build React frontend
npm run build

# Package Electron app (includes Python server)
npm run package:win
```

### 3. Test Before Distribution

```bash
# Test Python server standalone
cd python-server/dist/server
./server.exe

# Test Electron app
cd electron-app/dist/win-unpacked
./Celebium.exe
```

---

## Installer Details

### NSIS Installer Features

```ini
[NSIS Configuration]

# Installation
- Choose install directory
- Add to Start Menu
- Create Desktop shortcut
- Auto-start on Windows startup (optional)

# Components
- Main application (required)
- Desktop shortcut (optional)
- Start menu shortcut (optional)

# Post-Install
- Run Celebium (checkbox)
- Open documentation (checkbox)

# Uninstaller
- Remove all files
- Remove shortcuts
- Remove registry entries
- Keep user data (optional checkbox)
```

### Custom NSIS Script

**File: `electron-app/build/installer.nsi`**

```nsis
!macro customInstall
  # Create profiles directory
  CreateDirectory "$INSTDIR\profiles"
  CreateDirectory "$INSTDIR\database"

  # Set permissions
  AccessControl::GrantOnFile "$INSTDIR\database" "(S-1-5-32-545)" "FullAccess"
!macroend

!macro customUnInstall
  # Ask to keep user data
  MessageBox MB_YESNO "Do you want to keep your profiles and data?" IDYES KeepData
    RMDir /r "$INSTDIR\profiles"
    RMDir /r "$INSTDIR\database"
  KeepData:
!macroend
```

---

## Auto-Update System

### electron-updater Configuration

**File: `electron-app/src/main/updater.ts`**

```typescript
import { autoUpdater } from 'electron-updater';
import { dialog } from 'electron';

export function initAutoUpdater() {
  // Check for updates on startup (production only)
  if (!app.isPackaged) return;

  autoUpdater.checkForUpdatesAndNotify();

  autoUpdater.on('update-available', (info) => {
    dialog.showMessageBox({
      type: 'info',
      title: 'Update Available',
      message: `A new version ${info.version} is available. Do you want to download it now?`,
      buttons: ['Download', 'Later'],
    }).then((result) => {
      if (result.response === 0) {
        autoUpdater.downloadUpdate();
      }
    });
  });

  autoUpdater.on('update-downloaded', () => {
    dialog.showMessageBox({
      type: 'info',
      title: 'Update Ready',
      message: 'Update downloaded. The app will restart to install.',
      buttons: ['Restart'],
    }).then(() => {
      autoUpdater.quitAndInstall();
    });
  });
}
```

**Update Server:**
- Host `latest.yml` and installers on GitHub Releases
- Or use custom server (S3, CDN)

---

## CI/CD Pipeline (GitHub Actions)

**File: `.github/workflows/build.yml`**

```yaml
name: Build & Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build-python:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          cd python-server
          pip install -r requirements.txt
          pip install pyinstaller

      - name: Build server
        run: |
          cd python-server
          pyinstaller celebium.spec

      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: python-server
          path: python-server/dist/server

  build-electron:
    needs: build-python
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Download Python server
        uses: actions/download-artifact@v3
        with:
          name: python-server
          path: electron-app/resources/server

      - name: Install dependencies
        run: |
          cd electron-app
          npm install

      - name: Build & Package
        run: |
          cd electron-app
          npm run package:win

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            electron-app/dist/*.exe
            electron-app/dist/*.yml
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## File Sizes

**Expected sizes:**
- Python server.exe: ~30MB
- Python _internal/: ~150MB
- Electron app (unpacked): ~250MB
- **Final installer**: ~180MB (compressed)

---

## Code Signing (Optional)

### Windows Code Signing

```bash
# Get code signing certificate (DigiCert, Sectigo)

# Sign Python exe
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com python-server/dist/server/server.exe

# Sign Electron exe (electron-builder does this automatically)
```

**Add to `electron-builder.yml`:**
```yaml
win:
  certificateFile: cert.pfx
  certificatePassword: ${env.CERT_PASSWORD}
  signDlls: true
```

---

## Testing Checklist

- [ ] Python server starts independently
- [ ] Electron app launches Python server
- [ ] API endpoints work
- [ ] SeleniumBase launches browsers
- [ ] Profiles persist after restart
- [ ] Uninstaller removes files correctly
- [ ] Auto-update works (if enabled)
- [ ] No antivirus false positives
- [ ] Works on clean Windows 10/11 install
- [ ] File size < 200MB

## Next: See `09-development-roadmap.md` for timeline and milestones
