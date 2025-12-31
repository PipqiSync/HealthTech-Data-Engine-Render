import os
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Health Engine v0.1 | Stable Build</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        :root { --geo-red: #c8102e; --safe-green: #2ecc71; --warn-yellow: #f1c40f; }
        
        html, body { 
            margin: 0; padding: 0; height: 100vh; width: 100vw; 
            overflow: hidden; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: #f0f2f5; 
        }
        
        body { display: flex; }

        .sidebar { 
            width: 340px; height: 100vh; background: #ffffff; 
            padding: 30px; border-right: 1px solid #d1d1d1; 
            display: flex; flex-direction: column; box-sizing: border-box;
            z-index: 1000; box-shadow: 4px 0 10px rgba(0,0,0,0.05);
        }

        .header h2 { margin: 0; font-size: 22px; color: var(--geo-red); font-weight: 800; }
        .header p { margin: 4px 0 25px; font-size: 11px; color: #888; letter-spacing: 1px; }

        .score-display {
            background: #f8f9fa; border: 2px solid #edf0f2;
            border-radius: 16px; padding: 25px; text-align: center;
            margin-bottom: 30px; transition: all 0.4s ease;
        }

        #score-text { font-size: 56px; font-weight: 800; color: #333; display: block; }
        #status-text { font-size: 13px; font-weight: 700; color: #999; text-transform: uppercase; margin-top: 5px; }

        .input-group { margin-bottom: 18px; }
        label { display: block; font-size: 10px; font-weight: 700; color: #555; text-transform: uppercase; margin-bottom: 6px; }
        input { 
            width: 100%; background: #ffffff; border: 1px solid #ddd; 
            border-radius: 8px; padding: 12px; font-size: 16px; box-sizing: border-box;
        }

        button { 
            width: 100%; padding: 18px; background: var(--geo-red); color: white; 
            border: none; border-radius: 10px; font-weight: 700; cursor: pointer; 
            font-size: 15px; margin-top: auto; transition: background 0.2s;
        }
        button:hover { background: #a50d26; }

        #map { flex: 1; background: #e3e7ea; }
        
        /* Zorg dat de kaarttegels zichtbaar zijn */
        .leaflet-container { background: #cbd5e0 !important; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="header">
            <h2>HEALTH ENGINE</h2>
            <p>TBILISI RESEARCH HUB v0.1</p>
        </div>

        <div id="display-box" class="score-display">
            <span id="score-text">--%</span>
            <div id="status-text">READY FOR ANALYSIS</div>
        </div>

        <div class="input-group">
            <label>Systolic Pressure (mmHg)</label>
            <input type="number" id="sys" value="120">
        </div>
        <div class="input-group">
            <label>Glucose Level (mg/dL)</label>
            <input type="number" id="glu" value="95">
        </div>
        <div class="input-group">
            <label>Heart Rate (BPM)</label>
            <input type="number" id="bpm" value="75">
        </div>

        <button onclick="analyze()">RUN CORE ANALYSIS</button>
    </div>

    <div id="map"></div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // Gebruik een betrouwbare lichte kaartstijl
        const map = L.map('map', { 
            zoomControl: true, 
            attributionControl: false 
        }).setView([52, 18], 4);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

        const countryData = {
            "NLD": {color: "#2ecc71", name: "Netherlands"},
            "FRA": {color: "#2ecc71", name: "France"},
            "DEU": {color: "#f1c40f", name: "Germany"},
            "ITA": {color: "#f1c40f", name: "Italy"},
            "POL": {color: "#e74c3c", name: "Poland"},
            "GEO": {color: "#c8102e", name: "Georgia"}
        };

        // Stabiele GeoJSON bron met ingebouwde foutafhandeling
        fetch('https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson')
            .then(res => res.json())
            .then(data => {
                L.geoJson(data, {
                    style: function(feature) {
                        const code = feature.properties.ISO_A3;
                        const config = countryData[code];
                        return {
                            fillColor: config ? config.color : "#ffffff",
                            weight: 1.5,
                            opacity: 1,
                            color: '#444',
                            fillOpacity: 0.7
                        };
                    }
                }).addTo(map);
            })
            .catch(err => console.error("Map failed to load:", err));

        async function analyze() {
            const s = document.getElementById('sys').value;
            const g = document.getElementById('glu').value;
            const b = document.getElementById('bpm').value;

            const res = await fetch('/analyze', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ s, g, b })
            });
            const d = await res.json();
            
            const scoreTxt = document.getElementById('score-text');
            const statusTxt = document.getElementById('status-text');
            const box = document.getElementById('display-box');
            
            scoreTxt.innerText = Math.round(d.score) + "%";
            statusTxt.innerText = d.status;

            // Dynamische kleurverandering van het dashboard
            if (d.score > 70) {
                box.style.borderColor = var(--safe-green); scoreTxt.style.color = var(--safe-green);
                statusTxt.style.color = var(--safe-green);
            } else if (d.score > 40) {
                box.style.borderColor = var(--warn-yellow); scoreTxt.style.color = var(--warn-yellow);
                statusTxt.style.color = var(--warn-yellow);
            } else {
                box.style.borderColor = var(--geo-red); scoreTxt.style.color = var(--geo-red);
                statusTxt.style.color = var(--geo-red);
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML)

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        s, g, b = int(data['s']), int(data['g']), int(data['b'])
        penalty = (abs(s - 120) * 0.4) + (abs(g - 90) * 0.3) + (abs(b - 70) * 0.3)
        score = max(0, min(100, 100 - penalty))
        status = "HEALTHY / STABLE" if score > 70 else "OBSERVATION REQUIRED" if score > 40 else "URGENT INTERVENTION"
        return jsonify({"score": score, "status": status})
    except Exception as e:
        return jsonify({"score": 0, "status": "ERROR"}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
