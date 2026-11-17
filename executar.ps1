param(
    [string]$Etapas = "captura,processamento,ingestao",
    [int]$Amostra = 1000,
    [switch]$SemAnalises
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

. "$PSScriptRoot\ambiente.ps1"
& "$PSScriptRoot\iniciar_mongo.ps1"

$env:SAMPLE_ROWS = "$Amostra"
$ErrorActionPreference = "Continue"

python -m pipeline.main --etapas $Etapas
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not $SemAnalises) {
    python -m analises.perguntas
    python -m analises.recomendacao "Inception"
}
