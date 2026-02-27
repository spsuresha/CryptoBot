"""
Flask web dashboard for cryptocurrency trading bot.
Provides mobile-friendly interface to monitor bot status, positions, and trades.
"""
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from functools import wraps

from flask import Flask, render_template, jsonify, request, Response
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
import psutil

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.models import Base, Trade, Position, BotState, PerformanceMetrics
from src.config.settings import Settings

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('DASHBOARD_SECRET_KEY', 'change-this-secret-key-in-production')

# Load settings
settings = Settings()

# Database setup
engine = create_engine(f'sqlite:///{settings.database_path}')
Session = sessionmaker(bind=engine)

# Basic authentication
DASHBOARD_USERNAME = os.getenv('DASHBOARD_USERNAME', 'admin')
DASHBOARD_PASSWORD = os.getenv('DASHBOARD_PASSWORD', 'crypto123')


def check_auth(username: str, password: str) -> bool:
    """Check if username/password is valid."""
    return username == DASHBOARD_USERNAME and password == DASHBOARD_PASSWORD


def authenticate():
    """Send 401 response for authentication."""
    return Response(
        'Authentication required. Please login.',
        401,
        {'WWW-Authenticate': 'Basic realm="Trading Bot Dashboard"'}
    )


def requires_auth(f):
    """Decorator for routes that require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


def get_bot_status() -> Dict:
    """Get current bot status."""
    session = Session()
    try:
        # Check if bot process is running
        bot_running = False
        bot_pid = None
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('main.py' in cmd or 'run_bot_24_7.py' in cmd for cmd in cmdline):
                    bot_running = True
                    bot_pid = proc.info['pid']
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Get bot state from database
        bot_state = session.query(BotState).filter_by(key='status').first()

        # Get latest performance metrics
        latest_metrics = session.query(PerformanceMetrics).order_by(
            desc(PerformanceMetrics.date)
        ).first()

        # Get uptime
        uptime_state = session.query(BotState).filter_by(key='start_time').first()
        uptime = None
        if uptime_state and uptime_state.value:
            try:
                start_time = datetime.fromisoformat(uptime_state.value)
                uptime = str(datetime.now() - start_time).split('.')[0]
            except:
                pass

        return {
            'running': bot_running,
            'pid': bot_pid,
            'status': bot_state.value if bot_state else 'unknown',
            'uptime': uptime,
            'total_pnl': float(latest_metrics.total_pnl) if latest_metrics else 0.0,
            'win_rate': float(latest_metrics.win_rate) if latest_metrics else 0.0,
            'num_trades': latest_metrics.num_trades if latest_metrics else 0,
            'sharpe_ratio': float(latest_metrics.sharpe_ratio) if latest_metrics and latest_metrics.sharpe_ratio else 0.0,
            'max_drawdown': float(latest_metrics.max_drawdown) if latest_metrics and latest_metrics.max_drawdown else 0.0,
        }
    finally:
        session.close()


def get_open_positions() -> List[Dict]:
    """Get all open positions."""
    session = Session()
    try:
        positions = session.query(Position).filter_by(status='open').all()

        result = []
        for pos in positions:
            # Calculate unrealized P&L (simplified - would need current price for accurate calc)
            result.append({
                'id': pos.id,
                'symbol': pos.symbol,
                'entry_price': float(pos.entry_price),
                'quantity': float(pos.quantity),
                'entry_time': pos.entry_time.strftime('%Y-%m-%d %H:%M:%S'),
                'unrealized_pnl': float(pos.unrealized_pnl) if pos.unrealized_pnl else 0.0,
                'stop_loss': float(pos.stop_loss) if pos.stop_loss else None,
                'take_profit': float(pos.take_profit) if pos.take_profit else None,
            })

        return result
    finally:
        session.close()


def get_recent_trades(limit: int = 20) -> List[Dict]:
    """Get recent closed trades."""
    session = Session()
    try:
        trades = session.query(Trade).filter_by(status='closed').order_by(
            desc(Trade.exit_time)
        ).limit(limit).all()

        result = []
        for trade in trades:
            result.append({
                'id': trade.id,
                'symbol': trade.symbol,
                'side': trade.side,
                'entry_price': float(trade.entry_price),
                'exit_price': float(trade.exit_price) if trade.exit_price else None,
                'quantity': float(trade.quantity),
                'entry_time': trade.entry_time.strftime('%Y-%m-%d %H:%M:%S') if trade.entry_time else None,
                'exit_time': trade.exit_time.strftime('%Y-%m-%d %H:%M:%S') if trade.exit_time else None,
                'pnl': float(trade.pnl) if trade.pnl else 0.0,
                'pnl_percent': float(trade.pnl_percent) if trade.pnl_percent else 0.0,
                'fees': float(trade.fees) if trade.fees else 0.0,
                'exit_reason': trade.exit_reason,
            })

        return result
    finally:
        session.close()


def get_daily_stats(days: int = 7) -> Dict:
    """Get daily statistics for last N days."""
    session = Session()
    try:
        start_date = datetime.now() - timedelta(days=days)

        trades = session.query(Trade).filter(
            Trade.exit_time >= start_date,
            Trade.status == 'closed'
        ).all()

        # Calculate daily stats
        daily_pnl = {}
        for trade in trades:
            if trade.exit_time:
                date_key = trade.exit_time.strftime('%Y-%m-%d')
                if date_key not in daily_pnl:
                    daily_pnl[date_key] = 0.0
                daily_pnl[date_key] += float(trade.pnl) if trade.pnl else 0.0

        # Fill in missing days with 0
        for i in range(days):
            date_key = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            if date_key not in daily_pnl:
                daily_pnl[date_key] = 0.0

        # Sort by date
        sorted_dates = sorted(daily_pnl.keys())

        return {
            'dates': sorted_dates,
            'pnl': [daily_pnl[date] for date in sorted_dates]
        }
    finally:
        session.close()


def get_system_stats() -> Dict:
    """Get system resource usage."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_gb': memory.used / (1024**3),
            'memory_total_gb': memory.total / (1024**3),
            'disk_percent': disk.percent,
            'disk_used_gb': disk.used / (1024**3),
            'disk_total_gb': disk.total / (1024**3),
        }
    except Exception as e:
        return {
            'cpu_percent': 0,
            'memory_percent': 0,
            'memory_used_gb': 0,
            'memory_total_gb': 0,
            'disk_percent': 0,
            'disk_used_gb': 0,
            'disk_total_gb': 0,
        }


@app.route('/')
@requires_auth
def dashboard():
    """Main dashboard page."""
    return render_template('dashboard.html')


@app.route('/api/status')
@requires_auth
def api_status():
    """API endpoint for bot status."""
    return jsonify(get_bot_status())


@app.route('/api/positions')
@requires_auth
def api_positions():
    """API endpoint for open positions."""
    return jsonify(get_open_positions())


@app.route('/api/trades')
@requires_auth
def api_trades():
    """API endpoint for recent trades."""
    limit = request.args.get('limit', 20, type=int)
    return jsonify(get_recent_trades(limit))


@app.route('/api/daily_stats')
@requires_auth
def api_daily_stats():
    """API endpoint for daily statistics."""
    days = request.args.get('days', 7, type=int)
    return jsonify(get_daily_stats(days))


@app.route('/api/system')
@requires_auth
def api_system():
    """API endpoint for system stats."""
    return jsonify(get_system_stats())


@app.route('/health')
def health():
    """Health check endpoint (no auth required)."""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})


if __name__ == '__main__':
    # Create database tables if they don't exist
    Base.metadata.create_all(engine)

    # Get host and port from environment
    host = os.getenv('DASHBOARD_HOST', '0.0.0.0')
    port = int(os.getenv('DASHBOARD_PORT', 5000))
    debug = os.getenv('DASHBOARD_DEBUG', 'False').lower() == 'true'

    print("=" * 60)
    print("Trading Bot Web Dashboard")
    print("=" * 60)
    print(f"Starting dashboard on http://{host}:{port}")
    print(f"Username: {DASHBOARD_USERNAME}")
    print(f"Password: {DASHBOARD_PASSWORD}")
    print("\nTo access from your phone:")
    print(f"1. Find your computer's IP address (ipconfig/ifconfig)")
    print(f"2. Open browser on phone and go to: http://YOUR_IP:{port}")
    print(f"3. Login with username and password above")
    print("=" * 60)

    app.run(host=host, port=port, debug=debug)
