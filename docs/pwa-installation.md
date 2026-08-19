# ReliefChain AI — Progressive Web App (PWA) & Offline Guide

**ReliefChain AI** includes a full Progressive Web App (PWA) architecture allowing citizens, volunteers, and emergency commanders to install the application directly onto Android, iOS, Windows, and macOS devices.

---

## 1. PWA Installation Procedure

### On Android (Chrome / Edge)
1. Open `http://<HOST_IP>:8000/ui/` in Google Chrome.
2. Tap the **"Add ReliefChain AI to Home Screen"** banner prompt, or tap the three-dot menu icon ($\vdots$) $\rightarrow$ **Install app** / **Add to Home screen**.
3. Confirm installation. The application will launch in standalone display mode with a dedicated app icon and splash screen.

### On iOS (Safari)
1. Open `http://<HOST_IP>:8000/ui/` in Safari.
2. Tap the **Share** button ($\uparrow$).
3. Scroll down and tap **Add to Home Screen**.

### On Desktop (Chrome / Edge)
1. Look for the **Install App** icon in the browser address bar.
2. Click **Install**. The app will run in its own standalone window without browser URL bars.

---

## 2. Web App Manifest & Service Worker Architecture

- **Manifest File**: Mounted at `/ui/manifest.json`.
  - `display`: `standalone`
  - `start_url`: `/ui/`
  - `theme_color`: `#0f172a` (Dark Slate)
  - `background_color`: `#090d16`
  - `shortcuts`:
    - `🚨 One-Tap SOS`: `/ui/?action=sos`
    - `📍 Citizen Hub`: `/ui/?tab=citizen`
    - `🙋 Volunteer Ops`: `/ui/?tab=volunteer`
    - `🤖 AI Copilot`: `/ui/?tab=copilot`

- **Service Worker File**: Mounted at `/ui/sw.js`.
  - **Cache Strategy**: Cache-first for static UI assets (HTML, CSS, JS, icons), network-first for dynamic API routes.
  - **Background Sync**: Registers `sync-offline-sos` background synchronization listener. Unsynchronized SOS requests created while offline are queued locally and automatically synced when connectivity resumes.
  - **Offline Banner**: Renders offline fallback state without false claims of delivered emergency actions.
