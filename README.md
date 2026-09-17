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

## 天氣預報

每一天的頁籤與頁內標題下面都會顯示天氣，**開頁面時即時抓**，不寫死。

- 數值來源 [Open-Meteo](https://open-meteo.com/)：免 API key、`access-control-allow-origin: *`
- **每一天用自己的地點座標**，一次請求拿三個點：
  | 日期 | 地點 | tenki.jp 代碼 |
  |---|---|---|
  | 9/20、9/22 | 豐洲 | 13108 江東区 |
  | 9/21 | 大宮 | 11103 さいたま市大宮区 |
  | 9/23–9/25 | 舞濱 | 12227 浦安市 |
  地點差異是真的：實測 9/25 舞濱 37% vs 豐洲 29%、大宮最高溫常差 1–2°C。
- 頁籤上放「圖示＋降雨機率＋最高溫」一行擺完（例如 `⛈ 74% 26°`），
  頁內那一行放完整的降雨％、溫度區間、天氣文字
- 頁內那一行是連結，點了開**該日地點自己的** tenki.jp 十日預報（三個 URL 都驗證過）
- **刻意不進 service worker 快取** —— 預報會變，快取等於放過期資訊
- 抓失敗或沒網路時只有這一行降級成連結，不影響頁面其他部分（已實測）

⚠️ 頁內數值來自 Open-Meteo，連結過去的 tenki.jp 是**另一套來源**（日本気象協会），
兩者的數字會有幾個百分點的差異，這是正常的，不是壞掉。

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
