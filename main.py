import asyncio
import websockets
import uuid
import json
from gpt4all import GPT4All
from scraper import scrape_website

relay = "wss://relay.damus.io"
# modelName = "orca-mini-3b.ggmlv3.q4_0.bin"
# modelName = "wizardlm-13b-v1.1-superhot-8k.ggmlv3.q4_0"
modelName = "llama-2-7b-chat.ggmlv3.q4_0"

# 65003 = Summarize
kinds = "[65003]"
limit = "100"


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
                    model = GPT4All(modelName)
                    # scrape and truncate the url
                    print("=====================================")
                    print("Scraping URL: " + tag[1])
                    print("=====================================")
                    text = truncate_text(scrape_website(tag[1]))
                    print("=====================================")
                    print("Using Text: " + text)
                    print("=====================================")
                    output = model.generate("Summarize the following text: " + text)
                    print("=====================================")
                    print("Output: " + output)
                    print("=====================================")
                    break
                elif (tag[2] == "text"):
                    model = GPT4All(modelName)
                    # scrape the url
                    print("=====================================")
                    print("Using Text: " + tag[1])
                    print("=====================================")
                    text = tag[1]
                    output = model.generate("Summarize the following text: " + text)
                    print("=====================================")
                    print("Output: " + output)
                    print("=====================================")
                    break
                elif (tag[2] == "job"):
                    # scrape the other jobs response
                    print("Scraping nostr DVM Job with ID: " + tag[1])
                    break

        # print("Original Content: " + originalContent)

    # else:
        # EOSE
        # print(f"{messageJson}")

def truncate_text(text):
    if len(text) <= 4000:
        return text
    else:
        last_period_index = text[:4000].rfind('.')
        if last_period_index != -1:
            return text[:last_period_index+1]
        else:
            return text[:4000]

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