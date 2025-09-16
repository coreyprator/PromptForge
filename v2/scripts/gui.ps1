$env:PYTHONPATH = (Resolve-Path "$PSScriptRoot\..\src").Path
& "C:\venvs\promptforge-v2\Scripts\python.exe" -m promptforge_cli gui
