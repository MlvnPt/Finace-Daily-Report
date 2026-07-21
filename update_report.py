#!/usr/bin/env python3
import yfinance as yf
from datetime import datetime, timedelta
import json

STOCKS = {
    'AAPL': 'Apple', 'MSFT': 'Microsoft', 'NVDA': 'Nvidia',
    'INTC': 'Intel', 'ASML': 'Asml', 'ORCL': 'Oracle',
    'JPM': 'JP Morgan', 'MA': 'Mastercard', 'GS': 'Goldman Sachs',
    'NOC': 'Northrop Grumman', 'LMT': 'Lockheed Martin', 'RYCEY': 'Rolls Royce',
    'SIE.DE': 'Siemens', 'CAT': 'Caterpillar', 'TKA.DE': 'Thyssenkrupp',
    'XOM': 'Exxon Mobil', 'BYD': 'BYD',
    'NOVO.CO': 'Novo Nordisk', 'MRNA': 'Moderna', 'UNH': 'UnitedHealth',
    'AMZN': 'Amazon', 'NKE': 'Nike', 'TSLA': 'Tesla'
}

def get_data(ticker):
    try:
        data = yf.download(ticker, period='5d', progress=False)
        if len(data) >= 2:
            current = float(data['Close'].iloc[-1])
            previous = float(data['Close'].iloc[-2])
            change = ((current - previous) / previous) * 100
            return {
                'price': round(current, 2),
                'change': round(change, 2),
                'arrow': '↑' if change >= 0 else '↓',
                'color': 'positive' if change >= 0 else 'negative'
            }
    except Exception as e:
        print(f"Error for {ticker}: {e}")
    return None

now = datetime.now()
yesterday = now - timedelta(days=1)

stocks = {}
for ticker, name in STOCKS.items():
    data = get_data(ticker)
    if data:
        stocks[name] = data
        print(f"✅ {name}: {data['price']}€ {data['arrow']} {abs(data['change']):.1f}%")

html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Finance Daily Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
        }}
        .container {{ max-width: 600px; margin: 0 auto; }}
        .tab-navigation {{
            display: flex;
            background: rgba(0,0,0,0.3);
            border-bottom: 2px solid rgba(255,255,255,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        .tab-btn {{
            flex: 1;
            padding: 12px 10px;
            background: none;
            border: none;
            color: #aaa;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            border-bottom: 3px solid transparent;
        }}
        .tab-btn.active {{
            color: #10b981;
            border-bottom-color: #10b981;
            background: rgba(16,185,129,0.1);
        }}
        .tab-content {{ display: none; padding: 12px; }}
        .tab-content.active {{ display: block; }}
        .header {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
        .header .date {{ font-size: 12px; color: #aaa; }}
        .sector {{
            margin-bottom: 16px;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(255,255,255,0.02);
            overflow: hidden;
        }}
        .sector-header {{
            background: rgba(255,255,255,0.08);
            padding: 12px 14px;
            font-weight: 600;
            font-size: 14px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .stock-item {{
            padding: 12px 14px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            display: flex;
            justify-content: space-between;
        }}
        .stock-item:last-child {{ border-bottom: none; }}
        .stock-name {{ font-weight: 600; font-size: 14px; margin-bottom: 4px; }}
        .price-value {{ font-weight: bold; font-size: 15px; }}
        .positive {{ color: #10b981; }}
        .negative {{ color: #ef4444; }}
        .footer {{ text-align: center; font-size: 11px; color: #666; margin-top: 20px; padding: 16px 0; }}
        .update {{ text-align: center; font-size: 10px; color: #10b981; padding: 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="update">✅ Aktualisiert: {now.strftime('%d.%m.%Y %H:%M')} Uhr</div>
        <div class="tab-navigation">
            <button class="tab-btn active" onclick="switchTab(0)">📊 Finance Report</button>
            <button class="tab-btn" onclick="switchTab(1)">📰 Top News</button>
            <button class="tab-btn" onclick="switchTab(2)">📈 Prognose</button>
        </div>
        
        <div class="tab-content active">
            <div class="header">
                <h1>📊 Finance Daily Report</h1>
                <div class="date">{now.strftime('%d. %B %Y')} • Daten vom {yesterday.strftime('%d.%m.%Y')}</div>
            </div>
            
            <div class="sector">
                <div class="sector-header">💻 TECHNOLOGIE</div>
"""

tech = ['Apple', 'Microsoft', 'Nvidia', 'Intel', 'Asml', 'Oracle']
for stock in tech:
    if stock in stocks:
        s = stocks[stock]
        html += f"""                <div class="stock-item">
                    <div class="stock-name">{stock}</div>
                    <div><span class="{s['color']}">{s['price']}€ {s['arrow']} {abs(s['change']):.1f}%</span></div>
                </div>
"""

html += """            </div>
            
            <div class="sector">
                <div class="sector-header">🏦 FINANZDIENSTLEISTUNGEN</div>
"""

finance = ['JP Morgan', 'Mastercard', 'Goldman Sachs']
for stock in finance:
    if stock in stocks:
        s = stocks[stock]
        html += f"""                <div class="stock-item">
                    <div class="stock-name">{stock}</div>
                    <div><span class="{s['color']}">{s['price']}€ {s['arrow']} {abs(s['change']):.1f}%</span></div>
                </div>
"""

html += """            </div>
            
            <div class="sector">
                <div class="sector-header">🚀 DEFENSE & AEROSPACE</div>
"""

defense = ['Northrop Grumman', 'Lockheed Martin', 'Rolls Royce']
for stock in defense:
    if stock in stocks:
        s = stocks[stock]
        html += f"""                <div class="stock-item">
                    <div class="stock-name">{stock}</div>
                    <div><span class="{s['color']}">{s['price']}€ {s['arrow']} {abs(s['change']):.1f}%</span></div>
                </div>
"""

html += """            </div>
            
            <div class="sector">
                <div class="sector-header">🏭 INDUSTRIE</div>
"""

industry = ['Siemens', 'Caterpillar', 'Thyssenkrupp']
for stock in industry:
    if stock in stocks:
        s = stocks[stock]
        html += f"""                <div class="stock-item">
                    <div class="stock-name">{stock}</div>
                    <div><span class="{s['color']}">{s['price']}€ {s['arrow']} {abs(s['change']):.1f}%</span></div>
                </div>
"""

html += """            </div>
            
            <div class="sector">
                <div class="sector-header">⚡ ENERGIE & ROHSTOFFE</div>
"""

energy = ['Exxon Mobil', 'BYD']
for stock in energy:
    if stock in stocks:
        s = stocks[stock]
        html += f"""                <div class="stock-item">
                    <div class="stock-name">{stock}</div>
                    <div><span class="{s['color']}">{s['price']}€ {s['arrow']} {abs(s['change']):.1f}%</span></div>
                </div>
"""

html += """            </div>
            
            <div class="sector">
                <div class="sector-header">💊 PHARMA</div>
"""

pharma = ['Novo Nordisk', 'Moderna', 'UnitedHealth']
for stock in pharma:
    if stock in stocks:
        s = stocks[stock]
        html += f"""                <div class="stock-item">
                    <div class="stock-name">{stock}</div>
                    <div><span class="{s['color']}">{s['price']}€ {s['arrow']} {abs(s['change']):.1f}%</span></div>
                </div>
"""

html += """            </div>
            
            <div class="sector">
                <div class="sector-header">🛍️ CONSUMER</div>
"""

consumer = ['Amazon', 'Nike']
for stock in consumer:
    if stock in stocks:
        s = stocks[stock]
        html += f"""                <div class="stock-item">
                    <div class="stock-name">{stock}</div>
                    <div><span class="{s['color']}">{s['price']}€ {s['arrow']} {abs(s['change']):.1f}%</span></div>
                </div>
"""

html += """            </div>
            
            <div class="sector">
                <div class="sector-header">🚗 E-MOBILITÄT</div>
"""

mobility = ['Tesla']
for stock in mobility:
    if stock in stocks:
        s = stocks[stock]
        html += f"""                <div class="stock-item">
                    <div class="stock-name">{stock}</div>
                    <div><span class="{s['color']}">{s['price']}€ {s['arrow']} {abs(s['change']):.1f}%</span></div>
                </div>
"""

html += """            </div>
            <div class="footer">
                ✅ Report täglich um 10:00 Uhr<br>
                📊 Datenquellen: Yahoo Finance<br>
                ⚠️ Disclaimer: Keine Anlageberatung
            </div>
        </div>
        
        <div class="tab-content">
            <div class="header"><h1>📰 Top News</h1></div>
            <div style="padding: 20px; text-align: center; color: #aaa;">
                📊 News werden täglich aktualisiert
            </div>
        </div>
        
        <div class="tab-content">
            <div class="header"><h1>📈 Marktprognose</h1></div>
            <div style="padding: 20px; text-align: center; color: #aaa;">
                📈 Prognosen werden täglich aktualisiert
            </div>
        </div>
    </div>
    
    <script>
        function switchTab(i) {{
            document.querySelectorAll('.tab-content').forEach(e => e.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(e => e.classList.remove('active'));
            document.querySelectorAll('.tab-content')[i].classList.add('active');
            document.querySelectorAll('.tab-btn')[i].classList.add('active');
            window.scrollTo(0, 0);
        }}
    </script>
</body>
</html>
"""

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ Fertig! {len(stocks)} Aktien geladen!")
