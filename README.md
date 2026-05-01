# Havoc C3
Havoc Custom Communication Channels (Havoc C3) is a custom agent and listener template that integrates with Havoc C2 Framework to allow developers to easily implement their own custom communication channels between the agent implant and the C2 teamserver.

### Project Structure
The files you see in the repo are as follows:
- `havoc/*` - These are the Havoc C2 service Python files. They need to be in the same directory as the Listener and Handler.
- `agent.py` - This is the Python malware implant that runs on the victim machine. It's not FUD by any means, if you want it undetectable, that'll take some work from your side.
- `handler.py` - This registers the agent and listener with the Havoc teamserver and is also responsible for generating the agent payloads (but that part isn't implemented).
- `listener.py` - This script sits on the attacker side of the equation. It is responsible for translating agent communications from the custom channel and handing it over to the teamserver. It also takes commands from the teamserver and sends them over the custom channel to the agent. This is essentially the translation layer between the custom agent and the standard teamserver.

### Getting Started
1) Clone the repo.
2) Change the config at the top of the `python` class in `handler.py` to whatever you want.
3) Look inside `agent.py` and `listener.py`. You'll see two functions in each which are called `uploadData` and `downloadData`. These are the functions where you need to implement your custom channel.
4) `uploadData` - This receives a Base64 string as input and needs to encode that data and send it along the custom communication channel.
5) `downloadData` - This is called when the agent or listener wishes to retrieve data from the custom channel. This function must output the original data which was sent over the channel as a Base64 string.
6) Implement these two functions in both `agent.py` and `listener.py`.
7) Clone, build, and spin up Havoc C2 Framework.
8) Execute the handler.
9) Execute the listener.
10) Execute the agent on the victim machine.
11) Profit.

Everything between upload and download relies on your communication channel implementation. The vast majority of the Havoc related stuff is abstracted away, so all you need to deal with is moving Base64 data over a channel and downloading and decoding it on the other side.

### Known issues
- It's janky, if you have issues let me know and we can try fix them.
