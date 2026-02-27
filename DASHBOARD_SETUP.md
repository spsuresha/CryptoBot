# Web Dashboard Setup Guide

## Overview

The web dashboard provides a mobile-friendly interface to monitor your trading bot from anywhere. You can view:
- Bot status and uptime
- Total P&L and performance metrics
- Open positions with real-time unrealized P&L
- Recent trades with filters
- Daily P&L chart
- System resource usage

## Features

✅ **Mobile-Responsive Design** - Works perfectly on phones and tablets
✅ **Auto-Refresh** - Updates every 10 seconds automatically
✅ **Real-Time Data** - Shows current positions and recent trades
✅ **Performance Charts** - Visual representation of daily P&L
✅ **Basic Authentication** - Secure with username/password
✅ **System Monitoring** - CPU, memory, and disk usage

---

## Quick Start

### 1. Install Dependencies

```bash
pip install Flask==3.0.0 psutil==5.9.8
```

### 2. Configure Credentials

Create or update your `.env` file:

```env
# Dashboard authentication
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=your_secure_password_here

# Dashboard settings
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=5000
DASHBOARD_DEBUG=False
```

**Important:** Change the default password!

### 3. Start the Dashboard

```bash
python web_dashboard.py
```

You'll see output like:
```
============================================================
Trading Bot Web Dashboard
============================================================
Starting dashboard on http://0.0.0.0:5000
Username: admin
Password: your_secure_password_here

To access from your phone:
1. Find your computer's IP address (ipconfig/ifconfig)
2. Open browser on phone and go to: http://YOUR_IP:5000
3. Login with username and password above
============================================================
```

### 4. Access from Your Computer

Open browser and go to: **http://localhost:5000**

### 5. Access from Your Phone

**Step 1: Find Your Computer's IP Address**

**Windows:**
```cmd
ipconfig
```
Look for "IPv4 Address" under your active network adapter (e.g., `192.168.1.100`)

**Linux/Mac:**
```bash
ifconfig
# or
ip addr show
```

**Step 2: Connect Your Phone to Same WiFi**

Make sure your phone is on the same WiFi network as your computer.

**Step 3: Open Browser on Phone**

Go to: `http://YOUR_IP_ADDRESS:5000`

Example: `http://192.168.1.100:5000`

**Step 4: Login**

Enter your username and password when prompted.

---

## Firewall Configuration

### Windows Firewall

Allow incoming connections on port 5000:

**Option 1: Using PowerShell (Admin)**
```powershell
New-NetFirewallRule -DisplayName "Trading Bot Dashboard" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

**Option 2: Using GUI**
1. Open Windows Defender Firewall
2. Click "Advanced settings"
3. Click "Inbound Rules" → "New Rule"
4. Select "Port" → Next
5. Select "TCP" and enter port `5000` → Next
6. Select "Allow the connection" → Next
7. Apply to all profiles → Next
8. Name it "Trading Bot Dashboard" → Finish

### Linux Firewall (UFW)

```bash
sudo ufw allow 5000/tcp
sudo ufw reload
```

---

## Running as a Service

### Option 1: Windows Task Scheduler

Create `start_dashboard.bat`:
```batch
@echo off
cd C:\temp\Crypto_Bot
python web_dashboard.py
```

**Configure Task Scheduler:**
1. Open Task Scheduler
2. Create Basic Task → "Trading Bot Dashboard"
3. Trigger: "When the computer starts"
4. Action: Start a program
5. Program: `C:\temp\Crypto_Bot\start_dashboard.bat`
6. Check "Run with highest privileges"

### Option 2: Using NSSM (Windows)

```cmd
# Install NSSM service
nssm install TradingBotDashboard

# Configure in NSSM GUI:
# - Path: C:\Users\...\python.exe
# - Startup directory: C:\temp\Crypto_Bot
# - Arguments: web_dashboard.py

# Start service
nssm start TradingBotDashboard
```

### Option 3: Linux systemd

Create `/etc/systemd/system/trading-dashboard.service`:
```ini
[Unit]
Description=Trading Bot Dashboard
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/Crypto_Bot
ExecStart=/usr/bin/python3 /path/to/Crypto_Bot/web_dashboard.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable trading-dashboard
sudo systemctl start trading-dashboard
sudo systemctl status trading-dashboard
```

---

## Security Best Practices

### ✅ DO:

1. **Change Default Password**
   ```env
   DASHBOARD_PASSWORD=use_a_strong_unique_password
   ```

2. **Use Strong Password**
   - At least 12 characters
   - Mix of letters, numbers, symbols
   - Don't reuse passwords

3. **Bind to Specific IP (Production)**
   ```env
   # Only allow local connections
   DASHBOARD_HOST=127.0.0.1

   # Or bind to specific network interface
   DASHBOARD_HOST=192.168.1.100
   ```

4. **Use HTTPS (Production)**
   - Use a reverse proxy like nginx with SSL certificate
   - Use Let's Encrypt for free SSL certificates

5. **Limit Network Access**
   - Only open firewall port to trusted IPs
   - Use VPN for remote access

6. **Monitor Access**
   - Check logs regularly
   - Watch for failed login attempts

### ❌ DON'T:

1. **Don't Use Default Credentials**
2. **Don't Expose to Public Internet** without HTTPS
3. **Don't Use DEBUG=True** in production
4. **Don't Share Credentials**
5. **Don't Access Over Public WiFi** without VPN

---

## Advanced Configuration

### Custom Port

Change port in `.env`:
```env
DASHBOARD_PORT=8080
```

### Enable Debug Mode (Development Only)

```env
DASHBOARD_DEBUG=True
```

**Warning:** Never use debug mode in production!

### Custom Secret Key

For session security:
```env
DASHBOARD_SECRET_KEY=your-random-secret-key-here
```

Generate random key:
```python
import secrets
print(secrets.token_hex(32))
```

---

## Using a Reverse Proxy (Production)

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name tradingbot.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name tradingbot.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Update Flask config:
```env
DASHBOARD_HOST=127.0.0.1
```

---

## Accessing Remotely via VPN

### Option 1: Tailscale (Easiest)

1. **Install Tailscale** on computer and phone: https://tailscale.com/download
2. **Sign up** and connect both devices
3. **Access dashboard** using Tailscale IP (e.g., `http://100.x.x.x:5000`)

### Option 2: WireGuard

1. **Setup WireGuard server** on your computer
2. **Configure client** on your phone
3. **Connect** and access via internal IP

### Option 3: OpenVPN

1. **Setup OpenVPN server**
2. **Install OpenVPN client** on phone
3. **Connect** and access dashboard

---

## Troubleshooting

### Issue: Can't Access from Phone

**Check:**
```powershell
# Check if dashboard is running
Get-Process python | Where-Object {$_.CommandLine -like "*web_dashboard*"}

# Check if port is listening
netstat -an | findstr :5000

# Test from computer first
curl http://localhost:5000/health
```

**Solutions:**
- Verify computer and phone on same WiFi
- Check firewall allows port 5000
- Verify IP address is correct
- Try restarting dashboard

### Issue: Authentication Fails

**Check:**
```python
# Verify credentials in .env
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('User:', os.getenv('DASHBOARD_USERNAME')); print('Pass:', os.getenv('DASHBOARD_PASSWORD'))"
```

**Solutions:**
- Check username/password in `.env`
- Clear browser cache/cookies
- Try different browser
- Restart dashboard

### Issue: Data Not Showing

**Check:**
```bash
# Verify database exists
ls -la trading_bot.db

# Check database has data
python -c "from src.database.repository import TradeRepository; r = TradeRepository(); print('Trades:', len(r.get_all_trades()))"
```

**Solutions:**
- Run bot first to generate data
- Check database path in config
- Verify bot is actually trading

### Issue: Dashboard Crashes

**Check logs:**
```bash
# Run dashboard with debug output
DASHBOARD_DEBUG=True python web_dashboard.py
```

**Common causes:**
- Missing dependencies (`pip install -r requirements.txt`)
- Database locked (close other connections)
- Port already in use (change port)

### Issue: Slow Loading

**Solutions:**
- Reduce auto-refresh interval in `script.js`
- Limit number of trades displayed
- Check system resources
- Optimize database queries

---

## Mobile App Shortcuts

### iOS (Safari)

1. Open dashboard in Safari
2. Tap Share button
3. Tap "Add to Home Screen"
4. Name it "Trading Bot"
5. Tap "Add"

Now you have an app icon to launch dashboard!

### Android (Chrome)

1. Open dashboard in Chrome
2. Tap menu (3 dots)
3. Tap "Add to Home screen"
4. Name it "Trading Bot"
5. Tap "Add"

---

## API Endpoints

The dashboard provides REST API endpoints:

| Endpoint | Description | Auth Required |
|----------|-------------|---------------|
| `GET /` | Dashboard HTML | Yes |
| `GET /api/status` | Bot status & metrics | Yes |
| `GET /api/positions` | Open positions | Yes |
| `GET /api/trades?limit=N` | Recent trades | Yes |
| `GET /api/daily_stats?days=N` | Daily P&L data | Yes |
| `GET /api/system` | System resources | Yes |
| `GET /health` | Health check | No |

### Example API Usage

```bash
# Health check (no auth)
curl http://localhost:5000/health

# Get status (with auth)
curl -u admin:password http://localhost:5000/api/status

# Get trades
curl -u admin:password http://localhost:5000/api/trades?limit=10
```

---

## Customization

### Change Auto-Refresh Interval

Edit `static/script.js`:
```javascript
// Change from 10 seconds to 30 seconds
setInterval(updateAll, 30000);
```

### Change Color Scheme

Edit `static/style.css`:
```css
:root {
    --primary-color: #2563eb;  /* Change to your preferred color */
    --success-color: #10b981;
    --danger-color: #ef4444;
    /* ... */
}
```

### Add Custom Metrics

Edit `web_dashboard.py` and add new API endpoint:
```python
@app.route('/api/custom_metric')
@requires_auth
def api_custom_metric():
    # Your custom logic here
    return jsonify({'value': 123})
```

---

## Performance Tips

1. **Use Limits**: Fetch only necessary data
   ```python
   get_recent_trades(limit=20)  # Don't fetch too many trades
   ```

2. **Cache Data**: Implement caching for expensive queries
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=128)
   def expensive_calculation():
       # ...
   ```

3. **Database Indexes**: Ensure database has proper indexes
   ```sql
   CREATE INDEX idx_trades_exit_time ON trades(exit_time);
   CREATE INDEX idx_positions_status ON positions(status);
   ```

4. **Optimize Queries**: Use database pagination
   ```python
   trades = session.query(Trade).limit(20).offset(0).all()
   ```

---

## Monitoring Dashboard Itself

Check if dashboard is running:

**Windows:**
```powershell
Get-Process python | Where-Object {$_.CommandLine -like "*web_dashboard*"}
```

**Linux:**
```bash
ps aux | grep web_dashboard
```

Check access logs:
```bash
# Dashboard prints access logs to console
# Redirect to file:
python web_dashboard.py >> logs/dashboard.log 2>&1
```

---

## Quick Reference Commands

```bash
# START DASHBOARD
python web_dashboard.py

# START IN BACKGROUND (Windows)
start /B python web_dashboard.py

# START IN BACKGROUND (Linux)
nohup python web_dashboard.py &

# STOP DASHBOARD
# Press Ctrl+C or kill process

# CHECK IF RUNNING
curl http://localhost:5000/health

# VIEW FROM PHONE
http://YOUR_IP:5000

# TEST API
curl -u admin:password http://localhost:5000/api/status
```

---

## Screenshots Description

When you open the dashboard, you'll see:

1. **Header**: Title and last update timestamp
2. **Bot Status Card**:
   - Status badge (Running/Stopped)
   - Uptime
   - Total P&L (green/red)
   - Win rate
   - Total trades
   - Sharpe ratio
3. **Daily P&L Chart**: Bar chart showing last 7 days
4. **Open Positions**:
   - Symbol and unrealized P&L
   - Entry price, quantity, entry time
   - Stop loss and take profit levels
5. **Recent Trades**:
   - Filter buttons (All/Winners/Losers)
   - Trade cards with entry/exit, P&L, details
6. **System Resources**:
   - CPU, memory, disk usage bars
7. **Footer**: Auto-refresh info and manual refresh button

---

## Support

For issues or questions:

1. Check this guide first
2. Review Flask documentation: https://flask.palletsprojects.com/
3. Check bot logs in `logs/` directory
4. Verify database with: `sqlite3 trading_bot.db`

---

## Security Checklist

Before exposing dashboard remotely:

- [ ] Changed default password
- [ ] Using HTTPS (if over internet)
- [ ] Firewall configured properly
- [ ] VPN or reverse proxy in place
- [ ] Debug mode disabled
- [ ] Strong authentication credentials
- [ ] Regular monitoring of access logs
- [ ] Dashboard only on trusted networks

---

**Your dashboard is ready!** 📱

Access it from your phone and monitor your bot anywhere! 🚀
