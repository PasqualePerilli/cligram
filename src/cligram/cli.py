from cligram.meta_data import meta_extract
from cligram.inquirer import display_list
from cligram.progress_bar import progress
from argparse import ArgumentParser
from rich.console import Console 
from rich.panel import Panel
from os import path
import subprocess
import asyncio 
import socket
import json 
import sys


""" Get api id and hash from https://my.telegram.org """

SOCK_PATH = "/tmp/cligram.sock" 
CONFIG_DIR = "~/.config/cligram/"
HEADER = 4096
DEFAULT_LIMIT = 500

class DarkSendSocket:
    def __init__(self, path):
        self.path = path
        self.sock = None

    def __enter__(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.path)
        return self

    def start_server(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(SOCK_PATH)
        self.sock.listen(5)

    def relay_to_server(self, cmd_dict):
        message = json.dumps(cmd_dict).encode('utf-8') 
        message_length = len(message) 

        header_message = str(message_length).encode('utf-8')
        header_message += b' ' * (HEADER - len(header_message)) 

        self.sock.send(header_message)
        self.sock.send(message)

    def get_from_server(self): 
        message_length = self.sock.recv(HEADER).decode('utf-8') 
        message = self.sock.recv(int(message_length)).decode('utf-8') 
        return message 

    def relay_to_client(self, conn, cmd_dict):

        message = json.dumps(cmd_dict).encode('utf-8') 
        message_length = len(message) 

        header_message = str(message_length).encode('utf-8')
        header_message += b' ' * (HEADER - len(header_message)) 

        conn.send(header_message)
        conn.send(message)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sock.close()

async def cli(args):

    async def reload_chats(): 

        nonlocal chat_list 
        with DarkSendSocket(SOCK_PATH) as sock:
            cmd = [{"client": "user", "type": "get_chats"}]
            sock.relay_to_server(cmd) 
            response = sock.get_from_server() 

        chat_list = json.loads(response) 

        with open(chat_path, 'w') as chat_file: 
            json.dump(chat_list, chat_file) 

    async def load_chats(): 
        nonlocal chat_list
        with open(chat_path, 'r') as chat_file: 
            chat_list = json.load(chat_file) 

    def display_progress(files, colour): 

        count = len(files)

        for _ in range(0, count):
            while True:
                data = sock.get_from_server() 

                for line in data.splitlines():
                    msg = json.loads(line)
                    current = msg["current"]
                    total = msg["total"]
                    progress(current, total, colour) 

                if current == total:
                    break

    async def display_dialog():
        nonlocal chats
        nonlocal chat_list

        if args.chats: 
            for chat in args.chats: 
                if not chat in chat_list: 
                    print(f"Chat \"{chat}\" not found") 
                    exit(1)

        chat_list = dict(list(chat_list.items())[:args.nchats])
        chats = await display_list(args.chats, chat_list)  # Display chat list


    # Send Message
    async def send_message(sock, chats, messages):
        cmd_arr = [] 
        for message in messages:
            for chat in chats:
                cmd = {"client": client, "type": "send_message", "chat": chat[0], "text": message, "reply_to": chat[1]}
                cmd_arr.append(cmd)
                
        sock.relay_to_server(cmd_arr) 

    # Send Videos
    async def send_videos(sock, chats, videos):
        cmd_arr = [] 
        if not args.album:
            for video in videos:
                if path.exists(video):
                    height, width, duration = meta_extract(video)
                    cmd = {
                        "client": client,
                        "type": "send_video", "chats": chats,
                        "video": path.abspath(video), "caption": args.caption[0], 
                        "height": height, "width": width, "duration": duration,
                        "quiet": args.quiet,
                        "album": "no"
                    }
                    cmd_arr.append(cmd)
                else:
                    print(f"{video} doesnt exist")
                    return 1
        else:
            video_paths = [ path.abspath(video) for video in videos ]  # Send videos as album
            cmd = {
                "client": client,
                "type": "send_video", "chats": chats,
                "video": video_paths, "caption": args.caption[0], 
                "quiet": args.quiet,
                "album": "yes"
            }
            cmd_arr.append(cmd)

        sock.relay_to_server(cmd_arr) 
        if not args.quiet:
            display_progress(videos, args.progress_colour) 

    # Send Images
    async def send_images(sock, chats, images):
        cmd_arr = [] 
        if not args.album:
            for image in images:
                if path.exists(image):
                    cmd = {
                        "client": client,
                        "type": "send_image", "chats": chats, 
                        "image": path.abspath(image), "caption": args.caption[0], 
                        "quiet": args.quiet, "album": "no",
                    }

                    cmd_arr.append(cmd)
                else:
                    print("{} doesnt exist".format(image))
                    return 1
        else:                                                           
            image_paths = [ path.abspath(image) for image in images ]  # Send images as album
            cmd = {
                "client": client,
                "type": "send_image", "chats": chats, 
                "image": image_paths, "caption": args.caption[0], 
                "quiet": args.quiet, "album": "yes",
            }
            cmd_arr.append(cmd)

        sock.relay_to_server(cmd_arr) 
        if not args.quiet:
            display_progress(images, args.progress_colour) 

    # Send files
    async def send_files(sock, chats, files):
        cmd_arr = []
        if not args.album:
            for file in files:
                if path.exists(file):
                    cmd = {
                        "client": client,
                        "type": "send_file", "chats": chats, 
                        "file": path.abspath(file), "caption": args.caption[0], 
                        "quiet": args.quiet, 
                        "album": "no"
                    }
                    cmd_arr.append(cmd)
                else:
                    print("{} doesnt exist".format(file))
                    return 1

        else:
            files_album = [ path.abspath(file) for file in files ]  # Send files as album

            if files_album:
                cmd = {
                    "client": client,
                    "type": "send_file", "chats": chats, 
                    "file": files_album, "caption": args.caption[0], 
                    "quiet": args.quiet,
                    "album": "yes"
                }
                cmd_arr.append(cmd)

        sock.relay_to_server(cmd_arr) 
        if not args.quiet:
            display_progress(files, args.progress_colour) 

    async def get_bots(sock): 

        cmd = [{"client": "user", "type": "get_bots"}]
        sock.relay_to_server(cmd) 
        response = sock.get_from_server() 

        bot_list = json.loads(response)

        for bot in bot_list.values(): 
            print(bot) 

    async def list_messages(sock, channel_name, limit):
        cmd = [{"client": "user", "type": "list_messages", "channel": channel_name, "limit": limit}]
        sock.relay_to_server(cmd)
        response = sock.get_from_server()

        messages = json.loads(response)

        if "error" in messages:
            print(messages["error"])
            return

        #console = Console()
        #message_counter = 0
        for msg in messages:
            #message_counter = message_counter + 1
            #(sender, text), = msg.items()
            #text = str(text or "").replace('\n', ' ').replace('\r', ' ')
            sender = msg["sender"]
            text = msg["text"].replace(chr(10), ' ').replace(chr(13), ' ') if msg["text"] else ""
            msg_id = msg["id"]
            print(f" {msg_id} {sender}: {text}")

    async def list_channels(sock):
        cmd = [{"client": "user", "type": "list_channels"}]
        sock.relay_to_server(cmd)
        response = sock.get_from_server()

        channel_list = json.loads(response)

        for name in channel_list:
            print(name)


    async def download_attachment(sock, msg_id, channel_name, output_dir):
        abs_output = path.abspath(output_dir)
        print(f"Downloading attachment #{msg_id} from '{channel_name}' to {abs_output}...")
        cmd = [{"client": "user", "type": "download_attachment", "channel": channel_name, "msg_id": int(msg_id), "output_dir": abs_output}]
        sock.relay_to_server(cmd)
        response = sock.get_from_server()

        result = json.loads(response)

        if "error" in result:
            print(result["error"])
            return

        print(f"Downloaded: {result['path']}")


    async def unread_messages(sock): 
        cmd = [{
            "client": client, 
            "chats": chats, 
            "type": "unread_messages"
        }] 

        sock.relay_to_server(cmd) 
        response = sock.get_from_server() 

        messages = json.loads(response)

        console = Console()
        keys = list(name for _ , dialog in messages.items() for message in dialog for name in message.keys())
        senders = list(set(keys))

        COLORS = ["cyan", "magenta", "green", "yellow", "blue"]
        color_map = {name: COLORS[i % len(COLORS)] for i, name in enumerate(senders)}

        for chat, dialog in messages.items(): 
            if len(dialog) == 0:  
                console.print(f"[green]{chat}[/green] - No unread messages")
                continue

            console.print(f"──── [green]{chat}[/green] ─────")
            for message in dialog[::-1]: 
                (name, text), = message.items()
                console.print(
                  Panel(text, title=name, title_align="left", expand=False, style=color_map[name])
                )

            print("")

    chat_path = path.join(path.dirname(path.expanduser(CONFIG_DIR)), "chats.json")
    chats = []
    chat_list = {}

    if path.exists(chat_path) and not args.refresh: 
        await load_chats() 
    else: 
        await reload_chats() 
        print("Refreshed local chat store")
        exit()

    args.caption = args.caption or [None]
    client = args.bot_name or "user"

    if args.message:
        await display_dialog()
        with DarkSendSocket(SOCK_PATH) as sock:
            await send_message(sock, chats, args.message)

    if args.image:
        await display_dialog()
        with DarkSendSocket(SOCK_PATH) as sock:
            await send_images(sock, chats, args.image)

    if args.video:
        await display_dialog()
        with DarkSendSocket(SOCK_PATH) as sock:
            await send_videos(sock, chats, args.video)

    if args.file:
        await display_dialog()
        with DarkSendSocket(SOCK_PATH) as sock:
            await send_files(sock, chats, args.file)

    if args.list_bots: 
        with DarkSendSocket(SOCK_PATH) as sock:
            await get_bots(sock)

    if args.list_channels:
        with DarkSendSocket(SOCK_PATH) as sock:
            await list_channels(sock)

    if args.unread_messages: 
        await display_dialog()
        with DarkSendSocket(SOCK_PATH) as sock:
            await unread_messages(sock)

    if args.list_messages:
        with DarkSendSocket(SOCK_PATH) as sock:
            await list_messages(sock, args.list_messages, args.limit)

    if args.download_attachment:
        msg_id, chat_name = args.download_attachment
        with DarkSendSocket(SOCK_PATH) as sock:
            await download_attachment(sock, msg_id, chat_name, args.download)

async def main():

    parser = ArgumentParser(description='command line telegram client')
    parser.add_argument('message', type=str, help="the message you would like to send", nargs="*")
    parser.add_argument("--start-service", "-ss", "--service-start", "--start-background", "-sb", "--background-start" , "-bs", action="store_true", help="run service in background")
    parser.add_argument('-v', '--video', type=str, nargs="+", help="videos to send")
    parser.add_argument('-i', '--image', type=str, nargs="+", help="images to send")
    parser.add_argument('-f', '--file', type=str, nargs="+", help="files to send")
    parser.add_argument('-n', '--nchats', type=int, nargs="?", default=100, help="no chats to display")
    parser.add_argument('-c', '--chats', type=str, nargs="*", help="name of the chat")
    parser.add_argument('-t', '--caption', type=str, nargs="*", help="caption for file")
    parser.add_argument('-a', '--album', action="store_true", help="send files as albums")
    parser.add_argument('-q', '--quiet', action="store_true", help="suppress progress bar")
    parser.add_argument('-r', '--refresh', action="store_true", help="refresh local chat store")
    parser.add_argument('-p', '--progress-colour', type=str, default="#b4befe", help="progress bar color in hex format (e.g. #RRGGBB)")
    parser.add_argument('--initialize-bot', action="store_true", help="initialize bot account") 
    parser.add_argument('--list-bots', '-lb', action="store_true", help="list bot accounts") 
    parser.add_argument('-b', '--bot-name', type=str, nargs="?", help="use bot account instead of user") 
    parser.add_argument('--unread-messages', action="store_true", help="show unread messages from chat")
    parser.add_argument('--list-channels', '--list-conversations', '-lc', action="store_true", help="list all channels and conversations")
    parser.add_argument('--list-messages', '-lm', type=str, nargs="?", help="list all messages from a channel/conversation")
    parser.add_argument('--limit', '-l', type=int, default=DEFAULT_LIMIT, help="limit number of messages to fetch")
    parser.add_argument('--download-attachment', '--download-message', '-da', '-dm' , nargs=2, metavar=('MSG_NUM', 'CHAT_NAME'), help="download attachment from a message")
    parser.add_argument('--download', '-d', '--download-directory', '-dd', '--download-folder', '-df', '--output', '--output-directory', '--output-folder', '-o', '-od', '-of', type=str, default='.', help="directory to save downloaded files")
    parser.add_argument("--generate-session", "-gs", "--generate-session-string", "-gss", action="store_true", help="generate session string from existing configuration"  )

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        exit()

    if not path.exists(path.join(path.expanduser(CONFIG_DIR) + "cligram.conf")):
        import cligram.config as config
        await config.generate_userconf()

    if args.initialize_bot: 
        import cligram.config as config
        await config.generate_botconf()

    if args.generate_session:
        import cligram.config as config
        await config.generate_session()
        exit()

    if args.start_service:
        subprocess.Popen(
            [sys.executable, "-m", "cligram.daemon"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True
        )
        print("Service started in background")
        sys.exit(0)
    else:
        try:
            await cli(args)
        except (ConnectionRefusedError, FileNotFoundError) as e: 
            print(f"Caught error {e}") 
            print("Start the process in background using --start-service to initialize socket") 

def entrypoint():
    asyncio.run(main())

if __name__ == "__main__":
    entrypoint() 
