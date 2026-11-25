# run_full_pipeline.ps1
# Creates a timestamped deliverable archive of scripts, output, and qgis_project.
$ErrorActionPreference = "Stop"
$rootDir = "C:\GeoProjects\HornVulnerability"
$outDir = Join-Path $rootDir "output"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$zipPath = Join-Path $outDir "HornVulnerability_Deliverables_$stamp.zip"

$stageDir = Join-Path $env:TEMP "HornVuln_Stage_$stamp"
New-Item -ItemType Directory -Path $stageDir -Force | Out-Null

foreach ($item in @("scripts", "output", "qgis_project")) {
    $src = Join-Path $rootDir $item
    if (Test-Path $src) {
        if ($item -eq "output") {
            $dst = Join-Path $stageDir $item
            New-Item -ItemType Directory -Path $dst -Force | Out-Null
            Get-ChildItem -Path $src -Exclude "*.zip" | Copy-Item -Destination $dst -Recurse -Force
        } else {
            Copy-Item -Path $src -Destination (Join-Path $stageDir $item) -Recurse -Force
        }
    }
}

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}
Compress-Archive -Path "$stageDir\*" -DestinationPath $zipPath -CompressionLevel Optimal
Remove-Item -Path $stageDir -Recurse -Force

Write-Host "[OK] Archive created: $zipPath ($([math]::Round((Get-Item $zipPath).Length / 1MB, 2)) MB)"
