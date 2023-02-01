import os

import requests
import pandas as pd
from bs4 import BeautifulSoup
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
from random import choice


app = Flask(__name__)


headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36'
}

# LINE_CHANNEL_SECRET 和 LINE_CHANNEL_ACCESS_TOKEN 類似聊天機器人的密碼，記得不要放到 repl.it 或是和他人分享
# 從環境變數取出設定參數
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 儲存基金代碼對應
fund_map_dict = {}


def init_fund_list():
    """
    初始化建立基金列表 這邊我們儲存在 dict 中）
    """
    resp = requests.get(
        'https://www.sitca.org.tw/ROC/Industry/IN2421.aspx?txtMonth=02&txtYear=2020', headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')
    # 選擇基金列表 table
    table_content = soup.select('#ctl00_ContentPlaceHolder1_TableClassList')[0]
    # 選擇基金名稱連結
    fund_links = table_content.select('a')

    for fund_link in fund_links:
        # 去除沒有基金名稱的連結
        if fund_link.text:
            # 取出基金名稱
            fund_name = fund_link.text
            fund_group_id = fund_link['href'].split('txtGROUPID=')[1]
            fund_map_dict[fund_name] = fund_group_id
    return fund_map_dict


def fetch_fund_rule_items(group_id):

    resp = requests.get(
        f'https://www.sitca.org.tw/ROC/Industry/IN2422.aspx?txtYEAR=2020&txtMONTH=02&txtGROUPID={group_id}', headers=headers)

    soup = BeautifulSoup(resp.text, 'html.parser')

    # 觀察發現透過 id ctl00_ContentPlaceHolder1_TableClassList 可以取出 Morningstar table 資料。取出第一筆
    table_content = soup.select('#ctl00_ContentPlaceHolder1_TableClassList')[0]

    # 將 BeautifulSoup 解析的物件美化後交給 pandas 讀取 table，注意編碼為 UTF-8。取出第二筆
    fund_df = pd.read_html(table_content.prettify(), encoding='utf-8')[1]

    # 資料前處理，將不必要的列
    fund_df = fund_df.drop(index=[0])
    # 設置第一列為標頭
    fund_df.columns = fund_df.iloc[0]
    # 去除不必要列
    fund_df = fund_df.drop(index=[1])
    # 整理完後新設定 index
    fund_df.reset_index(drop=True, inplace=True)
    # NaN -> 0
    fund_df = fund_df.fillna(value=0)

    # 轉換資料型別從 object 轉為 float
    fund_df['一個月'] = fund_df['一個月'].astype(float)
    fund_df['三個月'] = fund_df['三個月'].astype(float)
    fund_df['六個月'] = fund_df['六個月'].astype(float)
    fund_df['一年'] = fund_df['一年'].astype(float)
    fund_df['二年'] = fund_df['二年'].astype(float)
    fund_df['三年'] = fund_df['三年'].astype(float)
    fund_df['五年'] = fund_df['五年'].astype(float)
    fund_df['自今年以來'] = fund_df['自今年以來'].astype(float)

    # 前二分之一筆資料數量
    half_of_row_count = len(fund_df.index) // 2

    # 316 法則篩選標準，ascending True 為由小到大排序，nlargest 為取出前面 x 筆資料，// 代表取整數去掉小數（轉為整數意思）
    rule_3_df = fund_df.sort_values(
        by=['三年'], ascending=['True']).nlargest(half_of_row_count, '三年')
    rule_1_df = fund_df.sort_values(
        by=['一年'], ascending=['True']).nlargest(half_of_row_count, '一年')
    rule_6_df = fund_df.sort_values(
        by=['六個月'], ascending=['True']).nlargest(half_of_row_count, '六個月')

    # 取三者交集（merge 一次只能兩個 DataFrame，先前兩個取交集再和後一個取交集）
    rule_31_df = pd.merge(rule_3_df, rule_1_df, how='inner')
    rule_316_df = pd.merge(rule_31_df, rule_6_df, how='inner')

    fund_rule_items_str = ''

    # 組成回傳篩選結果字串
    if not rule_6_df.empty:
        for _, row in rule_316_df.iterrows():
            fund_rule_items_str += f'{row["基金名稱"]}, {row["三年"]}, {row["一年"]}, {row["六個月"]}\n'

    return fund_rule_items_str


init_fund_list()

# 此為歡迎畫面處理函式，當網址後面是 / 時由它處理

#來點正能量的list
positiveEnergyList = ['不用太在意一些人說的話，因為他們有嘴卻不一定有腦 (・∀・)', '別動不動就把錯誤丟給時間去處理，時間才懶得理你這個爛攤子(´･ω･`)  ', '人生就像遊樂園，只不過大多數的人都是工作人員(눈_눈)',
'麻雀雖小，也沒有我小，因為我超雖小╮(╯_╰)╭',
'我不是討厭你，而是你沒有一點讓我喜歡ಠ_ಠ', '賴床是對週末最起碼的尊重(ㆆᴗㆆ)', '無能，也是一種答案┐(´д`)┌',
'追逐夢想路上你並不孤單，因為會有很多人陪你放棄(=´ω`=)', '沒有所謂的結束，決定結束才會有結束(☍﹏⁰)', '回到過去的方法就是閉上眼睛(つд⊂)', '戀愛就是在黑暗中開心的行走ʕ•̀ω•́ʔ✧',
'人們的關注不至於會少到讓你失望，但也不會多到讓你期待( ﾟдﾟ)',
'狠下心丟了的東西，常常隔天就會要用到(･ัω･ั)', '理想是沙漠上剛種下的一朵花٩(๑´3｀๑)۶',
'若是迷失在愛裡能了解真愛的話，再怎麼迷失都無所謂(๑•̀ㅁ•́๑)✧', '明天的你會為今天的你感到驕傲嗎 ( ・◇・)？',
'在比賽中一次也沒贏過，也是很了不起的紀錄(✽ ﾟдﾟ ✽)', '如果說關心是一種溫柔，那麼選擇不關心也是一種溫柔(´°̥̥̥̥̥̥̥̥ω°̥̥̥̥̥̥̥̥｀)',
'明天也會說「明天再做」(#･∀･)', '越是要求傳球的人，越不會傳球給別人(・へ・)']
# decorator 負責判斷 event 為 MessageEvent 實例，event.message 為 TextMessage 實例。所以此為處理 TextMessage 的 handler



# 此為 Webhook callback endpoint 處理函式，當網址後面是 /callback 時由它處理
@app.route("/callback", methods=['POST'])
def callback():
    # 取得網路請求的標頭 X-Line-Signature 內容，確認請求是從 LINE Server 送來的
    signature = request.headers['X-Line-Signature']

    # 將請求內容取出
    body = request.get_data(as_text=True)

    # handle webhook body（轉送給負責處理的 handler，ex. handle_message）
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


# decorator 負責判斷 event 為 MessageEvent 實例，event.message 為 TextMessage 實例。所以此為處理 TextMessage 的 handler
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 決定要回傳什麼 Component 到 Channel，這邊使用 TextSendMessage
    user_input = event.message.text
    if user_input == '@基金列表':
        # 將 dict 儲存的基金列表組成回傳字串
        fund_list_str = ''
        for fund_name in fund_map_dict:
            fund_list_str += fund_name + '\n'
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=fund_list_str))
    # 若使用者輸入基金名稱有在清單中則取出其績效資料回傳
    elif user_input in fund_map_dict:
        group_id = fund_map_dict[user_input]
        print('開始篩選...')
        fund_rule_items_str = fetch_fund_rule_items(group_id)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=fund_rule_items_str))
    elif user_input == '@來點正能量':
        choiceOne = choice(positiveEnergyList)
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=choiceOne))
    else:
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text='請輸入正確指令'))
# 初始化基金清單方便接下來查詢使用


"""
__name__ 為 Python 內建變數，若程式不是被當作模組引入則 __name__ 內容為 __main__ 字串，直接在本機電腦端執行此檔案會進入執行 app.run()
"""
if __name__ == '__main__':
    app.run()