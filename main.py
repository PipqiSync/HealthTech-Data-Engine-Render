import os
import requests
import pandas as pd
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_data():
    try:
        url = "https://ghoapi.azureedge.net/api/BP_01"
        r = requests.get(url, timeout=10)
        raw = r.json()
        df = pd.DataFrame(raw['value'])
        df = df[df['Dim1'] == 'BTSX']
        latest = df.sort_values('TimeDim').groupby('SpatialDim').last().reset_index()
        return {row['SpatialDim']: round(row['NumericValue'], 1) for _, row in latest.iterrows()}
    except:
        return {}

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Global Hypertension Intelligence</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        :root { --primary: #c8102e; --bg: #f4f7f6; }
        body { margin: 0; display: flex; height: 100vh; font-family: sans-serif; background: var(--bg); }
        .sidebar { width: 320px; padding: 25px; background: white; border-right: 1px solid #ddd; z-index: 1000; display: flex; flex-direction: column; }
        #map { flex: 1; }
        .stats { padding: 20px; border: 2px solid #eee; border-radius: 12px; text-align: center; margin-bottom: 20px; }
        #score { font-size: 40px; font-weight: 900; display: block; }
        .legend { position: absolute; bottom: 30px; left: 350px; background: white; padding: 10px; border-radius: 8px; z-index: 1000; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
        .bar { display: inline-block; width: 20px; height: 10px; margin: 0 2px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>HEALTH DATA</h2>
        <div class="stats">
            <span id="country-name">SELECT COUNTRY</span>
            <span id="score">--%</span>
            <small id="label">HYPERTENSION PREVALENCE</small>
        </div>
        <p style="font-size: 11px; color: #666;">Data Source: WHO Global Health Observatory (Live)</p>
    </div>
    <div id="map"></div>
    <div class="legend">
        <div style="font-size: 10px; font-weight: bold; margin-bottom: 5px;">RISK LEVEL</div>
        <div class="bar" style="background:#2ecc71"></div><20%
        <div class="bar" style="background:#f1c40f"></div>25%
        <div class="bar" style="background:#e67e22"></div>30%
        <div class="bar" style="background:#c8102e"></div>>35%
    </div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const map = L.map('map', { zoomControl: false }).setView([20, 0], 2);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png').addTo(map);

        function getColor(d) {
            return d > 35 ? '#c8102e' : d > 30 ? '#e67e22' : d > 25 ? '#f1c40f' : d > 0 ? '#2ecc71' : '#e0e0e0';
        }

        async function start() {
            const dataReq = await fetch('/api/data');
            const stats = await dataReq.json();
            const geoReq = await fetch('https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson');
            const geo = await geoReq.json();

            L.geoJson(geo, {
                style: (f) => ({
                    fillColor: getColor(stats[f.id] || 0),
                    weight: 1, opacity: 1, color: 'white', fillOpacity: 0.8
                }),
                onEachFeature: (f, l) => {
                    l.on('mouseover', function() {
                        const val = stats[f.id];
                        document.getElementById('country-name').innerText = f.properties.ADMIN.toUpperCase();
                        document.getElementById('score').innerText = val ? val + "%" : "N/A";
                        document.getElementById('score').style.color = getColor(val || 0);
                        this.setStyle({ fillOpacity: 1, weight: 2 });
                    });
                    l.on('mouseout', function() { this.setStyle({ fillOpacity: 0.8, weight: 1 }); });
                }
            }).addTo(map);
        }
        start();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/data')
def api_data():
    return jsonify(get_data())

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
