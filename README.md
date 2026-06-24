# Crude Oil Signal Bot (MCX, Upstox + Telegram)

An intraday signal bot for MCX Crude Oil. It pulls futures candle data from
Upstox, runs a simple rule-based strategy (EMA trend + ATR volatility filter
+ breakout trigger), and sends CE/PE buy alerts to a Telegram chat.

## ⚠️ Read this before you rely on it

- **This is not a profitable trading system.** It's a transparent rules
  framework so every alert is explainable. Backtest and paper-trade before
  risking real money. Past performance of any strategy (including this one)
  does not predict future results.
- **No live option premium.** Upstox's API does **not** provide a live
  options chain for the MCX exchange. The bot can only compute signals from
  the **futures** price and tell you the suggested strike/direction — you
  must check the actual CE/PE LTP on your broker app yourself before placing
  any order. The "BUY @ ___" line is intentionally left blank.
- **MCX API trading status changes.** Upstox has, in the past, temporarily
  disabled MCX algo/API trading during regulatory transitions (SEBI's
  "Safer participation of retail investors in Algorithmic trading"
  framework). This bot only *reads* data and sends Telegram messages — it
  never places orders — so it's unaffected by order-placement restrictions,
  but if Upstox disables MCX data access entirely, the bot will fail to
  fetch candles. Check https://community.upstox.com for current status if
  it stops working.
- **You place all trades manually.** This bot does not connect to your
  demat/trading account for order execution. It only sends you a Telegram
  message; you decide whether to act on it.

## How it works

1. On startup, downloads Upstox's MCX instrument master file and finds the
   current (nearest unexpired) CRUDEOIL futures contract automatically —
   so it doesn't break when the contract rolls over each month.
2. Every `CHECK_INTERVAL_SECONDS` (default 5 min) during market hours,
   fetches the latest intraday candles for that contract.
3. Computes EMA(9), EMA(21), ATR(14), and a rolling N-candle high/low.
4. If price breaks the recent high while in an EMA-confirmed uptrend →
   suggests a CE buy. Breaks the recent low in a downtrend → suggests PE.
5. SL/TP1/TP2 are set as ATR multiples from the current price (adapts to
   volatility instead of using fixed point distances).
6. Sends a formatted message to your Telegram chat. Repeated signals in the
   same direction are suppressed for `MIN_MINUTES_BETWEEN_SAME_SIGNAL` to
   avoid spam while a trend persists.

## Project structure

```
bot/
  config.py        # all settings, loaded from environment variables
  instruments.py    # finds current CRUDEOIL futures instrument_key
  upstox_client.py  # Upstox API wrapper (candle data)
  indicators.py     # EMA, ATR, rolling high/low (no external deps)
  strategy.py        # signal generation logic
  notifier.py        # Telegram message formatting + sending
  main.py             # scheduling loop, entry point
  test_sanity.py      # quick logic checks with synthetic data
requirements.txt
railway.toml
.env.example
```

## Setup

### 1. Get a Telegram bot token

1. Message [@BotFather](https://t.me/BotFather) on Telegram, send `/newbot`,
   follow the prompts. You'll get a token like `123456:ABC-DEF...`.
2. Send any message to your new bot from your personal account (or add it
   to a group/channel).
3. Find your chat ID by visiting:
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   and looking for `"chat":{"id": ...}` in the response.

### 2. Get an Upstox access token (do this every trading day)

Upstox access tokens are valid only for the current day and must be
regenerated each morning. The general flow:

1. Go to https://account.upstox.com/developer/apps and create an app if you
   haven't (you'll get an `api_key` / `api_secret` and set a redirect URI).
2. Each morning, open this URL in a browser (replace `YOUR_API_KEY` and
   `YOUR_REDIRECT_URI`):
   ```
   https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id=YOUR_API_KEY&redirect_uri=YOUR_REDIRECT_URI
   ```
3. Log in, approve access. You'll be redirected with a `code` query param.
4. Exchange that code for an access token:
   ```bash
   curl -X POST https://api.upstox.com/v2/login/authorization/token \
     -H 'Content-Type: application/x-www-form-urlencoded' \
     -d 'code=YOUR_CODE' \
     -d 'client_id=YOUR_API_KEY' \
     -d 'client_secret=YOUR_API_SECRET' \
     -d 'redirect_uri=YOUR_REDIRECT_URI' \
     -d 'grant_type=authorization_code'
   ```
5. Copy the `access_token` from the response and set it as the
   `UPSTOX_ACCESS_TOKEN` environment variable on Railway (under your
   project's **Variables** tab). The bot will keep using it until it
   expires; you'll need to repeat this each trading day.

   *(This manual step is the one part of the pipeline that can't be fully
   automated without storing your Upstox login credentials, which this
   project intentionally avoids for security reasons. Some people script
   steps 2-4 with a headless browser; that's outside this bot's scope.)*

### 3. Deploy to Railway

1. Push this folder to a new GitHub repository.
2. On [Railway](https://railway.app), create a new project → **Deploy from
   GitHub repo** → select your repo.
3. Railway will detect `railway.toml` and use Nixpacks automatically.
4. Under **Variables**, add:
   - `UPSTOX_ACCESS_TOKEN`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - (optionally) any of the strategy/scheduling overrides from
     `.env.example`
5. Deploy. Check the **Logs** tab to confirm it starts and resolves the
   current CRUDEOIL contract without errors.
6. Each trading morning, update `UPSTOX_ACCESS_TOKEN` in Railway's Variables
   tab with the fresh token (step 2 above), which will trigger a redeploy.

### 4. Local testing (optional, before deploying)

```bash
cp .env.example .env
# edit .env with real values
pip install -r requirements.txt
export $(grep -v '^#' .env | xargs)  # load env vars into shell
python -m bot.test_sanity   # sanity checks with synthetic data
python -m bot.main          # run the real loop (only sends real Telegram messages during market hours)
```

## Tuning the strategy

All of these are environment variables (see `.env.example` for defaults):

| Variable | Meaning |
|---|---|
| `EMA_FAST` / `EMA_SLOW` | Trend filter periods |
| `ATR_PERIOD` | Volatility lookback |
| `BREAKOUT_LOOKBACK` | N-candle high/low for breakout trigger |
| `CANDLE_INTERVAL_MINUTES` | Candle timeframe used for analysis |
| `SL_ATR_MULT` / `TP1_ATR_MULT` / `TP2_ATR_MULT` | Stop/target distance as ATR multiples |
| `STRIKE_STEP` | Strike rounding (50 for standard MCX crude oil cycles) |
| `CHECK_INTERVAL_SECONDS` | How often the bot polls for a new signal |
| `MIN_MINUTES_BETWEEN_SAME_SIGNAL` | Cooldown to avoid repeat alerts |

Edit `bot/strategy.py` directly if you want to replace the logic entirely —
it's intentionally written as one self-contained function (`evaluate()`) so
swapping in your own rules doesn't require touching the rest of the bot.

## License

Use, modify, and deploy freely for your own personal use.
