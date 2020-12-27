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
    
    if message.content.startswith('!pbdr'): #書き方汚いので整える
        try:
            evId = message.content.split()[1]
        except IndexError:
            embed = discord.Embed(title='エラー', description='イベントIDを入力してください．', color=discord.Colour.red())
            embed.set_image(url=errorimg_url)
            await message.channel.send(embed=embed)
            return
        
        url = 'https://api.matsurihi.me/mltd/v1/events/'

        response = requests.get(url)
        Data = response.json()

        lastevId = Data[-1]['id']

        if not 1 <= int(evId) <= lastevId:
            embed = discord.Embed(title='エラー', description='不正なイベントIDです．', color=discord.Colour.red())
            embed.set_image(url=errorimg_url)
            await message.channel.send(embed=embed)
            return
            
        pastEventData_url = 'https://api.matsurihi.me/mltd/v1/events/' + evId

        response = requests.get(pastEventData_url)
        pastEventData = response.json()

        try:
            evName = pastEventData['name']
            evType = pastEventData['type']
            beginTime = datetime.datetime.strptime(pastEventData['schedule']['beginDate'],'%Y-%m-%dT%H:%M:%S+09:00') #イベント開始日時
            endTime = datetime.datetime.strptime(pastEventData['schedule']['endDate'],'%Y-%m-%dT%H:%M:%S+09:00') #イベント終了日時
        except KeyError:
            embed = discord.Embed(title='エラー', description='イベントデータが見つかりませんでした．', color=discord.Colour.red())
            embed.set_image(url=errorimg_url)
            await message.channel.send(embed=embed)
            return

        # 表示するイベントデータが現在開催中のものか判定

        try: # TypeError
            if beginTime < datetime.datetime.now < endTime:
                embed = discord.Embed(title='エラー', description='現在開催中のイベントです．', color=discord.Colour.red())
                embed.set_image(url=errorimg_url)
                await message.channel.send(embed=embed)
                return
            elif datetime.datetime.now <= beginTime:
                embed = discord.Embed(title='エラー', description='未開催のイベントです．', color=discord.Colour.red())
                embed.set_image(url=errorimg_url)
                await message.channel.send(embed=embed)
                return
        except TypeError:
            pass

        try:
            boostTime = datetime.datetime.strptime(pastEventData['schedule']['boostBeginDate'],'%Y-%m-%dT%H:%M:%S+09:00') #イベント開始日時
        except KeyError:
            boostTime = None

        eventTime = endTime + datetime.timedelta(seconds=1) - beginTime
        eventTime_hours = int(eventTime.total_seconds() / 3600)

        title = evName
        msg = ''

        if evType in evType_to_Colour: # ランキング形式イベ
            if evType == 5: # 周年イベ
                try:
                    idolName = message.content.split()[2]
                    idolId = getKeyFromValue(idolId_to_idolName, idolName)
                    if idolId is None:
                        if idolName == '総合':
                            idolId = 0
                        else:
                            embed = discord.Embed(title='エラー', description='不正なアイドル名です．', color=discord.Colour.red())
                            embed.set_image(url=errorimg_url)
                            await message.channel.send(embed=embed)
                            return
                except IndexError:
                    embed = discord.Embed(title='エラー', description='アイドル名が入力されていません．\n周年イベントの場合はイベントIDの次にアイドル名を入力してください．\n総合ランキングを表示したい場合はアイドル名を「総合」としてください．', color=discord.Colour.red())
                    embed.set_image(url=errorimg_url)
                    await message.channel.send(embed=embed)
                    return
                if idolId == 0:
                    try:
                        printRanks = '/rankings/logs/eventPoint/' + str(message.content.split()[3])
                    except IndexError:
                        printRanks = '/rankings/logs/eventPoint/1-3,100,2500,5000,10000,25000,100000'
                else:
                    try:
                        printRanks = '/rankings/logs/idolPoint/' + str(idolId) + '/' + str(message.content.split()[3])
                    except IndexError:
                        printRanks = '/rankings/logs/idolPoint/' + str(idolId) + '/1-3,10,100,1000'
                title += ' {} ランキング'.format(idolName)
            else:
                try:
                    printRanks = '/rankings/logs/eventPoint/' + str(message.content.split()[2])
                except IndexError:
                    printRanks = '/rankings/logs/eventPoint/1-3,100,2500,5000,10000,25000,100000'           
            
            pastBdrData_url = pastEventData_url + printRanks

            print(pastBdrData_url)

            response = requests.get(pastBdrData_url)
            bdData = response.json()

            #順位表示しすぎかチェック
            if type(bdData) == dict:
                if bdData['error']['message'] == 'path parameter `ranks` contains invalid character(s)':
                    errormsg = '不正な順位が入力されています．'
                elif bdData['error']['message'] == 'too big range for path parameter `ranks`':
                    errormsg = '表示する順位の数が多すぎます．'
                else:
                    errormsg = '不明なエラーです．'
                embed = discord.Embed(title='エラー', description=errormsg, color=discord.Colour.red())
                embed.set_image(url=errorimg_url)
                await message.channel.send(embed=embed)
                return

            msg += '開催期間：{} ～ {} ({}h)\n'.format(beginTime.strftime('%m/%d %H:%M'), endTime.strftime('%m/%d %H:%M'), eventTime_hours) #開催期間をmsgに追加
            if boostTime is None:
                msg += '折り返し：なし\n'
            else:
                msg += '折り返し：{}\n'.format(boostTime.strftime('%m/%d %H:%M')) #折り返し日時をmsgに追加
            msg += '\n'
            msg += '最終結果'

            #msgにボーダー表を代入
            msg += '```      #:     score\n------------------\n'  
            for x in bdData:
                msg += '{:>7,d}: {:>9,d}\n'.format(int(x['rank']), int(x['data'][-1]['score']))
            msg += '```\n'
        else: # ランキング形式イベではない
            evType = 0
            msg += 'このイベントはランキング形式ではありません．\n\n'

        msg += '配信元：[matsurihi.me](https://www.matsurihi.me/)'

        #Fantasiaへのリンク
        fantasia_url = 'https://mltd.matsurihi.me/events/' + evId
        #サムネイルのリンク
        image_url = 'https://storage.matsurihi.me/mltd/event_bg/{:0>4}.png'.format(int(evId))

        embed = discord.Embed(title=title, url=fantasia_url, description=msg, color=evType_to_Colour[evType])
        embed.set_image(url=image_url)
        await message.channel.send(embed=embed)


client.run(token)
