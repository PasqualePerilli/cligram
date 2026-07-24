from telethon.sessions import StringSession
from telethon.sync import TelegramClient
import configparser 
import os 

fullpath = os.path.expanduser("~/.config/cligram/cligram.conf") 
parser = configparser.ConfigParser() 

async def generate_userconf():
    
    print("Get api id and hash from https://my.telegram.org") 

    api_id = input("Enter your api id: ").strip()
    api_hash = input("Enter your api hash: ").strip()
    phone = input("Enter your phone number (include country code, e.g. +1415555267): ").strip()

    string_session = ''

    if api_id and api_hash and phone:

        client = TelegramClient(StringSession(), api_id, api_hash)
        await client.start(phone)

        string_session = client.session.save()

        parser['cligram'] = {
                'api_id': api_id,
                'api_hash': api_hash, 
                'string_session': string_session
                } 

        os.makedirs(os.path.dirname(fullpath), exist_ok=True) 

        with open(fullpath, 'w') as f: 
            parser.write(f) 

async def generate_botconf(): 

    parser.read(fullpath) 
    bot_name = input("Enter bot name: ").strip()
    bot_token = input("Enter bot token: ").strip()

    api_id = ''
    api_hash = ''
    string_session = '' 
    
    if parser.has_section('cligram'): 
        api_id = parser.get('cligram', 'api_id') 
        api_hash = parser.get('cligram', 'api_hash') 
    else: 
        print("Generate user configuration first") 
        exit(1) 

    if bot_token: 
        client = TelegramClient(StringSession(), api_id, api_hash)
        await client.start(bot_token=bot_token)
        
        string_session = client.session.save() 

        if not parser.has_section(bot_name): 
            parser.add_section(bot_name) 

        parser.set(bot_name, 'string_session', string_session) 

        with open(fullpath, 'w') as f: 
            parser.write(f) 

        print("Restart daemon to load bot sessions") 


async def generate_session():

    if not os.path.exists(fullpath):
        print(f"Configuration file not found at {fullpath}")
        print("Run cligram first to create the configuration file with api_id and api_hash")
        exit(1)

    parser.read(fullpath)

    if not parser.has_section('cligram'):
        print("No [cligram] section found in config file")
        exit(1)

    api_id = parser.get('cligram', 'api_id')
    api_hash = parser.get('cligram', 'api_hash')

    if not api_id or not api_hash:
        print("api_id and api_hash must be set in the config file")
        exit(1)

    phone = input("Enter your phone number (include country code, e.g. +1415555267): ").strip()

    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.start(phone)

    string_session = client.session.save()

    parser.set('cligram', 'string_session', string_session)

    with open(fullpath, 'w') as f:
        parser.write(f)

    print("Session string generated and saved to config")