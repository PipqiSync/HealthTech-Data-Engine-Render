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
    <title>Health Engine v0.1 | Professional Build</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        :root { --geo-red: #c8102e; --safe-green: #2ecc71; --warn-orange: #f39c12; }
        
        html, body { 
            margin: 0; padding: 0; height: 100vh; width: 100vw; 
            overflow: hidden; font-family: 'Inter', -apple-system, sans-serif; 
            background: #ffffff; 
        }
        
        body { display: flex; }

        .sidebar { 
            width: 350px; height: 100vh; background: #ffffff; 
            padding: 30px; border-right: 1px solid #e1e4e8; 
            display: flex; flex-direction: column; box-sizing: border-box;
            z-index: 1000;
        }

        .header h2 { margin: 0; font-size: 24px; color: var(--geo-red); font-weight: 900; }
        .header p { margin: 4px 0 30px; font-size: 11px; color: #999; letter-spacing: 2px; text-transform: uppercase; }

        .score-box {
            background: #fcfcfc; border: 2px solid #f1f1f1;
            border-radius: 20px; padding: 30px; text-align: center;
            margin-bottom: 30px; transition: all 0.5s ease;
        }

        #score-text { font-size: 60px; font-weight: 800; color: #222; display: block; }
        #status-text { font-size: 12px; font-weight: 700; color: #aaa; text-transform: uppercase; margin-top: 8px; letter-spacing: 1px; }

        .input-group { margin-bottom: 20px; }
        label { display: block; font-size: 10px; font-weight: 700; color: #444; text-transform: uppercase; margin-bottom: 8px; }
        input { 
            width: 100%; background: #f9f9f9; border: 1px solid #e1e1e1; 
            border-radius: 10px; padding: 14px; font-size: 16px; box-sizing: border-box;
            transition: border-color 0.3s;
        }
        input:focus { border-color: var(--geo-red); outline: none; }

        button { 
            width: 100%; padding: 20px; background: var(--geo-red); color: white; 
            border: none; border-radius: 12px; font-weight: 700; cursor: pointer; 
            font-size: 15px; margin-top: auto; box-shadow: 0 4px 15px rgba(200, 16, 46, 0.2);
        }

        #map { flex: 1; height: 100vh; background: #f0f4f8; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="header">
            <h2>HEALTH ENGINE</h2>
            <p>Tbilisi Hub | Research v0.1</p>
        </div>

        <div id="display-box" class="score-box">
            <span id="score-text">--%</span>
            <div id="status-text">Ready for Core Analysis</div>
        </div>

        <div class="input-group">
            <label>Systolic Blood Pressure</label>
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

        <button onclick="analyze()">Run Core Analysis</button>
    </div>

    <div id="map"></div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // High-reliability Light Map
        const map = L.map('map', { zoomControl: false }).setView([48, 20], 4);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png').addTo(map);

        // Precise Country Color Mapping
        const countryStyle = {
            "NLD": "#27ae60", "FRA": "#27ae60", "ESP": "#27ae60", // Green zone
            "DEU": "#f39c12", "ITA": "#f39c12", "BEL": "#f39c12", // Orange zone
            "POL": "#e74c3c", "UKR": "#e74c3c",                  // Red zone
            "GEO": "#c8102e"                                     // Tbilisi Focus
        };

        // Loading Official GeoJSON boundaries
        fetch('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json')
            .then(res => res.json())
            .then(geoData => {
                L.geoJson(geoData, {
                    style: function(f) {
                        const code = f.id; // Official ISO_A3
                        return {
                            fillColor: countryStyle[code] || "#ecf0f1",
                            weight: 1.5,
                            color: "#ffffff",
                            fillOpacity: 0.8
                        };
                    },
                    onEachFeature: function(f, l) {
                        l.on('mouseover', function() { this.setStyle({fillOpacity: 1, weight: 2.5}); });
                        l.on('mouseout', function() { this.setStyle({fillOpacity: 0.8, weight: 1.5}); });
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

            // Visual feedback update
            if (d.score > 70) {
                box.style.borderColor = "#27ae60"; scoreTxt.style.color = "#27ae60";
            } else if (d.score > 40) {
                box.style.borderColor = "#f39c12"; scoreTxt.style.color = "#f39c12";
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
    status = "Condition Optimal" if score > 70 else "Observation Required" if score > 40 else "Urgent Intervention"
    return jsonify({"score": score, "status": status})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
