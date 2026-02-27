// Trading Bot Dashboard - Client-side JavaScript
// Auto-refreshing dashboard with real-time updates

let chart = null;
let currentFilter = 'all';
let allTrades = [];

// Format currency
function formatCurrency(value) {
    const num = parseFloat(value);
    const sign = num >= 0 ? '+' : '';
    return sign + '$' + num.toFixed(2);
}

// Format percentage
function formatPercent(value) {
    const num = parseFloat(value);
    const sign = num >= 0 ? '+' : '';
    return sign + num.toFixed(2) + '%';
}

// Update last update timestamp
function updateTimestamp() {
    const now = new Date();
    document.getElementById('last-update').textContent = now.toLocaleTimeString();
}

// Fetch and update bot status
async function updateStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        // Update status badge
        const statusBadge = document.getElementById('status-badge');
        const botStatus = data.running ? 'running' : 'stopped';
        statusBadge.textContent = botStatus.toUpperCase();
        statusBadge.className = 'status-badge ' + botStatus;

        // Update uptime
        document.getElementById('uptime').textContent = data.uptime || '-';

        // Update total P&L
        const pnlElement = document.getElementById('total-pnl');
        pnlElement.textContent = formatCurrency(data.total_pnl);
        pnlElement.className = 'status-value pnl';
        if (data.total_pnl > 0) {
            pnlElement.classList.add('positive');
        } else if (data.total_pnl < 0) {
            pnlElement.classList.add('negative');
        }

        // Update win rate
        document.getElementById('win-rate').textContent = data.win_rate.toFixed(1) + '%';

        // Update total trades
        document.getElementById('num-trades').textContent = data.num_trades;

        // Update Sharpe ratio
        document.getElementById('sharpe-ratio').textContent = data.sharpe_ratio.toFixed(2);

    } catch (error) {
        console.error('Error fetching status:', error);
    }
}

// Fetch and update open positions
async function updatePositions() {
    try {
        const response = await fetch('/api/positions');
        const positions = await response.json();

        const container = document.getElementById('positions-container');
        const countElement = document.getElementById('positions-count');

        countElement.textContent = positions.length;

        if (positions.length === 0) {
            container.innerHTML = '<p class="no-data">No open positions</p>';
            return;
        }

        container.innerHTML = positions.map(pos => `
            <div class="position-card">
                <div class="position-header">
                    <div class="position-symbol">${pos.symbol}</div>
                    <div class="position-pnl ${pos.unrealized_pnl >= 0 ? 'positive' : 'negative'}">
                        ${formatCurrency(pos.unrealized_pnl)}
                    </div>
                </div>
                <div class="position-details">
                    <div>
                        <span>Entry Price:</span>
                        <span>$${pos.entry_price.toFixed(2)}</span>
                    </div>
                    <div>
                        <span>Quantity:</span>
                        <span>${pos.quantity.toFixed(4)}</span>
                    </div>
                    <div>
                        <span>Entry Time:</span>
                        <span>${new Date(pos.entry_time).toLocaleString()}</span>
                    </div>
                    <div>
                        <span>Stop Loss:</span>
                        <span>${pos.stop_loss ? '$' + pos.stop_loss.toFixed(2) : '-'}</span>
                    </div>
                    <div>
                        <span>Take Profit:</span>
                        <span>${pos.take_profit ? '$' + pos.take_profit.toFixed(2) : '-'}</span>
                    </div>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error fetching positions:', error);
    }
}

// Fetch and update recent trades
async function updateTrades() {
    try {
        const response = await fetch('/api/trades?limit=20');
        allTrades = await response.json();

        renderTrades();

    } catch (error) {
        console.error('Error fetching trades:', error);
    }
}

// Render trades based on current filter
function renderTrades() {
    const container = document.getElementById('trades-container');

    let filteredTrades = allTrades;

    if (currentFilter === 'winners') {
        filteredTrades = allTrades.filter(t => t.pnl > 0);
    } else if (currentFilter === 'losers') {
        filteredTrades = allTrades.filter(t => t.pnl < 0);
    }

    if (filteredTrades.length === 0) {
        container.innerHTML = '<p class="no-data">No trades found</p>';
        return;
    }

    container.innerHTML = filteredTrades.map(trade => {
        const isWinner = trade.pnl >= 0;
        return `
            <div class="trade-card ${isWinner ? 'winner' : 'loser'}">
                <div class="trade-header">
                    <div>
                        <div class="trade-symbol">${trade.symbol}</div>
                        <span class="trade-side ${trade.side}">${trade.side.toUpperCase()}</span>
                    </div>
                    <div class="trade-pnl ${isWinner ? 'positive' : 'negative'}">
                        ${formatCurrency(trade.pnl)}
                        <div style="font-size: 0.875rem;">(${formatPercent(trade.pnl_percent)})</div>
                    </div>
                </div>
                <div class="trade-details">
                    <div>
                        <span>Entry:</span>
                        <span>$${trade.entry_price.toFixed(2)}</span>
                    </div>
                    <div>
                        <span>Exit:</span>
                        <span>$${trade.exit_price ? trade.exit_price.toFixed(2) : '-'}</span>
                    </div>
                    <div>
                        <span>Quantity:</span>
                        <span>${trade.quantity.toFixed(4)}</span>
                    </div>
                    <div>
                        <span>Fees:</span>
                        <span>$${trade.fees.toFixed(2)}</span>
                    </div>
                    <div>
                        <span>Exit Time:</span>
                        <span>${trade.exit_time ? new Date(trade.exit_time).toLocaleString() : '-'}</span>
                    </div>
                    ${trade.exit_reason ? `
                        <div>
                            <span>Reason:</span>
                            <span>${trade.exit_reason}</span>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
}

// Setup trade filters
function setupTradeFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn');

    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active state
            filterButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update current filter
            currentFilter = btn.dataset.filter;

            // Re-render trades
            renderTrades();
        });
    });
}

// Fetch and update daily P&L chart
async function updateChart() {
    try {
        const response = await fetch('/api/daily_stats?days=7');
        const data = await response.json();

        const canvas = document.getElementById('pnl-chart');
        const ctx = canvas.getContext('2d');

        // Destroy existing chart if any
        if (chart) {
            chart.destroy();
        }

        // Create simple bar chart
        const dates = data.dates.map(d => {
            const date = new Date(d);
            return `${date.getMonth() + 1}/${date.getDate()}`;
        });

        const pnlData = data.pnl;

        // Calculate canvas dimensions
        const width = canvas.width;
        const height = canvas.height;
        const padding = 40;
        const chartWidth = width - (padding * 2);
        const chartHeight = height - (padding * 2);

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        // Find min/max for scaling
        const maxPnl = Math.max(...pnlData, 0);
        const minPnl = Math.min(...pnlData, 0);
        const range = maxPnl - minPnl || 1;

        // Draw bars
        const barWidth = chartWidth / dates.length;
        const zeroY = padding + (maxPnl / range) * chartHeight;

        pnlData.forEach((value, index) => {
            const barHeight = Math.abs(value) / range * chartHeight;
            const x = padding + (index * barWidth);
            const y = value >= 0 ? zeroY - barHeight : zeroY;

            // Draw bar
            ctx.fillStyle = value >= 0 ? '#10b981' : '#ef4444';
            ctx.fillRect(x + 2, y, barWidth - 4, barHeight);

            // Draw date label
            ctx.fillStyle = '#d1d5db';
            ctx.font = '12px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(dates[index], x + barWidth / 2, height - 10);
        });

        // Draw zero line
        ctx.strokeStyle = '#6b7280';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padding, zeroY);
        ctx.lineTo(width - padding, zeroY);
        ctx.stroke();

        // Draw y-axis labels
        ctx.fillStyle = '#d1d5db';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText('$' + maxPnl.toFixed(0), padding - 5, padding + 5);
        ctx.fillText('$0', padding - 5, zeroY + 5);
        if (minPnl < 0) {
            ctx.fillText('$' + minPnl.toFixed(0), padding - 5, height - padding + 5);
        }

    } catch (error) {
        console.error('Error fetching daily stats:', error);
    }
}

// Fetch and update system stats
async function updateSystemStats() {
    try {
        const response = await fetch('/api/system');
        const data = await response.json();

        // Update CPU
        const cpuBar = document.getElementById('cpu-bar');
        cpuBar.style.width = data.cpu_percent + '%';
        if (data.cpu_percent > 80) {
            cpuBar.classList.add('warning');
        } else {
            cpuBar.classList.remove('warning');
        }
        document.getElementById('cpu-value').textContent = data.cpu_percent.toFixed(1) + '%';

        // Update Memory
        const memoryBar = document.getElementById('memory-bar');
        memoryBar.style.width = data.memory_percent + '%';
        if (data.memory_percent > 80) {
            memoryBar.classList.add('warning');
        } else {
            memoryBar.classList.remove('warning');
        }
        document.getElementById('memory-value').textContent =
            `${data.memory_percent.toFixed(1)}% (${data.memory_used_gb.toFixed(1)}/${data.memory_total_gb.toFixed(1)} GB)`;

        // Update Disk
        const diskBar = document.getElementById('disk-bar');
        diskBar.style.width = data.disk_percent + '%';
        if (data.disk_percent > 80) {
            diskBar.classList.add('warning');
        } else {
            diskBar.classList.remove('warning');
        }
        document.getElementById('disk-value').textContent =
            `${data.disk_percent.toFixed(1)}% (${data.disk_used_gb.toFixed(1)}/${data.disk_total_gb.toFixed(1)} GB)`;

    } catch (error) {
        console.error('Error fetching system stats:', error);
    }
}

// Update all data
async function updateAll() {
    updateTimestamp();
    await Promise.all([
        updateStatus(),
        updatePositions(),
        updateTrades(),
        updateChart(),
        updateSystemStats()
    ]);
}

// Initialize dashboard
async function init() {
    console.log('Initializing dashboard...');

    // Setup trade filters
    setupTradeFilters();

    // Setup manual refresh button
    document.getElementById('refresh-btn').addEventListener('click', updateAll);

    // Initial load
    await updateAll();

    // Auto-refresh every 10 seconds
    setInterval(updateAll, 10000);

    console.log('Dashboard initialized. Auto-refreshing every 10 seconds.');
}

// Start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
