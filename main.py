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
    <title>Health Engine v0.1 | High-Res Hub</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        :root { --geo-red: #c8102e; --safe-green: #2ecc71; --warn-orange: #f39c12; }
        
        html, body { 
            margin: 0; padding: 0; height: 100vh; width: 100vw; 
            overflow: hidden; font-family: 'Inter', sans-serif; 
            background: #ffffff; 
        }
        
        body { display: flex; }

        .sidebar { 
            width: 320px; height: 100vh; background: #ffffff; 
            padding: 20px; border-right: 1px solid #e1e4e8; 
            display: flex; flex-direction: column; box-sizing: border-box;
            z-index: 1000;
        }

        .header h2 { margin: 0; font-size: 20px; color: var(--geo-red); font-weight: 900; }
        .header p { margin: 2px 0 20px; font-size: 10px; color: #999; letter-spacing: 1px; text-transform: uppercase; }

        /* Score box reduced by 30% */
        .score-box {
            background: #fcfcfc; border: 1px solid #eee;
            border-radius: 12px; padding: 15px; text-align: center;
            margin-bottom: 20px; transition: all 0.4s ease;
            box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        }

        #score-text { font-size: 42px; font-weight: 800; color: #222; display: block; }
        #status-text { font-size: 10px; font-weight: 700; color: #aaa; text-transform: uppercase; margin-top: 4px; }

        .input-group { margin-bottom: 12px; }
        label { display: block; font-size: 9px; font-weight: 700; color: #444; text-transform: uppercase; margin-bottom: 4px; }
        input { 
            width: 100%; background: #f9f9f9; border: 1px solid #e1e1e1; 
            border-radius: 6px; padding: 10px; font-size: 14px; box-sizing: border-box;
        }

        button { 
            width: 100%; padding: 15px; background: var(--geo-red); color: white; 
            border: none; border-radius: 8px; font-weight: 700; cursor: pointer; 
            font-size: 13px; margin-top: auto; 
        }

        #map { flex: 1; height: 100vh; background: #f0f4f8; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="header">
            <h2>HEALTH ENGINE</h2>
            <p>Tbilisi Research Hub</p>
        </div>

        <div id="display-box" class="score-box">
            <span id="score-text">--%</span>
            <div id="status-text">SYSTEM READY</div>
        </div>

        <div class="input-group">
            <label>Systolic Pressure</label>
            <input type="number" id="sys" value="120">
        </div>
        <div class="input-group">
            <label>Glucose Level</label>
            <input type="number" id="glu" value="95">
        </div>
        <div class="input-group">
            <label>Heart Rate</label>
            <input type="number" id="bpm" value="75">
        </div>

        <button onclick="analyze()">RUN ANALYSIS v0.1</button>
    </div>

    <div id="map"></div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const map = L.map('map', { zoomControl: false }).setView([45, 25], 4);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png').addTo(map);

        const countryStyle = {
            "NLD": "#27ae60", "FRA": "#2ecc71", "ESP": "#2ecc71",
            "DEU": "#f1c40f", "ITA": "#f1c40f", "BEL": "#f1c40f",
            "POL": "#e67e22", "UKR": "#e74c3c", "GEO": "#c8102e"
        };

        // Fetching high-detail boundaries (110m is standard, 50m/10m is detail level)
        fetch('https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson')
            .then(res => res.json())
            .then(geoData => {
                L.geoJson(geoData, {
                    style: function(f) {
                        const code = f.properties.ISO_A3;
                        return {
                            fillColor: countryStyle[code] || "#f0f2f5",
                            weight: 0.8,
                            color: "#ffffff",
                            fillOpacity: 0.85
                        };
                    },
                    onEachFeature: function(f, l) {
                        l.on('mouseover', function() { this.setStyle({fillOpacity: 1, weight: 1.5}); });
                        l.on('mouseout', function() { this.setStyle({fillOpacity: 0.85, weight: 0.8}); });
                    }
                }).addTo(map);
            });

        async function analyze() {
            const res = await fetch('/analyze', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    s: document.getElementById('sys').value,
                    g: document.getElementById('glu').value,
                    b: document.getElementById('bpm').value
                })
            });
            const d = await res.json();
            
            const scoreTxt = document.getElementById('score-text');
            const statusTxt = document.getElementById('status-text');
            const box = document.getElementById('display-box');
            
            scoreTxt.innerText = Math.round(d.score) + "%";
            statusTxt.innerText = d.status;

            if (d.score > 70) {
                box.style.borderColor = "#27ae60"; scoreTxt.style.color = "#27ae60";
            } else if (d.score > 40) {
                box.style.borderColor = "#f1c40f"; scoreTxt.style.color = "#f1c40f";
            } else {
                box.style.borderColor = "#c8102e"; scoreTxt.style.color = "#c8102e";
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
    data = request.get_json()
    s, g, b = int(data['s']), int(data['g']), int(data['b'])
    penalty = (abs(s - 120) * 0.4) + (abs(g - 90) * 0.3) + (abs(b - 70) * 0.3)
    score = max(0, min(100, 100 - penalty))
    status = "OPTIMAL" if score > 70 else "WATCH" if score > 40 else "CRITICAL"
    return jsonify({"score": score, "status": status})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
