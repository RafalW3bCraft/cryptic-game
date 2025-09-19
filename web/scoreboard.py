#!/usr/bin/env python3
# web/scoreboard.py
# Simple Flask app to serve the leaderboard JSON and a tiny HTML page.
# Usage: python3 web/scoreboard.py

from flask import Flask, jsonify, render_template_string
import json, os

app = Flask(__name__, static_folder='static', template_folder='templates')

LEADERBOARD_JSON = 'web/leaderboard.json'

HTML = '''
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>TheFool Leaderboard</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; }
    table { border-collapse: collapse; width: 560px; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align:left; }
    th { background: #222; color: #fff; }
  </style>
</head>
<body>
  <h1>TheFool Leaderboard</h1>
  {% if board %}
  <table>
    <tr><th>Rank</th><th>Author</th><th>Points</th><th>Reports</th></tr>
    {% for entry in board %}
      <tr>
        <td>{{ loop.index }}</td>
        <td>{{ entry.author }}</td>
        <td>{{ entry.points }}</td>
        <td>{{ entry.reports }}</td>
      </tr>
    {% endfor %}
  </table>
  <p>Updated: {{ updated }}</p>
  {% else %}
  <p>No leaderboard data yet. Run the scorer: <code>python3 tools/scorer/score.py</code></p>
  {% endif %}
</body>
</html>
'''

@app.route('/leaderboard.json')
def leaderboard_json():
    if not os.path.exists(LEADERBOARD_JSON):
        return jsonify({'updated': None, 'leaderboard': []})
    with open(LEADERBOARD_JSON, 'r', encoding='utf-8') as fh:
        return jsonify(json.load(fh))

@app.route('/')
def index():
    data = {}
    if os.path.exists(LEADERBOARD_JSON):
        with open(LEADERBOARD_JSON, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
    board = data.get('leaderboard', [])
    updated = data.get('updated', 'unknown')
    return render_template_string(HTML, board=board, updated=updated)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
