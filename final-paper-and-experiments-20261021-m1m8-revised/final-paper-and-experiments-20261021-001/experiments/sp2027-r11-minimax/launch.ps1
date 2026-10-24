$ErrorActionPreference = 'Stop'
$experimentDirectory = $PSScriptRoot
$existing = Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python' -and $_.CommandLine -like "*$experimentDirectory*run.py*" }
if ($existing) { throw 'The collection process is already active.' }
$credentialDirectory = Join-Path $env:LOCALAPPDATA 'AgentSideChannelResearch'
$settings = Get-Content -LiteralPath (Join-Path $credentialDirectory 'endpoint.json') | ConvertFrom-Json
$credential = Import-Clixml -LiteralPath (Join-Path $credentialDirectory 'endpoint.credential.xml')
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
try {
    $env:ANTHROPIC_AUTH_TOKEN = $credential.GetNetworkCredential().Password
    $env:ANTHROPIC_BASE_URL = $settings.base_url
    $pythonPath = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
    $process = Start-Process -FilePath $pythonPath -ArgumentList @('-u',"$experimentDirectory/run.py") -WorkingDirectory $experimentDirectory -WindowStyle Hidden -RedirectStandardOutput "$experimentDirectory/collection-$stamp.stdout.log" -RedirectStandardError "$experimentDirectory/collection-$stamp.stderr.log" -PassThru
    Write-Output "Started collection PID $($process.Id)."
} finally {
    Remove-Item Env:ANTHROPIC_AUTH_TOKEN -ErrorAction SilentlyContinue
    Remove-Item Env:ANTHROPIC_BASE_URL -ErrorAction SilentlyContinue
    Remove-Variable credential -ErrorAction SilentlyContinue
}
