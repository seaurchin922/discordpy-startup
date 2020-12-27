import discord
import json
import requests
import datetime
from discord.ext import tasks
from pathlib import Path
from discord.ext import commands
import os
import traceback

client = discord.Client()

token = os.environ['DISCORD_BOT_TOKEN']

@client.event
async def on_ready():
    # 状態を '☆ピコピコプラネット☆を視聴中' にする
    activity = discord.Activity(name='☆ピコピコプラネット☆', type=discord.ActivityType.watching)
    await client.change_presence(activity=activity)
    #update_border.start()

@client.event
async def on_message(message):
    # メッセージ送信者がBotだった場合は無視する
    if message.author.bot:
        return
    # 「/neko」と発言したら「にゃーん」が返る処理
    if message.content == '/neko':
        await message.channel.send('にゃーん')


client.run(token)
