# JARVIS Android Architecture & Client Guide

The Android client serves as the **primary voice and mobile command interface** for JARVIS.

---

## 1. Design & UI Philosophy
The mobile interface is built entirely using **Jetpack Compose** with Material 3, themed with a sci-fi HUD aesthetic:
- **Obsidian Background**: `#0A0E17`
- **Surface Elevation**: `#121824` / `#1A2234`
- **Neon Cyan Accent**: `#00E5FF`
- **Amber Warning**: `#FF9100`

### Screens:
1. **HUD / Dashboard (`DashboardScreen.kt`)**: Displays the animated `OrbVisualizer`, current online status, chat transcript stream, and quick mic / send controls.
2. **Task Center (`TaskCenterScreen.kt`)**: Shows active autonomous coding and execution tasks, step progression, and a one-tap `HALT TASK` button.
3. **Memory Vault (`MemoryVaultScreen.kt`)**: Searchable memory cards categorized by Long-term, Project, and Episodic, with individual delete buttons.
4. **Device Mesh (`DeviceMeshScreen.kt`)**: Visualizes the topology of connected nodes (Phone, Laptop, Cloud Server) and their respective capabilities.

---

## 2. Persistent Foreground Voice Service (`JarvisVoiceService.kt`)
To ensure continuous availability without draining excessive battery:
- Runs as an Android **Foreground Service** with a sticky low-priority notification.
- Provides a clear **STOP** button directly in the notification bar to shut down the service at any time.
- Uses Android's native `SpeechRecognizer` for Speech-to-Text and `TextToSpeech` for synthesized voice replies.
- **Barge-In Interruptibility**: If JARVIS is speaking and the user begins talking or taps the microphone, ongoing audio is immediately halted (`stopSpeaking()`).

---

## 3. Home Screen Widget (`JarvisAppWidget.kt`)
A lightweight `AppWidgetProvider` remote view:
- Displays JARVIS branding and online/offline status.
- **One-Tap Activation**: Tapping the mic icon sends `ACTION_WIDGET_ACTIVATE`, launching the voice listening flow directly without waiting for the full UI to open.
- Does not run heavy background tasks itself; delegates entirely to `JarvisVoiceService`.

---

## 4. Permissions
Configured in `AndroidManifest.xml`:
- `RECORD_AUDIO`: Required for voice speech recognition.
- `FOREGROUND_SERVICE` & `FOREGROUND_SERVICE_MICROPHONE`: For persistent background voice sessions.
- `POST_NOTIFICATIONS`: For alerts regarding task completions and required approvals (Android 13+).
- `INTERNET` & `ACCESS_NETWORK_STATE`: For WebSocket and REST communications.

---

## 5. Building & Deploying
To build the debug APK using Gradle:
```bash
cd android
./gradlew assembleDebug
```
The output APK will be generated at `android/app/build/outputs/apk/debug/app-debug.apk`.
Install onto a device via ADB:
```bash
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```
