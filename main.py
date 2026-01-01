import os
import requests
import pandas as pd
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 1. DATA SERVICE: Ophalen van WHO Hypertensie data
def get_who_hypertension_data():
    try:
        # Indicator BP_01: Age-standardized prevalence of raised blood pressure
        url = "https://ghoapi.azureedge.net/api/BP_01"
        r = requests.get(url, timeout=10)
        data = r.json()
        
        # Filteren op de meest recente data (meestal per land het laatste jaar)
        df = pd.DataFrame(data['value'])
        # We pakken de 'Both sexes' data (Dim1 = BTSX)
        df = df[df['Dim1'] == 'BTSX']
        
        # Groepeer per land en pak het meest recente jaar (TimeDim)
        latest_data = df.sort_values('TimeDim').groupby('SpatialDim').last().reset_index()
        
        # Mapping naar een dictionary voor de frontend: { "NLD": 15.2, "FRA": 18.1, ... }
        # Let op: WHO gebruikt ISO3 codes in 'SpatialDim'
        stats_map = {row['SpatialDim']: round(row['NumericValue'], 1) for _, row in latest_data.iterrows()}
        return stats_map
    except Exception as e:
        print(f"Error fetching WHO data: {e}")
        return {}

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Global Hypertension Intelligence | WHO Powered</title>
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
        .legend-bars { display: flex; align-items: center; gap: 8px; font-size: 10px; font-weight: bold; }
        .bar-container { display: flex; gap: 2px; }
        .bar { width: 20px; height: 10px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="header"><h2>DATA ENGINE</h2><p>WHO Hypertension Prevalence</p></div>
        <div id="display-box" class="score-box">
            <span id="location-tag">MOVE CURSOR OVER MAP</span>
            <span id="score-text">--%</span>
            <div id="status-text">REAL-TIME WHO STATS</div>
        </div>
        <div class="input-group"><label>Personal Systolic</label><input type="number" id="sys" value="120"></div>
        <div class="input-group"><label>Personal Diastolic</label><input type="number" id="dia" value="80"></div>
        <button onclick="analyze()">Compare with Regional Data</button>
    </div>
    <div id="map"></div>
    <div class="legend">
        <div class="legend-title">Prevalence (Adults)</div>
        <div class="legend-bars">
            <span>Low</span>
            <div class="bar-container">
                <div class="bar" style="background:#2ecc71"></div>
                <div class="bar" style="background:#f1c40f"></div>
                <div class="bar" style="background:#e67e22"></div>
                <div class="bar" style="background:#c8102e"></div>
            </div>
            <span>High</span>
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const map = L.map('map', { zoomControl: false }).setView([20, 10], 2);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png').addTo(map);

        let whoData = {};

        // Kleurfunctie op basis van hypertensie %
        function getColor(d) {
            return d > 30 ? '#c8102e' :
                   d > 25 ? '#e67e22' :
                   d > 20 ? '#f1c40f' :
                   d > 0  ? '#2ecc71' : '#e0e0e0';
        }

        function style(feature) {
            const code = feature.id; // GeoJSON id is meestal ISO_A3
            const val = whoData[code] || 0;
            return {
                fillColor: getColor(val),
                weight: 1,
                opacity: 1,
                color: 'white',
                fillOpacity
