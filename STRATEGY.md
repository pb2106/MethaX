# MethaX Trading Strategy

**Complete Rule-Based Options Trading Strategy Documentation**

---

## 🎯 Strategy Philosophy

### Core Principles

1. **Trade WITH Trend, NEVER Predict**
   - We follow market structure, not forecast it
   - Indicators identify current state, not future direction
   - Reactive approach, not predictive

2. **Multi-Timeframe Confirmation**
   - Higher timeframe (15m) defines overall bias
   - Lower timeframe (5m) provides execution signals
   - ALL timeframes must align before entry

3. **Event-Driven Processing**
   - Process closed candles only (NO look-ahead)
   - Each decision must be reproducible
   - Log every filter evaluation

4. **Strict Risk Management**
   - Hard position limits
   - Automatic kill switch
   - No discretionary overrides

---

## 📊 Indicator Specification

### 1. EMA(10) - Fast Momentum Line

**Configuration:**
- Period: 10
- Timeframe: 5-minute
- Chart Color: RED

**Calculation:**
```python
EMA = Price(t) × k + EMA(t-1) × (1 - k)
where k = 2 / (period + 1) = 2 / 11 = 0.1818
```

**Purpose:** 
- Detects short-term momentum shifts
- Generates crossover signals with EMA(20)
- Primary signal generator

### 2. EMA(20) - Slow Momentum Line

**Configuration:**
- Period: 20
- Timeframe: 5-minute
- Chart Color: BLUE

**Calculation:**
```python
EMA = Price(t) × k + EMA(t-1) × (1 - k)
where k = 2 / (period + 1) = 2 / 21 = 0.0952
```

**Purpose:**
- Slower momentum confirmation
- Crossover partner with EMA(10)
- Filters noise in fast EMA

### 3. DEMA(100) - Dominant Trend Filter

**Configuration:**
- Period: 100
- Timeframe: 15-minute
- Chart Color: BLACK

**Calculation:**
```python
DEMA = 2 × EMA(period) - EMA(EMA(period))
# More responsive than simple EMA, less lag
```

**Slope Calculation:**
```python
slope = linear_regression_slope(DEMA[-3:])  # Last 3 candles
# Positive = uptrend (bullish bias)
# Negative = downtrend (bearish bias)
# Near-zero = no clear bias (no trades)
```

**Purpose:**
- Hard trend filter (never trade against this)
- Defines bullish/bearish market bias
- Prevents counter-trend trades

---

## ⏱️ Timeframe Architecture

### Dual-Timeframe System

**15-Minute Timeframe (Trend Identification)**

Role: Determine overall market bias

Logic:
```
IF price > DEMA(100) AND DEMA_slope ≥ 0:
    bias = BULLISH
    → Only CALL trades allowed

ELIF price < DEMA(100) AND DEMA_slope ≤ 0:
    bias = BEARISH
    → Only PUT trades allowed

ELSE:
    bias = NEUTRAL
    → NO trades allowed
```

**5-Minute Timeframe (Execution)**

Role: Generate precise entry signals

Indicators: EMA(10), EMA(20)

Logic:
- Detect crossovers on closed candles
- Signals are IGNORED unless 15m bias aligns

**Critical Rule:** 
5-minute signals MUST align with 15-minute bias. No exceptions.

---

## 🎯 Entry Logic (Complete Ruleset)

### Bullish Entry - BUY CALL Option

**All conditions must be TRUE:**

#### 1. Crossover Confirmation (5-Minute)
```
Previous Candle: EMA(10) < EMA(20)
Current Candle:  EMA(10) > EMA(20)
```
**Not Valid:**
- Touching but not crossing
- Overlapping
- Near-misses

#### 2. Trend Alignment (15-Minute)
```
Current NIFTY Price > DEMA(100)
AND
DEMA(100) slope ≥ 0 (flat or rising)
```
**Reject if:**
- Price below DEMA(100)
- DEMA slope is negative

#### 3. Time Filter
```
Non-Expiry Days: 09:30 - 14:45 IST
Expiry Days:     09:30 - 15:00 IST
```
**NO trades:**
- First 15 minutes (09:15-09:30) - opening volatility
- Last 45 minutes non-expiry (after 14:45)
- Weekends or market holidays

#### 4. Risk Limits
```
Daily Trades < MAX_DAILY_TRADES (2)
Daily Loss < MAX_DAILY_LOSS (1R)
Kill Switch = OFF
```

**Action:** Buy ATM Call option (CE)
- Strike: Round NIFTY to nearest 50
- If ATM unavailable: Use ATM+1 strike

**Example:**
```
NIFTY Spot: 22,347.50 → ATM Strike: 22,350 CE
Entry Price: ₹150.50
Stop Loss: ₹140.20 (0.8 × ATR)
Target: ₹170.80 (1.6 × ATR, 1:2 R:R)
```

---

### Bearish Entry - BUY PUT Option

**All conditions must be TRUE:**

#### 1. Crossover Confirmation (5-Minute)
```
Previous Candle: EMA(10) > EMA(20)
Current Candle:  EMA(10) < EMA(20)
```

#### 2. Trend Alignment (15-Minute)
```
Current NIFTY Price < DEMA(100)
AND
DEMA(100) slope ≤ 0 (flat or falling)
```

#### 3. Time Filter
(Same as bullish)

#### 4. Risk Limits
(Same as bullish)

**Action:** Buy ATM Put option (PE)
- Strike: Round NIFTY to nearest 50
- If ATM unavailable: Use ATM-1 strike

---

### Entry Rejection Logging

When **ANY** condition fails:

```json
{
  "timestamp": "2024-01-15 10:35:00 IST",
  "potential_signal": "bullish_crossover",
  "rejected": true,
  "reasons": [
    "FAILED: DEMA(100) slope is NEGATIVE (-0.23)",
    "FAILED: 15m bias is BEARISH but 5m signal is BULLISH",
    "MISMATCH: Trend alignment check failed"
  ],
  "filter_results": {
    "crossover_confirmation": true,
    "trend_alignment": false,
    "time_filter": true,
    "risk_limits": true
  }
}
```

---

## 🚪 Exit Logic (Multiple Conditions)

Position **MUST** be closed when **ANY** occurs:

### 1. Opposite Crossover

**For CALL position:**
```
EMA(10) crosses BELOW EMA(20)
→ Exit immediately at next available price
```

**For PUT position:**
```
EMA(10) crosses ABOVE EMA(20)
→ Exit immediately at next available price
```

### 2. Stop-Loss Hit

**Calculation at Entry:**
```python
ATR = calculate_atr(candles_5m, period=14)

For CALL:
    SL = entry_price - (ATR × 0.8)

For PUT:
    SL = entry_price + (ATR × 0.8)
```

**Action:** Close position immediately if breached

### 3. Target Hit

**Calculation at Entry:**
```python
For CALL:
    Target = entry_price + (ATR × 1.6)  # 1:2 Risk:Reward

For PUT:
    Target = entry_price - (ATR × 1.6)
```

**Minimum R:R:** 1:1 (but target 1:2 preferred)

### 4. Time-Based Exit

**Non-Expiry Days:**
```
Close ALL positions by 14:45 IST
No exceptions - liquidate at market price
```

**Expiry Days:**
```
Close ALL positions by 15:00 IST
```

### 5. Kill Switch Activation

**Triggers:**
- Daily loss exceeds 1R
- Manual activation

**Action:**
- Close all positions immediately
- Block new trades until manual reset

### 6. Maximum Time in Trade

**Hard Limit:** 30 minutes after entry

**Reason:** Prevents holding through major trend changes

**Action:** Force close at current market price

---

## 🛡️ Risk Management (Institution-Grade)

### Capital & Position Sizing

**Starting Capital:** ₹100,000 (virtual)

**Position Sizing Formula:**
```python
def calculate_position_size(
    capital: float,
    risk_per_trade: float,  # 0.01 = 1%
    stop_loss_points: float,
    lot_size: int = 25
) -> int:
    """
    Calculate lot size based on fixed R per trade
    
    Example:
    capital = 100,000
    risk_per_trade = 0.01 (1%)
    risk_amount = 100,000 × 0.01 = 1,000
    
    If SL is 10 points away:
    lots = 1,000 / (10 × 25) = 4 lots
    """
    risk_amount = capital * risk_per_trade
    sl_points = abs(stop_loss_points)
    
    if sl_points == 0:
        return 1  # Minimum 1 lot
    
    lots = int(risk_amount / (sl_points * lot_size))
    return max(1, lots)  # Minimum 1 lot
```

### Hard Limits (NEVER VIOLATED)

| Parameter | Value | Enforcement |
|-----------|-------|-------------|
| MAX_DAILY_TRADES | 2 | After 2nd trade, block all new entries |
| RISK_PER_TRADE | 1% (0.01) | Fixed R per position |
| MAX_DAILY_LOSS | 1R (₹1,000) | Activate kill switch if breached |
| MAX_POSITION_TIME | 30 minutes | Force close after time limit |
| NO_TRADE_MORNING | 09:15-09:30 | Hard block period |
| NO_TRADE_EOD | After 14:45 | Hard block (non-expiry) |

### Kill Switch Behavior

**Trigger Conditions:**
1. Daily loss exceeds 1R (₹1,000 on ₹100k capital)
2. Manual activation via API or UI

**Actions When Active:**
1. Close all open positions immediately
2. Set `kill_switch_active = True` in database
3. Reject all new trade requests
4. Log event with timestamp and reason

**Deactivation:**
- **Automatic:** Reset at 09:10 IST next trading day
- **Manual:** Admin endpoint (authenticated)

**Logging:**
```json
{
  "event": "kill_switch_activated",
  "timestamp": "2024-01-15 14:30:00 IST",
  "reason": "daily_loss_exceeded",
  "daily_loss_r": -1.05,
  "positions_closed": 1,
  "capital_before": 100000,
  "capital_after": 98950
}
```

---

## 🔢 Options Pricing Model

### ATM Strike Selection

```python
def get_atm_strike(spot_price: float, strike_interval: int = 50) -> float:
    """
    Round NIFTY spot to nearest strike
    
    Examples:
    22,347 → 22,350
    22,324 → 22,300
    22,375 → 22,400
    """
    return round(spot_price / strike_interval) * strike_interval
```

### Simplified Option Pricing

For virtual trading, we use a simplified model:

```python
def calculate_option_price(
    spot_price: float,
    strike: float,
    option_type: str,  # 'CE' or 'PE'
    time_to_expiry_days: float,
    volatility: float = 0.15
) -> float:
    """
    Simplified pricing for virtual trading
    
    Components:
    1. Intrinsic value
    2. Time value (delta-based)
    3. Decay factor
    """
    # Intrinsic value
    if option_type == 'CE':
        intrinsic = max(spot_price - strike, 0)
    else:  # PE
        intrinsic = max(strike - spot_price, 0)
    
    # Time value (simplified)
    # ATM options have ~0.5 delta
    extrinsic = 50 * (time_to_expiry_days / 7)
    
    # Bid-ask spread (slippage)
    slippage = 0.001  # 0.1%
    
    price = (intrinsic + extrinsic) * (1 + slippage)
    return round(price, 2)
```

### Delta Simulation

- **ATM options:** delta ≈ 0.45-0.55
- **Price movement:** For every 1 point NIFTY moves, ATM option moves ~0.5 points
- **Update frequency:** Every 5 minutes based on spot movement

### Transaction Costs

- **Entry slippage:** 0.05% - 0.1% of option price
- **Exit slippage:** 0.05% - 0.1% of option price
- **Brokerage:** 0% (virtual trading, but can add 0.05% if desired)

---

## 📋 Entry Checklist (Use This!)

Before entering ANY trade:

```
□ Candle is CLOSED (not in progress)
□ EMA(10) crossed EMA(20) on THIS candle
□ 15m DEMA(100) bias aligns (BULL/BEAR)
□ DEMA(100) slope matches direction (≥0 for BULL, ≤0 for BEAR)
□ Current time is 09:30-14:45 (non-expiry)
□ Daily trades < 2
□ Daily loss < 1R
□ Kill switch is OFF
□ ATR calculated for stops
□ Position size calculated correctly
□ All filters logged in entry_filters JSON
```

---

## 🧮 P&L Calculation

### Per Trade

```python
def calculate_trade_pnl(
    entry_price: float,
    exit_price: float,
    direction: str,  # 'CALL' or 'PUT'
    lots: int,
    lot_size: int = 25
) -> tuple[float, float]:
    """
    Calculate P&L in absolute and R terms
    """
    # Points difference
    pnl_per_lot = (exit_price - entry_price) * lot_size
    
    # Total P&L
    total_pnl = pnl_per_lot * lots
    
    # R multiple (risk was 1% = ₹1,000)
    risk_amount = 1000
    pnl_r = total_pnl / risk_amount
    
    return total_pnl, pnl_r
```

**Example:**
```
Entry: ₹150.50
Exit: ₹170.80 (target hit)
Lots: 2
Lot Size: 25

Points Gained: 170.80 - 150.50 = 20.30
P&L per Lot: 20.30 × 25 = ₹507.50
Total P&L: 507.50 × 2 = ₹1,015
R Multiple: 1,015 / 1,000 = 1.015R
```

---

## 🎓 Strategy Examples

### Example 1: Valid Bullish Entry

**Scenario:**
- Time: 10:30 IST (Monday)
- NIFTY Spot: 22,350
- 15m DEMA(100): 22,300 (slope: +0.15)
- 5m EMA(10): 22,348 (previous), 22,352 (current)
- 5m EMA(20): 22,350
- Daily trades: 0

**Evaluation:**
```
✅ Crossover: EMA(10) crossed ABOVE EMA(20)
✅ Trend: Price (22,350) > DEMA (22,300)
✅ Slope: DEMA slope positive (+0.15)
✅ Time: 10:30 is within 09:30-14:45
✅ Limits: 0 trades, no loss

RESULT: EXECUTE TRADE
Strike: 22,350 CE
Entry: ₹148.50
SL: ₹138.20
Target: ₹168.80
```

### Example 2: Rejected Entry (Trend Mismatch)

**Scenario:**
- Time: 11:00 IST
- NIFTY Spot: 22,280
- 15m DEMA(100): 22,320 (slope: -0.08)
- 5m EMA(10): 22,278 (previous), 22,283 (current)
- 5m EMA(20): 22,280

**Evaluation:**
```
✅ Crossover: EMA(10) crossed ABOVE EMA(20)
❌ Trend: Price (22,280) < DEMA (22,320)
❌ Slope: DEMA slope NEGATIVE (-0.08)
✅ Time: Valid
✅ Limits: OK

RESULT: REJECT TRADE
Reason: 15m bias is BEARISH, but 5m signal is BULLISH
Log: Filter mismatch - trend_alignment failed
```

---

## 📊 Performance Metrics

Track these metrics for strategy evaluation:

- **Total Trades:** Count of all executed trades
- **Win Rate:** Wins / Total Trades
- **Average R:** Total P&L in R / Total Trades
- **Expectancy:** (Win% × Avg Win) - (Loss% × Avg Loss)
- **Max Drawdown:** Largest peak-to-trough decline
- **Profit Factor:** Gross Profit / Gross Loss
- **Filter Effectiveness:** Executed / Total Signals

---

**Remember:** This strategy is deterministic. Same market conditions → same decisions. Every trade must be reproducible and auditable.
