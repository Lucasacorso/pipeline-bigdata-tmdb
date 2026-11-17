$raiz = $PSScriptRoot

if (-not $env:JAVA_HOME -or -not (Test-Path $env:JAVA_HOME)) {
    $jdk = Get-ChildItem "C:\Program Files\Eclipse Adoptium" -Directory -Filter "jdk-17*" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($jdk) { $env:JAVA_HOME = $jdk.FullName }
}

$caminhos = @("$env:JAVA_HOME\bin", "$raiz\tools\hadoop\bin")
$caminhos += Get-ChildItem "$raiz\tools" -Directory -Filter "mongosh-*" -ErrorAction SilentlyContinue | ForEach-Object { "$($_.FullName)\bin" }
$caminhos += Get-ChildItem "$raiz\tools" -Directory -Filter "mongodb-*" -ErrorAction SilentlyContinue | ForEach-Object { "$($_.FullName)\bin" }
$env:PATH = (($caminhos | Where-Object { Test-Path $_ }) -join ";") + ";$env:PATH"
$env:HADOOP_HOME = "$raiz\tools\hadoop"
$env:PYTHONIOENCODING = "utf-8"

if (Test-Path "$raiz\.venv\Scripts\Activate.ps1") { . "$raiz\.venv\Scripts\Activate.ps1" }

Write-Host "Ambiente carregado: JAVA_HOME=$env:JAVA_HOME | venv ativo | mongosh no PATH"
