# UI/UX Design & Components

## Design System

### Color Palette

```css
/* Dark Theme (Primary) */
--bg-primary: #111827;    /* Gray 900 */
--bg-secondary: #1F2937;  /* Gray 800 */
--bg-tertiary: #374151;   /* Gray 700 */

--text-primary: #F9FAFB;  /* Gray 50 */
--text-secondary: #9CA3AF; /* Gray 400 */

--accent-blue: #3B82F6;   /* Blue 500 */
--accent-green: #10B981;  /* Green 500 */
--accent-red: #EF4444;    /* Red 500 */
--accent-yellow: #F59E0B; /* Yellow 500 */

--border: #374151;        /* Gray 700 */
```

### Typography

```css
/* Fonts */
font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;

/* Sizes */
--text-xs: 0.75rem;   /* 12px */
--text-sm: 0.875rem;  /* 14px */
--text-base: 1rem;    /* 16px */
--text-lg: 1.125rem;  /* 18px */
--text-xl: 1.25rem;   /* 20px */
--text-2xl: 1.5rem;   /* 24px */
--text-3xl: 1.875rem; /* 30px */
```

---

## Main Pages

### 1. Profiles Page

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│ Profiles                    [+ New] [⟳ Refresh]     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [Search profiles...]      [📁 All] [🏷️ Tags ▾]   │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Profile1 │  │ Profile2 │  │ Profile3 │        │
│  │ 📁 Work  │  │ 📁 Work  │  │ 📁 Personal│       │
│  │ 💻 Chrome│  │ 💻 Edge  │  │ 💻 Chrome│        │
│  │ 🟢 Running│ │ ⚪ Stopped│ │ ⚪ Stopped│       │
│  │          │  │          │  │          │        │
│  │ [⏹ Stop] │  │ [▶ Start]│  │ [▶ Start]│       │
│  │ [✏ Edit] │  │ [✏ Edit] │  │ [✏ Edit] │       │
│  └──────────┘  └──────────┘  └──────────┘        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Component: ProfileCard**

```tsx
interface ProfileCardProps {
  profile: Profile;
  onStart: () => void;
  onStop: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

export function ProfileCard({ profile, onStart, onStop, onEdit, onDelete }: ProfileCardProps) {
  const isRunning = profile.status === 'running';

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-blue-500 transition group">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-white mb-1">{profile.name}</h3>
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <span>📁 {profile.folder}</span>
            {profile.tags?.map(tag => (
              <span key={tag} className="px-2 py-0.5 bg-blue-900/50 rounded text-blue-400 text-xs">
                {tag}
              </span>
            ))}
          </div>
        </div>

        {/* Status Indicator */}
        <div className={`w-3 h-3 rounded-full ${
          isRunning ? 'bg-green-500' : 'bg-gray-600'
        }`} />
      </div>

      {/* Details */}
      <div className="space-y-1 text-sm text-gray-400 mb-4">
        <div className="flex items-center gap-2">
          <span>💻</span>
          <span>{profile.browser}</span>
        </div>
        <div className="flex items-center gap-2">
          <span>🖥️</span>
          <span>{profile.screen_resolution}</span>
        </div>
        <div className="flex items-center gap-2">
          <span>🌐</span>
          <span>{profile.proxy_string ? 'Proxy' : 'No Proxy'}</span>
        </div>
        {isRunning && (
          <div className="flex items-center gap-2 text-green-400">
            <span>🔗</span>
            <span>Port: {profile.debug_port}</span>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        {isRunning ? (
          <button
            onClick={onStop}
            className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition font-medium"
          >
            ⏹️ Stop
          </button>
        ) : (
          <button
            onClick={onStart}
            className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition font-medium"
          >
            ▶️ Start
          </button>
        )}

        <button
          onClick={onEdit}
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition"
        >
          ✏️
        </button>

        <button
          onClick={onDelete}
          className="px-4 py-2 bg-gray-700 hover:bg-red-700 rounded-lg transition"
        >
          🗑️
        </button>
      </div>

      {/* Hidden: Quick Actions (shown on hover) */}
      <div className="mt-3 pt-3 border-t border-gray-700 opacity-0 group-hover:opacity-100 transition">
        <div className="flex gap-2 text-xs">
          <button className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded">
            📋 Copy WS URL
          </button>
          <button className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded">
            🔄 Clear Cache
          </button>
        </div>
      </div>
    </div>
  );
}
```

---

### 2. Profile Creation Form

**Modal Dialog:**

```tsx
export function ProfileFormModal({ isOpen, onClose, onSave }: ProfileFormModalProps) {
  const [formData, setFormData] = useState<ProfileCreate>({
    name: '',
    folder: 'Default',
    os: 'Windows 10',
    browser: 'Chrome 120.0.0.0',
    user_agent: '',
    screen_resolution: '1920x1080',
    language: 'en-US,en;q=0.9',
    cpu_cores: 8,
    memory_gb: 8,
  });

  const [step, setStep] = useState(1); // Multi-step form

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg w-full max-w-2xl max-h-[90vh] overflow-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <h2 className="text-2xl font-bold">Create New Profile</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            ✕
          </button>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center gap-4 p-6 border-b border-gray-700">
          <Step number={1} label="Basic" active={step === 1} completed={step > 1} />
          <div className="w-12 h-0.5 bg-gray-700" />
          <Step number={2} label="Fingerprint" active={step === 2} completed={step > 2} />
          <div className="w-12 h-0.5 bg-gray-700" />
          <Step number={3} label="Proxy" active={step === 3} completed={step > 3} />
        </div>

        {/* Form Content */}
        <div className="p-6">
          {step === 1 && (
            <div className="space-y-4">
              <FormField label="Profile Name" required>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="My Profile"
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg focus:border-blue-500 focus:outline-none"
                />
              </FormField>

              <FormField label="Folder">
                <select
                  value={formData.folder}
                  onChange={(e) => setFormData({ ...formData, folder: e.target.value })}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg focus:border-blue-500 focus:outline-none"
                >
                  <option value="Default">Default</option>
                  <option value="Work">Work</option>
                  <option value="Personal">Personal</option>
                </select>
              </FormField>

              <FormField label="Tags">
                <input
                  type="text"
                  placeholder="tag1, tag2, tag3"
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg focus:border-blue-500 focus:outline-none"
                />
              </FormField>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <div className="p-4 bg-blue-900/20 border border-blue-800 rounded-lg mb-4">
                <p className="text-blue-400 text-sm">
                  💡 Use a fingerprint template or customize below
                </p>
              </div>

              <FormField label="Operating System">
                <select
                  value={formData.os}
                  onChange={(e) => setFormData({ ...formData, os: e.target.value })}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg"
                >
                  <option value="Windows 10">Windows 10</option>
                  <option value="Windows 11">Windows 11</option>
                  <option value="Mac OS X 14.7">Mac OS X 14.7</option>
                  <option value="Linux">Linux</option>
                </select>
              </FormField>

              <FormField label="Browser">
                <select
                  value={formData.browser}
                  onChange={(e) => setFormData({ ...formData, browser: e.target.value })}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg"
                >
                  <option value="Chrome 120.0.0.0">Chrome 120</option>
                  <option value="Chrome 119.0.0.0">Chrome 119</option>
                  <option value="Edge 120.0.0.0">Edge 120</option>
                </select>
              </FormField>

              <FormField label="Screen Resolution">
                <select
                  value={formData.screen_resolution}
                  onChange={(e) => setFormData({ ...formData, screen_resolution: e.target.value })}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg"
                >
                  <option value="1920x1080">1920x1080 (Full HD)</option>
                  <option value="1366x768">1366x768</option>
                  <option value="2560x1440">2560x1440 (2K)</option>
                  <option value="3840x2160">3840x2160 (4K)</option>
                </select>
              </FormField>

              <div className="grid grid-cols-2 gap-4">
                <FormField label="CPU Cores">
                  <input
                    type="number"
                    value={formData.cpu_cores}
                    onChange={(e) => setFormData({ ...formData, cpu_cores: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg"
                  />
                </FormField>

                <FormField label="Memory (GB)">
                  <input
                    type="number"
                    value={formData.memory_gb}
                    onChange={(e) => setFormData({ ...formData, memory_gb: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg"
                  />
                </FormField>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <FormField label="Proxy (Optional)">
                <input
                  type="text"
                  placeholder="socks5://user:pass@host:port"
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg"
                />
              </FormField>

              <button className="w-full py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition">
                📋 Select from Proxy Manager
              </button>

              <button className="w-full py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition">
                🔍 Test Connection
              </button>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between p-6 border-t border-gray-700">
          <button
            onClick={() => setStep(Math.max(1, step - 1))}
            disabled={step === 1}
            className="px-6 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition disabled:opacity-50"
          >
            ← Back
          </button>

          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-6 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition"
            >
              Cancel
            </button>

            {step < 3 ? (
              <button
                onClick={() => setStep(step + 1)}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition"
              >
                Next →
              </button>
            ) : (
              <button
                onClick={() => onSave(formData)}
                className="px-6 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition"
              >
                ✓ Create Profile
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## Reusable Components

### Button Component

```tsx
type ButtonVariant = 'primary' | 'secondary' | 'success' | 'danger';

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: ButtonVariant;
  disabled?: boolean;
  fullWidth?: boolean;
  icon?: React.ReactNode;
}

export function Button({
  children,
  onClick,
  variant = 'primary',
  disabled,
  fullWidth,
  icon,
}: ButtonProps) {
  const baseClasses = 'px-4 py-2 rounded-lg font-medium transition flex items-center gap-2 justify-center';

  const variantClasses = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-gray-700 hover:bg-gray-600 text-white',
    success: 'bg-green-600 hover:bg-green-700 text-white',
    danger: 'bg-red-600 hover:bg-red-700 text-white',
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${variantClasses[variant]} ${
        fullWidth ? 'w-full' : ''
      } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      {icon}
      {children}
    </button>
  );
}
```

### Status Badge

```tsx
export function StatusBadge({ status }: { status: string }) {
  const colors = {
    running: 'bg-green-500/20 text-green-400 border-green-500',
    stopped: 'bg-gray-500/20 text-gray-400 border-gray-500',
    error: 'bg-red-500/20 text-red-400 border-red-500',
  };

  return (
    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${colors[status] || colors.stopped}`}>
      {status}
    </span>
  );
}
```

---

## Responsive Design

```css
/* Mobile (< 768px) - Stack cards vertically */
@media (max-width: 768px) {
  .profile-grid {
    grid-template-columns: 1fr;
  }

  .sidebar {
    width: 100%;
    height: 60px;
    flex-direction: row;
  }
}

/* Tablet (768px - 1024px) - 2 columns */
@media (min-width: 768px) and (max-width: 1024px) {
  .profile-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Desktop (> 1024px) - 3 columns */
@media (min-width: 1024px) {
  .profile-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
```

## Next: See `07-api-documentation.md` for complete API reference
