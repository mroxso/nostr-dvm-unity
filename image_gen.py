import asyncio
import websockets
import uuid
import json
from gpt4all import GPT4All
from scraper import scrape_website

relay = "wss://relay.damus.io"

# 65003 = Summarize
# 65005 = Image Generation
kinds = "[65005]"
limit = "2"


async def handle_request(uri, message):
    # # Add your request handling logic here
    messageJson = json.loads(message)
    if(messageJson[0] != "EOSE"):
        text = ""
        event = messageJson[2]
        tags = event["tags"]

        for tag in tags:
            if tag[0] == "i":
                text = tag[1]
                break
        
        if text != "":
            print("=====================================")
            print("Using Text: " + text)
            print("=====================================")

        # print("")
        # print(event)

async def single_request_ws(uri, originalContentId):
    async with websockets.connect(uri) as ws:
        # Send the message
        subscription_id = str(uuid.uuid1().hex)
        msgstr = '["REQ",' + f'"{subscription_id}"' + ', {"kinds": [1], "ids": [' + originalContentId + ']}]'
        await ws.send(msgstr)

        # Wait for response
        response = await ws.recv()
        return response

async def connect_to_ws(uri, send_message):
    async with websockets.connect(uri) as ws:
        # Send the initial message
        await ws.send(send_message)

        # Keep waiting for new messages
        while True:
            response = await ws.recv()
            asyncio.create_task(handle_request(uri, response))

async def main():
    # await connect_to_ws('ws://localhost:8080', 'Hello, server!')

    subscription_id = str(uuid.uuid1().hex)
    msgstr = '["REQ",' + f'"{subscription_id}"' + ', {"kinds": ' + kinds + ', "limit": ' + limit + '}]'
    await connect_to_ws(relay, msgstr)

# Start the event loop
asyncio.run(main())