#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import yfinance as yf
from datetime import datetime, timedelta

# Deine Watchlist
STOCKS = {
    'AAPL': 'Apple',
    'MSFT': 'Microsoft', 
    'NVDA': 'Nvidia',
    'INTC': 'Intel',
    'ASML': 'Asml',
    'ORCL': 'Oracle',
    'JPM': 'JP Morgan',
    'MA': 'Mastercard',
    'GS': 'Goldman Sachs',
    'NOC': 'Northrop Grumman',
    '0XGS.DE': 'Hensoldt',
    'LMT': 'Lockheed Martin',
    'RYCEY': 'Rolls Royce',
    'SIE.DE': 'Siemens',
    'CAT': 'Caterpillar',
    'TKA.DE': 'Thyssenkrupp',
    'XOM': 'Exxon Mobil',
    'BYD': 'BYD',
    'NOVO.CO': 'Novo Nordisk',
    'MRNA': 'Moderna',
    'UNH': 'UnitedHealth',
    'AMZN': 'Amazon',
    'NKE': 'Nike',
    'TSLA': 'Tesla'
}

INDEX = {
    '^GDAXI': 'DAX',
    '^GSPC': 'S&P 500',
    '^GSPLUSI': 'MSCI World',
    'EURUSD=X': 'Euro/USD'
}

def get_stock_data(ticker):
    """Hole Kursdaten von Yahoo Finance"""
    try:
        data = yf.download(ticker, period='2d', progress=False)
        if len(data) < 2:
            return None
        
        current = data['Close'].iloc[-1]
        previous = data['Close'].iloc[-2]
        change_pct = ((current - previous) / previous) * 100
        
        return {
            'price': round(current, 2),
            'change': round(change_pct, 2),
            'change_str': f"{'↑' if change_pct >= 0 else '↓'} {abs(change_pct):.1f}%"
        }
    except:
        return None

def get_indices():
    """Hole Index-Daten"""
    indices = {}
    for ticker, name in INDEX.items():
        data = get_stock_data(ticker)
        if data:
            indices[name] = data
    return indices

def get_stocks():
    """Hole alle Aktiendaten"""
    stocks = {}
    for ticker, name in STOCKS.items():
        data = get_stock_data(ticker)
        if data:
            stocks[name] = data
    return stocks

def generate_html(stocks, indices):
    """Generiere die HTML-Datei"""
    
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    
    # Sortiere Aktien nach Sektoren
    tech = ['Apple', 'Microsoft', 'Nvidia', 'Intel', 'Asml', 'Oracle']
    finance = ['JP Morgan', 'Mastercard', 'Goldman Sachs']
    defense = ['Northrop Grumman', 'Hensoldt', 'Lockheed Martin', 'Rolls Royce']
    industry = ['Siemens', 'Caterpillar', 'Thyssenkrupp']
    energy = ['Exxon Mobil', 'BYD']
    pharma = ['Novo Nordisk', 'Moderna', 'UnitedHealth']
    consumer = ['Amazon', 'Nike']
    mobility = ['Tesla']
    
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
            transition: all 0.3s ease;
            text-align: center;
        }}
        .tab-btn.active {{
            color: #10b981;
            border-bottom-color: #10b981;
            background: rgba(16,185,129,0.1);
        }}
        .tab-content {{
            display: none;
            padding: 12px;
        }}
        .tab-content.active {{
            display: block;
        }}
        .header {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
        .header .date {{ font-size: 12px; color: #aaa; }}
        .market-overview {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 12px;
        }}
        .index-card {{
            background: rgba(255,255,255,0.08);
            padding: 10px;
            border-radius: 8px;
            font-size: 13px;
            border-left: 3px solid;
        }}
        .index-card.positive {{ border-color: #10b981; }}
        .index-card.negative {{ border-color: #ef4444; }}
        .index-name {{ font-weight: 600; margin-bottom: 4px; }}
        .index-value {{ font-size: 16px; font-weight: bold; }}
        .positive {{ color: #10b981; }}
        .negative {{ color: #ef4444; }}
        .sector {{
            margin-bottom: 16px;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(255,255,255,0.02);
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
            align-items: flex-start;
        }}
        .stock-item:last-child {{ border-bottom: none; }}
        .stock-info {{ flex: 1; }}
        .stock-name {{
            font-weight: 600;
            font-size: 14px;
            margin-bottom: 4px;
        }}
        .stock-price {{
            text-align: right;
            min-width: 100px;
        }}
        .price-value {{
            font-weight: bold;
            font-size: 15px;
            margin-bottom: 4px;
        }}
        .price-change {{
            font-size: 13px;
            font-weight: 600;
        }}
        .rating {{
            display: inline-block;
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 3px;
            margin-top: 3px;
            font-weight: 600;
            background: rgba(16,185,129,0.3);
            color: #10b981;
        }}
        .footer {{
            text-align: center;
            font-size: 11px;
            color: #666;
            margin-top: 20px;
            padding: 16px 0;
        }}
        .update-time {{
            text-align: center;
            font-size: 10px;
            color: #10b981;
            padding: 8px;
            margin-bottom: 8px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="update-time">
            ✅ Aktualisiert: {now.strftime('%d.%m.%Y %H:%M')} Uhr
        </div>
        
        <div class="tab-navigation">
            <button class="tab-btn active" onclick="switchTab(0)">📊 Finance Report</button>
            <button class="tab-btn" onclick="switchTab(1)">📰 Top News</button>
            <button class="tab-btn" onclick="switchTab(2)">📈 Marktprognose</button>
        </div>
        
        <div class="tab-content active">
            <div class="header">
                <h1>📊 Finance Daily Report</h1>
                <div class="date">{now.strftime('%d. %B %Y')} • Daten vom {yesterday.strftime('%d.%m.%Y')}</div>
                
                <div class="market-overview">
"""
    
    # Indices
    for name, data in indices.items():
        if data:
            color_class = 'positive' if data['change'] >= 0 else 'negative'
            html += f"""                <div class="index-card {color_class}">
                    <div class="index-name">{name}</div>
                    <div class="index-value">{data['price']}</div>
                    <div class="index-change {color_class}">{data['change_str']}</div>
                </div>
"""
    
    html += """                </div>
            </div>
            
            <!-- TECHNOLOGIE -->
            <div class="sector">
                <div class="sector-header">💻 TECHNOLOGIE</div>
"""
    
    for stock in tech:
        if stock in stocks and stocks[stock]:
            data = stocks[stock]
            change_class = 'positive' if data['change'] >= 0 else 'negative'
            html += f"""                <div class="stock-item">
                    <div class="stock-info">
                        <div class="stock-name">{stock}</div>
                        <div class="rating">BUY</div>
                    </div>
                    <div class="stock-price">
                        <div class="price-value">{data['price']} €</div>
                        <div class="price-change {change_class}">{data['change_str']}</div>
                    </div>
                </div>
"""
    
    html += """            </div>
            
            <!-- FINANZDIENSTLEISTUNGEN -->
            <div class="sector">
                <div class="sector-header">🏦 FINANZDIENSTLEISTUNGEN</div>
"""
    
    for stock in finance:
        if stock in stocks and stocks[stock]:
            data = stocks[stock]
            change_class = 'positive' if data['change'] >= 0 else 'negative'
            html += f"""                <div class="stock-item">
                    <div class="stock-info">
                        <div class="stock-name">{stock}</div>
                        <div class="rating">HOLD</div>
                    </div>
                    <div class="stock-price">
                        <div class="price-value">{data['price']} €</div>
                        <div class="price-change {change_class}">{data['change_str']}</div>
                    </div>
                </div>
"""
    
    html += """            </div>
            
            <!-- DEFENSE & AEROSPACE -->
            <div class="sector">
                <div class="sector-header">🚀 DEFENSE & AEROSPACE</div>
"""
    
    for stock in defense:
        if stock in stocks and stocks[stock]:
            data = stocks[stock]
            change_class = 'positive' if data['change'] >= 0 else 'negative'
            html += f"""                <div class="stock-item">
                    <div class="stock-info">
                        <div class="stock-name">{stock}</div>
                        <div class="rating">BUY</div>
                    </div>
                    <div class="stock-price">
                        <div class="price-value">{data['price']} €</div>
                        <div class="price-change {change_class}">{data['change_str']}</div>
                    </div>
                </div>
"""
    
    html += """            </div>
            
            <!-- INDUSTRIE -->
            <div class="sector">
                <div class="sector-header">🏭 INDUSTRIE & MASCHINENBAU</div>
"""
    
    for stock in industry:
        if stock in stocks and stocks[stock]:
            data = stocks[stock]
            change_class = 'positive' if data['change'] >= 0 else 'negative'
            html += f"""                <div class="stock-item">
                    <div class="stock-info">
                        <div class="stock-name">{stock}</div>
                        <div class="rating">HOLD</div>
                    </div>
                    <div class="stock-price">
                        <div class="price-value">{data['price']} €</div>
                        <div class="price-change {change_class}">{data['change_str']}</div>
                    </div>
                </div>
"""
    
    html += """            </div>
            
            <!-- ENERGIE -->
            <div class="sector">
                <div class="sector-header">⚡ ENERGIE & ROHSTOFFE</div>
"""
    
    for stock in energy:
        if stock in stocks and stocks[stock]:
            data = stocks[stock]
            change_class = 'positive' if data['change'] >= 0 else 'negative'
            html += f"""                <div class="stock-item">
                    <div class="stock-info">
                        <div class="stock-name">{stock}</div>
                        <div class="rating">HOLD</div>
                    </div>
                    <div class="stock-price">
                        <div class="price-value">{data['price']} €</div>
                        <div class="price-change {change_class}">{data['change_str']}</div>
                    </div>
                </div>
"""
    
    html += """            </div>
            
            <!-- PHARMA -->
            <div class="sector">
                <div class="sector-header">💊 PHARMA & HEALTHCARE</div>
"""
    
    for stock in pharma:
        if stock in stocks and stocks[stock]:
            data = stocks[stock]
            change_class = 'positive' if data['change'] >= 0 else 'negative'
            html += f"""                <div class="stock-item">
                    <div class="stock-info">
                        <div class="stock-name">{stock}</div>
                        <div class="rating">BUY</div>
                    </div>
                    <div class="stock-price">
                        <div class="price-value">{data['price']} €</div>
                        <div class="price-change {change_class}">{data['change_str']}</div>
                    </div>
                </div>
"""
    
    html += """            </div>
            
            <!-- CONSUMER -->
            <div class="sector">
                <div class="sector-header">🛍️ CONSUMER & EINZELHANDEL</div>
"""
    
    for stock in consumer:
        if stock in stocks and stocks[stock]:
            data = stocks[stock]
            change_class = 'positive' if data['change'] >= 0 else 'negative'
            html += f"""                <div class="stock-item">
                    <div class="stock-info">
                        <div class="stock-name">{stock}</div>
                        <div class="rating">HOLD</div>
                    </div>
                    <div class="stock-price">
                        <div class="price-value">{data['price']} €</div>
                        <div class="price-change {change_class}">{data['change_str']}</div>
                    </div>
                </div>
"""
    
    html += """            </div>
            
            <!-- E-MOBILITÄT -->
            <div class="sector">
                <div class="sector-header">🚗 E-MOBILITÄT</div>
"""
    
    for stock in mobility:
        if stock in stocks and stocks[stock]:
            data = stocks[stock]
            change_class = 'positive' if data['change'] >= 0 else 'negative'
            html += f"""                <div class="stock-item">
                    <div class="stock-info">
                        <div class="stock-name">{stock}</div>
                        <div class="rating">BUY</div>
                    </div>
                    <div class="stock-price">
                        <div class="price-value">{data['price']} €</div>
                        <div class="price-change {change_class}">{data['change_str']}</div>
                    </div>
                </div>
"""
    
    html += """            </div>
            
            <div class="footer">
                ✅ Report generiert um 10:00 Uhr täglich<br>
                📊 Datenquellen: Yahoo Finance<br>
                ⚠️ Disclaimer: Keine Anlageberatung
            </div>
        </div>
        
        <div class="tab-content">
            <div class="header">
                <h1>📰 Top News</h1>
            </div>
            <div style="padding: 20px; text-align: center; color: #aaa;">
                📊 News werden täglich aktualisiert
            </div>
        </div>
        
        <div class="tab-content">
            <div class="header">
                <h1>📈 Marktprognose</h1>
            </div>
            <div style="padding: 20px; text-align: center; color: #aaa;">
                📈 Prognosen werden täglich aktualisiert
            </div>
        </div>
    </div>
    
    <script>
        function switchTab(tabIndex) {{
            const contents = document.querySelectorAll('.tab-content');
            contents.forEach(content => content.classList.remove('active'));
            const buttons = document.querySelectorAll('.tab-btn');
            buttons.forEach(button => button.classList.remove('active'));
            contents[tabIndex].classList.add('active');
            buttons[tabIndex].classList.add('active');
            window.scrollTo(0, 0);
        }}
    </script>
</body>
</html>
"""
    
    return html

if __name__ == "__main__":
    print("🔄 Fetching stock data...")
    indices = get_indices()
    stocks = get_stocks()
    
    print(f"📊 Got {len(stocks)} stocks and {len(indices)} indices")
    
    html = generate_html(stocks, indices)
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("✅ index.html updated!")
