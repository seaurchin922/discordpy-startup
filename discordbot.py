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

shiuntench = client.get_channel(776432703964708865) 
bdrbotch = client.get_channel(786021632522846269) # ボーダーbotチャンネルのID
botlogch = client.get_channel(790298428957261855)

errorimg_url = 'https://millionlive.info/?plugin=attach&refer=%E5%A4%A7%E7%A5%9E%E7%92%B0&openfile=05.png'

idolId_to_idolName = {
  "1": "天海春香",
  "2": "如月千早",
  "3": "星井美希",
  "4": "萩原雪歩",
  "5": "高槻やよい",
  "6": "菊地真",
  "7": "水瀬伊織",
  "8": "四条貴音",
  "9": "秋月律子",
  "10": "三浦あずさ",
  "11": "双海亜美",
  "12": "双海真美",
  "13": "我那覇響",
  "14": "春日未来",
  "15": "最上静香",
  "16": "伊吹翼",
  "17": "田中琴葉",
  "18": "島原エレナ",
  "19": "佐竹美奈子",
  "20": "所恵美",
  "21": "徳川まつり",
  "22": "箱崎星梨花",
  "23": "野々原茜",
  "24": "望月杏奈",
  "25": "ロコ",
  "26": "七尾百合子",
  "27": "高山紗代子",
  "28": "松田亜利沙",
  "29": "高坂海美",
  "30": "中谷育",
  "31": "天空橋朋花",
  "32": "エミリー",
  "33": "北沢志保",
  "34": "舞浜歩",
  "35": "木下ひなた",
  "36": "矢吹可奈",
  "37": "横山奈緒",
  "38": "二階堂千鶴",
  "39": "馬場このみ",
  "40": "大神環",
  "41": "豊川風花",
  "42": "宮尾美也",
  "43": "福田のり子",
  "44": "真壁瑞希",
  "45": "篠宮可憐",
  "46": "百瀬莉緒",
  "47": "永吉昴",
  "48": "北上麗花",
  "49": "周防桃子",
  "50": "ジュリア",
  "51": "白石紬",
  "52": "桜守歌織"
}

evType_to_Colour = {
    0:discord.Colour.default(),         # その他のイベント
    3:discord.Colour.teal(),            # プラチナスターシアター
    4:discord.Colour.blue(),            # プラチナスターツアー
    5:discord.Colour.gold(),            # 周年記念イベント
    10:discord.Colour.dark_purple(),    # ツインステージ
    11:discord.Colour.dark_green(),     # プラチナスターチューン
    12:discord.Colour.purple(),         # ツインステージ 2
    13:discord.Colour.dark_purple()     # プラチナスターテール
}

def getKeyFromValue(d, val):
    keys = [k for k, v in d.items() if v == val]
    if keys:
        return keys[0]
    return None

def maxDgtOfList(l):
    # lの要素をすべてstrにする
    l_str = [str(n) for n in l]
    return max(map(len, l_str))

@tasks.loop(seconds=60)
async def update_border(): # 自動ボーダー送信機能
    nowTime = datetime.datetime.now() # 現在時刻の取得
    # !!! ↑ debug ↓ !!!
    #nowTime = datetime.datetime(2020, 10, 3, 20, 36) # Persona Voice開始30分後
    # イベ開始一時間後から30分起きの時刻を設定する
    await botlogch.send('looping on ' + nowTime.strftime('%m/%d %H:%M:%S')) # ループ中であることを端末に出力


@client.event
async def on_ready():
    # 状態を '☆ピコピコプラネット☆を視聴中' にする
    activity = discord.Activity(name='☆ピコピコプラネット☆', type=discord.ActivityType.watching)
    await client.change_presence(activity=activity)
    update_border.start()

@client.event
async def on_message(message):
    # メッセージ送信者がBotだった場合は無視する
    if message.author.bot:
        return
    
    # 「/neko」と発言したら「にゃーん」が返る処理
    if message.content == '/neko':
        await message.channel.send('にゃ～ん')
    
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

            await botlogch.send(pastBdrData_url)

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
