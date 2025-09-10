from flask import Flask, render_template_string
import json
import os
from datetime import datetime

app = Flask(__name__)

# Find latest log file
log_files = [f for f in os.listdir('.') if f.startswith('security_log_') and f.endswith('.json')]
log_files.sort(reverse=True)
latest_log = log_files[0] if log_files else None

# Load log data
if latest_log:
    with open(latest_log, 'r') as f:
        log_entries = json.load(f)
else:
    log_entries = []

# Prepare data for charts
sod_count = sum(len(e['details']) for e in log_entries if e['type'] == 'SOD Violation')
least_priv_count = sum(len(e['details']) for e in log_entries if e['type'] == 'Least Privilege Violation')
mfa_count = sum(len(e['details']) for e in log_entries if e['type'] == 'MFA Enforcement Violation')

chart_data = {
    'labels': ['SOD Violations', 'Least Privilege Violations', 'MFA Violations'],
    'counts': [sod_count, least_priv_count, mfa_count]
}

# Anonymize details for analyst view
anonymized_entries = []
for entry in log_entries:
    anonymized = []
    for item in entry.get('details', []):
        anonymized.append({
            'risk_level': item.get('risk_level', 'N/A'),
            'type': entry['type'],
            'detected_date': item.get('detected_date', 'N/A'),
            'summary': f"Groups: {len(item.get('conflicting_groups', item.get('groups', [])))} | MFA: {item.get('mfa_enrolled', 'N/A')}"
        })
    anonymized_entries.append({'type': entry['type'], 'details': anonymized})

@app.route('/')
def dashboard():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Okta Security Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {
                font-family: 'Inter', Arial, sans-serif;
                background: linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%);
                margin: 0;
                padding: 0;
                color: #22223b;
            }
            .container {
                max-width: 1100px;
                margin: 40px auto;
                background: #fff;
                border-radius: 18px;
                box-shadow: 0 8px 32px rgba(60,72,88,0.12);
                padding: 32px 40px 40px 40px;
            }
            .header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 24px;
            }
            .logo {
                font-size: 2.2rem;
                font-weight: 700;
                color: #3f51b5;
                letter-spacing: 1px;
            }
            .badge {
                display: inline-block;
                padding: 6px 16px;
                border-radius: 8px;
                font-size: 1rem;
                font-weight: 600;
                background: #e0e7ff;
                color: #3f51b5;
                margin-left: 8px;
            }
            .kpi-row {
                display: flex;
                gap: 32px;
                margin-bottom: 32px;
            }
            .kpi-card {
                flex: 1;
                background: #f3f6fd;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(60,72,88,0.07);
                padding: 24px 18px;
                text-align: center;
            }
            .kpi-title {
                font-size: 1.1rem;
                color: #3f51b5;
                font-weight: 600;
                margin-bottom: 8px;
            }
            .kpi-value {
                font-size: 2.2rem;
                font-weight: 700;
                color: #22223b;
            }
            .chart-wrapper {
                margin: 32px 0 24px 0;
                background: #f3f6fd;
                border-radius: 12px;
                padding: 24px;
                box-shadow: 0 2px 8px rgba(60,72,88,0.07);
            }
            h2 {
                font-size: 1.5rem;
                font-weight: 600;
                margin-top: 32px;
                color: #22223b;
            }
            h3 {
                font-size: 1.1rem;
                font-weight: 600;
                margin-top: 24px;
                color: #3f51b5;
            }
            .summary-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 16px;
            }
            .summary-table th, .summary-table td {
                border: 1px solid #e0e7ff;
                padding: 8px 12px;
                text-align: left;
            }
            .summary-table th {
                background: #e0e7ff;
                color: #3f51b5;
                font-weight: 600;
            }
            .summary-table td {
                background: #f8fafc;
            }
            @media (max-width: 600px) {
                .container {
                    padding: 16px 8px;
                }
                .kpi-row {
                    flex-direction: column;
                    gap: 16px;
                }
                h1 {
                    font-size: 1.5rem;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <span class="logo">Okta Security Dashboard</span>
                <span class="badge">{{ date }}</span>
            </div>
            <div class="kpi-row">
                <div class="kpi-card">
                    <div class="kpi-title">SOD Violations</div>
                    <div class="kpi-value">{{ chart_data['counts'][0] }}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-title">Least Privilege Violations</div>
                    <div class="kpi-value">{{ chart_data['counts'][1] }}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-title">MFA Violations</div>
                    <div class="kpi-value">{{ chart_data['counts'][2] }}</div>
                </div>
            </div>
            <div class="chart-wrapper">
                <canvas id="securityChart" width="400" height="180"></canvas>
            </div>
            <script>
                var ctx = document.getElementById('securityChart').getContext('2d');
                var chart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: {{ chart_data['labels'] | safe }},
                        datasets: [{
                            label: 'Violations',
                            data: {{ chart_data['counts'] | safe }},
                            backgroundColor: [
                                'rgba(255, 99, 132, 0.3)',
                                'rgba(54, 162, 235, 0.3)',
                                'rgba(255, 206, 86, 0.3)'
                            ],
                            borderColor: [
                                'rgba(255, 99, 132, 1)',
                                'rgba(54, 162, 235, 1)',
                                'rgba(255, 206, 86, 1)'
                            ],
                            borderWidth: 2,
                            borderRadius: 8
                        }]
                    },
                    options: {
                        plugins: {
                            legend: {
                                display: false
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: { stepSize: 1 }
                            }
                        }
                    }
                });
            </script>
            <h2>Security Event Summary</h2>
            {% for entry in anonymized_entries %}
                <h3>{{ entry['type'] }}</h3>
                <table class="summary-table">
                    <tr>
                        <th>Risk Level</th>
                        <th>Type</th>
                        <th>Detected Date</th>
                        <th>Summary</th>
                    </tr>
                    {% for item in entry['details'] %}
                    <tr>
                        <td>{{ item['risk_level'] }}</td>
                        <td>{{ item['type'] }}</td>
                        <td>{{ item['detected_date'] }}</td>
                        <td>{{ item['summary'] }}</td>
                    </tr>
                    {% endfor %}
                </table>
            {% endfor %}
        </div>
    </body>
    </html>
    ''', chart_data=chart_data, anonymized_entries=anonymized_entries, date=datetime.now().strftime('%Y-%m-%d'))

if __name__ == '__main__':
    app.run(debug=True)
