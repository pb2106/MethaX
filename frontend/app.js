/**
 * MethaX - Interactive Dashboard
 * Real-time trading dashboard with TradingView charts
 */

// Configuration
const CONFIG = {
    API_BASE: 'http://localhost:8000/api/v1',
    WS_URL: 'ws://localhost:8000/api/v1/stream',
    UPDATE_INTERVAL: 5000, // 5 seconds
    DEFAULT_TIMEFRAME: '5m',
};

// Global state
const state = {
    chart: null,
    candleSeries: null,
    ema10Series: null,
    ema20Series: null,
    dema100Series: null,
    currentTimeframe: CONFIG.DEFAULT_TIMEFRAME,
    ws: null,
    lastPrice: null,
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 MethaX Dashboard initializing...');

    initializeChart();
    setupEventListeners();
    loadInitialData();
    startDataUpdates();

    console.log('✅ Dashboard initialized');
});

// Initialize TradingView Chart
function initializeChart() {
    const chartContainer = document.getElementById('tradingview-chart');

    state.chart = LightweightCharts.createChart(chartContainer, {
        layout: {
            background: { color: '#1e222d' },
            textColor: '#d1d4dc',
        },
        grid: {
            vertLines: { color: '#2a2e39' },
            horzLines: { color: '#2a2e39' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
        },
        rightPriceScale: {
            borderColor: '#2a2e39',
        },
        timeScale: {
            borderColor: '#2a2e39',
            timeVisible: true,
            secondsVisible: false,
        },
        watermark: {
            visible: true,
            fontSize: 48,
            horzAlign: 'center',
            vertAlign: 'center',
            color: 'rgba(255, 255, 255, 0.03)',
            text: 'NIFTY 50',
        },
    });

    // Create candlestick series
    state.candleSeries = state.chart.addCandlestickSeries({
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderVisible: false,
        wickUpColor: '#26a69a',
        wickDownColor: '#ef5350',
    });

    // Create EMA(10) line
    state.ema10Series = state.chart.addLineSeries({
        color: '#ff5252',
        lineWidth: 2,
        title: 'EMA(10)',
    });

    // Create EMA(20) line
    state.ema20Series = state.chart.addLineSeries({
        color: '#2979ff',
        lineWidth: 2,
        title: 'EMA(20)',
    });

    // Create DEMA(100) line
    state.dema100Series = state.chart.addLineSeries({
        color: '#ffd54f',
        lineWidth: 2,
        title: 'DEMA(100)',
    });

    // Make chart responsive
    new ResizeObserver(() => {
        state.chart.applyOptions({
            width: chartContainer.clientWidth,
        });
    }).observe(chartContainer);
}

// Setup event listeners
function setupEventListeners() {
    // Timeframe buttons
    document.querySelectorAll('.timeframe-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const timeframe = btn.dataset.timeframe;
            switchTimeframe(timeframe);
        });
    });

    // Kill switch button
    const killSwitchBtn = document.getElementById('kill-switch-btn');
    killSwitchBtn.addEventListener('click', () => {
        activateKillSwitch();
    });

    // Refresh signals
    const refreshBtn = document.getElementById('refresh-signals');
    refreshBtn.addEventListener('click', () => {
        loadInitialData();
    });
}

// Load initial data
async function loadInitialData() {
    try {
        updateStatus('Loading data...');

        // Load dashboard data
        await updateDashboard();

        // Load chart data
        await loadChartData(state.currentTimeframe);

        updateStatus('Connected', true);
    } catch (error) {
        console.error('Error loading initial data:', error);
        updateStatus('Error loading data', false);
    }
}

// Update dashboard data
async function updateDashboard() {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/dashboard`);
        const data = await response.json();

        // Update header stats
        updateElement('nifty-price', formatPrice(data.market.nifty_spot));
        updateElement('capital', formatCurrency(data.account.capital));
        updateElement('daily-pnl', formatCurrency(data.account.daily_pnl));
        updateElement('daily-pnl-r', `${data.account.daily_pnl_r.toFixed(2)}R`);

        // Update P&L color
        const pnlElement = document.getElementById('daily-pnl');
        const pnlRElement = document.getElementById('daily-pnl-r');
        if (data.account.daily_pnl >= 0) {
            pnlElement.classList.add('positive');
            pnlElement.classList.remove('negative');
            pnlRElement.classList.add('positive');
            pnlRElement.classList.remove('negative');
        } else {
            pnlElement.classList.add('negative');
            pnlElement.classList.remove('positive');
            pnlRElement.classList.add('negative');
            pnlRElement.classList.remove('positive');
        }

        // Update market status
        const statusBadge = document.getElementById('market-status');
        statusBadge.textContent = data.market.is_open ? 'Market Open' : 'Market Closed';
        statusBadge.className = `status-badge ${data.market.is_open ? 'open' : 'closed'}`;

        // Update risk status
        updateRiskStatus(data.risk_status, data.account);

        // Update position count
        updateElement('position-count', data.account.open_positions);

        // Store last price for change calculation
        state.lastPrice = data.market.nifty_spot;

    } catch (error) {
        console.error('Error updating dashboard:', error);
    }
}

// Load chart data
async function loadChartData(timeframe) {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/candles?timeframe=${timeframe}&limit=200`);
        const data = await response.json();

        if (data.candles.length === 0) {
            console.warn('No candle data available');
            return;
        }

        // Convert to TradingView format
        const candleData = data.candles.map(c => ({
            time: new Date(c.timestamp).getTime() / 1000,
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close,
        }));

        state.candleSeries.setData(candleData);

        // TODO: Calculate and display indicators when Phase 3 is complete
        // For now, show placeholder
        updateElement('ema-10', '--');
        updateElement('ema-20', '--');
        updateElement('dema-100', '--');

        // Fit chart to data
        state.chart.timeScale().fitContent();

    } catch (error) {
        console.error('Error loading chart data:', error);
    }
}

// Switch timeframe
function switchTimeframe(timeframe) {
    state.currentTimeframe = timeframe;

    // Update button states
    document.querySelectorAll('.timeframe-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.timeframe === timeframe);
    });

    // Reload chart data
    loadChartData(timeframe);
}

// Update risk status
function updateRiskStatus(riskStatus, account) {
    const canTradeElement = document.getElementById('can-trade');
    const badge = canTradeElement.querySelector('.badge');

    if (riskStatus.can_trade) {
        badge.textContent = 'YES';
        badge.className = 'badge badge-success';
    } else {
        badge.textContent = 'NO';
        badge.className = 'badge badge-danger';
    }

    updateElement('trade-reason', riskStatus.reason);
    updateElement('trades-count', `${account.trades_today} / 2`);
    updateElement('loss-limit', `${Math.abs(account.daily_pnl_r).toFixed(2)}R / 1.00R`);
}

// Activate kill switch
async function activateKillSwitch() {
    if (!confirm('⚠️ ACTIVATE KILL SWITCH?\n\nThis will:\n• Close all open positions immediately\n• Block new trades until manual reset\n\nAre you sure?')) {
        return;
    }

    try {
        const response = await fetch(`${CONFIG.API_BASE}/kill-switch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ activate: true, reason: 'manual_override' })
        });

        const result = await response.json();

        if (result.kill_switch_active) {
            alert('✅ Kill switch activated!\n\nAll positions closed. Trading disabled.');
            await updateDashboard();
        }
    } catch (error) {
        console.error('Error activating kill switch:', error);
        alert('❌ Error activating kill switch. Check console for details.');
    }
}

// Start periodic data updates
function startDataUpdates() {
    setInterval(async () => {
        await updateDashboard();

        // Update current price with real-time data
        try {
            const response = await fetch(`${CONFIG.API_BASE}/current-price`);
            const data = await response.json();

            // Update last update time
            const now = new Date();
            updateElement('last-update', now.toLocaleTimeString('en-IN'));

        } catch (error) {
            console.error('Error fetching current price:', error);
        }
    }, CONFIG.UPDATE_INTERVAL);
}

// Utility functions
function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

function formatPrice(price) {
    return `₹${price.toFixed(2)}`;
}

function formatCurrency(amount) {
    return `₹${amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function updateStatus(message, connected = null) {
    const statusElement = document.getElementById('connection-status');
    const dotElement = statusElement.querySelector('.status-dot');

    statusElement.childNodes[1].textContent = message;

    if (connected !== null) {
        if (connected) {
            dotElement.classList.remove('disconnected');
        } else {
            dotElement.classList.add('disconnected');
        }
    }
}

// Log to console
console.log('%cMethaX Trading Platform', 'color: #2962ff; font-size: 24px; font-weight: bold;');
console.log('%cInstitution-grade virtual trading', 'color: #26a69a; font-size: 14px;');
console.log('%cVersion: 1.0.0', 'color: #787b86; font-size: 12px;');
