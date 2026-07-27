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


def translate_to_de(text):
    """Übersetzt englischen Text nach Deutsch. Bei Fehler: Original-Text zurückgeben."""
    if not text or not text.strip():
        return text
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {'client': 'gtx', 'sl': 'auto', 'tl': 'de', 'dt': 't', 'q': text}
        res = requests.get(url, params=params, timeout=8)
        data = res.json()
        return ''.join([seg[0] for seg in data[0] if seg[0]])
    except Exception as e:
        print(f"Uebersetzung fehlgeschlagen: {e}")
        return text

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


# Manuelle Domain-Zuordnung fuer Ticker, die bei Finnhub kein Logo haben
# (v.a. europaeische Boersen & Indizes) -> Fallback ueber Google Favicon-Service
MANUAL_LOGO_DOMAINS = {
    'HAG.DE': 'hensoldt.net',
    'RHM.DE': 'rheinmetall.com',
    'DRO.AX': 'droneshield.com',
    'ENR.DE': 'siemens-energy.com',
    'SIE.DE': 'siemens.com',
    'TKA.DE': 'www.thyssenkrupp.com',
    'BAS.DE': 'basf.com',
    'URTH': 'ishares.com',
    '^GSPC': 'spglobal.com',
}


def get_company_logo(ticker):
    if ticker in MANUAL_LOGO_DOMAINS:
        domain = MANUAL_LOGO_DOMAINS[ticker]
        return f'https://www.google.com/s2/favicons?domain={domain}&sz=128'
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
    articles = []
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
        'articles': articles,
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

def classify_sentiment(text):
    text_l = text.lower()
    for kw in POSITIVE_KEYWORDS:
        if kw in text_l:
            return 'positive'
    for kw in NEGATIVE_KEYWORDS:
        if kw in text_l:
            return 'negative'
    return 'neutral'


def momentum_label(t):
    if t['momentum'] > 5:
        return '🚀 STARK'
    elif t['momentum'] > 2:
        return '📈 STARKER AUFWÄRTSTREND'
    elif t['momentum'] < -5:
        return '⚠️ SCHWACH'
    elif t['momentum'] < -2:
        return '📉 ABWÄRTSTREND'
    else:
        return '➡️ SEITWÄRTS'


def why_it_matters_bullets(d):
    """Echte Bulletpoints aus technischen Werten + News-Treffern, kein erfundener Text."""
    t = d['tech']
    bullets = []
    if t:
        bullets.append('Aufwärtstrend (SMA5 über SMA20)' if t['trend_up'] else 'Abwärtstrend (SMA5 unter SMA20)')
        if t['rsi'] < 30:
            bullets.append(f"RSI überverkauft ({t['rsi']}) — technische Erholung möglich")
        elif t['rsi'] > 70:
            bullets.append(f"RSI überkauft ({t['rsi']}) — Korrektur möglich")
        if abs(t['momentum']) > 3:
            bullets.append(f"5-Tage-Momentum {t['momentum']:+.1f}%")
    if d['news_reasons']:
        bullets.append(f"{len(d['news_reasons'])} weitere relevante News mit Sentiment-Signal")
    return bullets


def pick_representative_article(articles):
    """Wählt den aussagekräftigsten Artikel: erst Keyword-Treffer, sonst den neuesten."""
    for a in articles[:15]:
        text = (a.get('headline', '') + ' ' + a.get('summary', '')).lower()
        for kw in POSITIVE_KEYWORDS + NEGATIVE_KEYWORDS:
            if kw in text:
                return a
    return articles[0] if articles else None


# ---- TAB 2: TOP NEWS (allgemeine Marktnachrichten, uebersetzt) ----
news_html = ''
if general_news:
    for a in general_news:
        headline_de = translate_to_de(a.get('headline', ''))
        summary_de = translate_to_de((a.get('summary', '') or '').strip())
        source = a.get('source', '')
        d_str = datetime.fromtimestamp(a['datetime']).strftime('%d.%m.%Y')
        sentiment = classify_sentiment(a.get('headline', '') + ' ' + (a.get('summary', '') or ''))
        dot = {'positive': '🟢', 'negative': '🔴', 'neutral': '🟡'}[sentiment]
        body = f'<strong>Die Story:</strong> {summary_de or headline_de}<br><br><span style="color:#888;font-size:12px;">🗞️ {source} &middot; {d_str}</span>'
        news_html += f'''<div class="news-section">
            <div class="news-header">{dot} {headline_de}</div>
            <div class="news-item" style="margin-top: 8px;">{body}</div>
        </div>'''
    news_html += f'''<div class="footer">
        ✅ Nachrichten vom {data_date_global or today_str} &middot; 📊 Datenquelle: Finnhub<br>
        ⚠️ Disclaimer: Keine Anlageberatung | Informationszwecke
    </div>'''
else:
    news_html = '<div class="loading">Keine News für diesen Tag verfügbar</div>'


# ---- TAB 3 (NEU): AKTIEN NEWS (unternehmensspezifisch, uebersetzt) ----
stock_news_candidates = [(n, d) for n, d in results.items() if d.get('articles') and d['tech']]
stock_news_candidates.sort(key=lambda x: abs(x[1]['news_score']), reverse=True)
stock_news_candidates = stock_news_candidates[:8]

stock_news_html = ''
if stock_news_candidates:
    for name, d in stock_news_candidates:
        article = pick_representative_article(d['articles'])
        if not article:
            continue
        headline_de = translate_to_de(article.get('headline', ''))
        summary_de = translate_to_de((article.get('summary', '') or '').strip())
        t = d['tech']
        arrow = '↑' if t['change'] >= 0 else '↓'
        sentiment = classify_sentiment(article.get('headline', '') + ' ' + (article.get('summary', '') or ''))
        dot = {'positive': '🟢', 'negative': '🔴', 'neutral': '🟡'}[sentiment]
        bullets = why_it_matters_bullets(d)
        bullets_html = ''.join([f'• {b}<br>' for b in bullets]) if bullets else ''

        body = f'''<strong>Ticker:</strong> {d['ticker']} | Aktuell: {arrow} {abs(t['change'])}% auf {t['price']}{d['currency']}<br><br>
            <strong>Die Story:</strong> {summary_de or headline_de}<br><br>
            <strong>Was bedeutet das?</strong><br>
            {bullets_html}<br>
            <strong>Analyst Rating: {d['signal']}</strong><br>
            <strong>Momentum:</strong> {momentum_label(t)}'''

        stock_news_html += f'''<div class="news-section">
            <div class="news-header">{dot} {name.upper()} - {headline_de}</div>
            <div class="news-item" style="margin-top: 8px;">{body}</div>
        </div>'''
    stock_news_html += f'''<div class="footer">
        ✅ Aktien-News vom {data_date_global or today_str} &middot; 📊 Datenquelle: Finnhub<br>
        ⚠️ Disclaimer: Keine Anlageberatung | Informationszwecke
    </div>'''
else:
    stock_news_html = '<div class="loading">Keine unternehmensspezifischen News verfügbar</div>'


sorted_results = sorted(results.items(), key=lambda x: x[1]['score'], reverse=True)
buys = [(n, d) for n, d in sorted_results if d['signal'] == 'BUY']
sells = [(n, d) for n, d in sorted_results if d['signal'] == 'SELL']
holds = [(n, d) for n, d in sorted_results if d['signal'] == 'HOLD']

n_buy, n_sell, n_hold = len(buys), len(sells), len(holds)
all_scores = [d['score'] for d in results.values()]
avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
if avg_score > 0.7:
    sentiment_label = '📈 BULLISH (überwiegend positiv)'
elif avg_score < -0.7:
    sentiment_label = '📉 BEARISH (überwiegend negativ)'
else:
    sentiment_label = '➡️ NEUTRAL / GEMISCHT'

sector_perf = {}
for sector_key, sector_title in SECTORS.items():
    changes = [d['tech']['change'] for n, d in results.items() if d['sector'] == sector_key and d['tech']]
    if changes:
        sector_perf[sector_title] = sum(changes) / len(changes)
sector_sorted = sorted(sector_perf.items(), key=lambda x: x[1], reverse=True)
top_sector = sector_sorted[0] if sector_sorted else None
bottom_sector = sector_sorted[-1] if sector_sorted else None


def reason_bullets(d):
    """Baut die Begründungs-Bulletpoints aus echten technischen + News-Werten."""
    t = d['tech']
    bullets = []
    if t:
        bullets.append('Aufwärtstrend (SMA5 > SMA20)' if t['trend_up'] else 'Abwärtstrend (SMA5 < SMA20)')
        if t['rsi'] < 30:
            bullets.append(f"RSI überverkauft ({t['rsi']}) — technische Erholung möglich")
        elif t['rsi'] > 70:
            bullets.append(f"RSI überkauft ({t['rsi']}) — Korrektur möglich")
        if abs(t['momentum']) > 3:
            bullets.append(f"5-Tage-Momentum {t['momentum']:+.1f}%")
    if d['news_reasons']:
        bullets.append(f"{len(d['news_reasons'])} relevante News mit Sentiment-Signal")
    return bullets


def candidate_block(rank, name, d, arrow_icon):
    bullets = reason_bullets(d)
    bullets_html = ''.join([f'{b}<br>' for b in bullets]) if bullets else 'Neutrale Datenlage<br>'
    return f'''<strong>{rank}. {name} ({d['ticker']})</strong> &rarr; Signal-Score: {d['score']:+.1f}<br>
        {arrow_icon} {bullets_html}<br>'''


# ---- TAB 3 SEKTION 1: Markt-Sentiment ----
sentiment_reasons = []
if top_sector:
    sentiment_reasons.append(f"Stärkster Sektor: {top_sector[0]} ({top_sector[1]:+.1f}% Ø)")
if bottom_sector:
    sentiment_reasons.append(f"Schwächster Sektor: {bottom_sector[0]} ({bottom_sector[1]:+.1f}% Ø)")
sentiment_reasons.append(f"{n_buy} BUY-Signale gegenüber {n_sell} SELL-Signalen")
sentiment_bullets = ''.join([f'• {r}<br>' for r in sentiment_reasons])

forecast_html = f'''<div class="news-section">
    <div class="news-header">🎯 MARKT-SENTIMENT HEUTE</div>
    <div class="news-item" style="margin-top: 8px;">
        <strong>Allgemeine Stimmung:</strong> {sentiment_label}<br><br>
        <strong>Basis dieser Einschätzung:</strong><br>
        {sentiment_bullets}
    </div>
</div>'''

# ---- TAB 3 SEKTION 2: Top Gainer-Kandidaten ----
top_gainers = buys[:5]
if top_gainers:
    lines = '<br>'.join([candidate_block(i + 1, n, d, '🔥') for i, (n, d) in enumerate(top_gainers)])
else:
    lines = 'Aktuell keine BUY-Kandidaten'
forecast_html += f'''<div class="news-section">
    <div class="news-header">🟢 TOP GAINER-KANDIDATEN (stärkste BUY-Signale)</div>
    <div class="news-item" style="margin-top: 8px; line-height: 1.8;">{lines}</div>
</div>'''

# ---- TAB 3 SEKTION 3: Top Loser-Kandidaten ----
top_losers = sells[:5] if sells else sorted(holds, key=lambda x: x[1]['score'])[:3]
if top_losers:
    lines = '<br>'.join([candidate_block(i + 1, n, d, '📉') for i, (n, d) in enumerate(top_losers)])
else:
    lines = 'Aktuell keine SELL-Kandidaten'
forecast_html += f'''<div class="news-section">
    <div class="news-header">🔴 TOP LOSER-KANDIDATEN (schwächste Signale)</div>
    <div class="news-item" style="margin-top: 8px; line-height: 1.8;">{lines}</div>
</div>'''

# ---- TAB 3 SEKTION 4: Sektor-Performance kategorisiert ----
strong = [(t, a) for t, a in sector_sorted if a > 1]
neutral = [(t, a) for t, a in sector_sorted if -1 <= a <= 1]
weak = [(t, a) for t, a in sector_sorted if a < -1]


def sector_line(title, avg):
    return f'{title}: {avg:+.1f}% Ø<br>'


sector_body = ''
if strong:
    sector_body += '<strong style="color:#10b981;">✓ STARKE SEKTOREN (Ø &gt; +1%):</strong><br>'
    sector_body += ''.join([sector_line(t, a) for t, a in strong]) + '<br>'
if neutral:
    sector_body += '<strong style="color:#fbbf24;">⚠️ NEUTRALE SEKTOREN (-1% bis +1%):</strong><br>'
    sector_body += ''.join([sector_line(t, a) for t, a in neutral]) + '<br>'
if weak:
    sector_body += '<strong style="color:#ef4444;">✗ SCHWACHE SEKTOREN (Ø &lt; -1%):</strong><br>'
    sector_body += ''.join([sector_line(t, a) for t, a in weak])

forecast_html += f'''<div class="news-section">
    <div class="news-header">📊 SEKTOR-PERFORMANCE (Ø letzter Handelstag)</div>
    <div class="news-item" style="margin-top: 8px; line-height: 2;">{sector_body}</div>
</div>'''

# ---- TAB 3 SEKTION 5: Strategie für heute ----
buy_names = ', '.join([n for n, d in buys[:4]]) if buys else 'keine aktuell'
hold_names = ', '.join([n for n, d in holds[:4]]) if holds else 'keine aktuell'
sell_names = ', '.join([n for n, d in sells]) if sells else 'keine aktuell'
watch_candidates = [(n, d) for n, d in holds if abs(d['score']) >= 1.0]
watch_names = ', '.join([n for n, d in watch_candidates[:4]]) if watch_candidates else 'keine besonderen Grenzfälle'

forecast_html += f'''<div class="news-section">
    <div class="news-header">🎯 STRATEGIE FÜR HEUTE</div>
    <div class="news-item" style="margin-top: 8px; line-height: 1.8;">
        <strong>🟢 BUY (stärkste Signale):</strong><br>
        &rarr; {buy_names}<br><br>
        <strong>🔄 HOLD (abwarten):</strong><br>
        &rarr; {hold_names}<br><br>
        <strong>🔴 SELL (Signale zur Vorsicht):</strong><br>
        &rarr; {sell_names}<br><br>
        <strong>💡 WATCH (Grenzfälle nahe der Schwelle):</strong><br>
        &rarr; {watch_names}
    </div>
</div>'''

# ---- TAB 3 SEKTION 6: Risiko-Warnung ----
forecast_html += '''<div class="news-section">
    <div class="news-header">🎲 RISIKO-WARNUNG</div>
    <div class="news-item" style="margin-top: 8px;">
        <strong>Was könnte diese Prognose kippen?</strong><br><br>
        ⚠️ Unerwartete Makrodaten (Inflation, Arbeitsmarkt, Zinsentscheide)<br>
        ⚠️ Geopolitische Eskalationen<br>
        ⚠️ Gewinnüberraschungen einzelner Unternehmen<br>
        ⚠️ Plötzliche Sentiment-Wechsel an den Märkten<br><br>
        <strong>Fazit:</strong> Diese Einschätzung basiert auf technischen Indikatoren (RSI, Trend, Momentum)
        und einfachem News-Keyword-Matching — kein Ersatz für eigene Recherche. Immer eigenes Risikomanagement betreiben. 🎯
    </div>
</div>'''

forecast_html += f'''<div class="footer">
    ✅ Prognose vom {today_str} morgens &middot; 📊 Basis: Yahoo Finance + Finnhub<br>
    ⚠️ Disclaimer: Keine Anlageberatung | Informationszwecke
</div>'''


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
.news-section {{ background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.1); border-radius:12px; padding:14px 16px; margin-bottom:16px; }}
.news-header {{ font-weight:700; font-size:16px; margin-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:8px; line-height:1.35; }}
.news-item {{ font-size:14px; margin-bottom:8px; padding-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.05); line-height:1.6; }}
.news-item:last-child {{ border-bottom:none; margin-bottom:0; }}
.news-item strong {{ color:#10b981; }}
.footer {{ text-align:center; font-size:12px; color:#666; margin-top:20px; padding:16px 0; }}
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
<button class="tab-btn" onclick="switchTab(2)">🏢 Aktien News</button>
<button class="tab-btn" onclick="switchTab(3)">📈 Prognose</button>
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
<h1>🏢 Aktien News</h1>
<div class="date">Unternehmensspezifische Meldungen vom {data_date_global or today_str}</div>
</div>
{stock_news_html}
</div>

<div class="tab-content">
<div class="header">
<h1>📈 Marktprognose</h1>
<div class="date">für {today_str}</div>
</div>
{forecast_html}
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
