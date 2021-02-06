#!/usr/bin/env python3

import sys
import json
import subprocess
import logging
import time

import cleverbotfree.cbfree
from better_profanity import profanity

CONTROL_PREFIXES = ["!signalbot ", "!sb "]
USER = "XXX"
GROUP = "XXX"

cb = cleverbotfree.cbfree.Cleverbot()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_message(message, user=USER, group=GROUP):
    message = message.replace("'", "")
    logger.info(f"sending: {group}: {message}")
    cmd = f'''signal-cli -u {user} send -m '{message}' -g "{group}"'''
    subprocess.call(cmd, shell=True)
    

def parse_commands(messages):
    commands = []
    for message in messages.split("\n"):
        message = message.strip()
        if message:
            message = json.loads(message)
            data = message.get("envelope", {}).get("dataMessage", {}).get("message") or ""
            data = data.strip()
            for CONTROL_PREFIX in  CONTROL_PREFIXES:
                if data.startswith(CONTROL_PREFIX):
                    commands.append(data.split(' ', 1)[1])
    if commands:
        logger.info(f"received commands: {commands}")
    return commands


def action_commands(commands):
    for command in commands:
        logger.info(f"processing command: {command}")
        if profanity.contains_profanity(command):
            send_message("Don't be rude or I'll eat all your crypto.")
        elif command.startswith("getprice") or command.startswith("gp"):
            sep = command.startswith("gp") and "gp" or "getprice"
            symbol = command.split(sep)[1].strip()
            if not 3 <= len(symbol) <= 4  or not symbol.isalpha():
                send_message("Symbol must contain alpha characters only and be 3 or 4 characters in length.")
                continue
            logger.info(f"********* fetching price for symbol: {symbol}")
            p = subprocess.Popen(f"""coinmon -f {symbol} | tail -n2 | head -n1 | awk '{{print $6}}'""", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
            p.wait()
            result = p.stdout.read().decode('utf-8').strip()
            send_message(f"1 {symbol} = USD ${result}")
        elif command.lower() == "help":
            send_message("get a crypto price: !db gp <symbol>\nchat with me: !db chat <some message>")
        elif command.lower().startswith("chat"):
            text = command[4:].strip()
            response = cb.single_exchange(text)
            send_message(response)
        else:
            send_message(f"unrecognised command: {command}")


def get_messages():
    cmd = f"signal-cli -u {USER} --output=json receive"
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
    p.wait()
    result = p.stdout.read().decode('utf-8')
    return result


if __name__ == "__main__":
    while True:
        sys.stdout.write(".")
        sys.stdout.flush()
        input_data = get_messages()
        commands = parse_commands(input_data)
        if commands:
            action_commands(commands)
        time.sleep(1)

