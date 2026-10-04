param([Parameter(ValueFromRemainingArguments=$true)][string[]]$HarnessArgs)
$ErrorActionPreference='Stop'
$rootDir=$PSScriptRoot
if($env:BLENDER_BIN){$blenderPath=$env:BLENDER_BIN}
elseif(Get-Command blender -ErrorAction SilentlyContinue){$blenderPath=(Get-Command blender).Source}
else{$blenderPath=(Get-ChildItem 'C:/Program Files/Blender Foundation/Blender */blender.exe' | Sort-Object { [version]([regex]::Match($_.Directory.Name,'[0-9]+\.[0-9]+').Value) } | Select-Object -Last 1).FullName}
if(-not $blenderPath){throw 'Blender를 설치하거나 BLENDER_BIN을 지정하세요.'}
$pythonPath=(Get-ChildItem (Join-Path (Split-Path $blenderPath) '*/python/bin/python.exe') | Select-Object -First 1).FullName
if(-not $pythonPath){throw 'Blender 내장 Python을 찾지 못했습니다. Python 3.10+로 harness/cli.py를 실행하세요.'}
$env:PYTHONIOENCODING='utf-8'
& $pythonPath (Join-Path $rootDir 'harness/cli.py') @HarnessArgs
exit $LASTEXITCODE
