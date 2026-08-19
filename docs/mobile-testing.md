# ReliefChain AI — Mobile Phone & Real Device Testing Guide

This guide provides exact instructions for testing **ReliefChain AI** on physical Android and iOS mobile devices.

---

## 1. Local Area Network (LAN) Wi-Fi Testing Setup

When running the application on your laptop, `localhost` (127.0.0.1) is **not** accessible directly from a mobile phone connected to the same Wi-Fi network. Follow these steps to test on a physical phone:

### Step 1: Find Your Laptop's Local IP Address
- **On Windows (PowerShell / Command Prompt)**:
  ```powershell
  ipconfig
  ```
  Look for `IPv4 Address` under your active Wi-Fi adapter (e.g., `192.168.1.5` or `10.0.0.12`).

- **On macOS / Linux**:
  ```bash
  ifconfig  # or ip a
  ```

### Step 2: Launch Server Bound to `0.0.0.0`
Start the FastAPI server bound to all interfaces (`0.0.0.0`):
```bash
py -3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### Step 3: Open on Mobile Phone Browser
1. Connect your mobile phone to the **same Wi-Fi network** as your laptop.
2. Open Chrome (Android) or Safari (iOS) on your phone.
3. Navigate to:
   ```
   http://<YOUR_LAPTOP_IP>:8000/ui/
   ```
   *Example*: `http://192.168.1.5:8000/ui/`

---

## 2. Mobile Responsive Layout & UX Features

- **Touch-Friendly Controls**: Minimum 44px $\times$ 44px tap targets for buttons, inputs, and tab navigation pills.
- **Zero Horizontal Overflow**: Fluid flex and grid CSS containers ensuring content fits within 360px--412px viewports without horizontal scrolling.
- **Mobile SOS Trigger**: Prominent, high-contrast `🚨 One-Tap Emergency SOS` button pinned at top of Citizen Hub.
- **Offline Network Pill**: Live connectivity status indicator in header (`🟢 ONLINE`, `🔴 OFFLINE`, `🟡 SYNCING`).

---

## 3. Graceful Degradation on Mobile

- **WebSocket Reconnection**: Auto-reconnects with exponential backoff when mobile device switches networks or toggles Airplane Mode.
- **Offline Push Graceful Fallback**: If Web Push notifications are disabled or unsupported by the mobile browser, in-app notification toasts and database alerts display seamlessly without JS errors.
