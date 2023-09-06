import asyncio
import websockets
import os
import uuid
import json
from pynostr.event import Event, EventKind
from pynostr.relay_manager import RelayManager
from pynostr.message_type import ClientMessageType
from pynostr.key import PrivateKey
from pynostr.filters import FiltersList, Filters
from pynostr.encrypted_dm import EncryptedDirectMessage
from gpt4all import GPT4All

fallback_relay = "wss://relay.damus.io"

system_message = "You are a Data Vending Machine. Your job is to translate the input and output the translated version. Nothing more."

relay_manager = RelayManager(timeout=2)

env_private_key = os.environ.get("PRIVATE_KEY")
if not env_private_key:
    # print('The environment variable "PRIVATE_KEY" is not set.')
    # exit(1)
    env_private_key = PrivateKey().hex()
private_key = PrivateKey(bytes.fromhex(env_private_key))

env_relays = os.getenv('RELAYS')
if env_relays is None:
    env_relays = "wss://relay.damus.io"
for relay in env_relays.split(","):
    print("Adding relay: " + relay)
    relay_manager.add_relay(relay)

print("Pubkey: " + private_key.public_key.bech32())
print("Pubkey (hex): " + private_key.public_key.hex())

async def connect_and_listen():
    # Connect to the WebSocket server
    async with websockets.connect(fallback_relay) as websocket:
        subscription_id = str(uuid.uuid1().hex)
        # Send a message
        msgstr = '["REQ",' + f'"{subscription_id}"' + ', {"kinds": [65004], "limit": 1000}]'
        await websocket.send(msgstr)

        # Listen for responses
        while True:
            response = await websocket.recv()
            responseJson = json.loads(response)
            # Process the received response
            if responseJson[0] == "EVENT":
                print(f"{responseJson[2]}")
            elif responseJson[0] == "EOSE":
                print(f"{responseJson}")

# Run the event loop
asyncio.get_event_loop().run_until_complete(connect_and_listen())