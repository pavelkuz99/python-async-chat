# Messenger
Simple chat in Python with asynchronous run server and client.

## Installation
Server requires [passlib](https://pypi.org/project/passlib/) library for proper password encryption and decryption, use pip to install, or from requirements.txt

```bash
pip install passlib
```
```bash
pip install -r requirements.txt
```

## Usage
Both server and client scripts supposed to be run from separete terminals 
with the following positional arguments:
* hostname
* port

Example:
```bash
python3 server.py localhost 1066
```
```bash
python3 client.py localhost 1066
```

Given server is running, when launched the client, it will prompt to choose authentication operation. User can whether log in or register(client automatically logs in after successful registration). After succesful authentication user can start chatting with others.

Every message is broadcast by default. To send a message to one user, specify his name with '@' sign.

Example:
```sh
@username Hey, there!
```


To exit either type 'quit' in prompt or press 'Ctrl-C'.

