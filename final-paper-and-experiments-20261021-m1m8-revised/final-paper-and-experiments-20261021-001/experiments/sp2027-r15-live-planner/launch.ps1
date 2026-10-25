$ErrorActionPreference = 'Stop'
$experimentDirectory = $PSScriptRoot
$protocol = Get-Content -LiteralPath (Join-Path $experimentDirectory 'protocol.json') | ConvertFrom-Json
if ($protocol.status -ne 'frozen-ready') { throw 'GLM requires trusted TLS verification, a task-free interface probe, and protocol refreeze before collection.' }
$existing = Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python' -and $_.CommandLine -like "*$experimentDirectory*" }
if ($existing) { throw 'The collection process is already active.' }
$credentialDirectory = Join-Path $env:LOCALAPPDATA 'AgentSideChannelResearch'
$settings = Get-Content -LiteralPath (Join-Path $credentialDirectory 'glm.json') | ConvertFrom-Json
$credential = Import-Clixml -LiteralPath (Join-Path $credentialDirectory 'glm.credential.xml')
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
try {
    $env:GLM_API_KEY = $credential.GetNetworkCredential().Password
    $env:GLM_BASE_URL = $settings.base_url
    if ($settings.ca_bundle) { $env:GLM_CA_BUNDLE = $settings.ca_bundle }
    $pythonPath = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
    $process = Start-Process -FilePath $pythonPath -ArgumentList @('-u',"$experimentDirectory/run_resolved.py") -WorkingDirectory $experimentDirectory -WindowStyle Hidden -RedirectStandardOutput "$experimentDirectory/collection-$stamp.stdout.log" -RedirectStandardError "$experimentDirectory/collection-$stamp.stderr.log" -PassThru
    Write-Output "Started collection PID $($process.Id)."
} finally {
    Remove-Item Env:GLM_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:GLM_BASE_URL -ErrorAction SilentlyContinue
    Remove-Item Env:GLM_CA_BUNDLE -ErrorAction SilentlyContinue
    Remove-Variable credential -ErrorAction SilentlyContinue
}
