$ErrorActionPreference = "Stop"

function Run-Step($label, $command) {
    Write-Host "==> $label"
    Write-Host "    $command"
    Invoke-Expression $command
    Write-Host ""
}

Run-Step "Check env" "python -c `"import os; assert os.getenv('GEMINI_API_KEY'), 'GEMINI_API_KEY missing'`""
Run-Step "Basic professional report" "python stt.py https://www.youtube.com/watch?v=T9aRN5JkmL8 --lang en --reports professional"
Run-Step "Timestamps" "python stt.py https://www.youtube.com/watch?v=T9aRN5JkmL8 --lang en --reports professional --timestamps"
Run-Step "With transcript" "python stt.py https://www.youtube.com/watch?v=T9aRN5JkmL8 --lang en --reports professional --with-transcript"
Run-Step "Dry run cost estimate" "python stt.py https://www.youtube.com/watch?v=T9aRN5JkmL8 --dry-run"
Run-Step "Batch file" "@'
https://www.youtube.com/watch?v=T9aRN5JkmL8
'@ | Set-Content playlist.txt; python stt.py --batch playlist.txt --lang en --reports professional"
Run-Step "Compare mode" "python stt.py --compare https://www.youtube.com/watch?v=T9aRN5JkmL8 https://www.youtube.com/watch?v=T9aRN5JkmL8"
Run-Step "Export formats" "python stt.py https://www.youtube.com/watch?v=T9aRN5JkmL8 --format pdf,docx --lang en --reports professional"

if ($env:RUN_FEEDS -eq "1") {
    if (Test-Path "feeds.yaml") {
        $content = Get-Content "feeds.yaml" -Raw
        if ($content -notmatch "simplecast.com/yourfeed") {
            Run-Step "Podcast feeds" "python stt.py --feeds feeds.yaml"
        } else {
            Write-Host "Skipping feeds: feeds.yaml still contains placeholder URL."
        }
    } else {
        Write-Host "Skipping feeds: feeds.yaml not found."
    }
}

if ($env:RUN_WEB_UI -eq "1") {
    Write-Host "==> Web UI / API smoke"
    $job = Start-Job -ScriptBlock { python stt.py --serve --port 8080 }
    Start-Sleep -Seconds 3
    try {
        Invoke-WebRequest -Uri "http://localhost:8080/" -UseBasicParsing | Out-Null
        Invoke-WebRequest -Uri "http://localhost:8080/process" -Method Post -Body @{
            url = "https://www.youtube.com/watch?v=T9aRN5JkmL8"
            lang = "en"
            reports = "professional"
        } -UseBasicParsing | Out-Null
        Write-Host "    Web UI / API smoke: OK"
    } finally {
        Stop-Job $job | Out-Null
        Remove-Job $job | Out-Null
    }
    Write-Host ""
}

if ($env:RUN_WATCH -eq "1") {
    Write-Host "==> Watch mode smoke"
    $watchDir = "incoming_audio"
    New-Item -ItemType Directory -Force -Path $watchDir | Out-Null
    $job = Start-Job -ScriptBlock { python stt.py --watch incoming_audio }
    Start-Sleep -Seconds 3
    $mp3 = Get-ChildItem -Recurse -Filter *.mp3 -Path output -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($mp3) {
        Copy-Item $mp3.FullName -Destination (Join-Path $watchDir $mp3.Name) -Force
        Write-Host "    Dropped file into watch dir: $($mp3.Name)"
        Start-Sleep -Seconds 5
    } else {
        Write-Host "    No MP3 found in output; skipping watch trigger."
    }
    Stop-Job $job | Out-Null
    Remove-Job $job | Out-Null
    Write-Host ""
}

if ($env:RUN_PLUGINS -eq "1") {
    Write-Host "==> Plugins smoke"
    Write-Host "    Ensure plugins are configured in config.yaml before running."
    Run-Step "Plugins run" "python stt.py https://www.youtube.com/watch?v=T9aRN5JkmL8 --lang en --reports professional"
}

Write-Host "Smoke QA complete."
