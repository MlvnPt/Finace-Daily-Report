#!/usr/bin/env python3
"""
Finance Daily Report Generator
Kombiniert technische Analyse (RSI, Trend, Momentum) mit News-Sentiment
zu BUY/HOLD/SELL-Signalen für heute, basierend auf den Schlusskursen von gestern.
"""

import os
import time
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

FINNHUB_KEY = os.environ.get('FINNHUB_API_KEY', '')

# ticker -> (Anzeigename, Sektor-Key, Waehrung)
STOCKS = {
    'HAG.DE':  ('Hensoldt', 'defense', '€'),
    'NBIS':    ('Nebius AI', 'ai', '$'),
    'CSCO':    ('Cisco Systems', 'tech', '$'),
    'RHM.DE':  ('Rheinmetall', 'defense', '€'),
    'ATRO':    ('Astronics', 'industrie', '$'),
    'ZETA':    ('Zeta Global', 'ai', '$'),
    'NET':     ('Cloudflare', 'tech', '$'),
    'CAT':     ('Caterpillar', 'industrie', '$'),
    'XOM':     ('Exxon Mobil', 'energie', '$'),
    'ENR.DE':  ('Siemens Energy', 'industrie', '€'),
    'SIE.DE':  ('Siemens', 'industrie', '€'),
    'SAP':     ('SAP', 'tech', '$'),
    'UNH':     ('UnitedHealth', 'pharma', '$'),
    'AAPL':    ('Apple', 'tech', '$'),
    'NOC':     ('Northrop Grumman', 'defense', '$'),
    'TKA.DE':  ('Thyssenkrupp', 'industrie', '€'),
    'PYPL':    ('PayPal', 'finanz', '$'),
    'LMT':     ('Lockheed Martin', 'defense', '$'),
    'JPM':     ('JP Morgan', 'finanz', '$'),
    'URTH':    ('MSCI World', 'indizes', '$'),
    '^GSPC':   ('S&P 500', 'indizes', '$'),
    'RYCEY':   ('Rolls Royce', 'defense', '$'),
    'AMZN':    ('Amazon', 'consumer', '$'),
    'NKE':     ('Nike', 'consumer', '$'),
    'PLTR':    ('Palantir', 'ai', '$'),
    'MA':      ('Mastercard', 'finanz', '$'),
    'MSFT':    ('Microsoft', 'tech', '$'),
    'PAAS':    ('Pan American Silver', 'energie', '$'),
    'NVDA':    ('Nvidia', 'tech', '$'),
    'NVO':     ('Novo Nordisk', 'pharma', '$'),
    'MRNA':    ('Moderna', 'pharma', '$'),
    'TSLA':    ('Tesla', 'mobilitaet', '$'),
    'GOOGL':   ('Alphabet', 'tech', '$'),
    'GS':      ('Goldman Sachs', 'finanz', '$'),
    'DRO.AX':  ('Droneshield', 'defense', '$'),
    'META':    ('Meta', 'tech', '$'),
    'SNDK':    ('Sandisk', 'tech', '$'),
    'ASML':    ('ASML', 'tech', '$'),
    'BAS.DE':  ('BASF', 'energie', '€'),
    'ORCL':    ('Oracle', 'tech', '$'),
    'INTC':    ('Intel', 'tech', '$'),
    'BYDDY':   ('BYD', 'mobilitaet', '$'),
}
# Hinweis: Space X ist nicht boersennotiert und daher nicht enthalten.

SECTORS = {
    'tech':        '💻 TECHNOLOGIE',
    'finanz':      '🏦 FINANZDIENSTLEISTUNGEN',
    'defense':     '🚀 DEFENSE & AEROSPACE',
    'industrie':   '🏭 INDUSTRIE & MASCHINENBAU',
    'energie':     '⚡ ENERGIE & ROHSTOFFE',
    'pharma':      '💊 PHARMA & HEALTHCARE',
    'consumer':    '🛍️ CONSUMER & EINZELHANDEL',
    'mobilitaet':  '🚗 E-MOBILITÄT',
    'ai':          '🤖 AI & EMERGING',
    'indizes':     '📊 INDIZES & ETFs',
}

POSITIVE_KEYWORDS = [
    'beats estimates', 'beat estimates', 'record revenue', 'record profit',
    'acquisition', 'acquires', 'to acquire', 'partnership', 'invest', 'investment',
    'upgrade', 'raises guidance', 'raises forecast', 'strong demand', 'contract win',
    'new order', 'breakthrough', 'expansion', 'buyback', 'raises dividend'
]
NEGATIVE_KEYWORDS = [
    'misses estimates', 'miss estimates', 'lawsuit', 'recall', 'downgrade',
    'layoffs', 'job cuts', 'investigation', 'decline', 'plunge', 'warns',
    'delay', 'fraud', 'fine', 'penalty', 'weak demand', 'cuts guidance',
    'cuts forecast', 'strike', 'data breach'
]


def compute_rsi(closes, period=14):
    delta = closes.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, 0.0001)
    rsi = 100 - (100 / (1 + rs))
    val = rsi.iloc[-1]
    return float(val) if pd.notna(val) else 50.0


def get_technical(ticker):
    try:
        hist = yf.Ticker(ticker).history(period='3mo')
        if len(hist) < 10:
            return None
        closes = hist['Close']
        current = float(closes.iloc[-1])
        previous = float(closes.iloc[-2])
        change_pct = (current - previous) / previous * 100
        sma5 = float(closes.tail(5).mean())
        sma20 = float(closes.tail(20).mean()) if len(closes) >= 20 else sma5
        rsi = compute_rsi(closes)
        momentum = (current / float(closes.iloc[-6]) - 1) * 100 if len(closes) >= 6 else 0.0
        data_date = hist.index[-1].strftime('%d.%m.%Y')
        trend_up = sma5 > sma20

        score = 0
        if rsi < 30:
            score += 2
        elif rsi > 70:
            score -= 2
        score += 1 if trend_up else -1
        if momentum > 3:
            score += 1
        elif momentum < -3:
            score -= 1

        return {
            'price': round(current, 2),
            'change': round(change_pct, 2),
            'rsi': round(rsi, 1),
            'momentum': round(momentum, 1),
            'trend_up': trend_up,
            'score': score,
            'data_date': data_date,
        }
    except Exception as e:
        print(f"Technical error {ticker}: {e}")
        return None


def get_company_logo(ticker):
    if not FINNHUB_KEY:
        return None
    try:
        url = f"https://finnhub.io/api/v1/stock/profile2?symbol={ticker}&token={FINNHUB_KEY}"
        res = requests.get(url, timeout=10)
        data = res.json()
        logo = data.get('logo')
        return logo if logo else None
    except Exception:
        return None


def get_general_news(target_date_str):
    if not FINNHUB_KEY:
        return []
    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_KEY}"
        res = requests.get(url, timeout=10)
        articles = res.json()
        filtered = []
        for a in articles:
            d = datetime.fromtimestamp(a['datetime']).strftime('%d.%m.%Y')
            if d == target_date_str:
                filtered.append(a)
        return filtered[:8]
    except Exception as e:
        print(f"News error: {e}")
        return []


def get_company_news(finnhub_symbol, from_date, to_date):
    if not FINNHUB_KEY:
        return []
    try:
        url = (f"https://finnhub.io/api/v1/company-news?symbol={finnhub_symbol}"
               f"&from={from_date}&to={to_date}&token={FINNHUB_KEY}")
        res = requests.get(url, timeout=10)
        data = res.json()
        return data if isinstance(data, list) else []
    except Exception:
        return []


def score_news(articles):
    score = 0
    reasons = []
    for a in articles[:15]:
        text = (a.get('headline', '') + ' ' + a.get('summary', '')).lower()
        matched = False
        for kw in POSITIVE_KEYWORDS:
            if kw in text:
                score += 1
                reasons.append(f"🟢 {a.get('headline', '')[:60]}")
                matched = True
                break
        if not matched:
            for kw in NEGATIVE_KEYWORDS:
                if kw in text:
                    score -= 1
                    reasons.append(f"🔴 {a.get('headline', '')[:60]}")
                    break
    return score, reasons[:3]


def build_signal(tech, news_score):
    if tech is None:
        return 'HOLD', '⚪', 0
    total = tech['score'] * 0.6 + news_score * 0.4
    if total >= 1.5:
        return 'BUY', '🟢', total
    elif total <= -1.5:
        return 'SELL', '🔴', total
    else:
        return 'HOLD', '🟡', total


# ---- Hauptprogramm ----
print("📊 Sammle Aktiendaten & News...")

now = datetime.now()
today_str = now.strftime('%d.%m.%Y')

results = {}
data_date_global = None

for ticker, (name, sector, currency) in STOCKS.items():
    tech = get_technical(ticker)
    if tech:
        data_date_global = tech['data_date']
    time.sleep(0.3)

    news_score = 0
    news_reasons = []
    if tech and FINNHUB_KEY and '.' not in ticker and '^' not in ticker:
        to_date = now.strftime('%Y-%m-%d')
        from_date = (now - timedelta(days=5)).strftime('%Y-%m-%d')
        articles = get_company_news(ticker, from_date, to_date)
        news_score, news_reasons = score_news(articles)
        time.sleep(0.3)

    signal, icon, score = build_signal(tech, news_score)

    logo = get_company_logo(ticker) if tech else None
    time.sleep(0.2)

    results[name] = {
        'ticker': ticker,
        'sector': sector,
        'currency': currency,
        'tech': tech,
        'news_score': news_score,
        'news_reasons': news_reasons,
        'signal': signal,
        'icon': icon,
        'score': score,
        'logo': logo,
    }
    if tech:
        print(f"✅ {name}: {tech['price']}{currency} {tech['change']:+.1f}% -> {icon} {signal}")
    else:
        print(f"⚠️ {name}: keine Daten")

general_news = get_general_news(data_date_global or today_str)


# ---- HTML generieren ----

def logo_html(name, d):
    initial = name[0].upper()
    if d.get('logo'):
        return (f'<img class="stock-logo" src="{d["logo"]}" alt="{name}" '
                f'onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\';">'
                f'<div class="stock-logo-placeholder" style="display:none;">{initial}</div>')
    return f'<div class="stock-logo-placeholder">{initial}</div>'


def stock_row(name, d):
    logo = logo_html(name, d)
    if not d['tech']:
        return f'''<div class="stock-item">
            <div class="stock-left">{logo}<div class="stock-name">{name}</div></div>
            <div>⚪ n/a</div>
        </div>'''
    t = d['tech']
    color = 'positive' if t['change'] >= 0 else 'negative'
    arrow = '↑' if t['change'] >= 0 else '↓'
    return f'''<div class="stock-item">
        <div class="stock-left">{logo}<div class="stock-name">{name}</div></div>
        <div class="stock-data">
            <div class="price {color}">{t['price']}{d['currency']} {arrow} {abs(t['change'])}%</div>
            <div class="signal-badge sig-{d['signal'].lower()}">{d['icon']} {d['signal']}</div>
        </div>
    </div>'''


sectors_html = ''
for sector_key, sector_title in SECTORS.items():
    members = [(n, d) for n, d in results.items() if d['sector'] == sector_key]
    if not members:
        continue
    sectors_html += f'<div class="sector"><div class="sector-header">{sector_title}</div>'
    for n, d in members:
        sectors_html += stock_row(n, d)
    sectors_html += '</div>'

news_html = ''
if general_news:
    for a in general_news:
        d = datetime.fromtimestamp(a['datetime']).strftime('%d.%m.%Y')
        news_html += f'''<div class="news-item">
            <div class="news-title">{a.get('headline', '')}</div>
            <div class="news-desc">{(a.get('summary', '') or '')[:150]}</div>
            <div class="news-source">📰 {a.get('source', '')} - {d}</div>
        </div>'''
else:
    news_html = '<div class="loading">Keine News für diesen Tag verfügbar</div>'

sorted_results = sorted(results.items(), key=lambda x: x[1]['score'], reverse=True)
buys = [(n, d) for n, d in sorted_results if d['signal'] == 'BUY']
sells = [(n, d) for n, d in sorted_results if d['signal'] == 'SELL']
holds = [(n, d) for n, d in sorted_results if d['signal'] == 'HOLD']


def forecast_item(name, d):
    t = d['tech']
    reasons = []
    if t:
        if t['rsi'] < 30:
            reasons.append(f"RSI überverkauft ({t['rsi']})")
        elif t['rsi'] > 70:
            reasons.append(f"RSI überkauft ({t['rsi']})")
        reasons.append("Aufwärtstrend" if t['trend_up'] else "Abwärtstrend")
        if abs(t['momentum']) > 3:
            reasons.append(f"Momentum {t['momentum']:+.1f}%")
    if d['news_reasons']:
        reasons.append(f"{len(d['news_reasons'])} relevante News")
    reason_str = ' • '.join(reasons) if reasons else 'Neutrale Datenlage'
    return f'''<div class="prognose-item sig-{d['signal'].lower()}">
        <strong>{d['icon']} {name} — {d['signal']}</strong><br>
        <span style="font-size:11px;color:#aaa;">{reason_str}</span>
    </div>'''


forecast_html = f'<div class="sector"><div class="sector-header">🟢 BUY-Signale ({len(buys)})</div>'
forecast_html += ''.join([forecast_item(n, d) for n, d in buys]) if buys else '<div class="loading">Keine BUY-Signale heute</div>'
forecast_html += '</div>'

forecast_html += f'<div class="sector"><div class="sector-header">🔴 SELL-Signale ({len(sells)})</div>'
forecast_html += ''.join([forecast_item(n, d) for n, d in sells]) if sells else '<div class="loading">Keine SELL-Signale heute</div>'
forecast_html += '</div>'

forecast_html += f'<div class="sector"><div class="sector-header">🟡 HOLD ({len(holds)})</div>'
forecast_html += ''.join([forecast_item(n, d) for n, d in holds])
forecast_html += '</div>'

html = f'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Finance Daily Report</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%); color:#fff; min-height:100vh; }}
.container {{ max-width:600px; margin:0 auto; }}
.tab-navigation {{ display:flex; background:rgba(0,0,0,0.3); border-bottom:2px solid rgba(255,255,255,0.1); position:sticky; top:0; z-index:100; }}
.tab-btn {{ flex:1; padding:12px 10px; background:none; border:none; color:#aaa; font-size:13px; font-weight:600; cursor:pointer; border-bottom:3px solid transparent; }}
.tab-btn.active {{ color:#10b981; border-bottom-color:#10b981; background:rgba(16,185,129,0.1); }}
.tab-content {{ display:none; padding:12px; }}
.tab-content.active {{ display:block; }}
.header {{ background:rgba(255,255,255,0.05); border-radius:12px; padding:16px; margin-bottom:16px; border:1px solid rgba(255,255,255,0.1); }}
.header h1 {{ font-size:24px; margin-bottom:8px; }}
.header .date {{ font-size:12px; color:#aaa; }}
.sector {{ margin-bottom:16px; border-radius:12px; border:1px solid rgba(255,255,255,0.1); background:rgba(255,255,255,0.02); }}
.sector-header {{ background:rgba(255,255,255,0.08); padding:12px 14px; font-weight:600; font-size:14px; }}
.stock-item {{ padding:12px 14px; border-bottom:1px solid rgba(255,255,255,0.05); display:flex; justify-content:space-between; align-items:center; }}
.stock-item:last-child {{ border-bottom:none; }}
.stock-left {{ display:flex; align-items:center; gap:10px; min-width:0; }}
.stock-logo {{ width:28px; height:28px; border-radius:7px; object-fit:contain; background:#fff; padding:3px; flex-shrink:0; }}
.stock-logo-placeholder {{ width:28px; height:28px; border-radius:7px; background:rgba(16,185,129,0.15); color:#10b981; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:700; flex-shrink:0; }}
.stock-name {{ font-weight:600; font-size:14px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.stock-data {{ text-align:right; }}
.price {{ font-weight:bold; font-size:14px; }}
.positive {{ color:#10b981; }}
.negative {{ color:#ef4444; }}
.signal-badge {{ font-size:11px; margin-top:2px; padding:2px 6px; border-radius:6px; display:inline-block; }}
.sig-buy {{ background:rgba(16,185,129,0.2); color:#10b981; }}
.sig-sell {{ background:rgba(239,68,68,0.2); color:#ef4444; }}
.sig-hold {{ background:rgba(234,179,8,0.2); color:#eab308; }}
.update {{ text-align:center; font-size:10px; color:#10b981; padding:8px; }}
.news-item {{ padding:12px 14px; margin-bottom:10px; background:rgba(255,255,255,0.05); border-radius:8px; border-left:3px solid #10b981; }}
.news-title {{ font-weight:600; font-size:13px; margin-bottom:4px; }}
.news-desc {{ font-size:12px; color:#bbb; margin-bottom:6px; line-height:1.4; }}
.news-source {{ font-size:10px; color:#888; }}
.prognose-item {{ padding:10px 14px; margin-bottom:8px; border-radius:8px; background:rgba(255,255,255,0.04); border-left:3px solid #666; }}
.prognose-item.sig-buy {{ border-left-color:#10b981; }}
.prognose-item.sig-sell {{ border-left-color:#ef4444; }}
.prognose-item.sig-hold {{ border-left-color:#eab308; }}
.loading {{ text-align:center; padding:20px; color:#aaa; }}
.disclaimer {{ font-size:10px; color:#666; text-align:center; padding:16px; }}
</style>
</head>
<body>
<div class="container">
<div class="update">✅ Generiert: {now.strftime('%d.%m.%Y %H:%M')} Uhr</div>
<div class="tab-navigation">
<button class="tab-btn active" onclick="switchTab(0)">📊 Finance Report</button>
<button class="tab-btn" onclick="switchTab(1)">📰 Top News</button>
<button class="tab-btn" onclick="switchTab(2)">📈 Prognose</button>
</div>

<div class="tab-content active">
<div class="header">
<h1>📊 Finance Daily Report</h1>
<div class="date">{today_str} • Daten vom {data_date_global or '?'}</div>
</div>
{sectors_html}
</div>

<div class="tab-content">
<div class="header">
<h1>📰 Top News</h1>
<div class="date">vom {data_date_global or today_str}</div>
</div>
{news_html}
</div>

<div class="tab-content">
<div class="header">
<h1>📈 Marktprognose</h1>
<div class="date">für {today_str}</div>
</div>
{forecast_html}
<div class="disclaimer">⚠️ Keine Anlageberatung. Automatisch generiert aus Chart- &amp; News-Daten.</div>
</div>
</div>

<script>
function switchTab(i) {{
  document.querySelectorAll('.tab-content').forEach(e => e.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(e => e.classList.remove('active'));
  document.querySelectorAll('.tab-content')[i].classList.add('active');
  document.querySelectorAll('.tab-btn')[i].classList.add('active');
  window.scrollTo(0,0);
}}
</script>
</body>
</html>
'''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ Fertig! {len([r for r in results.values() if r['tech']])}/{len(STOCKS)} Aktien geladen.")
