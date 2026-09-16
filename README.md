# 2026 東京 · 六天五夜

2026/9/20–9/25 的家庭行程頁。純靜態，沒有 build step、沒有框架，放在 GitHub Pages 上。

**Live**：https://freetempo.github.io/tokyo-2026/

手機用 Safari 開 → 分享 → 加入主畫面，之後離線也打得開（日本沒網路時很有用）。

## 檔案

| 檔案 | 說明 |
|---|---|
| `index.html` | 整個頁面。版面在 `<style>`、內容在最下面的 `TRIP` 陣列，改內容只要動 `TRIP`。 |
| `manifest.webmanifest` | PWA 設定（名稱、顏色、icon）。 |
| `sw.js` | Service worker，由 `tools/build-sw.py` 產生，**不要手改**。 |
| `icons/` | `icon.svg` 是原始檔，三個 png 由它產生。 |
| `tools/build-sw.py` | 重算快取清單與版本號。 |

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
