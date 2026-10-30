# Android Calculator

A simple Android calculator for addition, subtraction, multiplication, and division. It calculates two numbers at a time. Division results are rounded to at most 12 decimal places.

## Requirements

- Android 10 (API 29) or later
- To build: JDK 17, Gradle 8.13, Android SDK Platform 36, and Build Tools 35.0.0
- The shared development tools are installed under `D:\software\AndroidDev`

## Build

From this project directory in PowerShell:

```powershell
$env:JAVA_HOME = 'D:\software\AndroidDev\jdk-17.0.20.1+1'
$env:ANDROID_HOME = 'D:\software\AndroidDev\sdk'
$env:ANDROID_USER_HOME = 'D:\software\AndroidDev\android-user'
$env:GRADLE_USER_HOME = 'D:\software\AndroidDev\gradle-cache'
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
& 'D:\software\AndroidDev\gradle-8.13\bin\gradle.bat' assembleDebug
```

The build produces `app/build/outputs/apk/debug/app-debug.apk`; move the tested APK to `deliverables/app-debug.apk` for delivery. Installing subsequent builds as updates requires the same signing key.

## Install and Use

Transfer `deliverables/app-debug.apk` to the phone and open it to install. If Android asks, allow installation from the app used to open the file. Open Calculator, enter a number, choose an operator, enter a second number, and tap `=`. Use `C` to clear and `DEL` to delete the last character. Tap `C` to dismiss a division-by-zero error.

## Device Verification

The user reported that the application worked correctly when tested on the vivo X300. The phone's exact Android version has not been confirmed.
