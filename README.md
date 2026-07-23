# cligram 

Cligram is a CLI telegram client written in python. It sends messages and files through your personal telegram account using a daemon that maintains a connection in the background, much like the stock telegram desktop app.

## Dependencies 

``` shell 
pip3 install . 
``` 

## Installation 

Install directly from PyPi
```shell 
pip3 install cligram 
```


Or 

Clone the repository to a local directory
``` shell
git clone https://github.com/mindhuntr/cligram 
```

For system wide installation 
```shell
cd cligram
pip3 install .
```

For user specific installation 
```shell
cd cligram
pip3 install --user .
```

## Configuration

cligram requires a daemon process running in the background. The daemon can be initialized using a parameter 

```shell
cligram --start-service
```

Once the config file is generated, it is more robust to create a systemd-unit file that automatically executes the daemon once the system is up 

```

[Unit]
Description=Daemon for cligram
After=network.target

[Service]
Type=simple
User=YOUR_USER
ExecStart=/usr/bin/python3 -m cligram.daemon
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Create a file called cligram.service with the above content and place it in "/etc/systemd/system". Replace "YOUR_USER" with your username and execute the following commands

```shell
sudo systemctl daemon-reload 
sudo systemctl enable cligram.service
sudo systemctl start cligram.service
```


## Usage 

Display help: 
``` shell 
cligram --help 

``` 
To send a message:
``` shell
cligram Hello!
``` 


To send an image: 
``` shell 
cligram -i /path/to/image 

``` 
To send files as album: 
``` shell 
cligram -a -f /path/to/file /path/to/file 
``` 


To send a video directly without selecting from the chats list
``` shell 
cligram -v /path/to/file -c "Alienists" 
```
You can also send messages or files to topics within a group 

To get a list of channels/conversations
```shell
cligram --list-channels
```

To get a list of messages (most recent at the top) from a conversation/channel

```shell
cligram --list-messages "channel name"
```

To limit the number of messages, you can use the --limit flag, such as:

```shell
cligram --list-messages "channel name" --limit 200
```

In the above scenario the most recent 200 messages are going to be displayed (with the most recent at the top).

To download an attachment, knowing the channel name and message id:

```shell
cligram --download-attachment $messageId "channel name" --download-folder "$HOME/Downloads"
```



## Note 

cligram now supports bot logins from v1.2.0. It leverages the user client to fetch chats and then the bot account to send messages and files. Users can initialize several bot accounts and use them by names they designate. 

```shell 
cligram -b FelineBot -f /path/to/file 
```
