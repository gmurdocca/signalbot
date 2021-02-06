#!/usr/bin/env python3

import os
import sys
import json
import subprocess
import logging
import time
from collections import defaultdict
from pathlib import Path

import cleverbotfree.cbfree
from better_profanity import profanity
import dotenv

CONTROL_PREFIXES = ["!signalbot ", "!sb ", "!dojobot ", "!db "]

cb = cleverbotfree.cbfree.Cleverbot()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

dotenv.load_dotenv(dotenv_path=Path('.') / '.env')
SIGNAL_USER = os.getenv("SIGNAL_USER")


def send_message(message, user, group):
    message = message.replace("'", "")
    logger.info(f"sending: {group}: {message}")
    cmd = f'''signal-cli -u {user} send -m '{message}' -g "{group}"'''
    subprocess.call(cmd, shell=True)
    

def parse_commands(messages):
    commands = defaultdict(list)
    for raw_message in messages.split("\n"):
        if raw_message.strip():
            try:
                raw_message = json.loads(raw_message)
            except json.decoder.JSONDecodeError as e:
                logger.warning(f"Malformed message (skipping): {raw_message}")
                continue
            message = raw_message.get("envelope", {}).get("dataMessage", {}).get("message") or ""
            message = message.strip()
            group_id = raw_message.get("envelope", {}).get("dataMessage", {}).get("groupInfo", {}).get("groupId") or ""
            for CONTROL_PREFIX in CONTROL_PREFIXES:
                if message.startswith(CONTROL_PREFIX):
                    command = message.split(' ', 1)[1]
                    commands[group_id].append(command)
    if  commands:
        logger.info(f"received commands: {commands}")
    return commands


def action_commands(commands):
    for group_id in commands:
        for command in commands[group_id]:
            logger.info(f"processing command: {command}")
            if profanity.contains_profanity(command):
                send_message("Don't be rude or I'll eat all your crypto.", SIGNAL_USER, group_id)
            elif command.startswith("getprice") or command.startswith("gp"):
                sep = command.startswith("gp") and "gp" or "getprice"
                symbol = command.split(sep)[1].strip()
                if not 3 <= len(symbol) <= 4  or not symbol.isalpha():
                    send_message("Symbol must contain alpha characters only and be 3 or 4 characters in length.", SIGNAL_USER, group_id)
                    continue
                logger.info(f"********* fetching price for symbol: {symbol}")
                p = subprocess.Popen(f"""coinmon -f {symbol} | tail -n2 | head -n1 | awk '{{print $6}}'""", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
                p.wait()
                result = p.stdout.read().decode('utf-8').strip()
                send_message(f"1 {symbol} = USD ${result}", SIGNAL_USER, group_id)
            elif command.lower() == "help":
                send_message("get a crypto price: !sb gp <symbol>\nchat with me: !sb chat <some message>", SIGNAL_USER, group_id)
            elif command.lower().startswith("chat"):
                text = command[4:].strip()
                response = cb.single_exchange(text)
                send_message(response, SIGNAL_USER, group_id)
            else:
                send_message(f"unrecognised command: {command}", SIGNAL_USER, group_id)


def get_messages():
    cmd = f"signal-cli -u {SIGNAL_USER} --output=json receive"
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

