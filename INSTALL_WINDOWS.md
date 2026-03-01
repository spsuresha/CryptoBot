# Windows Installation Guide

## Quick Fix for "Failed to build pandas" Error

If you're getting the pandas build error, use one of these solutions:

### Solution 1: Use Pre-built Packages (Fastest)

```bash
# Install packages that don't need compilation first
pip install PyYAML==6.0.1 python-dotenv==1.0.0 ccxt==4.2.25 SQLAlchemy==2.0.25 requests==2.31.0 python-dateutil==2.8.2 schedule==1.2.1 Flask==3.0.0 psutil==5.9.8

# Install data science packages (pre-built wheels)
pip install numpy pandas matplotlib seaborn

# Install remaining packages
pip install pandas-ta python-telegram-bot pytest pytest-asyncio pytest-mock
```

### Solution 2: Install from Conda (Recommended for Data Science)

```bash
# If you have Anaconda or Miniconda installed
conda create -n cryptobot python=3.10
conda activate cryptobot
conda install numpy pandas matplotlib seaborn
pip install -r requirements.txt
```

### Solution 3: Install Microsoft C++ Build Tools (Complete Solution)

1. **Download**: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. **Install**: Visual Studio Build Tools 2022
3. **Select**: "Desktop development with C++"
4. **Install size**: ~6 GB
5. **Restart** your terminal
6. **Run**: `pip install -r requirements.txt`

---

## Step-by-Step Installation

### 1. Install Python

Download Python 3.9+ from: https://www.python.org/downloads/

✅ **Important**: Check "Add Python to PATH" during installation!

### 2. Open PowerShell/CMD as Administrator

```powershell
# Right-click PowerShell → "Run as Administrator"
```

### 3. Navigate to Project Directory

```bash
cd C:\temp\Crypto_Bot
```

### 4. Install Dependencies (Choose Method)

**Method A: Pre-built Packages (Fast - 2 minutes)**
```bash
pip install PyYAML python-dotenv ccxt SQLAlchemy requests python-dateutil schedule Flask psutil
pip install numpy pandas matplotlib seaborn
pip install pandas-ta python-telegram-bot pytest pytest-asyncio pytest-mock
```

**Method B: From Requirements (Requires Build Tools - 10 minutes)**
```bash
pip install -r requirements.txt
```

### 5. Create Configuration Files

```bash
# Copy example files
copy .env.example .env
copy config.yaml.example config.yaml
```

### 6. Configure API Keys

Edit `.env` file:
```env
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here
ENVIRONMENT=testnet
```

### 7. Test Installation

```bash
# Test with demo (no API needed)
python demo_backtest.py

# Test web dashboard (no trading)
python web_dashboard.py
```

---

## Troubleshooting

### Issue: "pip is not recognized"

**Solution:**
```bash
# Add Python to PATH
# Windows Key → "Environment Variables"
# Edit PATH → Add: C:\Users\YOUR_USERNAME\AppData\Local\Programs\Python\Python311\
# And: C:\Users\YOUR_USERNAME\AppData\Local\Programs\Python\Python311\Scripts\
```

Or reinstall Python with "Add to PATH" checked.

### Issue: "ModuleNotFoundError: No module named 'yaml'"

**Solution:**
```bash
pip install PyYAML
```

### Issue: "error: Microsoft Visual C++ 14.0 or greater is required"

**Solutions:**

**Option 1: Use pre-built wheels**
```bash
pip install --only-binary :all: numpy pandas matplotlib
```

**Option 2: Install Build Tools**
- Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Install: "Desktop development with C++"
- Restart terminal

**Option 3: Use conda**
```bash
conda install numpy pandas matplotlib seaborn
```

### Issue: "Access Denied" when installing packages

**Solution:**
```bash
# Run as Administrator, or install for user only:
pip install --user -r requirements.txt
```

### Issue: SSL Certificate Error

**Solution:**
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### Issue: Packages install but imports fail

**Solution:**
```bash
# Verify Python version (needs 3.9+)
python --version

# Check installed packages
pip list

# Reinstall specific package
pip uninstall numpy
pip install numpy
```

---

## Alternative: Minimal Installation

If you only want to test the dashboard or demo:

```bash
# Minimal install (no backtesting/trading)
pip install Flask psutil SQLAlchemy python-dotenv PyYAML

# Run dashboard only
python web_dashboard.py
```

For backtesting/trading, you'll need the full installation.

---

## Virtual Environment (Recommended)

Keep dependencies isolated:

```bash
# Create virtual environment
python -m venv venv

# Activate (PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (CMD)
.\venv\Scripts\activate.bat

# Install packages
pip install PyYAML python-dotenv ccxt SQLAlchemy Flask psutil
pip install numpy pandas matplotlib seaborn pandas-ta

# Deactivate when done
deactivate
```

---

## Python Version Compatibility

| Python | Status | Notes |
|--------|--------|-------|
| 3.11 | ✅ Recommended | Best compatibility |
| 3.10 | ✅ Good | Well tested |
| 3.9 | ✅ Good | Stable |
| 3.12 | ⚠️ Experimental | Some packages may have issues |
| 3.8 | ⚠️ Old | End of life soon |

---

## Firewall Configuration

After installation, allow dashboard access:

```powershell
# Run as Administrator
New-NetFirewallRule -DisplayName "Trading Bot Dashboard" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

---

## Quick Start After Installation

```bash
# 1. Configure API keys in .env
notepad .env

# 2. Run demo backtest
python demo_backtest.py

# 3. Start web dashboard
python web_dashboard.py

# 4. Run actual backtest (requires API)
python main.py backtest --pair BTC/USDT --start 2024-06-01 --end 2024-12-31
```

---

## Getting Help

If installation fails:

1. **Check Python version**: `python --version` (needs 3.9+)
2. **Update pip**: `python -m pip install --upgrade pip`
3. **Try pre-built wheels**: See Solution 1 above
4. **Use conda**: See Solution 2 above
5. **Check error messages**: Google specific error

---

## Installation Checklist

- [ ] Python 3.9+ installed
- [ ] Python added to PATH
- [ ] Dependencies installed (one of the 3 solutions)
- [ ] `.env` file created and configured
- [ ] `config.yaml` file created
- [ ] Firewall configured (for dashboard)
- [ ] Demo backtest runs successfully
- [ ] Web dashboard accessible

---

## Next Steps

After successful installation:

1. **Read**: [QUICKSTART.md](QUICKSTART.md)
2. **Configure**: Edit `.env` and `config.yaml`
3. **Test**: Run demo backtest
4. **Dashboard**: Launch web dashboard
5. **Backtest**: Test strategy on historical data
6. **Paper Trade**: Practice with fake money
7. **Go Live**: Deploy 24/7 (see WINDOWS_24_7_SETUP.md)

---

**Need help?** Open an issue on GitHub with:
- Python version (`python --version`)
- Error message (full traceback)
- Installation method tried
- Windows version
