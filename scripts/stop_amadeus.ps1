param(
    [switch]$WhatIf
)

$projectPorts = @(5173, 8000, 9880)
$listeners = @{}

foreach ($line in (netstat -ano -p tcp)) {
    if ($line -notmatch '^\s*TCP\s+\S+:(\d+)\s+\S+\s+LISTENING\s+(\d+)\s*$') {
        continue
    }

    $port = [int]$Matches[1]
    $processId = [int]$Matches[2]
    if ($projectPorts -contains $port) {
        $listeners[$processId] = $port
    }
}

if ($listeners.Count -eq 0) {
    Write-Host "Amadeus is already stopped. No project ports are listening."
    exit 0
}

foreach ($entry in $listeners.GetEnumerator()) {
    $processId = $entry.Key
    $port = $entry.Value
    if ($WhatIf) {
        Write-Host "Would stop PID $processId and its child processes (port $port)."
        continue
    }

    Write-Host "Stopping PID $processId and its child processes (port $port)..."
    & taskkill.exe /PID $processId /T /F
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to stop PID $processId. Run this script as Administrator."
        exit $LASTEXITCODE
    }
}

if ($WhatIf) {
    Write-Host "Dry run complete. No processes were stopped."
    exit 0
}

Write-Host "Amadeus has stopped completely."
