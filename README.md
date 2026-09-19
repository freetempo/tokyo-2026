# 2026 東京 · 六天五夜

2026/9/20–9/25 的家庭行程頁。純靜態，沒有 build step、沒有框架，放在 GitHub Pages 上。

**Live**：https://freetempo.github.io/tokyo-2026/

手機用 Safari 開 → 分享 → 加入主畫面，之後離線也打得開（日本沒網路時很有用）。

## 檔案

| 檔案 | 說明 |
|---|---|
| `index.html` | 整個頁面（行程 + 迪士尼攻略 + 店家清單）。版面在 `<style>`、內容在 `TRIP` 陣列。 |
| `shops.js` | LaLaport 店家資料，由 `tools/fetch-shops.py` 產生。刻意是 `.js` 而不是 `.json`：用 `<script>` 載入跟 index.html 走同一條路，離線才可靠（`fetch()` 抓 json 在 service worker 底下試過會失敗）。 |
| `manifest.webmanifest` | PWA 設定（名稱、顏色、icon）。 |
| `sw.js` | Service worker，由 `tools/build-sw.py` 產生，**不要手改**。 |
| `icons/` | `icon.svg` 是原始檔，三個 png 由它產生。 |
| `tools/build-sw.py` | 重算快取清單與版本號。 |
| `tools/fetch-shops.py` | 從三井官網重抓店家清單，產生 `shops.js`。裡面的 `EN`（官方英文名）、`ALIASES`（搜尋別名）、`STARRED`（行程相關）都是手工維護，鍵必須跟官網店名完全一致 —— 對不到時腳本會在 stderr 警告。 |

## 改內容

1. 編輯 `index.html` 裡的 `TRIP` 陣列。每個元素就是一個頁籤：

   ```js
   {
     id:"d3", tab:"9/22", tabSub:"Day 3", dow:"二", date:"2026-09-22",
     title:"街區散步 · 三選一",
     meta:"住：三井花園飯店 豐洲普米爾",
     html:`...`
   }
   ```

   `date` 用 `YYYY-MM-DD`，旅程期間頁面會自動開那一天。

2. **一定要跑這個**，不然手機會一直吃舊的快取：

   ```bash
   python3 tools/build-sw.py
   ```

3. commit、push，GitHub Pages 一兩分鐘後生效。

## 可以用的樣式

寫在 `html` 字串裡，直接用這些 class：

- `<ul class="tl">` 時間軸，每個 `<li>` 是 `<div class="time">` + `<div class="body">`（裡面 `.what` 標題、`.note` 說明）。時間留白用 `<div class="time blank">`。
- `<div class="card">` 一般卡片，`<h3>` 當標題。
- `<details><summary><span class="n">1</span>標題</summary><div class="dbody">…</div></details>` 可收合區塊。
- `<div class="note-box">` 藍色提醒、`<div class="note-box warm">` 橘色警告。
- `<span class="tag book">已訂位</span>`、`tag stroll` 推車、`tag check` 待確認。
- 地圖按鈕：`<a class="map" target="_blank" rel="noopener" href="${G('店名 地址')}">🗺 …</a>`，`G()` 會產 Google Maps 搜尋連結。官網連結用同一個 class，直接寫 `href`。

## 深淺色

右上角的按鈕循環切換 **跟隨系統 → 淺色 → 深色**，選擇記在 `localStorage` 的 `theme`。

預設是**跟隨系統**（`system`）。顏色都定義在 CSS 變數：`:root` 淺色、`:root[data-theme="dark"]` 手動深色、`@media (prefers-color-scheme:dark) :root[data-theme="system"]` 系統深色。三處都要一起改，不要只改一個。

## 換 icon

改 `icons/icon.svg`，然後：

```bash
sips -s format png icons/icon.svg --out icons/icon-512.png
sips -Z 192 icons/icon-512.png --out icons/icon-192.png
sips -Z 180 icons/icon-512.png --out icons/icon-180.png
python3 tools/build-sw.py
```

## 本機預覽

```bash
python3 -m http.server 8765
# 開 http://localhost:8765/
```

Service worker 需要 http（不能用 file://）才會註冊。

## 這個 repo 是公開的

不要 commit 訂位號碼、訂票代號、護照或保單資訊、本機路徑、email。訂位號碼放在本機的速查檔，沒有進版控。

## 店家清單的英文名稱

官網雖有英文版，但**店名是圖片**（`<img src=".../KFC_xxx.jpg">`、alt 空的）、沒有 store-id、只涵蓋約 60 家，
無法自動對接，所以 `EN` 是手工整理的。

- 67 家店名本身就是拉丁字母
- 108 家補了官方英文寫法，顯示成「日文名 (English)」
- **40 家只有日文** —— ATM、診所、保險店、彩券行、小餐館，官方本來就沒有英文名。
  **不要自己翻譯補上**，那會產生現場查不到的假名稱；那些用羅馬字就搜得到。

⚠️ 羅馬字是照片假名機械轉的（オリンピア → orinpia、イリオ → irio），跟官方拼法
（OLYMPIA、ilio）可能差很多 —— 這種店**一定要補 `EN`**，否則使用者照招牌拼法搜會搜不到
（2026/9/19 實際發生：搜 olympia 找不到）。補之前開官方店鋪頁看官網連結確認拼法。

## 店家收藏（星號）

每家店左邊的 ☆ 按一下變 ★ 並加入收藏，類別列最前面的「★ 星號 N」只顯示收藏的店。

- 存在 `localStorage` 的 `shopFavs`（一組 store id），**per-device** —— 兩支手機各自獨立，不會同步
- 第一次開啟時會用 `shops.js` 裡 `star` 欄位（行程相關的四家）當預設收藏，
  之後就完全由使用者控制（取消掉不會再自動加回來）
- key 用官網的 store id（214 筆全部唯一），不是店名 —— 店名有重複的（セブン銀行ATM ×5）

## 天氣預報（只用氣象廳）

每一天的頁籤與頁內標題下面都會顯示天氣，**開頁面時即時抓**，不寫死。

來源只有一個：**氣象廳 bosai 預報 JSON**（`www.jma.go.jp/bosai/forecast/data/forecast/<pref>.json`，
CORS 開放、無需 key、走 CloudFront，實測整趟 0.04 秒）。抓兩個縣（東京 130000、埼玉 110000）。

### 為什麼不用 Open-Meteo 了

之前用過 Open-Meteo（座標級、16 天），後來也並用過。拿掉的理由，按重要性：

1. **權威度**：氣象廳是日本官方；Open-Meteo 是免費整合服務，把各國模式（日本這塊就是氣象廳的
   MSM/GSM）內插到座標上，沒有預報員。
2. **「座標級差異」是假的**：官方週間預報裡東京地方／埼玉県／千葉県的降水機率是**同一組數字**
   （實測 `— 90 80 30 40 40 40` 三縣一字不差）。Open-Meteo 給的舞濱 37% vs 豐洲 29% 是內插雜訊，
   五天外沒有實際意義。
3. **兩邊真的不一樣時該信官方**：迪士尼那三天 Open-Meteo 說 16–29%，氣象廳說 40%，
   這是「帶不帶雨具」等級的差異。
4. **穩定性**：`api.open-meteo.com` 只有一個 IP（`188.40.99.226`，Hetzner 德國）、沒有 CDN，
   固網 TLS 握手就 0.7 秒；曾造成手機上長時間「查詢中」。

一個來源、一套程式、數字不會跳。

### 區域與測站對應

| 行程地點 | 縣 | 3 天預報區域／測站 | 週間預報區域／測站 |
|---|---|---|---|
| 豐洲、都內 | 東京 | 東京地方／東京 | 東京地方／東京 |
| **舞濱** | 東京 | 東京地方／東京 | 東京地方／東京 |
| 大宮 | 埼玉 | 南部／**さいたま** | 埼玉県／**熊谷** |

舞濱行政上屬千葉，但官方週間預報千葉縣只有**銚子**測站（90 km 外的海角），
東京車站離舞濱 15 km、而且降水機率千葉県＝東京地方，所以直接用東京。
大宮週間只有熊谷可選（同為內陸，約差 1°C），3 天預報就有さいたま。

### 兩份預報怎麼合併

同一份 JSON 裡有兩段：`j[0]` 3 天預報、`j[1]` 週間預報。

- 週間：7 天，`pops` / `weatherCodes` / `reliabilities`（信賴度 A/B/C）/ `tempsMax` / `tempsMin`。
  **「今天」那格一定是空字串**，近日也可能沒有信賴度。
- 3 天：`timeSeries[0]` 每日天氣代碼、`timeSeries[1]` **6 小時一格**的降水機率、
  `timeSeries[2]` 溫度（`T00:00` 是最低、`T09:00` 是最高；傍晚發布只有明天）。

規則：先鋪週間，再讓 3 天預報**蓋上去**（更近、更細）。降水機率取當日各格最大值。
所以旅程中「今天」會顯示剩餘時段的降雨機率，溫度若當天沒有就不硬湊。
已用存下來的 JSON 在 node 裡跑過整個模組驗證這條路徑。

### 天氣代碼

氣象廳自己的一套：1xx 晴系、2xx 曇系、3xx 雨、4xx 雪。只挑九月東京用得到的分法：
100 晴；101/110/111 晴時多雲；其他 1xx 晴有雨；200 陰；201/210/211 陰轉晴；其他 2xx 陰有雨。
雪的變體（104、204…）會被歸到「有雨」，九月可接受。

### 其他

- 頁籤放「圖示＋降雨機率＋最高溫」（例如 `🌧 90% 25°`），頁內放完整的降雨％、溫度區間、
  天氣文字、來源、信賴度
- 頁內那一行是連結，開**該日地點自己的** tenki.jp 十日預報（豐洲 13108、大宮 11103、浦安 12227）。
  tenki.jp 是日本気象協会、**另一套來源**，數字差幾個百分點是正常的
- **刻意不進 service worker 快取** —— 預報會變；fetch 帶 `?_t=` 時間戳、`cache:'no-store'`
- 逾時 8 秒（走 CDN，8 秒不回就是真的不通）
- 抓不到就降級成 tenki.jp 連結，頁籤清空不留舊值，並在下面一行寫出失敗原因方便回報
- 整段包在 `safe()` 裡，出錯不影響頁面其他部分

### 驗證方式

把 `index.html` 複製一份、把 `www.jma.go.jp/bosai/forecast` 換成不存在的主機，用 headless Chrome 開，
讓頁面在 t=9s 把 `.wx` 的文字 POST 回本機 server（`--virtual-time-budget` 配真網路會掛住，
`--dump-dom` 又只在 load 時輸出，所以用頁面自己回報）。
另外用存下來的官方 JSON 在 node 裡 eval 整個模組，檢查 3 天／週間合併。

⚠️ 不要用「body.innerHTML 裡還有幾個『天氣查詢中』」當指標 —— inline `<script>` 原始碼也在
innerHTML 裡，字串字面會被一起數到。要看 `.wx` 元素本身的文字。

## 颱風資訊（總覽頁最上面）

資料取自氣象庁的 bosai JSON（CORS 開放、無需 key）：

- `typhoon/data/targetTc.json` → 目前有哪些熱帶氣旋
- `typhoon/data/<TC編號>/specifications.json` → 實況與各時間點的預報

顯示實況與預報各點的位置、**與東京的大圓距離**、氣壓、風速，並在開頭寫出
**「最接近東京：X/X（週X）HH:MM 約 XXX km」**，最接近的那一列標橘色。

距離是把官方座標換算成好懂的數字（東京車站 35.681N 139.767E），
不做任何自己的預測。低於 500 km 才多加一句「行程可能受影響」。
同時顯示該時間點的**預報圓半徑**，讓人知道不確定性有多大。

注意事項：

- 這是官方但**沒有正式文件**的端點，格式可能改 → 整段包在 catch 裡，
  解析失敗就退成「去官方頁看」的連結，**絕不顯示可能錯的內容**
- 會計算資料年齡，**超過 6 小時就明確標示「這是 N 小時前的資料」** ——
  颱風資訊過期就是危險
- 不進 service worker 快取；fetch 帶 `?_t=` 時間戳
- 沒網路時整塊降級成官方連結（已用不存在的主機逼出 catch 分支驗證過，
  六格天氣與頁籤上的數字都不會殘留舊值）

### 測試離線時的注意
只關掉本機 `python3 -m http.server` **不算離線** —— 外網還通，天氣與颱風
還是抓得到（那是正確行為）。要測降級，把 `index.html` 複製一份、
把兩個 API 網址換成不存在的主機再開。

## 刷卡回饋（頁籤）

商家清單與條款**抄自玉山官方活動頁**（`event.esunbank.com.tw/credit/kumamon-card/japan-discount.html`），
寫死在 `index.html` 的 `CARD_SHOPS` 裡，四個分類共 23 組。

刻意寫死而不即時抓的原因：

- 那是公告過的名單，不會每天變
- **離線也要看得到** —— 在店裡結帳前查最需要
- 官方頁是靜態 HTML 但用 UIkit switcher 分頁，直接 fetch 會受 CORS 限制

活動有變就重抄一次，並同時更新 panel meta 裡的「資料抓取於」日期。

抓取方式（官方頁結構）：四個分類在 `#japan-switcher` 的 `<li>` 裡，
每組是 `p.p2.font-weight-bold.decoration-wavy`（小分類）＋
`p.p2.font-weight-normal`（商家）。注意 class 屬性會跨行。

### 三張卡的資料來源

| 卡 | 來源 |
|---|---|
| 熊本熊卡 | `event.esunbank.com.tw/credit/kumamon-card/japan-discount.html` |
| 玉山國外消費加碼 | `event.esunbank.com.tw/credit/travel/index.html`（全玉山卡適用，**含熊本熊卡**） |
| 玉山世界卡 | `esunbank.com/zh-tw/personal/credit-card/intro/world-card/world` |
| 匯豐 Live+ | `hsbc.com.tw/credit-cards/products/liveplus/` |
| 台新 Richart（玩旅刷） | `taishinbank.com.tw/TSB/personal/credit/intro/overview/future/ab46dfa7-5d88-11f1-b50f-0050568c09e3` |
| 國外交易服務費 | 三家都是 1.5% |

決策表的排法（2026/9/19 定案）：

1. 熊本熊指定商店前約 8,300 台幣（+6% 每期上限 500）
2. Live+ 只在四種 MCC 店型（餐飲 5441/5499/5812/5813/5814、購物 5311/5944/5948、
   娛樂 7832/7996/7998）拿出來，三類共用每期 888（約 29,600 封頂）
3. 其他全部先刷熊本熊把**玉山日幣帳戶**的日幣用掉（雙幣卡扣日幣；官方條款寫明扣日幣
   仍收 1.5%；回饋折台幣帳單）
4. 日幣用完才換 Richart 玩旅刷（3.3%、上限＝額度＋30 萬，實務上無上限）

理由：只比單筆回饋率會誤導大額消費（上限一定刷破，使用者指出）；而帳戶裡已換好的日幣
沒有利息、賣回要吃價差，花掉就是最好的用途，熊本熊 +1% 對 Richart +1.8% 的差距
每萬日圓只有約 NT$15。使用者的日幣平均成本是沉沒成本，不進決策。

Live+ 的 MCC 對照表是照匯豐官網條款寫的；日本店型對應到哪個 MCC 是一般常識
（百貨店 5311、藥妝 5912、電器 5732 等），**購物中心租戶各自收銀、多半不是 5311**
這點要記得，之前頁面寫「PARCO」是錯的。迪士尼在匯豐「海外娛樂」名單上明列。

匯豐的「精選餐飲通路」是 **MCC Code 判定，沒有具名商家清單**，所以頁面上寫的是
「櫃台無法確認」而不是給清單 —— 這點不要自作聰明補名單。

玉山世界卡的旅遊不便險條款在 `esunbank.com/.../credit-card/travel-card/insurance.pdf`
（19 頁）。macOS 沒有 pdftotext 時，可以用內建 PDFKit 抽文字：

```bash
osascript -l JavaScript tools/pdftxt.js <檔案> <起頁> <迄頁>
```
