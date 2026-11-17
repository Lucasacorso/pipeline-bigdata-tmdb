$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$ProgressPreference = "SilentlyContinue"

foreach ($id in "Python.Python.3.11", "EclipseAdoptium.Temurin.17.JDK", "Git.Git") {
    if (-not (winget list -e --id $id | Select-String $id)) {
        winget install -e --id $id --accept-source-agreements --accept-package-agreements --silent
    }
}

$tools = Join-Path $PSScriptRoot "tools"
$hadoop = Join-Path $tools "hadoop\bin"
New-Item -ItemType Directory -Force $hadoop | Out-Null
foreach ($f in "winutils.exe", "hadoop.dll") {
    if (-not (Test-Path "$hadoop\$f")) {
        Invoke-WebRequest "https://raw.githubusercontent.com/cdarlint/winutils/master/hadoop-3.3.5/bin/$f" -OutFile "$hadoop\$f" -UseBasicParsing
    }
}

$pacotes = @{
    "mongodb-windows-x86_64-*" = "https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-8.0.4.zip"
    "mongosh-*"                = "https://downloads.mongodb.com/compass/mongosh-2.3.8-win32-x64.zip"
}
foreach ($padrao in $pacotes.Keys) {
    if (-not (Get-ChildItem $tools -Directory -Filter $padrao -ErrorAction SilentlyContinue)) {
        $zip = Join-Path $tools "pacote.zip"
        curl.exe -L -s -o $zip $pacotes[$padrao]
        Expand-Archive $zip -DestinationPath $tools -Force
        Remove-Item $zip
    }
}

$py = @("$env:LOCALAPPDATA\Programs\Python\Python311\python.exe", "C:\Program Files\Python311\python.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not (Test-Path ".venv")) { & $py -m venv .venv }
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "Ambiente pronto. Execute: .\executar.ps1"
