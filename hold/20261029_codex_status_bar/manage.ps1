param(
    [ValidateSet('doctor', 'quota', 'start', 'inspect')]
    [string]$Action = 'doctor'
)

$ErrorActionPreference = 'Stop'
$taskNodeCandidates = [System.Collections.Generic.List[string]]::new()
$taskNodeCommand = Get-Command node -ErrorAction SilentlyContinue
if ($taskNodeCommand) { $taskNodeCandidates.Add($taskNodeCommand.Source) }
$taskNodeCandidates.Add((Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'))

foreach ($taskNodePath in $taskNodeCandidates) {
    if (-not (Test-Path -LiteralPath $taskNodePath -PathType Leaf)) { continue }
    try {
        $taskNodeVersion = & $taskNodePath --version 2>$null
        if ($LASTEXITCODE -ne 0 -or $taskNodeVersion -notmatch '^v(\d+)\.') { continue }
        if ([int]$Matches[1] -lt 24) { continue }
    } catch {
        continue
    }

    # Preserve native diagnostics and the entry's exit code in both PowerShell hosts.
    $taskPreviousErrorPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $taskNodePath (Join-Path $PSScriptRoot 'manage.cjs') $Action
        $taskEntryExitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $taskPreviousErrorPreference
    }
    exit $taskEntryExitCode
}

Write-Error 'Node.js 24 or later is required. No compatible existing runtime was found.'
exit 1
