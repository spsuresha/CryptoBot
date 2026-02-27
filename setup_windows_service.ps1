# PowerShell Script to Setup Trading Bot as Windows Service
# Run this script as Administrator

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Trading Bot - Windows Service Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Get current directory
$BotPath = Get-Location
$PythonExe = (Get-Command python).Source
$RunnerScript = Join-Path $BotPath "run_bot_24_7.py"

Write-Host "Bot Path: $BotPath" -ForegroundColor Green
Write-Host "Python: $PythonExe" -ForegroundColor Green
Write-Host "Runner Script: $RunnerScript" -ForegroundColor Green
Write-Host ""

# Ask for configuration
Write-Host "Configuration:" -ForegroundColor Yellow
$Mode = Read-Host "Trading Mode (paper/live) [default: paper]"
if ([string]::IsNullOrWhiteSpace($Mode)) { $Mode = "paper" }

$Pair = Read-Host "Trading Pair [default: BTC/USDT]"
if ([string]::IsNullOrWhiteSpace($Pair)) { $Pair = "BTC/USDT" }

$Timeframe = Read-Host "Timeframe [default: 5m]"
if ([string]::IsNullOrWhiteSpace($Timeframe)) { $Timeframe = "5m" }

Write-Host ""
Write-Host "Creating Scheduled Task..." -ForegroundColor Yellow

# Create Task Action
$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "$RunnerScript --mode $Mode --pair `"$Pair`" --timeframe $Timeframe" `
    -WorkingDirectory $BotPath

# Create Task Trigger (at startup)
$Trigger = New-ScheduledTaskTrigger -AtStartup

# Create Task Settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -ExecutionTimeLimit (New-TimeSpan -Days 365)

# Create Task Principal (run as current user)
$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Highest

# Register the task
$TaskName = "CryptoTradingBot"

try {
    # Remove existing task if it exists
    $ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($ExistingTask) {
        Write-Host "Removing existing task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }

    # Register new task
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Principal $Principal `
        -Description "Cryptocurrency Trading Bot - Runs 24/7 with automatic restart"

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "SUCCESS! Trading Bot Scheduled Task Created" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Configuration:" -ForegroundColor Cyan
    Write-Host "  Task Name: $TaskName" -ForegroundColor White
    Write-Host "  Mode: $Mode" -ForegroundColor White
    Write-Host "  Pair: $Pair" -ForegroundColor White
    Write-Host "  Timeframe: $Timeframe" -ForegroundColor White
    Write-Host ""
    Write-Host "The bot will:" -ForegroundColor Cyan
    Write-Host "  - Start automatically when Windows boots" -ForegroundColor White
    Write-Host "  - Restart automatically if it crashes (up to 3 times)" -ForegroundColor White
    Write-Host "  - Run continuously 24/7" -ForegroundColor White
    Write-Host ""
    Write-Host "Management Commands:" -ForegroundColor Yellow
    Write-Host "  Start:   Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    Write-Host "  Stop:    Stop-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    Write-Host "  Status:  Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    Write-Host "  Logs:    Check logs\ directory" -ForegroundColor White
    Write-Host ""
    Write-Host "To start the bot now, run:" -ForegroundColor Yellow
    Write-Host "  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Green
    Write-Host ""

} catch {
    Write-Host ""
    Write-Host "ERROR: Failed to create scheduled task" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
