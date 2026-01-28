# Project Overview: SeleniumBase Profile Manager

## Project Name
**Celebium** - Professional Browser Profile Manager with SeleniumBase Integration

## Vision
Build a Windows desktop application that manages multiple browser profiles with advanced fingerprinting and stealth capabilities, powered by SeleniumBase UC/CDP Mode for undetectable automation.

## Core Value Proposition
- **Profile Management**: Create unlimited browser profiles with unique fingerprints
- **Stealth Automation**: SeleniumBase UC Mode bypasses bot detection (Cloudflare, DataDome, etc.)
- **Local API**: REST API for automation tool integration (Puppeteer, Playwright, Selenium)
- **No Cloud Dependency**: Everything runs locally, full data privacy

## Target Users
1. **Automation Developers** - Need multiple browser profiles for testing/scraping
2. **QA Engineers** - Test websites with different browser configurations
3. **Social Media Managers** - Manage multiple accounts safely
4. **E-commerce Professionals** - Monitor competitor prices, test checkouts
5. **Web Scrapers** - Extract data without getting blocked

## Key Differentiators vs Competitors

### vs Undetectable Browser
- ✅ **Better Stealth**: SeleniumBase UC/CDP Mode (proven against Cloudflare)
- ✅ **Built-in CAPTCHA Solving**: `sb.solve_captcha()` works automatically
- ✅ **Open Source Core**: SeleniumBase is open source, auditable
- ✅ **Lower Price**: $29/mo vs Undetectable's $49/mo

### vs MultiLogin/GoLogin
- ✅ **Local First**: No cloud dependency, faster
- ✅ **Developer Friendly**: Clean REST API, not proprietary SDK
- ✅ **Python Native**: Full SeleniumBase ecosystem access

## Technical Architecture

```
┌─────────────────────────────────────────────────────┐
│                 Electron Desktop App                │
│  ┌─────────────────────────────────────────────┐   │
│  │          React Frontend (Renderer)          │   │
│  │  - Profile List View                        │   │
│  │  - Profile Create/Edit Forms                │   │
│  │  - Proxy Manager                            │   │
│  │  - Settings Panel                           │   │
│  └─────────────────────────────────────────────┘   │
│                        ↓ IPC/HTTP                   │
│  ┌─────────────────────────────────────────────┐   │
│  │      Node.js Main Process (Electron)        │   │
│  │  - Spawns Python Server                     │   │
│  │  - Window Management                        │   │
│  │  - System Tray Integration                  │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                         ↓ HTTP (localhost:25325)
┌─────────────────────────────────────────────────────┐
│              Python FastAPI Server                  │
│  ┌─────────────────────────────────────────────┐   │
│  │           REST API Endpoints                │   │
│  │  - Profile CRUD                             │   │
│  │  - Browser Start/Stop                       │   │
│  │  - Proxy Management                         │   │
│  └─────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────┐   │
│  │      SeleniumBase Manager                   │   │
│  │  - UC Mode Launch                           │   │
│  │  - CDP Mode Control                         │   │
│  │  - Fingerprint Injection                    │   │
│  └─────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────┐   │
│  │          SQLite Database                    │   │
│  │  - Profile Storage                          │   │
│  │  - Proxy List                               │   │
│  │  - Config Templates                         │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│         Chrome Browsers (UC Mode)                   │
│  Profile 1 (PID:1234, Port:9222)                   │
│  Profile 2 (PID:5678, Port:9223)                   │
│  Profile 3 (PID:9012, Port:9224)                   │
└─────────────────────────────────────────────────────┘
```

## Tech Stack

### Frontend (Electron App)
- **Framework**: Electron 28+
- **UI Library**: React 18 with TypeScript
- **State Management**: Zustand (lightweight)
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Build Tool**: Vite

### Backend (Python Server)
- **Web Framework**: FastAPI 0.110+
- **Database**: SQLite3 (via SQLAlchemy 2.0)
- **Automation**: SeleniumBase 4.26+
- **Data Validation**: Pydantic v2
- **Process Management**: psutil
- **Async**: asyncio + uvicorn

### Development Tools
- **Python Version**: 3.10+
- **Node Version**: 18 LTS
- **Package Managers**: npm (frontend), pip (backend)
- **Version Control**: Git
- **Code Quality**: ESLint, Black, mypy

## Project Structure

```
celebium/
├── electron-app/               # Electron frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Page views
│   │   ├── services/          # API client
│   │   ├── store/             # State management
│   │   ├── App.tsx            # Root component
│   │   └── main.ts            # Electron main process
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── python-server/              # FastAPI backend
│   ├── app/
│   │   ├── api/               # API routes
│   │   ├── core/              # Config, database
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   │   ├── selenium_manager.py
│   │   │   ├── profile_service.py
│   │   │   └── proxy_service.py
│   │   └── main.py            # FastAPI app
│   ├── tests/
│   ├── requirements.txt
│   └── pyproject.toml
│
├── database/                   # SQLite files
│   └── celebium.db
│
├── profiles/                   # Chrome profile data
│   ├── profile_abc123/
│   └── profile_def456/
│
├── docs/                       # Documentation
│   ├── api.md                 # API documentation
│   ├── architecture.md
│   └── user-guide.md
│
├── build/                      # Build artifacts
│   ├── python/                # PyInstaller output
│   └── electron/              # Electron builder output
│
└── plan/                       # This folder
    ├── 01-project-overview.md
    ├── 02-database-schema.md
    └── ...
```

## Development Phases

### Phase 1: MVP Backend (Week 1-2)
- FastAPI server with basic endpoints
- SQLite database with profile storage
- SeleniumBase integration (launch profiles)
- Profile CRUD operations

### Phase 2: MVP Frontend (Week 2-3)
- Electron app skeleton
- Profile list view
- Create/edit profile forms
- Start/stop profile controls

### Phase 3: Advanced Features (Week 3-4)
- Fingerprint override system
- Proxy manager UI
- Cookie import/export
- Profile folders/tags

### Phase 4: Polish & Package (Week 4-5)
- Error handling and logging
- Settings panel
- Build Windows installer
- User documentation

### Phase 5: Testing & Launch (Week 5-6)
- Test against protected sites (Cloudflare, etc.)
- Performance optimization
- Beta testing
- Public release

## Success Metrics

### Technical KPIs
- Profile launch time: < 5 seconds
- API response time: < 200ms
- Memory per profile: < 500MB
- Concurrent profiles: 10+ without performance degradation

### Product KPIs
- Bot detection bypass rate: > 95%
- User retention (30 days): > 60%
- Profile creation time: < 2 minutes
- App crash rate: < 0.1%

## Pricing Strategy (Future)

### Free Tier
- 3 profiles
- Basic fingerprints
- Community support

### Pro - $29/month
- Unlimited profiles
- Advanced fingerprints
- Priority support
- Auto-updates

### Team - $99/month
- Everything in Pro
- 5 team seats
- Profile sharing
- API access

## Risk Assessment

### Technical Risks
1. **Bot Detection Evolution** - Sites constantly update detection
   - Mitigation: Regular SeleniumBase updates, community feedback

2. **Profile Corruption** - Chrome profile data can get corrupted
   - Mitigation: Backup system, profile validation

3. **Performance Issues** - Running many browsers uses resources
   - Mitigation: Resource monitoring, warnings, optimization

### Business Risks
1. **Legal Gray Area** - TOS violations on some sites
   - Mitigation: Clear legal disclaimer, focus on legitimate use cases

2. **Competition** - Established players (MultiLogin, GoLogin)
   - Mitigation: Better tech (SeleniumBase), lower price, superior UX

## Next Steps
1. Review all 10 plan documents
2. Set up development environment
3. Create Git repository
4. Start Phase 1: Backend MVP
