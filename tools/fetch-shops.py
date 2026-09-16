#!/usr/bin/env python3
"""從三井官網抓 LaLaport 豐洲的全部店家，產生 shops.json。

官網的店家清單是靜態 HTML（<li class="js-item">），一次就把全部店家吐出來，
不用分頁也不用跑 JS。

    python3 tools/fetch-shops.py
    python3 tools/build-sw.py     # 抓完記得重建快取

店家有變動時重跑即可。抓不到就先用 curl 看一下版面是不是改了。
"""
import html as H
import json
import pathlib
import re
import sys
import urllib.request

URL = "https://mitsui-shopping-park.com/lalaport/toyosu/shopguide/"
SITE = "https://mitsui-shopping-park.com"
OUT = pathlib.Path(__file__).resolve().parent.parent / "shops.json"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0 Safari/537.36")

# 官網的主類別收斂成四類，太細的長尾併進去
CAT_MAP = {
    "グルメ＆フーズ": "美食",
    "マリーナキッチン（フードコート）": "美食",
    "レストラン": "美食",
    "食料品・食物販": "美食",
    "ファッション": "服飾",
    "ファッション雑貨": "服飾",
    "キッズ・ベビー": "服飾",
    "レディス": "服飾",
    "スポーツ・アウトドア": "服飾",
    "インテリア・生活雑貨": "居家雜貨",
    "サービス・カルチャー・その他": "服務・其他",
}

# 行程上會用到的店，在頁面上標星號
STARRED = {
    "アカチャンホンポ": "Day 1 買 Cybex Melio 推車",
    "ババ・ガンプ・シュリンプ": "Day 1 18:00 晚餐（已訂位）",
    "ALOHA TABLE": "Day 2 19:00 晚餐（已訂位）",
    "Royal Garden Cafe&TAVERN": "Day 2 晚餐備案",
}

FLOOR_ORDER = ["B1", "1F", "2F", "3F", "4F"]


def strip_tags(s: str) -> str:
    return H.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def parse_loc(loc: str) -> tuple[str, str, str]:
    """「ららぽーと豊洲１ NORTH PORT 3F」→ ("豊洲1", "NORTH PORT", "3F")"""
    if not loc or loc == "なし":
        return ("", "", "")
    m = re.match(r"ららぽーと豊洲([１２３1-3])\s*(.*)$", loc)
    if not m:
        return ("", "", loc)
    bld = "豊洲" + {"１": "1", "２": "2", "３": "3"}.get(m.group(1), m.group(1))
    rest = m.group(2).strip()
    fm = re.search(r"(B?\d+F?|B1)$", rest)
    floor = fm.group(1) if fm else ""
    zone = rest[: fm.start()].strip() if fm else rest
    return (bld, zone, floor)


def main() -> int:
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        page = r.read().decode("utf-8", errors="replace")

    items = re.findall(r'<li class="js-item">(.*?)</li>', page, re.S)
    if not items:
        print("解析不到 js-item，官網版面可能改了", file=sys.stderr)
        return 1

    shops = []
    for it in items:
        def grab(pat: str) -> str:
            m = re.search(pat, it, re.S)
            return strip_tags(m.group(1)) if m else ""

        name = grab(r'<dt class="box-ttl">(.*?)</dt>')
        if not name:
            continue
        cat_raw = grab(r'<dd class="box-sub">(.*?)</dd>')
        loc_raw = grab(r'<dd class="box-dtl ico-floor">(.*?)</dd>')
        href = re.search(r'href="([^"]+)"', it)
        bld, zone, floor = parse_loc(loc_raw)

        shops.append({
            "name": name,
            "cat": CAT_MAP.get(cat_raw.split("/")[0], "服務・其他"),
            "catRaw": cat_raw,
            "bld": bld,
            "zone": zone,
            "floor": floor,
            "url": SITE + href.group(1) if href else "",
            "star": STARRED.get(name, ""),
        })

    # 官網本身會列出同名多筆，多數是真的（セブン銀行ATM 有 5 台分散各層、
    # ZARA 跨 1F/2F、フレッシュネスバーガー 有獨立店與美食廣場店）。
    # 只有「店名＋樓層＋類別」完全相同的才是重複，那種才合併。
    seen: set[tuple[str, ...]] = set()
    deduped = []
    for s in shops:
        key = (s["name"], s["bld"], s["zone"], s["floor"], s["catRaw"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(s)
    if len(deduped) != len(shops):
        print(f"合併了 {len(shops) - len(deduped)} 筆完全重複")
    shops = deduped

    shops.sort(key=lambda s: (
        s["bld"], s["zone"],
        FLOOR_ORDER.index(s["floor"]) if s["floor"] in FLOOR_ORDER else 99,
        s["name"],
    ))

    OUT.write_text(json.dumps({"source": URL, "shops": shops},
                              ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")

    from collections import Counter
    print(f"shops.json 已更新　{len(shops)} 家店　{OUT.stat().st_size / 1024:.0f} KB")
    for k, v in Counter(f'{s["bld"]} {s["zone"]} {s["floor"]}'.strip() for s in shops).most_common():
        print(f"  {v:>3}  {k}")
    missing = [n for n in STARRED if not any(s["name"] == n for s in shops)]
    if missing:
        print("⚠️ 標星的店沒對到：" + "、".join(missing), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
