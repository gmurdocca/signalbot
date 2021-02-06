# SignalBot: A basic Signal bot

Bot Commands:

Chat to the bot in Signal using the below commands:

Get current price in USD for a crypto symbol: `!sb getprice <symbol>`

Chat with an AI (cleverbot): `!sb chat <some message>`

# Installation: 

## install deps:

Note: These are best wrapped in a docker image. Manual install process is:

Install npm deps:
```
npm -g install coinmon
```

Install Python deps:
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

4. set a profile
```
signal-cli -u <phone_number> updateProfile --name <name_of_bot_in_Signal>
```

5. Join a signal Group. Get group id from Signal app in group settings.
```
signal-cli -u <phone_number> joinGroup --uri 'https://signal.group/<group_id>'
```
6. Send a test group message:
```
signal-cli -u <phone_number> send -m "hello world" -g <group_id>
```
7. Update signalbot.py and set USER and GROUP variables to <phone_number> and <group_id> respectively.
8. Start the bot:
```
python3 signalbot.py
```
