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

# 片假名 → 羅馬字。給「打拉丁字母找日文店名」用，不求標準只求找得到。
KANA_ROMAJI = [
    ("キャ", "kya"), ("キュ", "kyu"), ("キョ", "kyo"),
    ("シャ", "sha"), ("シュ", "shu"), ("ショ", "sho"),
    ("チャ", "cha"), ("チュ", "chu"), ("チョ", "cho"),
    ("ニャ", "nya"), ("ニュ", "nyu"), ("ニョ", "nyo"),
    ("ヒャ", "hya"), ("ヒュ", "hyu"), ("ヒョ", "hyo"),
    ("ミャ", "mya"), ("ミュ", "myu"), ("ミョ", "myo"),
    ("リャ", "rya"), ("リュ", "ryu"), ("リョ", "ryo"),
    ("ギャ", "gya"), ("ギュ", "gyu"), ("ギョ", "gyo"),
    ("ジャ", "ja"), ("ジュ", "ju"), ("ジョ", "jo"),
    ("ビャ", "bya"), ("ビュ", "byu"), ("ビョ", "byo"),
    ("ピャ", "pya"), ("ピュ", "pyu"), ("ピョ", "pyo"),
    ("ティ", "ti"), ("ディ", "di"), ("トゥ", "tu"), ("ドゥ", "du"),
    ("ファ", "fa"), ("フィ", "fi"), ("フェ", "fe"), ("フォ", "fo"),
    ("ヴァ", "va"), ("ヴィ", "vi"), ("ヴェ", "ve"), ("ヴォ", "vo"), ("ヴ", "v"),
    ("シェ", "she"), ("ジェ", "je"), ("チェ", "che"), ("ツァ", "tsa"), ("ツォ", "tso"),
    ("ア", "a"), ("イ", "i"), ("ウ", "u"), ("エ", "e"), ("オ", "o"),
    ("カ", "ka"), ("キ", "ki"), ("ク", "ku"), ("ケ", "ke"), ("コ", "ko"),
    ("サ", "sa"), ("シ", "shi"), ("ス", "su"), ("セ", "se"), ("ソ", "so"),
    ("タ", "ta"), ("チ", "chi"), ("ツ", "tsu"), ("テ", "te"), ("ト", "to"),
    ("ナ", "na"), ("ニ", "ni"), ("ヌ", "nu"), ("ネ", "ne"), ("ノ", "no"),
    ("ハ", "ha"), ("ヒ", "hi"), ("フ", "fu"), ("ヘ", "he"), ("ホ", "ho"),
    ("マ", "ma"), ("ミ", "mi"), ("ム", "mu"), ("メ", "me"), ("モ", "mo"),
    ("ヤ", "ya"), ("ユ", "yu"), ("ヨ", "yo"),
    ("ラ", "ra"), ("リ", "ri"), ("ル", "ru"), ("レ", "re"), ("ロ", "ro"),
    ("ワ", "wa"), ("ヰ", "i"), ("ヱ", "e"), ("ヲ", "o"), ("ン", "n"),
    ("ガ", "ga"), ("ギ", "gi"), ("グ", "gu"), ("ゲ", "ge"), ("ゴ", "go"),
    ("ザ", "za"), ("ジ", "ji"), ("ズ", "zu"), ("ゼ", "ze"), ("ゾ", "zo"),
    ("ダ", "da"), ("ヂ", "ji"), ("ヅ", "zu"), ("デ", "de"), ("ド", "do"),
    ("バ", "ba"), ("ビ", "bi"), ("ブ", "bu"), ("ベ", "be"), ("ボ", "bo"),
    ("パ", "pa"), ("ピ", "pi"), ("プ", "pu"), ("ペ", "pe"), ("ポ", "po"),
    ("ァ", "a"), ("ィ", "i"), ("ゥ", "u"), ("ェ", "e"), ("ォ", "o"),
    ("ャ", "ya"), ("ュ", "yu"), ("ョ", "yo"), ("ー", ""), ("ッ", ""),
]

# 品牌的拉丁字母／中文寫法跟羅馬字拼不起來的，手動補別名。
# 只列旅客實際會打的。鍵要跟官網店名完全一致。
ALIASES = {
    "ユニクロ": "uniqlo",
    "無印良品": "muji mujirushi",
    "ザ・ダイソー": "daiso",
    "ハンズ": "hands tokyu hands",
    "トイザらス": "toysrus toys r us",
    "ゴディバ": "godiva",
    "ゴディパン": "godiva godipan",
    "スターバックスコーヒー　シーサイドデッキ店": "starbucks",
    "スターバックスコーヒー サウスポート2階店": "starbucks",
    "スターバックスコーヒー 地下１階店": "starbucks",
    "サンマルクカフェ": "st marc saint marc",
    "ケンタッキーフライドチキン": "kfc kentucky",
    "クリスピー・クリーム・ドーナツ": "krispy kreme",
    "サーティワンアイスクリーム": "31 baskin robbins",
    "フレッシュネスバーガー": "freshness burger",
    "ババ・ガンプ・シュリンプ": "bubba gump shrimp",
    "ゴンチャ": "gong cha",
    "カルディコーヒーファーム": "kaldi",
    "珈琲所 コメダ珈琲店": "komeda",
    "ルピシア": "lupicia",
    "ドンク": "donq",
    "築地銀だこ": "gindako tsukiji",
    "京鼎樓": "jin din rou",
    "中国火鍋専門店 小肥羊": "little sheep xiaofeiyang",
    "とんかつ新宿さぼてん": "saboten",
    "日本橋 天丼 金子半之助": "kaneko hannosuke",
    "宮武讃岐うどん": "miyatake sanuki udon",
    "東京スタイルみそラーメン ど・みそ": "domiso miso ramen",
    "富澤商店": "tomiz tomizawa",
    "成城石井": "seijo ishii",
    "アカチャンホンポ": "akachan honpo akachanhonpo",
    "ゲンキ・キッズ": "genki kids",
    "プティマイン": "petit main petitmain",
    "アプレ レ クール": "apres les cours",
    "グローバルワーク": "global work globalwork",
    "ローリーズファーム": "lowrys farm",
    "ナチュラルビューティーベーシック": "natural beauty basic nbb",
    "ジャーナル スタンダード レリューム": "journal standard relume",
    "ユナイテッドアローズ グリーンレーベル リラクシング": "united arrows green label relaxing",
    "ビューティー＆ユース ユナイテッドアローズ": "beauty youth united arrows",
    "コラージュ ガリャルダガランテ": "collage gallardagalante",
    "ポロラルフローレン": "polo ralph lauren",
    "トミー ヒルフィガー": "tommy hilfiger",
    "サムソナイト": "samsonite",
    "レスポートサック": "lesportsac",
    "サックスバー": "sacsbar sac's bar",
    "オークリーストア": "oakley",
    "コロンビア スポーツウェア": "columbia",
    "スーパースポーツゼビオ": "xebio super sports",
    "ヴィクトリアゴルフ": "victoria golf",
    "ドゥ・スポーツプラザ": "do sports plaza",
    "フランフラン": "francfranc",
    "アフタヌーンティー・リビング": "afternoon tea living",
    "カリモク60": "karimoku",
    "ジンズ": "jins",
    "メガネスーパー": "megane super",
    "ラフィネ": "raffine",
    "ウエルシア薬局": "welcia",
    "ウエルシア": "welcia",
    "ノジマ": "nojima",
    "有隣堂": "yurindo",
    "島村楽器": "shimamura",
    "ドコモショップ": "docomo",
    "ファミマ！!": "famima familymart",
    "キッザニア東京": "kidzania",
    "ユナイテッド・シネマ豊洲": "united cinemas",
    "千葉銀行": "chiba bank",
    "三井のリハウス": "mitsui rehouse",
    "靴下屋": "tabio kutsushitaya",
    "100本のスプーン": "100 spoons",
    "アーバンドック ららぽーと豊洲": "urban dock lalaport toyosu",
    "整体×骨盤 カラダファクトリー": "karada factory",
    "韓美膳（ハンビジェ）": "hanbijae",
    "イング": "ing",
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


def to_romaji(s: str) -> str:
    """把店名裡的片假名轉成羅馬字。平假名先轉片假名，漢字原樣留著。"""
    s = "".join(
        chr(ord(c) + 0x60) if "ぁ" <= c <= "ゖ" else c
        for c in s
    )
    for kana, roma in KANA_ROMAJI:
        s = s.replace(kana, roma)
    return "".join(c for c in s.lower() if c.isascii() and c.isalnum())


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

        # 搜尋用字串：店名 + 羅馬字 + 手動別名 + 類別，前端只比對這一欄
        alias = ALIASES.get(name, "")
        search = " ".join(filter(None, [name, to_romaji(name), alias, cat_raw]))

        shops.append({
            "name": name,
            "cat": CAT_MAP.get(cat_raw.split("/")[0], "服務・其他"),
            "catRaw": cat_raw,
            "bld": bld,
            "zone": zone,
            "floor": floor,
            "url": SITE + href.group(1) if href else "",
            "star": STARRED.get(name, ""),
            "s": search,
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
    names = {s["name"] for s in shops}
    for label, keys in (("標星", STARRED), ("別名", ALIASES)):
        bad = [n for n in keys if n not in names]
        if bad:
            print(f"⚠️ {label}對不到店名：" + "、".join(bad), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
