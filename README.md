# MethaX

**Institution-Grade NIFTY 50 Options Virtual Trading Platform**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

MethaX is a production-grade virtual trading platform that simulates disciplined, rule-based NIFTY 50 options trading. This is **not** a toy bot or prediction system—it's a serious portfolio project demonstrating institution-level system design, quant-style rule formalization, and realistic market simulation.

**Core Identity:**
- ✅ Virtual/Paper trading ONLY (no real money)
- ✅ Rule-based, deterministic, and fully auditable
- ✅ Designed for intraday options trading on NSE
- ✅ Zero tolerance for look-ahead bias or repainting
- ✅ Professional risk management with hard limits

## 🏗️ Architecture

**Tech Stack:**
- **Backend:** Python 3.10+, FastAPI (async), SQLAlchemy (async ORM)
- **Database:** PostgreSQL (production), SQLite (development)
- **Data:** pandas, numpy for indicator calculations
- **Frontend:** Vanilla JavaScript, TradingView Lightweight Charts
- **Task Scheduling:** APScheduler for background jobs

**Key Features:**
- Multi-timeframe analysis (5m execution, 15m trend filter)
- Event-driven, candle-by-candle processing (NO look-ahead bias)
- Real-time WebSocket updates
- Hard risk limits (2 trades/day, 1R loss limit, kill switch)
- Comprehensive logging and testing

## 📋 Quick Start

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- (Optional) PostgreSQL 15+ for production

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd MethaX
```

2. **Create environment file:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Install dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

4. **Run database migrations:**
```bash
alembic upgrade head
```

5. **Start the backend server:**
```bash
python run.py
```

The API will be available at `http://localhost:8000`

### Accessing the Application

- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/v1/health
- **Dashboard:** http://localhost:8000/api/v1/dashboard

## 🔧 Configuration

Key environment variables in `.env`:

```bash
# Trading Parameters
DEFAULT_CAPITAL=100000          # Starting capital (₹)
MAX_DAILY_TRADES=2              # Max trades per day
RISK_PER_TRADE=0.01            # Risk 1% per trade
MAX_DAILY_LOSS_R=1.0           # Max daily loss (1R)

# Indicator Periods
EMA_FAST_PERIOD=10             # Fast EMA
EMA_SLOW_PERIOD=20             # Slow EMA
DEMA_TREND_PERIOD=100          # DEMA trend filter
ATR_PERIOD=14                  # ATR for stops

# Database
DATABASE_URL=sqlite+aiosqlite:///./methax.db
```

## 📊 Trading Strategy

### Core Philosophy
1. **Trade WITH trend, NEVER predict**
2. **Multi-timeframe confirmation required** (15m bias + 5m signals)
3. **Event-driven processing** (closed candles only)
4. **Explicit rule validation** at every step

### Indicators
- **EMA(10)** - Fast momentum line (5m)
- **EMA(20)** - Slow momentum line (5m)
- **DEMA(100)** - Dominant trend filter (15m)

### Entry Rules

**Bullish (BUY CALL):**
- ✅ EMA(10) crosses **above** EMA(20) on 5m
- ✅ Price > DEMA(100) on 15m
- ✅ DEMA(100) slope ≥ 0
- ✅ Valid trading time (09:30-14:45)
- ✅ Risk limits not breached

**Bearish (BUY PUT):**
- ✅ EMA(10) crosses **below** EMA(20) on 5m
- ✅ Price < DEMA(100) on 15m
- ✅ DEMA(100) slope ≤ 0
- ✅ Valid trading time
- ✅ Risk limits not breached

### Exit Rules
- Opposite crossover
- Stop-loss hit (0.8 × ATR)
- Target hit (1.6 × ATR, 1:2 R:R)
- Time-based (EOD or 30 min max)
- Kill switch activation

## 📁 Project Structure

```
MethaX/
├── backend/
│   ├── app/
│   │   ├── api/          # REST & WebSocket endpoints
│   │   ├── models/       # Database models
│   │   ├── data/         # Data fetching & caching
│   │   ├── indicators/   # Technical calculations
│   │   ├── strategy/     # Trading logic
│   │   ├── execution/    # Virtual order execution
│   │   ├── scheduler/    # Background jobs
│   │   └── utils/        # Helpers
│   ├── alembic/          # Database migrations
│   ├── tests/            # Unit, integration, backtest
│   └── run.py            # Entry point
└── frontend/
    ├── index.html        # Dashboard
    ├── styles.css        # Dark theme
    └── app.js            # WebSocket & UI
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/backtest/ -v
```

## 🚀 Development Phases

- [x] **Phase 1:** Foundation & database setup
- [ ] **Phase 2:** Data layer & mock generator
- [ ] **Phase 3:** Indicator calculations
- [ ] **Phase 4:** Strategy engine
- [ ] **Phase 5:** Execution engine
- [ ] **Phase 6:** API endpoints
- [ ] **Phase 7:** Frontend dashboard
- [ ] **Phase 8:** Background jobs
- [ ] **Phase 9:** Testing & optimization
- [ ] **Phase 10:** Deployment

## 📚 Documentation

- [STRATEGY.md](STRATEGY.md) - Complete trading strategy documentation
- [API Docs](http://localhost:8000/docs) - Interactive API documentation
- [Implementation Plan](implementation_plan.md) - Detailed development plan

## ⚠️ Critical Rules

1. **NO LOOK-AHEAD BIAS** - Only use data available at that moment
2. **NO REPAINTING** - Wait for candle close before processing
3. **DETERMINISTIC** - Same input → same trades
4. **EXPLICIT VALIDATION** - Log WHY trades are rejected
5. **HARD RISK LIMITS** - Enforced at code level, no exceptions

## 🔐 Risk Management

- Maximum 2 trades per day
- Risk 1% of capital per trade
- Daily loss limit: 1R (₹1,000 on ₹100k capital)
- Kill switch auto-activates on limit breach
- Force close all positions at EOD

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

This is a portfolio project. Feel free to fork and adapt for your own learning!

## ⚡ Performance

- Multi-timeframe analysis with async processing
- Real-time WebSocket updates (5s market, 10s positions)
- Event-driven architecture for scalability
- Comprehensive error handling and logging

---

**Disclaimer:** This is a virtual trading platform for educational purposes only. No real money is involved. Past performance does not guarantee future results.
