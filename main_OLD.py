import requests
import time
import ssl
import os
import json
import uuid
from pynostr.event import Event, EventKind
from pynostr.relay_manager import RelayManager
from pynostr.message_type import ClientMessageType
from pynostr.key import PrivateKey
from pynostr.filters import FiltersList, Filters
from pynostr.encrypted_dm import EncryptedDirectMessage
from gpt4all import GPT4All
import gc

system_message = "You are Unity. You are a Data Vending Machine on a public and open-source social media protocol called nostr. You should always stay happy and kind. You as an AI have a lot of knowledge about everything in the world. Please answer the question of the user as good as you can."

relay_manager = RelayManager(timeout=2)

def run():
    messages_done = []

    env_private_key = os.environ.get("PRIVATE_KEY")
    if not env_private_key:
        print('The environment variable "PRIVATE_KEY" is not set.')
        exit(1)

    private_key = PrivateKey(bytes.fromhex(env_private_key))
    # Read env variable and add relays
    env_relays = os.getenv('RELAYS') # None
    if env_relays is None:
        env_relays = "wss://relay.damus.io"
    for relay in env_relays.split(","):
        print("Adding relay: " + relay)
        relay_manager.add_relay(relay)

    print("Pubkey: " + private_key.public_key.bech32())
    print("Pubkey (hex): " + private_key.public_key.hex())

    while(True):
        filters = FiltersList([Filters(pubkey_refs=[private_key.public_key.hex()], kinds=[EventKind.ENCRYPTED_DIRECT_MESSAGE])])
        subscription_id = uuid.uuid1().hex
        relay_manager.add_subscription_on_all_relays(subscription_id, filters)
        relay_manager.run_sync()
        while relay_manager.message_pool.has_notices():
            notice_msg = relay_manager.message_pool.get_notice()
            print("Notice: " + notice_msg.content)
        while relay_manager.message_pool.has_events():
            event_msg = relay_manager.message_pool.get_event()
            recipient_pubkey = event_msg.event.pubkey
            msg_decrypted = EncryptedDirectMessage()
            msg_decrypted.decrypt(private_key_hex=private_key.hex(), encrypted_message=event_msg.event.content, public_key_hex=event_msg.event.pubkey)
            currentTime = time.time()
            if(currentTime - 60 < event_msg.event.created_at):
                if(event_msg.event.id in messages_done):
                    continue
                print ("'" +msg_decrypted.cleartext_content + "' from " + event_msg.event.pubkey)
                print ("-> Generating Answer..")
                # response = gptj.generate(msg_decrypted.cleartext_content, False)[1:]
                gc.collect()
                messages = [{"role": "system", "content": system_message},{"role": "user", "content": msg_decrypted.cleartext_content}]
                # gptj = GPT4All("ggml-gpt4all-j-v1.3-groovy")
                # gptj = GPT4All("nous-hermes-13b.ggmlv3.q4_0.bin")
                gptj = GPT4All("wizardLM-13B-Uncensored.ggmlv3.q4_0.bin")
                response = gptj.chat_completion(messages)['choices'][0]['message']['content']
                if(response == ""):
                    response = "I don't know what to say."
                # check if first char in response is a space
                if(response[0] == " "):
                    response = response[1:]
                # print("--> " + response)
                print("Sending response to " + event_msg.event.pubkey)

                dm = EncryptedDirectMessage()
                dm.encrypt(private_key.hex(),
                    recipient_pubkey=recipient_pubkey,
                    cleartext_content=response,
                )
                dm_event = dm.to_event()
                dm_event.sign(private_key.hex())
                relay_manager.publish_event(dm_event)
                print("Response sent to " + event_msg.event.pubkey)

                # Free memory
                del gptj
                gc.collect()

                messages_done.append(event_msg.event.id)
                continue
        time.sleep(10)
        relay_manager.close_all_relay_connections()

try:
    run()
except KeyboardInterrupt:
    print("KeyboardInterrupt")
    relay_manager.close_all_relay_connections()
    exit(1)
except:
    print("Exception")
    relay_manager.close_all_relay_connections()
    run()
