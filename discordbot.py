#データ提供元:matsurihi.me様

import discord
import json
import requests
import datetime
from discord.ext import tasks
from pathlib import Path

token = os.environ['DISCORD_BOT_TOKEN']

client = discord.Client()

evTypeToColor = {3:discord.Colour.teal(), 4:discord.Colour.blue(), 5:discord.Colour.gold(),\
                10:discord.Colour.dark_purple(), 11:discord.Colour.dark_green(), 12:discord.Colour.purple()}


@tasks.loop(seconds=60)
async def update_border(): #自動ボーダー送信機能
    
    shiuntench = client.get_channel(776432703964708865) 
    bdrbotch = client.get_channel(786021632522846269) #ボーダーbotチャンネルのID

    nowTime = datetime.datetime.now() # 現在時刻の取得
    #!!!debug!!!
    #nowTime = datetime.datetime(2020, 10, 3, 16, 00) # Persona Voice開始30分後
    #debug = -5 # = 経過時間[分]/30 - 1
    #!!!debug!!!

    print('looping now on ' + nowTime.strftime('%m/%d %H:%M:%S')) # ループ中であることを端末に出力



    ###   現在開催中のイベント情報の取得   ###
    nowEventData_url = 'https://api.matsurihi.me/mltd/v1/events/?at=' + str(nowTime)

    response = requests.get(nowEventData_url)
    nowEventData = response.json()

    try:
        id = str(nowEventData[0]['id'])
    except IndexError:
        print('イベント未開催') #安定したらコメントアウト
        return #イベント未開催

    evType = nowEventData[0]['type']
    evName = nowEventData[0]['name']

    beginTime = datetime.datetime.strptime(nowEventData[0]['schedule']['beginDate'],'%Y-%m-%dT%H:%M:%S+09:00') #イベント開始日時
    endTime = datetime.datetime.strptime(nowEventData[0]['schedule']['endDate'],'%Y-%m-%dT%H:%M:%S+09:00') #イベント終了日時

    eventTime = endTime - beginTime #開催期間 = 終了時間 - 開始時間



    ###   イベント形式の判別   ###
    if evType != 3 and evType != 4 and evType != 5 and evType != 10 and evType != 11 and evType != 12:
        print('開催中のイベントはランキング形式ではありません') #安定したらコメントアウト
        return #ランキング形式イベントではない



    ###   イベントランキングの集計情報の取得   ###
    updateData_url = 'https://api.matsurihi.me/mltd/v1/events/' + id + '/rankings/summaries/eventPoint'

    response = requests.get(updateData_url)
    updateData = response.json()

    currentUpdateTime = datetime.datetime.strptime(updateData[-1]['updateTime'],'%Y-%m-%dT%H:%M:%S+09:00')
    currentSummaryTime = datetime.datetime.strptime(updateData[-1]['summaryTime'],'%Y-%m-%dT%H:%M:%S+09:00')
    #!!!debug!!!
    #currentUpdateTime = datetime.datetime.strptime(updateData[debug]['updateTime'],'%Y-%m-%dT%H:%M:%S+09:00')
    #currentSummaryTime = datetime.datetime.strptime(updateData[debug]['summaryTime'],'%Y-%m-%dT%H:%M:%S+09:00')
    #!!!debug!!!

    
    elapsedTime = currentSummaryTime - beginTime #経過時間 = 現在時刻 - 開始時間
    remainingTime = endTime - currentSummaryTime #残り時間 = 終了時間 - 現在時刻

    

    ###   取得した集計情報が1分以内のものか(=ボーダー情報が更新されたか)判定   ###
    timediffsec = (nowTime - currentUpdateTime).seconds

    if timediffsec >= 60:
        print('ボーダー情報はまだ更新されていません') #安定したらコメントアウト
        #return #更新されてから一分以内ではない
    else:
        print('ボーダー情報が更新されました')



    ###   ひとつ前と現在のイベントのボーダースコアの取得   ###
    nowBdrData_url = 'https://api.matsurihi.me/mltd/v1/events/' + id + '/rankings/logs/eventPoint/1-20'

    response = requests.get(nowBdrData_url)
    nowBdrData = response.json()

    num = len(nowBdrData) #表示する順位の個数
    beforeScores = [] #前回のスコアのリスト
    borderRank = [] #各ボーダーの順位（基本的に不変）
    nowScores = [] #現時点でのスコアのリスト

    #currentScoresファイルの読み込み
    try:
        beforeBdrData = json.load(open('currentScores/' + id + '.json', 'r'))
    except OSError:
        #"id + '.json'" ファイルを作る
        Path('currentScores/' + id + '.json').touch()
        with open('currentScores/' + id + '.json', 'w') as f:
            json.dump([], f)
        beforeBdrData = json.load(open('currentScores/' + id + '.json', 'r'))

    #リストへの書き込み
    for i in range(num):
        try:
            beforeScores.append(int(beforeBdrData[i]['data'][-1]['score']))
            #!!!debug!!!
            #beforeScores.append(int(beforeBdrData[i]['data'][debug-1]['score']))
            #!!!debug!!!
        except IndexError:
            beforeScores.append(0)
        borderRank.append(int(nowBdrData[i]['rank']))
        nowScores.append(int(nowBdrData[i]['data'][-1]['score']))
        #!!!debug!!!
        #nowScores.append(int(nowBdrData[i]['data'][debug]['score']))
        #!!!debug!!!

    #currentScoresファイルの更新
    with open('currentScores/' + id + '.json', 'w') as f:
        json.dump(nowBdrData, f, indent=2)



    ###   titleにタイトルを代入   ###
    title = '' #タイトル用の空のstr変数
    msg = '' #メッセージ用の空のstr変数

    title += evName + '\n' #開催中のイベントの名前をtitleに追加

    #title += '開催期間: ' + beginTime.strftime('%m/%d %H:%M') + ' ～ ' + endTime.strftime('%m/%d %H:%M') + '\n\n' #開催期間をtitleに追加
    title += currentSummaryTime.strftime('%m/%d %H:%M') + '更新\n' #更新時間をtitleに追加

    elapsedTimeRaito = elapsedTime.total_seconds()/eventTime.total_seconds() #経過時間の割合
    remainingTime_hours =  int(remainingTime.days * 24 + (remainingTime.seconds + 1) / 3600)
    remainingTime_minutes = int((remainingTime.seconds + 1) / 60 + remainingTime.days * 1440 - remainingTime_hours * 60)
    title += '({:.1%}経過 残り{}時間{}分)'.format(elapsedTimeRaito,remainingTime_hours,remainingTime_minutes)
    


    ###   msgにボーダー表を代入   ###
    msg += '` #:     score    -0.5h\n'
    for i in range(num):
        diff = nowScores[i] - beforeScores[i]
        msg += '{:>2,d}: {:>9,d} (+{:>6,d}'.format(borderRank[i],nowScores[i],diff)
        # "{:>2,d}" の2は表示する順位の最大桁数に合わせて変更 (100,000位まで表示するのならば "{:>6,d}" )
        if evType == 3: #シアターならdiffから貯めか消費か判断、プレイ回数を出力
            if diff % 595 == 0 and diff != 0: #貯め
                playtimes = int(diff/595)
                msg += ' =    SV * {:>2}'.format(playtimes)
            elif diff % 2148 == 0 and diff != 0: #消費
                playtimes = int(diff/2148)
                msg += ' = EVENT * {:>2}'.format(playtimes)
        msg += ')\n'
    msg += '`'



    ###   書式を整えてメッセージを送信   ###
    embed = discord.Embed(title=title, description=msg, color=evTypeToColor[evType])
    await bdrbotch.send(embed=embed)

@client.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print('ログインしました')
    # 状態を '☆ピコピコプラネット☆を視聴中' にする
    activity = discord.Activity(name='☆ピコピコプラネット☆', type=discord.ActivityType.watching)
    await client.change_presence(activity=activity)
    update_border.start()

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content == '$bye':  # !byeが入力されたら強制終了
        await client.logout()
        print('ログアウトしました')

    if message.content.startswith('$pbdr'): #書き方汚いので整える
        try:
            evId = message.content.split()[1]
        except IndexError:
            await message.channel.send('イベントIDを入力してください')
            return
        
        url = 'https://api.matsurihi.me/mltd/v1/events/'

        response = requests.get(url)
        Data = response.json()

        lastevId = Data[-1]['id']

        if not 1 <= int(evId) <= lastevId:
            await message.channel.send('無効なイベントIDです')
            return

        title = ''
        msg = ''

        pastEventData_url = 'https://api.matsurihi.me/mltd/v1/events/' + evId

        response = requests.get(pastEventData_url)
        pastEventData = response.json()

        evName = pastEventData['name']
        evType = pastEventData['type']
        beginDate = pastEventData['schedule']['beginDate']
        endDate = pastEventData['schedule']['endDate']
        
        #await message.channel.send('event name: ' + evName)
        title += evName + '\n'

        if not evType == 3 and not evType == 4 and not evType == 5 and \
            not evType == 10 and not evType == 11 and not evType == 12:
            await message.channel.send('このイベントはランキング形式ではありません')
            return
        elif evType == 5:
            anniv = True
            all = False
            try:
                idolId = message.content.split()[2]
            except IndexError:
                idolId = 0
            
            if not 1 <= int(idolId) <= 52:
                all = True
            
            if all:
                await message.channel.send('不正なアイドルIDが入力されました．総合ランキングの結果を出力します')
                title += '総合ランキング '
            else:
                idolBdrData_url = 'https://api.matsurihi.me/mltd/v1/cards?idolId=' + idolId

                response = requests.get(idolBdrData_url)
                idolBdrData = response.json()

                idolName = idolBdrData[0]['name']

                #await message.channel.send('idol name: ' + idolName)
                title += idolName + 'ランキング '
        else:
            anniv = False
            
        title += '最終結果'

        if anniv and not all:
            pastBdrData_url = pastEventData_url  + '/rankings/logs/idolPoint/' + idolId + '/1-3,10,100,1000'
        else:
            pastBdrData_url = pastEventData_url  + '/rankings/logs/eventPoint/1-3,100,2500,5000,10000,25000,100000'

        response = requests.get(pastBdrData_url)
        bdData = response.json()

        borderRank = []  #各ボーダーの順位（基本的に不変）
        nowScores = []      #現時点でのスコアのリスト

        #リストへの書き込み
        for i in range(len(bdData)):
            borderRank.append(int(bdData[i]['rank']))
            nowScores.append(int(bdData[i]['data'][-1]['score']))

        msg += '`      #:     score\n'  
        for i in range(len(bdData)):
            msg += '{:>7,d}: {:>9,d}\n'.format(borderRank[i], nowScores[i])
        msg += '`'
        
        embed = discord.Embed(title=title, description=msg, color=evTypeToColor[evType])
        await message.channel.send(embed=embed)


client.run(token)
