#!/usr/bin/env python3
"""重建 sw.js：掃出要快取的檔案，用內容 hash 當版本號。

內容改完一定要跑這個，否則手機會一直吃舊的快取。

    python3 tools/build-sw.py
"""
import datetime
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
# 要離線快取的東西。tools/ 與 .git/ 不進去。
PATTERNS = ("index.html", "shops.html", "shops.json", "update.js",
            "manifest.webmanifest", "icons/*.png", "img/*")
SKIP_DIRS = {".git", "tools"}
SKIP_FILES = {"version.json"}


def collect() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for pat in PATTERNS:
        for p in sorted(ROOT.glob(pat)):
            if not p.is_file():
                continue
            rel = p.relative_to(ROOT)
            if any(part in SKIP_DIRS for part in rel.parts) or rel.name in SKIP_FILES:
                continue
            files.append(p)
    return files


def main() -> int:
    files = collect()
    if not files:
        print("沒找到任何要快取的檔案，是不是路徑跑掉了？", file=sys.stderr)
        return 1

    h = hashlib.sha256()
    for p in files:
        h.update(p.relative_to(ROOT).as_posix().encode())
        h.update(p.read_bytes())
    version = h.hexdigest()[:10]

    assets = ["./"] + [p.relative_to(ROOT).as_posix() for p in files]
    listing = ",\n  ".join(f'"{a}"' for a in assets)

    sw = f"""// 由 tools/build-sw.py 產生，請不要手改。
const VERSION = "{version}";
const CACHE = "tokyo2026-" + VERSION;
const ASSETS = [
  {listing}
];

// 內容檔走 network-first：有網路一定看到最新版，沒網路才退回快取。
// 圖片、icon、manifest 走 cache-first（很少變，而且要快）。
const FRESH = /(\\.html|\\.json|\\.js|\\/)$/;

self.addEventListener("install", e => {{
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
}});

self.addEventListener("activate", e => {{
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
}});

self.addEventListener("message", e => {{
  if (e.data === "VERSION") {{
    e.source && e.source.postMessage({{ type: "VERSION", version: VERSION }});
  }}
  if (e.data === "SKIP_WAITING") self.skipWaiting();
}});

self.addEventListener("fetch", e => {{
  const req = e.request;
  const url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== location.origin) return;

  const fresh = req.mode === "navigate" || FRESH.test(url.pathname);

  if (fresh) {{
    e.respondWith(
      fetch(req)
        .then(res => {{
          if (res.ok && res.type === "basic") {{
            const copy = res.clone();
            caches.open(CACHE).then(c => c.put(req, copy));
          }}
          return res;
        }})
        .catch(() => caches.match(req, {{ ignoreSearch: true }})
          .then(hit => hit || caches.match("./")))
    );
    return;
  }}

  e.respondWith(
    caches.match(req, {{ ignoreSearch: true }}).then(hit => hit || fetch(req).then(res => {{
      if (res.ok && res.type === "basic") {{
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(req, copy));
      }}
      return res;
    }}))
  );
}});
"""
    (ROOT / "sw.js").write_text(sw, encoding="utf-8")

    # version.json 刻意不進快取清單，永遠走網路，頁面用它判斷有沒有新版
    built = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
    (ROOT / "version.json").write_text(
        json.dumps({"version": version, "builtAt": built}, ensure_ascii=False),
        encoding="utf-8")

    total = sum(p.stat().st_size for p in files)
    print(f"sw.js 已更新　版本 {version}　{len(assets)} 個項目　{total / 1024:.0f} KB")
    print(f"version.json　{version}　{built}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
