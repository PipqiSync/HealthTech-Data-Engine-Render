import os
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# High-end UI with CSS Glassmorphism and Animated Gradients
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Health Engine v0.1 | Tbilisi Hub</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        :root { 
            --geo-red: #ff3b30; 
            --bg-dark: #0a0a0c;
            --glass: rgba(255, 255, 255, 0.05);
            --border: rgba(255, 255, 255, 0.1);
        }

        html, body { 
            margin: 0; padding: 0; height: 100vh; width: 100vw; 
            overflow: hidden; font-family: 'Inter', -apple-system, sans-serif; 
            background: var(--bg-dark); color: white;
        }

        body { display: flex; }

        .sidebar { 
            width: 340px; height: 100vh; background: #111114; 
            padding: 30px; border-right: 1px solid var(--border); 
            display: flex; flex-direction: column; box-sizing: border-box;
            z-index: 1000;
        }

        .header { margin-bottom: 30px; }
        .header h2 { margin: 0; font-size: 20px; letter-spacing: -0.5px; color: var(--geo-red); }
        .header p { margin: 5px 0 0; font-size: 10px; opacity: 0.5; text-transform: uppercase; letter-spacing: 2px; }

        .score-display {
            background: var(--glass);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 30px;
            text-align: center;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
            transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        }

        #score-text { font-size: 64px; font-weight: 800; display: block; line-height: 1; margin-bottom: 10px; }
        #status-text { font-size: 12px; font-weight: 700; letter-spacing: 1.5px; opacity: 0.8; }

        .input-section { flex-grow: 1; }
        .input-group { margin-bottom: 20px; }
        label { display: block; font-size: 9px; font-weight: 600; text-transform: uppercase; color: #888; margin-bottom: 8px; }
        input { 
            width: 100%; background: #1a1a1e; border: 1px solid var(--border); 
            border-radius: 8px; padding: 12px; color: white; font-size: 16px; 
            transition: border 0.3s;
        }
        input:focus { outline: none; border-color: var(--geo-red); }

        button { 
            width: 100%; padding: 16px; background: var(--geo-red); color: white; 
            border: none; border-radius: 12px; font-weight: 700; cursor: pointer; 
            font-size: 14px; text-transform: uppercase; letter-spacing: 1px;
            box-shadow: 0 10px 20px rgba(255, 59, 48, 0.2); transition: transform 0.2s;
        }
        button:hover { transform: translateY(-2px); }

        #map { flex: 1; background: #0e0e10; }

        /* Dark Map Overrides */
        .leaflet-container { background: #0a0a0c !important; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="header">
            <h2>HEALTH ENGINE <small style="color:white; opacity:0.3">v0.1</small></h2>
            <p>Tbilisi Research Hub</p>
        </div>

        <div id="display-box" class="score-display">
            <span id="score-text">--</span>
            <div id="status-text">INITIALIZING...</div>
        </div>

        <div class="input-section">
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
        </div>

        <button onclick="analyze()">Execute Analysis</button>
    </div>

    <div id="map"></div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // Use a dark, minimal map style
        const map = L.map('map', { zoomControl: false, attributionControl: false }).setView([50, 20], 4);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png').addTo(map);

        // High-precision color mapping
        const regionColors = {
            "NLD": "#2ecc71", "FRA": "#2ecc71", "ESP": "#2ecc71", // Healthy (Pastel Green)
            "DEU": "#f1c40f", "ITA": "#f1c40f", "BEL": "#f1c40f", // Warning (Pastel Yellow)
            "POL": "#e74c3c", "UKR": "#e74c3c", "GEO": "#ff3b30"  // Critical (Red)
        };

        fetch('https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson')
            .then(res => res.json())
            .then(data => {
                L.geoJson(data, {
                    style: (f) => ({
                        fillColor: regionColors[f.properties.ISO_A3] || "#222",
                        weight: 1,
                        color: "#333",
                        fillOpacity: 0.6
                    }),
                    onEachFeature: (f, l) => {
                        l.on('mouseover', () => l.setStyle({ fillOpacity: 0.9, weight: 2 }));
                        l.on('mouseout', () => l.setStyle({ fillOpacity: 0.6, weight: 1 }));
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

            // Hip visual feedback
            if (d.score > 70) {
                box.style.borderColor = "#2ecc71"; scoreTxt.style.color = "#2ecc71";
            } else if (d.score > 40) {
                box.style.borderColor = "#f1c40f"; scoreTxt.style.color = "#f1c40f";
            } else {
                box.style.borderColor = "#ff3b30"; scoreTxt.style.color = "#ff3b30";
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
    status = "OPTIMAL" if score > 70 else "DEVIATING" if score > 40 else "CRITICAL"
    return jsonify({"score": score, "status": status})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
