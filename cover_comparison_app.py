#!/usr/bin/env python3
"""
Flask App for Cover Image Comparison Results

Displays HTML table comparing DeepSeek vs Google Books cover images.
"""

import sqlite3

from flask import Flask, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.after_request
def add_csp(response):
    response.headers["Content-Security-Policy"] = "img-src * data: blob:; upgrade-insecure-requests"
    return response

@app.route("/images/<filename>")
def serve_image(filename):
    return send_from_directory("cache/images", filename)

def get_comparison_results() -> list[dict]:
    """Get results from database"""
    db = sqlite3.connect("project_state.db")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM cover_comparison_results ORDER BY id")
    columns = [desc[0] for desc in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    db.close()
    return results

@app.route("/")
def index():
    """Main page with comparison table"""
    results = get_comparison_results()

    # Calculate stats
    total = len(results)
    deepseek_success = sum(1 for r in results if r["deepseek_success"])
    google_success = sum(1 for r in results if r["google_success"])
    both_success = sum(1 for r in results if r["deepseek_success"] and r["google_success"])
    deepseek_only = sum(1 for r in results if r["deepseek_success"] and not r["google_success"])
    google_only = sum(1 for r in results if not r["deepseek_success"] and r["google_success"])

    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cover Image Comparison Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .stats {
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
            padding: 15px;
            background: #e8f4fd;
            border-radius: 5px;
        }
        .stat {
            text-align: center;
        }
        .stat-number {
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #007bff;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        .cover-img {
            max-width: 80px;
            max-height: 120px;
            object-fit: cover;
            border: 1px solid #ddd;
        }
        .no-image {
            color: #999;
            font-style: italic;
        }
        .success {
            color: #28a745;
            font-weight: bold;
        }
        .failure {
            color: #dc3545;
            font-weight: bold;
        }
        .series-title {
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖼️ Cover Image Comparison Test</h1>
        <p>Comparing cover image URLs from DeepSeek API vs Google Books API (keyless) for {{ total }} popular manga volumes.</p>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{{ deepseek_success }}</div>
                <div>DeepSeek Success</div>
            </div>
            <div class="stat">
                <div class="stat-number">{{ google_success }}</div>
                <div>Google Success</div>
            </div>
            <div class="stat">
                <div class="stat-number">{{ both_success }}</div>
                <div>Both Success</div>
            </div>
            <div class="stat">
                <div class="stat-number">{{ deepseek_only }}</div>
                <div>DeepSeek Only</div>
            </div>
            <div class="stat">
                <div class="stat-number">{{ google_only }}</div>
                <div>Google Only</div>
            </div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Series</th>
                    <th>Volume</th>
                    <th>ISBN</th>
                    <th>DeepSeek Cover</th>
                    <th>Google Cover</th>
                    <th>DeepSeek Status</th>
                    <th>Google Status</th>
                </tr>
            </thead>
            <tbody>
                {% for result in results %}
                <tr>
                    <td class="series-title">{{ result.series_name }}</td>
                    <td>{{ result.volume }}</td>
                    <td>{{ result.isbn or 'N/A' }}</td>
                    <td>
                        {% if result.deepseek_cover %}
                            <img src="{{ result.deepseek_cover }}" alt="DeepSeek Cover" class="cover-img" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                            <span style="display:none;" class="no-image">Image failed to load</span>
                        {% else %}
                            <span class="no-image">No image</span>
                        {% endif %}
                    </td>
                    <td>
                        {% if result.google_cover %}
                            <img src="{{ result.google_cover }}" alt="Google Cover" class="cover-img" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                            <span style="display:none;" class="no-image">Image failed to load</span>
                        {% else %}
                            <span class="no-image">No image</span>
                        {% endif %}
                    </td>
                    <td class="{{ 'success' if result.deepseek_success else 'failure' }}">
                        {{ '✓ Success' if result.deepseek_success else '✗ Failed' }}
                    </td>
                    <td class="{{ 'success' if result.google_success else 'failure' }}">
                        {{ '✓ Success' if result.google_success else '✗ Failed' }}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
    """

    return render_template_string(html_template,
                                results=results,
                                total=total,
                                deepseek_success=deepseek_success,
                                google_success=google_success,
                                both_success=both_success,
                                deepseek_only=deepseek_only,
                                google_only=google_only)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001, ssl_context=("cert.pem", "key.pem"))
