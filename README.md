## Python證券投資分析&股票聊天機器人入門共學營期末專題
with [Ruizellen](https://github.com/Ruizellen)
## 專題簡報連結
[每日豹報](https://drive.google.com/file/d/1laFqeWkxyl4Vde7OX0Ut3mJ2JXzGMyr4/view?usp=sharing)

## 功能規劃
* 選單(被動)-基金列表
  1. 使用基金篩選 316 法則於 F01.基金類別績效(晨星)
  2. 整合到聊天機器人中
  3. 讓使用者點選選單基金列表，可以查詢基金類別清單
  4. 輸入基金類別名稱（ex. 大中華股票、拉丁美洲股票等）查詢基金績效清單

* 選單(被動)-來點正能量
  1. 事先找好20句佳句，並存入List中
  2. 當使用者點選「來點正能量」選單，回傳「@來點正能量」
  3. 再利用Random從List中隨機選出一個句子並回傳到LINEBOT

* 每日推播(主動)-今天節日
  1. 每日上午8點從中華民國節日與歲時列表抓取資料並存入List
  2. 判斷當天日期是否為一般國曆特殊節日
  3. 若非則將日期轉換為農曆日期，並對照是否為國曆特殊節日
  4. 如為特殊節日則顯示「今天是X月X日，XX節」
  5. 如非則顯示「今天是X月X日，是個平凡無奇的一天」

* 每日推播(主動)-歷史上的今天
  1. 每日上午8點從歷史上的今天抓取資料並存入List
  2. 利用Random的方式從List中隨機挑出一組故事/事件
  3. 並與「今天節日」一併使用廣播功能進行推播
