import asyncio
import websockets
import uuid
import json
from gpt4all import GPT4All

relay = "wss://relay.damus.io"

# 65003 = Summarize
kinds = "[65003]"
limit = "100"

model = GPT4All("orca-mini-3b.ggmlv3.q4_0.bin")


async def handle_request(uri, message):
    # Add your request handling logic here
    messageJson = json.loads(message)
    if(messageJson[0] != "EOSE"):
        event = messageJson[2]
        content = event["content"]
        tags = event["tags"]

        originalContent = ""
        originalContentId = ""

        # print(tags)
        for tag in tags:
            # print(tag)
            if(tag[0] == "i"):
                # print("Found i tag")
                # print(tag[1])
                # originalContentId = tag[1]
                # originalContent = await single_request_ws(uri, originalContentId)
                if (tag[2] == "event"):
                    originalContentId = tag[1]
                    print("Scraping nostr event with ID: " + originalContentId)
                    # originalContent = await single_request_ws(uri, originalContentId)
                    break
                elif (tag[2] == "url"):
                    # scrape the url
                    print("Scraping URL: " + tag[1])
                    break
                elif (tag[2] == "text"):
                    # scrape the url
                    print("Using Text: " + tag[1])
                    break
                elif (tag[2] == "job"):
                    # scrape the other jobs response
                    print("Scraping nostr DVM Job with ID: " + tag[1])
                    break

        # print("Original Content: " + originalContent)

    # else:
        # EOSE
        # print(f"{messageJson}")

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