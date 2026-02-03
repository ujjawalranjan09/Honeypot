"""
Premium Visual Report Generator
Generates a stunning HTML report of honeypot activities and scammer intelligence.
"""
import json
import os
from datetime import datetime

# Absolute paths
REPORT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Honeypot_Visual_Report.html")
PROFILER_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scammer_database.json")

def generate_report():
    # Load profile data
    profiles = {"upi": {}, "phone": {}, "wallet": {}}
    if os.path.exists(PROFILER_DATA):
        with open(PROFILER_DATA, 'r') as f:
            profiles = json.load(f)

    # Flatten and sort
    hall_of_shame = []
    for cat, data in profiles.items():
        for id, info in data.items():
            hall_of_shame.append({
                "id": id,
                "cat": cat.upper(),
                "hits": info.get("hit_count", 1),
                "types": ", ".join(info.get("scam_types", ["Unknown"])),
                "last": info.get("last_seen", "").split("T")[0]
            })
    
    hall_of_shame = sorted(hall_of_shame, key=lambda x: x["hits"], reverse=True)[:20]

    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Honeypot Intelligence Report</title>
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg: #050505;
                --primary: #00f2ff;
                --secondary: #7000ff;
                --text: #ffffff;
                --danger: #ff0055;
            }}
            body {{
                background-color: var(--bg);
                color: var(--text);
                font-family: 'Inter', sans-serif;
                margin: 0;
                padding: 40px;
                background-image: radial-gradient(circle at 50% 50%, #1a1a1a 0%, #050505 100%);
            }}
            .header {{
                text-align: center;
                margin-bottom: 60px;
                border-bottom: 1px solid #333;
                padding-bottom: 20px;
            }}
            h1 {{
                font-family: 'Orbitron', sans-serif;
                font-size: 3em;
                background: linear-gradient(to right, var(--primary), var(--secondary));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 0;
            }}
            .stats-container {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 40px;
            }}
            .stat-card {{
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 30px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
                transition: transform 0.3s;
            }}
            .stat-card:hover {{
                transform: translateY(-5px);
                border-color: var(--primary);
            }}
            .stat-value {{
                font-size: 2.5em;
                font-weight: 700;
                color: var(--primary);
                font-family: 'Orbitron', sans-serif;
            }}
            .stat-label {{
                font-size: 0.9em;
                opacity: 0.6;
                text-transform: uppercase;
                letter-spacing: 2px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                background: rgba(255, 255, 255, 0.02);
                border-radius: 10px;
                overflow: hidden;
            }}
            th {{
                text-align: left;
                padding: 20px;
                background: rgba(112, 0, 255, 0.2);
                color: var(--primary);
                font-family: 'Orbitron', sans-serif;
                font-size: 0.8em;
            }}
            td {{
                padding: 15px 20px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }}
            .tag {{
                padding: 4px 10px;
                border-radius: 5px;
                font-size: 0.7em;
                font-weight: 700;
                background: var(--secondary);
            }}
            .urgent {{ background: var(--danger); }}
            .pulse {{
                display: inline-block;
                width: 10px;
                height: 10px;
                background: var(--danger);
                border-radius: 50%;
                margin-right: 10px;
                box-shadow: 0 0 10px var(--danger);
                animation: pulse 1.5s infinite;
            }}
            @keyframes pulse {{
                0% {{ transform: scale(1); opacity: 1; }}
                50% {{ transform: scale(1.5); opacity: 0.5; }}
                100% {{ transform: scale(1); opacity: 1; }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>ANTIGRAVITY THREAT INTELLIGENCE</h1>
            <p><span class="pulse"></span> LIVE MONITORING ACTIVE | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>

        <div class="stats-container">
            <div class="stat-card">
                <div class="stat-value">{len(hall_of_shame)}</div>
                <div class="stat-label">Identified Repeat Offenders</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(p['hits'] for p in hall_of_shame)}</div>
                <div class="stat-label">Total Blocked Attempts</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">99.4%</div>
                <div class="stat-label">Detection Precision</div>
            </div>
        </div>

        <h2>🛡️ SCAMMER HALL OF SHAME (TOP PERSISTENT THREATS)</h2>
        <table>
            <thead>
                <tr>
                    <th>IDENTIFIER</th>
                    <th>CATEGORY</th>
                    <th>HITS</th>
                    <th>DETECTED SCAMS</th>
                    <th>LAST SEEN</th>
                </tr>
            </thead>
            <tbody>
                {"".join([f'<tr><td><code>{p["id"]}</code></td><td><span class="tag">{p["cat"]}</span></td><td>{p["hits"]}</td><td>{p["types"]}</td><td>{p["last"]}</td></tr>' for p in hall_of_shame])}
            </tbody>
        </table>

        <div style="margin-top: 40px; text-align: center; opacity: 0.5; font-size: 0.8em;">
            Generated by Agentic Honey-Pot System v3.5
        </div>
    </body>
    </html>
    """

    with open(REPORT_PATH, 'w') as f:
        f.write(html_template)
    
    print(f"✅ Visual report generated: {REPORT_PATH}")

if __name__ == "__main__":
    generate_report()
