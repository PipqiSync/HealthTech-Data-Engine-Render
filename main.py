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
    <title>Health Engine | Public Data Edition</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        :root { 
            --ahti-blue: #003057; 
            --ahti-red: #c8102e; 
            --ui-bg: #f8f9fa;
        }
        
        html, body { 
            margin: 0; padding: 0; height: 100vh; width: 100vw; 
            overflow: hidden; font-family: 'Segoe UI', Roboto, sans-serif; 
            background: white; 
        }
        
        body { display: flex; }

        /* Compact AHTI Sidebar */
        .sidebar { 
            width: 300px; height: 100vh; background: var(--ahti-blue); 
            padding: 20px; display: flex; flex-direction: column; 
            box-sizing: border-box; color: white; z-index: 1000;
        }

        .header h2 { 
            margin: 0; font-size: 18px; color: #fff; font-weight: 700; 
            border-left: 4px solid var(--ahti-red); padding-left: 10px; 
        }
        .header p { margin: 5px 0 20px 14px; font-size: 9px; color: #adb5bd; text-transform: uppercase; letter-spacing: 1px; }

        /* Score box: 30% smaller, modern glass-style */
        .score-box {
            background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15);
            border-radius: 8px; padding: 12px; text-align: center;
            margin-bottom: 20px; transition: 0.3s;
        }

        #score-text { font-size: 36px; font-weight: 800; color: #fff; display: block; }
        #status-text { font-size: 9px; font-weight: 600; color: #2ecc71; text-transform: uppercase; }

        .input-group { margin-bottom: 12px; }
        label { display: block; font-size: 9px; font-weight: 600; color: #adb5bd; margin-bottom: 4px; text-transform: uppercase; }
        input { 
            width: 100%; background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.2); 
            border-radius: 4px; padding: 10px; font-size: 14px; color: white; box-sizing: border-box;
        }
        input:focus { border-color: var(--ahti-red); outline: none; }

        button { 
            width: 100%; padding: 15px; background: var(--ahti-red); color: white; 
            border: none; border-radius: 4px; font-weight: 700; cursor: pointer; 
            font-size: 12px; margin-top: auto; text-transform: uppercase;
        }

        #map { flex: 1; height: 100vh; background: #e9ecef; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="header">
            <h2>HEALTH ENGINE</h2>
            <p>Open Data Integrated Hub</p>
        </div>

        <div id="display-box" class="score-box">
            <span id="score-text">--%</span>
            <div id="status-text">Ready for Processing</div>
        </div>

        <div class="input-group">
            <label>Public Demographic Index</label>
            <input type="number" id="sys" value="120">
        </div>
        <div class="input-group">
            <label>Claims-based Proxy (Open)</label>
            <input type="number" id="glu" value="95">
        </div>
        <div class="input-group">
            <label>Regional Mortality Rate</label>
            <input type="number" id="bpm" value="75">
        </div>

        <button onclick="analyze()">⚡ RUN CORE ANALYSIS</button>
    </div>

    <div id="map"></div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // High-resolution Map Engine focused on Georgia/Europe
        const map = L.map('map', { zoomControl: false }).setView([42.3, 43.9], 6);
        
        // ArcGIS-style professional light tiles (Free)
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png').addTo(map);

        const highlightCountries = {
            "GEO": "#c8102e", "NLD": "#003057", "DEU": "#f1c40f", 
            "POL": "#e67e22", "UKR": "#e74c3c"
        };

        // Fetching high-detail 10m Natural Earth dataset mirror
        fetch('https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson')
            .then(res => res.json())
            .then(data => {
                L.geoJson(data, {
                    style: (f) => ({
                        fillColor: highlightCountries[f.properties.ISO_A3] || "#dee2e6",
                        weight: 0.8, // 10x more detail requires thinner lines for clarity
                        color: "#ffffff",
                        fillOpacity: 0.8
                    }),
                    onEachFeature: (f, l) => {
                        l.on('mouseover', () => l.setStyle({fillOpacity: 1, weight: 1.5}));
                        l.on('mouseout', () => l.setStyle({fillOpacity: 0.8, weight: 0.8}));
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
            document.getElementById('score-text').innerText = d.score + "%";
            const statusEl = document.getElementById('status-text');
            statusEl.innerText = d.status;
            statusEl.style.color = d.score > 70 ? "#2ecc71" : "#f1c40f";
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(DASHBOARD_HTML)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    s, g, b = int(data['s']), int(data['g']), int(data['b'])
    # Simplified AHTI weighting formula
    score = round(max(0, min(100, 100 - ((abs(s-120) + abs(g-95) + abs(b-75))*0.4))), 1)
    status = "THRESHOLD MET" if score > 75 else "ANOMALY DETECTED"
    return jsonify({"score": score, "status": status})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
