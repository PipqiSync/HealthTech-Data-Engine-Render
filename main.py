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
    <title>Europe Health Monitor | Hypertension v0.1</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        :root { 
            --ahti-red: #c8102e; 
            --panel-bg: #ffffff;
            --text-main: #333333;
        }
        
        html, body { 
            margin: 0; padding: 0; height: 100vh; width: 100vw; 
            overflow: hidden; font-family: 'Inter', 'Helvetica Neue', sans-serif; 
            background: #f4f7f6; 
        }
        
        body { display: flex; }

        /* Sidebar - Exact match to image layout */
        .sidebar { 
            width: 320px; height: 100vh; background: var(--panel-bg); 
            padding: 25px; display: flex; flex-direction: column; 
            box-sizing: border-box; border-right: 1px solid #e0e0e0;
            z-index: 1000; box-shadow: 2px 0 10px rgba(0,0,0,0.05);
        }

        .header h2 { margin: 0; font-size: 22px; color: var(--ahti-red); font-weight: 800; }
        .header p { margin: 5px 0 20px; font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 1px; }

        /* Score-box: 30% smaller as requested */
        .score-box {
            background: #fff; border: 2px solid #f0f0f0;
            border-radius: 12px; padding: 15px; text-align: center;
            margin-bottom: 25px; transition: all 0.4s ease;
        }

        #score-text { font-size: 44px; font-weight: 900; color: #222; display: block; line-height: 1; }
        #status-text { font-size: 10px; font-weight: 700; color: #999; text-transform: uppercase; margin-top: 8px; }

        .input-group { margin-bottom: 15px; }
        label { display: block; font-size: 11px; font-weight: 700; color: #444; margin-bottom: 6px; }
        input { 
            width: 100%; border: 1.5px solid #e0e0e0; border-radius: 6px; 
            padding: 12px; font-size: 15px; box-sizing: border-box; background: #fafafa;
        }

        button { 
            width: 100%; padding: 18px; background: var(--ahti-red); color: white; 
            border: none; border-radius: 8px; font-weight: 800; cursor: pointer; 
            font-size: 14px; text-transform: uppercase; margin-top: auto;
            letter-spacing: 1px; transition: 0.2s;
        }
        button:hover { background: #a50d26; transform: translateY(-1px); }

        #map { flex: 1; height: 100vh; background: #cbd5e1; }

        /* Legend Style from image */
        .legend {
            position: absolute; bottom: 30px; left: 350px;
            background: white; padding: 15px; border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1); z-index: 1000;
        }
        .legend-title { font-size: 10px; font-weight: 800; margin-bottom: 8px; text-transform: uppercase; }
        .legend-bars { display: flex; gap: 4px; }
        .bar { width: 30px; height: 12px; border-radius: 2px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="header">
            <h2>HEALTH MONITOR</h2>
            <p>Hypertension Risk Assessment</p>
        </div>

        <div id="display-box" class="score-box">
            <span id="score-text">--%</span>
            <div id="status-text">INPUT DATA</div>
        </div>

        <div class="input-group">
            <label>Systolic BP (mmHg)</label>
            <input type="number" id="sys" value="120">
        </div>
        <div class="input-group">
            <label>Diastolic BP (mmHg)</label>
            <input type="number" id="dia" value="80">
        </div>
        <div class="input-group">
            <label>Lifestyle Factors (0-10)</label>
            <input type="number" id="life" value="5">
        </div>

        <button onclick="analyze()">Execute Analysis</button>
    </div>

    <div id="map"></div>

    <div class="legend">
        <div class="legend-title">Risk Level Index</div>
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

        // 5-Tier Hypertension Risk Color Mapping (Simulated Regional Data)
        function getColor(code) {
            const riskMap = {
                "FRA": "#2ecc71", "ESP": "#a2d149", "DEU": "#c8102e", 
                "ITA": "#f1c40f", "GBR": "#e67e22", "POL": "#c8102e",
                "NLD": "#2ecc71", "BEL": "#a2d149", "GEO": "#c8102e",
                "TUR": "#c8102e", "GRC": "#e67e22", "UKR": "#e67e22"
            };
            return riskMap[code] || "#eeeeee";
        }

        fetch('https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson')
            .then(res => res.json())
            .then(data => {
                L.geoJson(data, {
                    style: (f) => ({
                        fillColor: getColor(f.properties.ISO_A3),
                        weight: 1, color: "#ffffff", fillOpacity: 0.85
                    })
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
            const data = await res.json();
            
            const scoreTxt = document.getElementById('score-text');
            const box = document
