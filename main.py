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
    <title>Europe Health Monitor | Verified Build</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        :root { --ahti-red: #c8102e; --panel-bg: #ffffff; }
        html, body { margin: 0; padding: 0; height: 100vh; width: 100vw; overflow: hidden; font-family: 'Inter', sans-serif; background: #f4f7f6; }
        body { display: flex; }
        .sidebar { width: 320px; height: 100vh; background: var(--panel-bg); padding: 25px; display: flex; flex-direction: column; box-sizing: border-box; border-right: 1px solid #e0e0e0; z-index: 1000; }
        .header h2 { margin: 0; font-size: 20px; color: var(--ahti-red); font-weight: 800; }
        .header p { margin: 2px 0 15px; font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
        .score-box { background: #fff; border: 2px solid #f0f0f0; border-radius: 12px; padding: 15px; text-align: center; margin-bottom: 20px; }
        #score-text { font-size: 40px; font-weight: 900; color: #222; display: block; }
        #status-text { font-size: 9px; font-weight: 700; color: #999; text-transform: uppercase; margin-top: 5px; }
        #location-tag { font-size: 11px; font-weight: 800; color: var(--ahti-red); margin-bottom: 5px; display: block; }
        .input-group { margin-bottom: 12px; }
        label { display: block; font-size: 10px; font-weight: 700; color: #444; margin-bottom: 4px; text-transform: uppercase; }
        input { width: 100%; border: 1.5px solid #e0e0e0; border-radius: 6px; padding: 10px; font-size: 14px; box-sizing: border-box; background: #fafafa; }
        button { width: 100%; padding: 16px; background: var(--ahti-red); color: white; border: none; border-radius: 8px; font-weight: 800; cursor: pointer; font-size: 13px; text-transform: uppercase; margin-top: auto; }
        #map { flex: 1; height: 100vh; background: #cbd5e1; }
        .legend { position: absolute; bottom: 30px; left: 340px; background: white; padding: 12px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); z-index: 1000; }
        .legend-title { font-size: 9px; font-weight: 800; margin-bottom: 5px; text-transform: uppercase; }
        .legend-bars { display: flex; gap: 3px; }
        .bar { width: 25px; height: 10px; border-radius: 1px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="header"><h2>HEALTH MONITOR</h2><p>Europe Risk Intelligence</p></div>
        <div id="display-box" class="score-box">
            <span id="location-tag">HOVER OVER MAP</span>
            <span id="score-text">--%</span>
            <div id="status-text">WAITING FOR DATA</div>
        </div>
        <div class="input-group"><label>Systolic BP</label><input type="number" id="sys" value="120"></div>
        <div class="input-group"><label>Diastolic BP</label><input type="number" id="dia" value="80"></div>
        <div class="input-group"><label>Lifestyle Score</label><input type="number" id="life" value="5"></div>
        <button onclick="analyze()">Individual Analysis</button>
    </div>
    <div id="map"></div>
    <div class="legend">
        <div class="legend-title">Risk Index</div>
        <div class="legend-bars">
            <div class="bar" style="background:#2ecc71"></div>
            <div class="bar" style="background:#a2d149"></div>
            <div class="bar" style="background:#f1c40f"></div>
            <div class="bar" style="background:#e67e22"></div>
            <div class="bar" style="background:#c8102e"></div>
        </div>
    </div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const map = L.map('map', { zoomControl: false }).setView([50, 15], 4);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png').addTo(map);

        const db = {
            "FRA": {s: 18, t: "Optimal", c: "#2ecc71", n: "France"},
            "NLD": {s: 15, t: "Optimal", c: "#2ecc71", n: "Netherlands"},
            "ESP": {s: 32, t: "Normal", c: "#a2d149", n: "Spain"},
            "ITA": {s: 45, t: "Elevated", c: "#f1c40f", n: "Italy"},
            "GBR": {s: 62, t: "Stage 1", c: "#e67e22", n: "UK"},
            "DEU": {s: 84, t: "Critical", c: "#c8102e", n: "Germany"},
            "POL": {s: 79, t: "Critical", c: "#c8102e", n: "Poland"},
            "GEO": {s: 88, t: "Critical", c: "#c8102e", n: "Georgia"},
            "UKR": {s: 75, t: "Stage 2", c: "#e67e22", n: "Ukraine"},
            "TUR": {s: 81, t: "Critical", c: "#c8102e", n: "Turkey"}
        };

        function style(feature) {
            const code = feature.properties.ISO_A3 || feature.properties.iso_a3;
            return {
                fillColor: db[code] ? db[code].c : "#e0e0e0",
                weight: 1.5,
                opacity: 1,
                color: 'white',
                fillOpacity: 0.85
            };
        }

        fetch('https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson')
            .then(res => res.json())
            .then(data => {
                L.geoJson(data, {
                    style: style,
                    onEachFeature: (f, l) => {
                        l.on('mouseover', function(e) {
                            const code = f.properties.ISO_A3 || f.properties.iso_a3;
                            const country = db[code];
                            if(country) {
                                document.getElementById('location-tag').innerText = country.n.toUpperCase();
                                document.getElementById('score-text').innerText = country.s + "%";
                                document.getElementById('status-text').innerText = country.t;
                                document.getElementById('score-text').style.color = country.c;
                                this.setStyle({ fillOpacity: 1, weight: 3, color: '#666' });
                            }
                        });
                        l.on('mouseout', function(e) {
                            this.setStyle({ fillOpacity: 0.85, weight: 1.5, color: 'white' });
                        });
                    }
                }).addTo(map);
            });

        async function analyze() {
            const res = await fetch('/analyze', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    s: document.getElementById('sys').value,
                    d: document.getElementById('dia').value,
                    l: document.getElementById('life').value
                })
            });
            const d = await res.json();
            document.getElementById('location-tag').innerText = "INDIVIDUAL RESULT";
            document.getElementById('score-text').innerText = d.score + "%";
            document.getElementById('status-text').innerText = d.status;
            document.getElementById('score-text').style.color = d.score < 25 ? "#2ecc71" : d.score < 65 ? "#f1c40f" : "#c8102e";
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
        s, d, l = int(data.get('s', 120)), int(data.get('d', 80)), int(data.get('l', 5))
        penalty = (abs(s - 120) * 0.5) + (abs(d - 80) * 0.8) + ((10 - l) * 2)
        score = round(max(0, min(100, penalty)), 1)
        status = "Optimal" if score < 20 else "Elevated" if score < 60 else "Critical"
        return jsonify({"score": score, "status": status})
    except Exception:
        return jsonify({"score": 0, "status": "Error"}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
