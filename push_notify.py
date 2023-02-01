import os
import sxtwl
import random
import requests
import pandas as pd
import urllib.request
from bs4 import BeautifulSoup
from datetime import date
from apscheduler.schedulers.blocking import BlockingScheduler
from opencc import OpenCC #繁簡轉換器

# 引入套件 flask
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
# 引入 linebot 異常處理
from linebot.exceptions import (
    InvalidSignatureError
)
# 引入 linebot 訊息元件
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
#引入random(來點正能量用)
from random import choice

# 創建一個 Scheduler 物件實例
sched = BlockingScheduler()

cc = OpenCC('s2tw') # 簡體中字 > 繁體中文(台灣，包含慣用詞轉換)

# LINE Chatbot token
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_USER_ID = os.environ.get('LINE_USER_ID')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

today = str(date.today())  # 如 2019-08-08
today_list = today.split('-') # ['2019', '08', '08']

#  今日節日
@sched.scheduled_job('interval', minutes=1)
def crawl_for_festival():
  url = ('https://zh.wikipedia.org/wiki/%E4%B8%AD%E8%8F%AF%E6%B0%91%E5%9C%8B%E7%AF%80%E6%97%A5%E8%88%87%E6%AD%B2%E6%99%82%E5%88%97%E8%A1%A8')

  headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'}

  resp = requests.get(url, headers=headers)
  resp.encoding = 'utf-8'

  soup = BeautifulSoup(resp.text, 'html.parser')

  festival_name = []
  festival_date = []

  for num in range(2, 25):

    festival_name.append(soup.select(f'.wikitable_festival tr:nth-child({num}) td:nth-child(1)')[0].text)

    festival_date.append(soup.select(f'.wikitable_festival tr:nth-child({num}) td:nth-child(2)')[0].text)

  festival_date[1] = '農曆 十二月卅一'
  festival_date[2] = '農曆 正月初二'
  festival_date[9] = '農曆 四月初五'

  # 日曆庫實例化
  lunar = sxtwl.Lunar()

  #日曆中文索引
  ymc = [u"十一", u"十二", u"正", u"二", u"三", u"四", u"五", u"六", u"七", u"八", u"九", u"十" ]
  rmc = [u"初一", u"初二", u"初三", u"初四", u"初五", u"初六", u"初七", u"初八", u"初九", u"初十", \
              u"十一", u"十二", u"十三", u"十四", u"十五", u"十六", u"十七", u"十八", u"十九", \
              u"二十", u"廿一", u"廿二", u"廿三", u"廿四", u"廿五", u"廿六", u"廿七", u"廿八", u"廿九", u"三十", u"卅一"]

  # 陽歷轉農歷
  today_date = f'{today_list[1]}月{today_list[2]}日'

  lunar_day = lunar.getDayBySolar((int)(today_list[0]),(int)(today_list[1]),(int)(today_list[2])) # 輸入年月日

  # 判斷是否爲潤年
  if(lunar_day.Lleap):
      lunar_date = ("農曆 {0}月{1}".format(ymc[lunar_day.Lmc],rmc[lunar_day.Ldi]))
      
  else:
      lunar_date = ("農曆 {0}月{1}".format(ymc[lunar_day.Lmc],rmc[lunar_day.Ldi]))

  # 判斷當天日期是否有特殊節日
  # 國曆節日對照
  if today_date in festival_date:
    judge = festival_date.index(today_date)
    today_msg = f'今天是{today_date}，{festival_name[judge]}'

  # 農曆節日對照
  elif lunar_date in festival_date:
    judge = festival_date.index(lunar_date)
    today_msg = f'今天是{today_date}，{festival_name[judge]}'

  else:
    today_msg = f'今天是{today_date}，是個平凡無奇的一天~\n'

    return cc.convert(today_msg) 

# 歷史上的今天
@sched.scheduled_job('interval', minutes=1)
def crawl_for_history_today():
  url = (f'https://zh.wikipedia.org/wiki/{today_list[1]}月{today_list[2]}日')

  headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'}

  resp = requests.get(url, headers=headers)
  resp.encoding = 'utf-8'

  soup = BeautifulSoup(resp.text, 'html.parser')

  history_today = []

  li_tags = soup.select('li')
  for t in li_tags:
    #print(t.text)
    if '年' in t.text:
      history_today.append(t.text)

  r = random.randint(0,len(history_today))
  history_msg = f'\n歷史上的今天有發生的事件 / 出生的人：\n{history_today[r]}'

  return cc.convert(history_msg)


# decorator 設定 Scheduler 的類型和參數，例如 interval 間隔多久執行
#@sched.scheduled_job('interval', minutes=2)
@sched.scheduled_job('interval',days=1,start_date='2021-11-3 8:00:00')
def get_notify():
    # 要注意不要太頻繁抓取，但測試時可以調整時間少一點方便測試
    print('執行每日推撥')

    today_push_msg = crawl_for_festival()
    history_push_msg = crawl_for_history_today()
    line_bot_api.broadcast(TextSendMessage(text=today_push_msg+history_push_msg))

# 定義排程：周一到周五，每20分鐘喚醒一次
@sched.scheduled_job('cron',day_of_week='mon-fri',minute='*/20')
def scheduled_job():
    url = "https://daily-seal-notify.herokuapp.com/"
    connect = urllib.request.urlopen(url)

# 開始執行
sched.start()