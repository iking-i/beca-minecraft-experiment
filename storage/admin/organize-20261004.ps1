$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskStorage = Join-Path $taskRoot 'storage'
$taskPrefix = $taskStorage + [IO.Path]::DirectorySeparatorChar
$taskPlan = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'storage-reorganization-plan.json') -Raw | ConvertFrom-Json
$taskPin = Join-Path $taskRoot 'individual/lifetime.json'
$taskOriginalPin = [IO.File]::ReadAllText($taskPin)
$taskMoved = [Collections.Generic.List[object]]::new()
$taskRecords = [Collections.Generic.List[object]]::new()

# Preflight every source and destination before moving any file.
foreach ($taskMove in $taskPlan.moves) {
    $taskSource = (Resolve-Path -LiteralPath $taskMove.source).Path
    $taskDestination = [IO.Path]::GetFullPath($taskMove.destination)
    if (-not $taskSource.StartsWith($taskPrefix, [StringComparison]::OrdinalIgnoreCase) -or
        -not $taskDestination.StartsWith($taskPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Refusing a path outside the project storage directory'
    }
    if (Test-Path -LiteralPath $taskDestination) { throw "Destination already exists: $taskDestination" }
    $taskInfo = Get-Item -LiteralPath $taskSource
    $taskRecords.Add([pscustomobject]@{
        source = $taskSource; destination = $taskDestination; bytes = $taskInfo.Length;
        sha256 = (Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash;
        individual_id = $taskMove.individual_id
    })
}
foreach ($taskRecord in $taskRecords) {
    # A running database writer or lifetime lease prevents exclusive access.
    $taskHandle = [IO.File]::Open($taskRecord.source, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::None)
    $taskHandle.Dispose()
}
if ([IO.File]::ReadAllText($taskPin) -ne $taskOriginalPin) { throw 'Current lifetime pointer changed during preparation' }

try {
    foreach ($taskRecord in $taskRecords) {
        $taskDirectory = Split-Path -Parent $taskRecord.destination
        [IO.Directory]::CreateDirectory($taskDirectory) | Out-Null
        Move-Item -LiteralPath $taskRecord.source -Destination $taskRecord.destination
        $taskMoved.Add($taskRecord)
        if ((Get-FileHash -LiteralPath $taskRecord.destination -Algorithm SHA256).Hash -ne $taskRecord.sha256) {
            throw "Moved file failed content verification: $($taskRecord.destination)"
        }
    }
    $taskNewPin = $taskPlan.new_pin | ConvertTo-Json -Depth 10
    [IO.File]::WriteAllText($taskPin, $taskNewPin + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
    $taskReport = [pscustomobject]@{
        status = 'files_relocated_and_hash_verified'; created_at = [DateTimeOffset]::UtcNow.ToString('o');
        original_pin = $taskPlan.original_pin; new_pin = $taskPlan.new_pin;
        database_contents_rewritten = $false; records = $taskRecords; individuals = $taskPlan.individuals
    }
    [IO.File]::WriteAllText((Join-Path $PSScriptRoot 'storage-reorganization-report.json'),
        ($taskReport | ConvertTo-Json -Depth 20) + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
    Write-Output "Relocated and SHA-256 verified $($taskRecords.Count) files across $($taskPlan.individuals.Count) individuals."
} catch {
    # Restore exact original paths if any part of the relocation fails.
    [IO.File]::WriteAllText($taskPin, $taskOriginalPin, [Text.UTF8Encoding]::new($false))
    for ($taskIndex = $taskMoved.Count - 1; $taskIndex -ge 0; $taskIndex--) {
        $taskRecord = $taskMoved[$taskIndex]
        if (Test-Path -LiteralPath $taskRecord.destination) {
            Move-Item -LiteralPath $taskRecord.destination -Destination $taskRecord.source
        }
    }
    throw
}
