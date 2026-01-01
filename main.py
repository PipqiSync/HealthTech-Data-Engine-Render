import os
import requests
import pandas as pd
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_who_data():
    """Fetches real-time hypertension data from WHO GHO API"""
    try:
        # BP_01: Prevalence of raised blood pressure (Age-standardized)
        url = "https://ghoapi.azureedge.net/api/BP_01"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        df = pd.DataFrame(data['value'])
        # Filter for 'Both sexes' and most recent year
        df = df[df['Dim1'] == 'BTSX']
        latest_indices = df.groupby('SpatialDim')['TimeDim'].idxmax()
        latest_df = df.loc[latest_indices]
        
        return {row['SpatialDim']: round(row['NumericValue'], 1) for _, row in latest_df.iterrows()}
    except Exception as e:
        print(f"WHO API Error: {e}")
        return {}

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>HealthTech Data Engine</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { margin: 0; display: flex; height: 100vh; font-family: sans-serif; background: #f8f9fa; }
        .sidebar { width: 300px; padding: 20px; background: white; border-right: 1px solid #ddd; z-index: 1000; }
        #map { flex: 1; background: #aad3df; }
        .stat-card { padding: 15px; border-radius: 8px; border: 1px solid #eee; text-align: center; margin-top: 20px; }
        #val { font-size: 32px; font-weight: bold; color: #c8102e; display: block; }
        .legend { position: absolute; bottom: 20px; right: 20px; background: white; padding: 10px; border-radius: 5px; z-index: 1000; box-shadow: 0 0 10px rgba(0,0,0,0.1); font-size: 12px; }
        .dot { height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 5px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h3 style="color:#c8102e">Engine v2.0</h3>
        <p style="font-size: 12px; color: #666;">Hypertension Prevalence (WHO Data)</p>
        <div class="stat-card">
            <span id="loc" style="font-size: 14px; color: #999;">SELECT COUNTRY</span>
            <span id="val">--%</span>
        </div>
    </div>
    <div id="map"></div>
    <div class="legend">
        <div><span class="dot" style="background:#2ecc71"></span> &lt; 20%</div>
        <div><span class="dot" style="background:#f1c40f"></span> 20-30%</div>
        <div><span class="dot" style="background:#c8102e"></span> &gt; 30%</div>
    </div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const map = L.map('map', { zoomControl: false }).setView([20, 0], 2);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png').addTo(map);

        function getColor(v) {
            return v > 30 ? '#c8102e' : v > 20 ? '#f1c40f' : v > 0 ? '#2ecc71' : '#e0e0e0';
        }

        async function load() {
            const [d, g] = await Promise.all([
                fetch('/api/data').then(r => r.json()),
                fetch('https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson').then(r => r.json())
            ]);
            
            L.geoJson(g, {
                style: f => ({
                    fillColor: getColor(d[f.id] || 0),
                    weight: 1, opacity: 1, color: 'white', fillOpacity: 0.7
                }),
                onEachFeature: (f, l) => {
                    l.on('mouseover', function() {
                        const v = d[f.id];
                        document.getElementById('loc').innerText = f.properties.ADMIN;
                        document.getElementById('val').innerText = v ? v + '%' : 'N/A';
                        this.setStyle({ fillOpacity: 0.9, weight: 2 });
                    });
                    l.on('mouseout', function() { this.setStyle({ fillOpacity: 0.7, weight: 1 }); });
                }
            }).addTo(map);
        }
        load();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(INDEX_HTML)

@app.route('/api/data')
def api_data():
    return jsonify(get_who_data())

# Required for local testing; Gunicorn uses the 'app' object directly
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
