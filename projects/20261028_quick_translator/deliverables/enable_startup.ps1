$ErrorActionPreference = 'Stop'
$taskProject = Split-Path -Parent $PSScriptRoot
$taskPython = Join-Path $taskProject '.venv\Scripts\pythonw.exe'
$taskApp = Join-Path $taskProject 'app.py'
$taskStartup = 'C:\Users\Administrator\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup'
$taskShortcutPath = Join-Path $taskStartup 'QuickTranslator.lnk'

foreach ($taskFile in @($taskPython, $taskApp)) {
    if (-not (Test-Path -LiteralPath $taskFile -PathType Leaf)) {
        throw "Required file is missing: $taskFile"
    }
}

$taskShell = New-Object -ComObject WScript.Shell
if (Test-Path -LiteralPath $taskShortcutPath) {
    $taskExisting = $taskShell.CreateShortcut($taskShortcutPath)
    if ($taskExisting.TargetPath -ne $taskPython) {
        throw 'An existing QuickTranslator.lnk points to another executable. Review it before replacing it.'
    }
}

[System.IO.Directory]::CreateDirectory($taskStartup) | Out-Null
$taskShortcut = $taskShell.CreateShortcut($taskShortcutPath)
$taskShortcut.TargetPath = $taskPython
$taskShortcut.Arguments = '"' + $taskApp + '" --background'
$taskShortcut.WorkingDirectory = $taskProject
$taskShortcut.WindowStyle = 7
$taskShortcut.Description = 'Quick Translator - start in the system tray after Administrator signs in'
$taskShortcut.Save()

$taskVerified = $taskShell.CreateShortcut($taskShortcutPath)
if ($taskVerified.TargetPath -ne $taskPython -or $taskVerified.Arguments -ne $taskShortcut.Arguments) {
    throw 'Startup shortcut verification failed.'
}
Write-Output "Login startup enabled: $taskShortcutPath"
