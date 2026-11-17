$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$conexao = Test-NetConnection -ComputerName 127.0.0.1 -Port 27017 -InformationLevel Quiet -WarningAction SilentlyContinue
if ($conexao) {
    Write-Host "MongoDB já está rodando em localhost:27017"
    exit 0
}

$servico = Get-Service MongoDB -ErrorAction SilentlyContinue
if ($servico) {
    Start-Service MongoDB
    Write-Host "Serviço MongoDB iniciado"
    exit 0
}

$mongod = Get-ChildItem "tools\mongodb-*\bin\mongod.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $mongod) { throw "mongod.exe não encontrado. Rode .\setup.ps1" }

$dados = Join-Path $PSScriptRoot "data\mongodb"
New-Item -ItemType Directory -Force $dados | Out-Null
Start-Process -FilePath $mongod.FullName -ArgumentList "--dbpath `"$dados`" --port 27017 --bind_ip 127.0.0.1 --logpath `"$dados\mongod.log`"" -WindowStyle Hidden

for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    if (Test-NetConnection -ComputerName 127.0.0.1 -Port 27017 -InformationLevel Quiet -WarningAction SilentlyContinue) {
        Write-Host "MongoDB portátil rodando em localhost:27017 (dados em data\mongodb)"
        exit 0
    }
}
throw "MongoDB não respondeu; veja data\mongodb\mongod.log"
