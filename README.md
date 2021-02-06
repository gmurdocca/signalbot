# SignalBot: A basic Signal bot

A crude and simple Signal bot that wraps `signal-cli` for integreation with Signal private messenger, `coinmon` for retrieving latest crypto prices and CleverBot API for chatting to an AI.

## Bot Commands:

Chat to the bot in Signal using the below commands:

- Get current price in USD for a crypto symbol: `!sb getprice <symbol>`
- Chat with an AI (CleverBot): `!sb chat <some message>`

# Installation: 

## Install deps:

Note: These are best wrapped in a Docker image. Manual install process is:

Install npm deps:
```
npm -g install coinmon
```

Install Python deps (consider using a virtualenv if not Docker):
```
pip3 install requirements.txt
```

Install signal-cli: https://github.com/AsamK/signal-cli

Install geckodriver: https://github.com/mozilla/geckodriver

## Configure signal-cli and start SignalBot

1. Register the bot with Signal. 
To  get the value for <captcha_token>, go to https://signalcaptchas.org/registration/generate.html then use your browser's developer tools to check for a redirect starting with signalcaptcha://. Everything after signalcaptcha:// is the captcha token.

The <phone_number> must be in international format and must include the country calling code. Hence it should start with a "+" sign. It also should be a unique phone number, eg a land line, etc.

```
signal-cli -u <phone_number> register --voice --captcha <captcha_token>
```

2. Wait for a phone call and note the PIN that is given. Verify using command.
```
signal-cli -u <phone_number> verify <PIN>
```
Note you can specify an optional `--pin <PIN>` if there is a Signal security pin associated with <phone_number>

3. Send a test message
```
signal-cli -u <phone_number> send -m "test message" <phone_number>
```

4. Set a profile
<name_of_bot_in_Signal> will be the bot's name in the group chat in Signal.

```
signal-cli -u <phone_number> updateProfile --name <name_of_bot_in_Signal>
```

5. Join one or more signal Groups. Get group id from Signal app in group settings.
```
signal-cli -u <phone_number> joinGroup --uri 'https://signal.group/<group_id>'
```
6. Send a test group message:
```
signal-cli -u <phone_number> send -m "hello world" -g <group_id>
```
7. Create a file named `.env` in the root of this project and set its contents to:
```
SIGNAL_USER=<phone_number>
```
8. Start the bot:
```
python3 signalbot.py
```
