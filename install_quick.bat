@echo off
echo ========================================
echo Trading Bot - Quick Windows Install
echo ========================================
echo.
echo This script installs packages without compilation errors.
echo.
pause

echo.
echo [1/4] Installing core packages...
pip install PyYAML==6.0.1 python-dotenv==1.0.0 ccxt==4.2.25 SQLAlchemy==2.0.25 requests==2.31.0 python-dateutil==2.8.2 schedule==1.2.1 Flask==3.0.0 psutil==5.9.8

echo.
echo [2/4] Installing data science packages (pre-built)...
pip install numpy pandas matplotlib seaborn

echo.
echo [3/4] Installing remaining packages...
pip install pandas-ta python-telegram-bot pytest pytest-asyncio pytest-mock

echo.
echo [4/4] Creating config files...
if not exist .env copy .env.example .env
if not exist config.yaml copy config.yaml.example config.yaml

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your API keys
echo 2. Run demo: python demo_backtest.py
echo 3. Start dashboard: python web_dashboard.py
echo.
echo See INSTALL_WINDOWS.md for troubleshooting.
echo.
pause
