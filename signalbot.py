#!/usr/bin/env python3

import os
import sys
import json
import subprocess
import logging
import time
from collections import defaultdict
from pathlib import Path
import textwrap

import cleverbotfree.cbfree
from better_profanity import profanity
import dotenv

CONTROL_PREFIXES = ["!signalbot", "!sb", "!dojobot", "!db"]
LOGLEVEL = logging.INFO
SLEEP = 2
RECEIVE_TIMEOUT = 2
UPDATE_ACCOUNT_INTERVAL = 30

cb = cleverbotfree.cbfree.Cleverbot()

logger = logging.getLogger()
logger.setLevel(LOGLEVEL)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(LOGLEVEL)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

dotenv.load_dotenv(dotenv_path=Path('.') / '.env')
SIGNAL_USER = os.getenv("SIGNAL_USER")
HELP_TEXT = """
        Commands I understand:\n
        Get a crypto price:    !sb gp <symbol>
        Chat with me:    !sb <some message>

        See coincap.io for supported symbols
        """



def send_message(message, from_user, target):
    message = message.replace("'", r"'\''")
    logger.info(f"Sending message to: {target}: {message}")
    if target.startswith("+"):
        # direct chat
        cmd = f'''signal-cli -u {from_user} send -m '{message}' {target}'''
    else:
        # group chat
        cmd = f'''signal-cli -u {from_user} send -m '{message}' -g "{target}"'''
    logger.debug(f"running command: {cmd}")
    subprocess.Popen(cmd, shell=True, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).wait()
    

def strip_control_prefix(message):
    prefix = has_control_prefix(message)
    if prefix:
        message = message.split(prefix, 1)[1].strip()
    return message


def has_control_prefix(message):
    for CONTROL_PREFIX in CONTROL_PREFIXES:
        if message.startswith(f"{CONTROL_PREFIX} "):
            return CONTROL_PREFIX
    return False


def parse_commands(messages):
    commands = defaultdict(list)
    for raw_message in messages.split("\n"):
        if raw_message.strip():
            try:
                raw_message = json.loads(raw_message)
                logger.debug(f"raw_message: {raw_message}")
            except json.decoder.JSONDecodeError as e:
                logger.warning(f"Malformed message (skipping): {raw_message}")
                continue
            source = raw_message.get("envelope", {}).get("source")
            message = raw_message.get("envelope", {}).get("dataMessage", {}).get("message") or ""
            message = message.strip()
            logger.debug(f"source: {source} ; message: {message}")
            if source == SIGNAL_USER or not message:
                # ignore our own direct chat messages or empty messages
                logger.debug(f"Ignoring message from {source}: {message}")
                continue
            group_id = raw_message.get("envelope", {}).get("dataMessage", {}).get("groupInfo", {}).get("groupId") or ""
            if group_id:
                # this was a group message
                logger.debug("got a group message")
                source = group_id
                if has_control_prefix(message):
                    commands[source].append(strip_control_prefix(message))
            else:
                # this was a direct message
                logger.debug("got a direct message")
                prefix = has_control_prefix(message)
                if prefix:
                    send_message(f"BTW, you can drop the {prefix} when direct messaging me.", SIGNAL_USER, source)
                commands[source].append(strip_control_prefix(message))
    if  commands:
        logger.info(f"received commands: {commands}")
    return commands


def action_commands(commands):
    for target in commands:
        for command in commands[target]:
            message = command
            command = command.lower()
            logger.info(f"processing command: {command}")
            if profanity.contains_profanity(command):
                send_message("Don't be rude or I'll eat all your crypto.", SIGNAL_USER, target)
            elif command == "help":
                send_message(textwrap.dedent(HELP_TEXT), SIGNAL_USER, target)
            elif command.startswith("getprice") or command.startswith("gp"):
                sep = command.startswith("gp") and "gp" or "getprice"
                symbol = command.split(sep)[1].strip()
                if not 3 <= len(symbol) <= 4  or not symbol.isalpha():
                    send_message("Symbol must contain alpha characters only and be 3 or 4 characters in length.", SIGNAL_USER, target)
                    continue
                logger.debug(f"Fetching price for symbol: {symbol}")
                p = subprocess.Popen("""coinmon -f %s | tail -n2 | head -n1 | sed 's/\x1B\[[0-9;]\{1,\}[A-Za-z]//g'  | awk '{print $2, $4, $6, $8, $10, $12, $14}'""" % symbol, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
                p.wait()
                result = p.stdout.read().decode('utf-8').strip()
                if result:
                    rank, coin, price, change24h, marketcap, supply, volume24h = result.split()
                    message = f"Coin: {coin}\nRank: {rank}\nPrice: {price}\nChange 24h: {change24h}\nMarket Cap: {marketcap}\nSupply: {supply}\nVolume 24h: {volume24h}"
                else:
                    message = f"I've got no info about crypto symbol '{symbol}'. See coincap.io for a list of supported symbols."
                send_message(message, SIGNAL_USER, target)
            else:
                response = cb.single_exchange(message)
                send_message(response, SIGNAL_USER, target)


def get_messages():
    cmd = f"signal-cli -u {SIGNAL_USER} --output=json receive --timeout {RECEIVE_TIMEOUT} --ignore-attachments"
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
    p.wait()
    result = p.stdout.read().decode('utf-8')
    return result


if __name__ == "__main__":
    # main loop
    logger.info("Starting to waiting for messages...")
    update_account_timer = time.time()
    while True:
        input_data = get_messages()
        commands = parse_commands(input_data)
        if commands:
            action_commands(commands)
        time.sleep(SLEEP)
        # fix issue with direct messages
        if time.time() - update_account_timer > UPDATE_ACCOUNT_INTERVAL:
            logger.debug("Updating signal account")
            subprocess.Popen(f"signal-cli -u {SIGNAL_USER} updateAccount", shell=True, close_fds=True).wait()
            update_account_timer = time.time()
