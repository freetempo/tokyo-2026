#!/usr/bin/env python3
"""重建 sw.js：掃出要快取的檔案，用內容 hash 當版本號。

內容改完一定要跑這個，否則手機會一直吃舊的快取。

    python3 tools/build-sw.py
"""
import hashlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
# 要離線快取的東西。tools/ 與 .git/ 不進去。
PATTERNS = ("index.html", "shops.js",
            "manifest.webmanifest", "icons/*.png", "img/*")
SKIP_DIRS = {".git", "tools"}


def collect() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for pat in PATTERNS:
        for p in sorted(ROOT.glob(pat)):
            if not p.is_file():
                continue
            if any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts):
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
const CACHE = "tokyo2026-{version}";
const ASSETS = [
  {listing}
];

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

// 同網域的 GET 走 cache-first，離線也開得起來；快取沒有的就照常連網。
self.addEventListener("fetch", e => {{
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  e.respondWith(
    caches.match(e.request, {{ ignoreSearch: true }}).then(hit => {{
      if (hit) return hit;
      return fetch(e.request)
        .then(res => {{
          if (res.ok && res.type === "basic") {{
            const copy = res.clone();
            caches.open(CACHE).then(c => c.put(e.request, copy));
          }}
          return res;
        }})
        .catch(() => caches.match("./"));
    }})
  );
}});
"""
    (ROOT / "sw.js").write_text(sw, encoding="utf-8")
    total = sum(p.stat().st_size for p in files)
    print(f"sw.js 已更新　版本 {version}　{len(assets)} 個項目　{total / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
