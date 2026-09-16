/* 加入主畫面後沒有網址列、也就沒有重新整理按鈕，所以更新要自己處理。
 *
 * 做三件事：
 *   1. 註冊 service worker，並主動去檢查有沒有新版
 *   2. 比對 version.json（永遠走網路）與目前 SW 的版本，不一樣就跳橫幅
 *   3. 提供強制更新：清掉所有快取 → 換掉 SW → 重新載入
 *
 * 頁面上可以放這兩個東西（有就用，沒有也不會壞）：
 *   <span id="ver"></span>            顯示版本與建置時間
 *   <button id="forceupdate">…</button> 手動強制更新
 */
(function () {
  const BANNER_ID = 'sw-update-banner';
  let liveVersion = null;   // version.json 上的版本（伺服器最新）
  let swVersion = null;     // 目前這個 SW 的版本

  /* ---------- 版面 ---------- */

  function injectStyle() {
    if (document.getElementById('sw-update-style')) return;
    const s = document.createElement('style');
    s.id = 'sw-update-style';
    s.textContent = `
      #${BANNER_ID}{
        position:fixed;left:12px;right:12px;bottom:12px;z-index:9999;
        background:var(--accent,#1b4965);color:#fff;border-radius:14px;
        padding:13px 15px;box-shadow:0 6px 24px rgba(0,0,0,.25);
        font:inherit;font-size:14px;line-height:1.5;
        display:flex;align-items:center;gap:12px;
      }
      #${BANNER_ID} span{flex:1 1 auto}
      #${BANNER_ID} button{
        flex:0 0 auto;border:0;border-radius:9px;padding:8px 13px;
        background:#fff;color:var(--accent,#1b4965);
        font:inherit;font-size:14px;font-weight:700;cursor:pointer;
      }
      #${BANNER_ID} .x{background:transparent;color:#fff;opacity:.7;padding:8px 4px;font-weight:400}
    `;
    document.head.appendChild(s);
  }

  function showBanner() {
    if (document.getElementById(BANNER_ID)) return;
    injectStyle();
    const d = document.createElement('div');
    d.id = BANNER_ID;

    const t = document.createElement('span');
    t.textContent = '有新版本的行程';

    const go = document.createElement('button');
    go.textContent = '立即更新';
    go.onclick = forceUpdate;

    const x = document.createElement('button');
    x.className = 'x';
    x.textContent = '稍後';
    x.setAttribute('aria-label', '稍後再說');
    x.onclick = () => d.remove();

    d.append(t, go, x);
    document.body.appendChild(d);
  }

  /* ---------- 強制更新 ---------- */

  async function forceUpdate(ev) {
    const btn = ev && ev.currentTarget;
    if (btn) { btn.disabled = true; btn.textContent = '更新中…'; }
    try {
      if ('serviceWorker' in navigator) {
        const reg = await navigator.serviceWorker.getRegistration();
        if (reg) {
          await reg.update().catch(() => {});
          if (reg.waiting) reg.waiting.postMessage('SKIP_WAITING');
        }
      }
      if (window.caches) {
        const keys = await caches.keys();
        await Promise.all(keys.map(k => caches.delete(k)));
      }
    } catch (e) { /* 清不掉也還是重載，至少會走網路 */ }
    /* 加一個一次性參數，確保連 HTML 都不吃任何層的快取 */
    const u = new URL(location.href);
    u.searchParams.set('_r', Date.now().toString(36));
    location.replace(u.toString());
  }

  /* ---------- 版本比對 ---------- */

  function paintVersion() {
    const el = document.getElementById('ver');
    if (!el || !liveVersion) return;
    el.textContent = `版本 ${liveVersion.version}（${liveVersion.builtAt}）`;
  }

  function askSwVersion() {
    return new Promise(resolve => {
      const sw = navigator.serviceWorker && navigator.serviceWorker.controller;
      if (!sw) return resolve(null);
      const timer = setTimeout(() => resolve(null), 1500);
      const onMsg = e => {
        if (e.data && e.data.type === 'VERSION') {
          clearTimeout(timer);
          navigator.serviceWorker.removeEventListener('message', onMsg);
          resolve(e.data.version);
        }
      };
      navigator.serviceWorker.addEventListener('message', onMsg);
      sw.postMessage('VERSION');
    });
  }

  async function checkForUpdate() {
    try {
      const r = await fetch('version.json', { cache: 'no-store' });
      if (!r.ok) return;
      liveVersion = await r.json();
      paintVersion();
      swVersion = await askSwVersion();
      if (swVersion && liveVersion.version && swVersion !== liveVersion.version) {
        showBanner();
      }
    } catch (e) { /* 離線就算了，畫面照用 */ }
  }

  /* ---------- 啟動 ---------- */

  addEventListener('load', () => {
    const btn = document.getElementById('forceupdate');
    if (btn) btn.onclick = forceUpdate;

    if (!('serviceWorker' in navigator)) { checkForUpdate(); return; }

    navigator.serviceWorker.register('sw.js').then(reg => {
      reg.addEventListener('updatefound', () => {
        const sw = reg.installing;
        if (!sw) return;
        sw.addEventListener('statechange', () => {
          if (sw.state === 'installed' && navigator.serviceWorker.controller) showBanner();
        });
      });
    }).catch(() => {});

    checkForUpdate();
  });

  /* 從主畫面切回前景時再檢查一次 —— 這是加入主畫面後最常見的使用方式 */
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) checkForUpdate();
  });
})();
