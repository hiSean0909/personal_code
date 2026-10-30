# Magic Box

An offline Android toolbox containing Display, Ruler, 2048, Minesweeper, and Flappy Bird.

## Requirements

- Android 10 (API 29) or later
- JDK 17, Gradle 8.13, Android SDK Platform 36, and Build Tools 35.0.0 to build
- Shared development tools under `D:\software\AndroidDev`

## Build

From this directory in PowerShell:

```powershell
$env:JAVA_HOME = 'D:\software\AndroidDev\jdk-17.0.20.1+1'
$env:ANDROID_HOME = 'D:\software\AndroidDev\sdk'
$env:ANDROID_USER_HOME = 'D:\software\AndroidDev\android-user'
$env:GRADLE_USER_HOME = 'D:\software\AndroidDev\gradle-cache'
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
& 'D:\software\AndroidDev\gradle-8.13\bin\gradle.bat' assembleDebug
```

## Install and Use

Transfer `deliverables/app-debug.apk` to the phone and open it to install. Allow installation from the selected source if Android asks. Use the Tools, Search, and Games tabs to browse or search; Search opens by default. In Display, enter text and select its size, colors, and italic style, then tap Show; use Back to edit. In Ruler, compare the marks to a physical ruler and use the calibration slider if needed; the adjustment is saved. Swipe in 2048; tap cells and long-press to flag mines in Minesweeper; tap to fly in Flappy Bird. Use Back to return home and New Game to restart.

## Device Verification

The user installed and tried the first version and requested the current navigation and game changes. The vivo X300 Android version and feedback on this iteration are pending.
