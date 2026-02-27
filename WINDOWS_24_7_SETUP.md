# Windows 11 - 24/7 Trading Bot Setup Guide

Complete guide to running your cryptocurrency trading bot 24/7 on Windows 11 with automatic restart on failure.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Setup](#quick-setup)
3. [Manual Setup Methods](#manual-setup-methods)
4. [Monitoring & Management](#monitoring--management)
5. [Troubleshooting](#troubleshooting)
6. [Advanced Configuration](#advanced-configuration)

---

## Prerequisites

### ✅ Required
- Windows 11 (or Windows 10)
- Python 3.9+ installed
- Trading bot dependencies installed (`pip install -r requirements.txt`)
- Administrator access
- Configured `.env` and `config.yaml` files

### ⚙️ Optional
- NSSM (Non-Sucking Service Manager) for advanced service management
- PowerShell 5.1+ (included in Windows 11)

---

## Quick Setup

### Method 1: Using PowerShell Script (Recommended)

**Step 1: Open PowerShell as Administrator**
```powershell
# Right-click PowerShell and select "Run as Administrator"
```

**Step 2: Navigate to bot directory**
```powershell
cd C:\temp\Crypto_Bot
```

**Step 3: Run setup script**
```powershell
# Allow script execution (one-time)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run setup
.\setup_windows_service.ps1
```

**Step 4: Follow prompts**
- Trading Mode: `paper` or `live`
- Trading Pair: `BTC/USDT`
- Timeframe: `5m`, `15m`, `1h`, etc.

**Step 5: Start the bot**
```powershell
Start-ScheduledTask -TaskName "CryptoTradingBot"
```

✅ **Done!** Bot is now running 24/7 with auto-restart.

---

### Method 2: Using Python Runner Script

**Step 1: Open Command Prompt**
```cmd
cd C:\temp\Crypto_Bot
```

**Step 2: Run the bot**
```cmd
# Paper trading (safe)
python run_bot_24_7.py --mode paper --pair BTC/USDT --timeframe 5m

# Live trading (requires confirmation)
python run_bot_24_7.py --mode live --pair BTC/USDT --timeframe 5m
```

**Features:**
- ✅ Automatic restart on crash (up to 5 attempts)
- ✅ Exponential backoff between restarts
- ✅ Comprehensive logging
- ✅ System resource monitoring
- ⚠️ Runs in current session only (stops when you log out)

---

## Manual Setup Methods

### Option A: Windows Task Scheduler (GUI)

**Step 1: Open Task Scheduler**
```
Press Win + R → type "taskschd.msc" → Enter
```

**Step 2: Create Basic Task**
1. Click "Create Basic Task" in the right panel
2. Name: `CryptoTradingBot`
3. Description: `24/7 Cryptocurrency Trading Bot`
4. Click "Next"

**Step 3: Configure Trigger**
1. Select "When the computer starts"
2. Click "Next"

**Step 4: Configure Action**
1. Select "Start a program"
2. Program/script: `C:\Users\YourUsername\AppData\Local\Programs\Python\Python39\python.exe`
   - (Find your Python path: `where python` in cmd)
3. Arguments: `run_bot_24_7.py --mode paper --pair BTC/USDT --timeframe 5m`
4. Start in: `C:\temp\Crypto_Bot`
5. Click "Next" → "Finish"

**Step 5: Advanced Settings**
1. Right-click the task → Properties
2. **General Tab:**
   - ✅ Run whether user is logged on or not
   - ✅ Run with highest privileges
3. **Settings Tab:**
   - ✅ Allow task to be run on demand
   - ✅ Run task as soon as possible after a scheduled start is missed
   - ✅ If the task fails, restart every: `5 minutes`
   - ✅ Attempt to restart up to: `3 times`
   - Stop the task if it runs longer than: `Disabled` or `365 days`
4. Click "OK"

---

### Option B: Using NSSM (Advanced)

NSSM provides the most robust service management.

**Step 1: Download NSSM**
```powershell
# Download from: https://nssm.cc/download
# Or use Chocolatey:
choco install nssm
```

**Step 2: Install Service**
```cmd
cd C:\temp\Crypto_Bot

# Open NSSM GUI
nssm install CryptoTradingBot
```

**Step 3: Configure in NSSM GUI**

**Application Tab:**
- Path: `C:\Users\...\python.exe`
- Startup directory: `C:\temp\Crypto_Bot`
- Arguments: `run_bot_24_7.py --mode paper --pair BTC/USDT --timeframe 5m`

**Details Tab:**
- Display name: `Crypto Trading Bot`
- Description: `24/7 Cryptocurrency Trading Bot with automatic restart`
- Startup type: `Automatic`

**I/O Tab:**
- Output (stdout): `C:\temp\Crypto_Bot\logs\nssm_output.log`
- Error (stderr): `C:\temp\Crypto_Bot\logs\nssm_error.log`

**Rotation Tab:**
- ✅ Rotate files
- Rotate when bigger than: `10240` KB (10 MB)
- Restrict rotation to: `5` files

**Exit Actions Tab:**
- Restart Action: `Restart application`
- Delay restart: `5000` ms (5 seconds)

**Step 4: Start Service**
```cmd
nssm start CryptoTradingBot
```

---

## Monitoring & Management

### Check Bot Status

**PowerShell (Task Scheduler):**
```powershell
# Check if running
Get-ScheduledTask -TaskName "CryptoTradingBot" | Select-Object State

# Get detailed info
Get-ScheduledTask -TaskName "CryptoTradingBot" | Format-List *

# Check last run result
Get-ScheduledTaskInfo -TaskName "CryptoTradingBot"
```

**NSSM Service:**
```cmd
# Check status
nssm status CryptoTradingBot

# View service configuration
nssm get CryptoTradingBot *
```

### Start/Stop/Restart Bot

**PowerShell (Task Scheduler):**
```powershell
# Start
Start-ScheduledTask -TaskName "CryptoTradingBot"

# Stop
Stop-ScheduledTask -TaskName "CryptoTradingBot"

# Restart (stop then start)
Stop-ScheduledTask -TaskName "CryptoTradingBot"
Start-Sleep -Seconds 3
Start-ScheduledTask -TaskName "CryptoTradingBot"
```

**NSSM Service:**
```cmd
# Start
nssm start CryptoTradingBot

# Stop
nssm stop CryptoTradingBot

# Restart
nssm restart CryptoTradingBot
```

### View Logs

**Log Files Location:**
```
C:\temp\Crypto_Bot\logs\
├── bot_runner.log       # Main runner log
├── main.log             # Bot application log
├── trading.log          # Trading operations
├── errors.log           # Error messages
├── bot_stats.json       # Runtime statistics
└── nssm_output.log      # NSSM output (if using NSSM)
```

**View Logs:**
```powershell
# Tail main log (real-time)
Get-Content C:\temp\Crypto_Bot\logs\bot_runner.log -Wait -Tail 50

# View last 100 lines
Get-Content C:\temp\Crypto_Bot\logs\main.log -Tail 100

# Search for errors
Select-String -Path C:\temp\Crypto_Bot\logs\*.log -Pattern "ERROR"

# View stats
Get-Content C:\temp\Crypto_Bot\logs\bot_stats.json | ConvertFrom-Json
```

### Monitor Resource Usage

**PowerShell:**
```powershell
# Find Python process
Get-Process python | Format-Table Name, CPU, WorkingSet, StartTime

# Continuous monitoring
while ($true) {
    Clear-Host
    Get-Process python | Format-Table Name, CPU, WorkingSet, StartTime
    Start-Sleep -Seconds 5
}
```

**Task Manager:**
1. Press `Ctrl + Shift + Esc`
2. Go to "Details" tab
3. Find `python.exe` process
4. Right-click → "Set Priority" (if needed)

---

## Troubleshooting

### Issue: Task/Service Won't Start

**Check:**
```powershell
# Verify Python path
where python

# Test bot manually
cd C:\temp\Crypto_Bot
python run_bot_24_7.py --mode paper --pair BTC/USDT --timeframe 5m

# Check Task Scheduler logs
Get-WinEvent -LogName "Microsoft-Windows-TaskScheduler/Operational" -MaxEvents 20
```

**Solution:**
- Update Python path in task/service configuration
- Run as Administrator
- Check `.env` and `config.yaml` exist
- Verify dependencies are installed

### Issue: Bot Crashes Repeatedly

**Check Logs:**
```powershell
# View errors
Get-Content C:\temp\Crypto_Bot\logs\errors.log -Tail 50

# Check runner log
Get-Content C:\temp\Crypto_Bot\logs\bot_runner.log -Tail 50
```

**Common Causes:**
- API key issues (check `.env`)
- Network connectivity problems
- Exchange API rate limits
- Insufficient permissions
- Missing dependencies

**Solutions:**
```cmd
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Test exchange connection
python -c "from src.exchange.connector import ExchangeConnector; c = ExchangeConnector(); c.connect(); print('OK')"

# Verify configuration
python -c "from src.config.settings import Settings; s = Settings(); print(s)"
```

### Issue: Bot Stops When You Log Out

**If using Task Scheduler:**
- Ensure "Run whether user is logged on or not" is checked
- Task must run with highest privileges

**If using Python runner directly:**
- Use Task Scheduler or NSSM instead
- Direct execution stops when session ends

### Issue: High CPU/Memory Usage

**Monitor:**
```powershell
# Check resource usage
Get-Process python | Format-Table Name, CPU, WorkingSet -AutoSize

# View threads
Get-Process python | Select-Object -ExpandProperty Threads
```

**Solutions:**
- Increase timeframe (use 15m or 1h instead of 1m)
- Reduce number of pairs being monitored
- Check for memory leaks in logs
- Restart the bot periodically (scheduled task)

---

## Advanced Configuration

### Automatic Daily Restart

Some traders prefer to restart the bot daily to clear memory.

**Create Additional Trigger:**
```powershell
# Get the task
$Task = Get-ScheduledTask -TaskName "CryptoTradingBot"

# Add daily restart trigger
$Trigger = New-ScheduledTaskTrigger -Daily -At 3:00AM

# Register with new trigger
Set-ScheduledTask -TaskName "CryptoTradingBot" -Trigger $Trigger
```

### Email Notifications on Crash

**Using PowerShell Script:**

Create `monitor_and_alert.ps1`:
```powershell
$TaskName = "CryptoTradingBot"
$EmailTo = "your-email@example.com"
$EmailFrom = "bot@example.com"
$SMTPServer = "smtp.gmail.com"

while ($true) {
    $Task = Get-ScheduledTask -TaskName $TaskName
    $Info = Get-ScheduledTaskInfo -TaskName $TaskName

    if ($Info.LastTaskResult -ne 0) {
        # Task failed, send email
        Send-MailMessage `
            -To $EmailTo `
            -From $EmailFrom `
            -Subject "Trading Bot Alert: Task Failed" `
            -Body "The trading bot has encountered an error. Check logs immediately." `
            -SmtpServer $SMTPServer `
            -Port 587 `
            -UseSsl `
            -Credential (Get-Credential)
    }

    Start-Sleep -Seconds 300  # Check every 5 minutes
}
```

### Remote Management

**Enable PowerShell Remoting:**
```powershell
# On bot machine (as Admin)
Enable-PSRemoting -Force

# From another machine
Enter-PSSession -ComputerName BotMachine -Credential (Get-Credential)

# Manage bot remotely
Get-ScheduledTask -TaskName "CryptoTradingBot" | Select-Object State
```

### Backup Configuration

**Automated Backup Script:**
```powershell
# backup_config.ps1
$BackupDir = "C:\temp\Crypto_Bot\backups\$(Get-Date -Format 'yyyy-MM-dd')"
New-Item -ItemType Directory -Path $BackupDir -Force

Copy-Item ".env" -Destination $BackupDir
Copy-Item "config.yaml" -Destination $BackupDir
Copy-Item "trading_bot.db" -Destination $BackupDir

Write-Host "Backup created: $BackupDir"
```

**Schedule Daily Backup:**
```powershell
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "C:\temp\Crypto_Bot\backup_config.ps1"
$Trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM
Register-ScheduledTask -TaskName "BotBackup" -Action $Action -Trigger $Trigger
```

---

## Performance Optimization

### Prevent Sleep Mode

**PowerShell (as Admin):**
```powershell
# Disable sleep
powercfg -change -standby-timeout-ac 0
powercfg -change -standby-timeout-dc 0

# Disable hibernation
powercfg -h off
```

### Optimize Python Performance

**Use Release Mode:**
```cmd
# Run with optimizations
python -O run_bot_24_7.py --mode paper --pair BTC/USDT
```

**Increase Process Priority:**
```powershell
# Set to Above Normal (do not use Realtime)
$Process = Get-Process python
$Process.PriorityClass = "AboveNormal"
```

---

## Security Best Practices

### ✅ DO:
- Use paper trading mode for testing
- Start with testnet before live trading
- Keep `.env` file secure (never commit to git)
- Regularly backup database and configuration
- Monitor logs daily
- Set up alerts for unusual activity
- Use 2FA on exchange account
- Limit API key permissions (no withdrawals)

### ❌ DON'T:
- Share API keys
- Run as SYSTEM account (use your user account)
- Ignore error logs
- Run multiple instances simultaneously
- Disable Windows Firewall completely
- Use weak passwords

---

## Quick Reference Commands

```powershell
# START BOT
Start-ScheduledTask -TaskName "CryptoTradingBot"

# STOP BOT
Stop-ScheduledTask -TaskName "CryptoTradingBot"

# CHECK STATUS
Get-ScheduledTask -TaskName "CryptoTradingBot" | Select-Object State

# VIEW LOGS (real-time)
Get-Content C:\temp\Crypto_Bot\logs\bot_runner.log -Wait -Tail 50

# SEARCH ERRORS
Select-String -Path C:\temp\Crypto_Bot\logs\*.log -Pattern "ERROR" | Select-Object -Last 20

# CHECK PERFORMANCE
Get-Process python | Format-Table Name, CPU, WorkingSet, StartTime

# RESTART BOT
Stop-ScheduledTask -TaskName "CryptoTradingBot"; Start-Sleep -Seconds 5; Start-ScheduledTask -TaskName "CryptoTradingBot"

# REMOVE SERVICE (if needed)
Unregister-ScheduledTask -TaskName "CryptoTradingBot" -Confirm:$false
```

---

## Support

- **Documentation**: [README.md](README.md)
- **Installation Help**: [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)
- **Backtest Guide**: [BACKTEST_RESULTS_GUIDE.md](BACKTEST_RESULTS_GUIDE.md)
- **GitHub**: https://github.com/spsuresha/CryptoBot.git

---

## ⚠️ Final Checklist Before Going 24/7

- [ ] Tested extensively with backtesting
- [ ] Paper traded for 2-4 weeks
- [ ] Tested on Binance testnet
- [ ] `.env` and `config.yaml` properly configured
- [ ] All dependencies installed
- [ ] Logs directory exists and is writable
- [ ] Task Scheduler / NSSM service configured
- [ ] Automatic restart enabled
- [ ] Monitoring and alerts set up
- [ ] Backup strategy in place
- [ ] Emergency stop procedure documented
- [ ] API keys have correct permissions
- [ ] Initial position sizes are small
- [ ] Sleep mode disabled
- [ ] Network connection is stable

---

**Your bot is ready to run 24/7!** 🚀

Start with paper trading and gradually transition to live trading once you're confident.

**Happy Trading!** 💰
