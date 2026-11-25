# run_all_gee.ps1
$env:Path += ";C:\Miniforge3;C:\Miniforge3\Scripts;C:\Miniforge3\Library\bin"
$condaHook = "C:\Users\SHIMELES_TADESSE\miniforge3\shell\condabin\conda-hook.ps1"
if (Test-Path $condaHook) {
    . $condaHook
    conda activate gee_horn
}

$scripts = @(
    "01_climate_hazard.py",
    "02_gender_proxy.py",
    "03_terrain.py"
)

foreach ($s in $scripts) {
    Write-Host "Running $s..." -ForegroundColor Yellow
    python "C:\GeoProjects\HornVulnerability\scripts\$s"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR in $s" -ForegroundColor Red
        break
    }
}

Write-Host "Checking exported GeoTIFFs in C:\GeoProjects\HornVulnerability\data\raw..." -ForegroundColor Green
Get-ChildItem "C:\GeoProjects\HornVulnerability\data\raw" -Filter "*.tif*" | Select-Object Name, Length, LastWriteTime
