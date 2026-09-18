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

- 89 家店名本身就是拉丁字母
- 103 家補了官方英文寫法，顯示成「日文名 (English)」
- **22 家只有日文** —— 診所、保險店、彩券行、小餐館，官方本來就沒有英文名。
  **不要自己翻譯補上**，那會產生現場查不到的假名稱；那些用羅馬字就搜得到。

## 店家收藏（星號）

每家店左邊的 ☆ 按一下變 ★ 並加入收藏，類別列最前面的「★ 星號 N」只顯示收藏的店。

- 存在 `localStorage` 的 `shopFavs`（一組 store id），**per-device** —— 兩支手機各自獨立，不會同步
- 第一次開啟時會用 `shops.js` 裡 `star` 欄位（行程相關的四家）當預設收藏，
  之後就完全由使用者控制（取消掉不會再自動加回來）
- key 用官網的 store id（214 筆全部唯一），不是店名 —— 店名有重複的（セブン銀行ATM ×5）

## 天氣預報（兩個來源並發）

每一天的頁籤與頁內標題下面都會顯示天氣，**開頁面時即時抓**，不寫死。

**兩個來源同時發，先回來的先畫** —— 不是「先等一個、失敗才換」：

1. **Open-Meteo** —— 免 API key、`access-control-allow-origin: *`、**座標級**、16 天。
   一次請求拿三個點，所以每天用自己的地點座標：

   | 日期 | 地點 | 座標 | tenki.jp 代碼 |
   |---|---|---|---|
   | 9/20、9/22 | 豐洲 | 35.655, 139.795 | 13108 江東区 |
   | 9/21 | 大宮 | 35.906, 139.624 | 11103 さいたま市大宮区 |
   | 9/23–9/25 | 舞濱 | 35.632, 139.882 | 12227 浦安市 |

   地點差異是真的：實測 9/25 舞濱 37% vs 豐洲 29%、大宮最高溫常差 1–2°C。

2. **氣象廳 bosai 週間預報** —— `forecast/data/forecast/<pref>.json`，**區域級**、7 天。
   比較粗，但快得多，而且是日本官方。區域只有固定選項：

   | 地點 | 降水機率區域 | 氣溫區域 |
   |---|---|---|
   | 豐洲／都內 | 東京地方 | 東京 |
   | 大宮 | 埼玉県 | **熊谷**（比大宮更內陸、偏熱） |
   | 舞濱 | 千葉県 | **銚子**（比舞濱更東、偏海） |

   ⚠️ 週間預報裡三個縣的**降水機率其實是同一組數字**，只有氣溫不同。

氣象廳先回來就先畫，Open-Meteo 到了再蓋成座標級的細資料（單向：細的到了之後
不會再被粗的蓋回去）。畫面上的來源標示會跟著變（`· 豐洲 ↗` vs `· 氣象廳 東京 ↗`），
所以**數字小幅跳動是「換成更細的來源」，不是壞掉**。

### 為什麼並發，而不是排順序

實測兩個主機的差距（固網 curl，各 4 次）：

| | api.open-meteo.com | www.jma.go.jp |
|---|---|---|
| A 紀錄數 | **1**（`188.40.99.226`，Hetzner／德國） | **4**（`65.9.180.x`，CloudFront） |
| AAAA | 無 | 無 |
| TLS 握手 | 0.71–0.79 s | 0.025 s |
| 整趟 | 約 1.0 s | 0.037 s |

Open-Meteo 是**德國的一台單機，沒有 CDN、沒有備援**；氣象廳掛在 CDN 邊際節點上。
兩者都只有 A 紀錄、沒有 AAAA，**所以與 IPv6 無關**。

曾經回報「同一支 iPhone 下午看得到、晚上看不到，而颱風那段（走 jma.go.jp）
一直正常」。當時先猜是裝置或網路擋掉 Open-Meteo —— **那個猜測是錯的**。
真正的問題是舊寫法要先等 Open-Meteo 逾時才換備援，那台遠端單機一慢或一忙，
畫面就整段空著顯示「查詢中」。現在兩邊並發，氣象廳幾十毫秒就先把數字填上，
**不存在「等滿逾時」的空窗**。

逾時也跟著調整：Open-Meteo 給 **20 秒**（它不再擋第一次上色，慢慢回來還能把資料
換細，不必急著放棄），氣象廳給 **8 秒**（走 CDN、實測 0.04 秒，8 秒不回就是真的不通）。

### 其他

- 天氣代碼兩套不同，各自對應：Open-Meteo 是 **WMO code**，氣象廳是自己的
  **1xx 晴 / 2xx 曇 / 3xx 雨 / 4xx 雪**
- 頁籤上放「圖示＋降雨機率＋最高溫」一行擺完（例如 `⛈ 74% 26°`），
  頁內那一行放完整的降雨％、溫度區間、天氣文字
- 頁內那一行是連結，點了開**該日地點自己的** tenki.jp 十日預報（三個 URL 都驗證過）
- **刻意不進 service worker 快取** —— 預報會變，快取等於放過期資訊
- 兩個都失敗才降級成 tenki.jp 連結，並把失敗原因寫在下面一行方便回報
- 抓失敗時只有這幾行受影響，頁面其他部分照常（`safe()` 包住，已實測）

⚠️ 頁內數值來自 Open-Meteo 或氣象廳，連結過去的 tenki.jp 是**第三套來源**
（日本気象協会），數字會有幾個百分點的差異，這是正常的，不是壞掉。

### 驗證方式（五個情境都跑過）

把 `index.html` 複製成幾份，把 API 網址換掉，再用 headless Chrome 開，
讓頁面在 t=3s 與 t=14s 自己把 `.wx` 的文字 POST 回本機 server：

| 情境 | 做法 | 預期 |
|---|---|---|
| 正常 | 不改 | 最後是 `· 豐洲／大宮／舞濱`（座標級） |
| Open-Meteo 不通 | 換成不存在的主機 | `· 氣象廳 東京` 等，頁籤有數字 |
| 氣象廳不通 | 換成不存在的主機 | `· 豐洲` 等，不受影響 |
| 兩個都不通 | 都換掉 | 降級成 tenki.jp 連結，頁籤清空不留舊值 |
| **Open-Meteo 很慢** | 指到本機一個 sleep 6 秒的端點 | **t=3s 顯示氣象廳、t=14s 換成豐洲** |

最後一個才是真正要防的情況。`--virtual-time-budget` 配真網路會掛住，
所以用「頁面自己回報」而不是 `--dump-dom`。

⚠️ 不要用「body.innerHTML 裡還有幾個『天氣查詢中』」當指標 —— inline `<script>`
的原始碼也在 innerHTML 裡，那個字串字面會被一起數到。要數 `.wx` 元素本身的文字。

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
| 國外交易服務費 | 兩家都是 1.5% |

匯豐的「精選餐飲通路」是 **MCC Code 判定，沒有具名商家清單**，所以頁面上寫的是
「櫃台無法確認」而不是給清單 —— 這點不要自作聰明補名單。

玉山世界卡的旅遊不便險條款在 `esunbank.com/.../credit-card/travel-card/insurance.pdf`
（19 頁）。macOS 沒有 pdftotext 時，可以用內建 PDFKit 抽文字：

```bash
osascript -l JavaScript tools/pdftxt.js <檔案> <起頁> <迄頁>
```
