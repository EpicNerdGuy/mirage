# Mirage
**Mirage** is a custom C3 (Custom Communication Channel) built on top of the [Havoc C2 Framework](https://github.com/HavocFramework/Havoc). It routes agent traffic covertly through a public-facing website turning ordinary HTTP endpoints into a fully functional command-and-control channel.

The teamserver never speaks directly to the agent. Instead, commands and responses flow through a website acting as a dead drop, making traffic indistinguishable from normal web activity.

---

## How It Works

<img width="1517" height="642" alt="image" src="https://github.com/user-attachments/assets/4a7f047c-9106-4705-b5c7-b3bb3785c0fd" />


**Step by step:**

1. Operator types a command in the Havoc client
2. `listener.py` polls the Havoc client for pending commands
3. Listener sees the queued command
4. Listener uploads the command to the website via `POST /api/sync` (`uploadData`)
5. Agent polls the website for new commands via `GET /api/telemetry` (`downloadData`)
6. Website returns the command to the agent
7. Agent executes the command and uploads the response via `POST /api/telemetry` (`uploadData`)
8. Listener fetches the agent response from the website via `GET /api/sync` (`downloadData`)
9. Listener sends the response back to the Havoc client
10. Output appears in the teamserver UI

The website is the covert dead drop, neither the teamserver nor the agent ever talk to each other directly.

---

## Project Structure

```
mirage/
├── havoc/          # Havoc C2 service Python files (must stay alongside handler/listener)
├── agent.py        # Implant — runs on the victim machine
├── handler.py      # Registers the agent & listener with the Havoc teamserver
├── listener.py     # Translation layer between the custom channel and the teamserver
└── main.py         # Entry point
```

### Component Breakdown

| File | Role | Runs on |
|------|------|---------|
| `handler.py` | Registers agent + listener with teamserver, handles payload config | Attacker machine |
| `listener.py` | Polls teamserver for cmds, relays via website (`/api/sync`) | Attacker machine |
| `agent.py` | Executes commands, relays output via website (`/api/telemetry`) | Victim machine |

---

## Getting Started

### Prerequisites

- [Havoc C2 Framework](https://github.com/HavocFramework/Havoc) cloned, built, and running
- Python 3.x
- A web server exposing `/api/sync` and `/api/telemetry` endpoints (your custom channel)

### Setup

**1. Clone the repo**
```bash
git clone https://github.com/yourname/mirage
cd mirage
```

**2. Configure the handler**

Open `handler.py` and edit the config block at the top of the `python` class:
```python
# Teamserver connection
HOST = "127.0.0.1"
PORT = 40056
USER = "operator"
PASS = "your-password"
```

**3. Implement your custom channel**

In both `agent.py` and `listener.py`, implement two functions:

```python
def uploadData(data: str):
    """
    Receives a Base64 string.
    Encode and send it over your custom channel (e.g. POST to your website).
    """
    pass

def downloadData() -> str:
    """
    Poll your custom channel for incoming data.
    Return the raw Base64 string that was uploaded on the other side.
    """
    pass
```

Everything else is abstracted away. Your only job is moving Base64 blobs through your chosen medium a website, a pastebin, a tweet, an image whatever you want the channel to be.

**4. Start the Havoc teamserver** (if not already running)
```bash
cd /path/to/Havoc
./havoc server --profile ./profiles/havoc.yaotl --debug
```

**5. Run in order**
```bash
# Terminal 1 — register with teamserver
python3 handler.py

# Terminal 2 — start the listener (translation layer)
python3 listener.py

# Terminal 3 — run the agent on the victim machine
python3 agent.py
```

---

## Extending Mirage

The channel implementation is entirely up to you. Some ideas:

- **Website dead drop** — POST/GET to a Flask or Express app (reference implementation)
- **Cloud storage** — S3 bucket, Google Drive, Dropbox
- **Social media** — Twitter/X DMs, Discord webhooks, Reddit posts
- **DNS** — encode data in DNS TXT record queries
- **Steganography** — hide payloads inside images uploaded to Imgur

As long as `uploadData` and `downloadData` are inverse operations that round-trip Base64 cleanly, any channel works.

## Disclaimer

Mirage is intended for authorized penetration testing and red team engagements only. Use against systems you do not own or have explicit written permission to test is illegal. The authors assume no liability for misuse.
