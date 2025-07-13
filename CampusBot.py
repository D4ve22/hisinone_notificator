#!/usr/bin/python3

import feedparser
import telegram
import asyncio
import json
import os
import pytz
from datetime import datetime
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv()

# Telegram Bot Token und Chat-ID konfigurieren
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
RSS_FEED_URL = os.getenv("RSS_FEED_URL")

bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

data_path = os.path.join(BASE_DIR, "data.json")
dataFile = open(data_path, "r+")
data = json.load(dataFile)
dataFile.close()

log_path = os.path.join(BASE_DIR, "log.txt")
logFileSize = os.stat(log_path).st_size
data["log_file_size"] = logFileSize
if logFileSize > 536870912:
    logFile = open(log_path, "w")
else:
    logFile = open(log_path, "a")
logText = ""

last_entry_title = data['last_entry_title']


def get_latest_entry(feed_url):
    feed = feedparser.parse(feed_url)
    if feed.entries:
        latest_entry = feed.entries[0]
        return latest_entry
    return None


def getTime():
    now = datetime.now()
    current_time = now.strftime("%d.%m.%Y %H:%M:%S")
    return current_time

def gmt_to_berlin(gmt_string):
    input_format = "%a, %d %b %Y %H:%M:%S %Z"
    gmt_time = datetime.strptime(gmt_string, input_format)
    gmt_time = gmt_time.replace(tzinfo=pytz.timezone('GMT'))
    berlin_tz = pytz.timezone('Europe/Berlin')
    berlin_time = gmt_time.astimezone(berlin_tz)
    output_format = " %d.%m.%Y %H:%M:%S"
    berlin_time_string = berlin_time.strftime(output_format)
    return berlin_time_string

def getPrefix():
    prefix = "[" + getTime() + "] "
    return prefix


async def send_telegram_message(message):
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


async def main():
    global last_entry_title
    logText = ""
    logText += getPrefix() + "Rufe neusten Eintrag ab..." + "\n"
    latest_entry = get_latest_entry(RSS_FEED_URL)
    # print(latest_entry)
    if latest_entry:
        entry_title = latest_entry.title
        if last_entry_title is None or entry_title != last_entry_title:
            logText += getPrefix() + "Eintrag abgerufen - Änderung vorhanden:" + "\n"
            data["last_entry_title"] = entry_title
            message = f"{latest_entry.title}\nVeröffentlicht: " + gmt_to_berlin(str(latest_entry.published)) + "\nLink: " + str(latest_entry.link)
            logText += getPrefix() + message + "\n"
            await send_telegram_message(message)

        else:
            logText += getPrefix() + "Eintrag abgerufen - Keine Änderung" + "\n"
    else:
        logText += getPrefix() + "Abrufen des neusten Eintrages nicht möglich." + "\n"

    logText += getPrefix() + "--------------------------------------" + "\n"
    data["last_execution"] = getTime()
    json_string = json.dumps(data)

    dataFile = open(data_path, "w")
    dataFile.write(json_string)
    logFile.write(logText)

    dataFile.close()
    logFile.close()


if __name__ == "__main__":
    asyncio.run(main())
