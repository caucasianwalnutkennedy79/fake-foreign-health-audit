#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lnhpd_search.py — 加拿大 Health Canada「已许可天然健康产品数据库」(LNHPD) 检索。

为什么这个脚本价值最高
----------------------
加拿大天然健康产品(NHP)**上市前必须取得许可**，标签必须印 **NPN**。
许可持有人、成分剂量、许可日期、市场状态全部公开可查 —— 是"假洋货"鉴别中
最好用的一击命中式核查。

示例
----
python3 lnhpd_search.py --brand "LOEON"
python3 lnhpd_search.py --company "Bethune Health Develops Limited" --summary-only
python3 lnhpd_search.py --npn 80145377 --detail          # 抓详情页，含 Market status
python3 lnhpd_search.py --brand LOEON --detail --limit 5
python3 lnhpd_search.py --refresh                        # 强制重下数据（约 140 MB）

仅依赖标准库。
"""

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

API = ("https://health-products.canada.ca/api/natural-licences/"
       "ProductLicence/?lang=en&type=json")
DETAIL = "https://health-products.canada.ca/lnhpd-bdpsnh/info?licence={npn}&lang={lang}"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")

DEFAULT_CACHE = os.path.join(os.path.expanduser("~"), ".cache", "lnhpd")
MAX_AGE_DAYS = 14


def fetch(url, timeout=300):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept-Language": "en-CA,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            import gzip
            data = gzip.decompress(data)
        elif r.headers.get("Content-Encoding") == "deflate":
            import zlib
            data = zlib.decompress(data)
        return data


def ensure_dataset(cache_dir, refresh=False):
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, "ProductLicence.json")
    if refresh or not os.path.exists(path):
        print(f"↓ 下载 LNHPD 全量数据（约 140 MB）… 这是首次运行，请稍候", file=sys.stderr)
        data = fetch(API)
        with open(path, "wb") as f:
            f.write(data)
        print(f"  已保存到 {path}", file=sys.stderr)
    else:
        age = (time.time() - os.path.getmtime(path)) / 86400
        if age > MAX_AGE_DAYS:
            print(f"⚠ 本地缓存已 {age:.0f} 天（>{MAX_AGE_DAYS} 天），建议 --refresh",
                  file=sys.stderr)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def unique_rows(rows):
    """同一 NPN 会因多个品牌名出现多行，按 (NPN, 品牌名) 去重。"""
    seen, out = set(), []
    for r in rows:
        k = (r.get("licence_number"), r.get("product_name"))
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def group_by_npn(rows):
    g = {}
    for r in rows:
        g.setdefault(r["licence_number"], {"_names": [], "_holders": set(),
                                           "_first": r})
        e = g[r["licence_number"]]
        if r.get("product_name") not in e["_names"]:
            e["_names"].append(r.get("product_name"))
        e["_holders"].add(r.get("company_name"))
    return g


def parse_detail(npn, lang="eng"):
    """抓许可详情页，返回 dict（含 Market status / 许可状态 / 成分表）。"""
    try:
        raw = fetch(DETAIL.format(npn=npn, lang=lang), timeout=60).decode("utf-8", "replace")
    except Exception as e:                                    # noqa: BLE001
        return {"error": str(e)}

    s = re.sub(r"(?is)<(script|style|nav|header|footer).*?</\1>", " ", raw)
    t = html.unescape(re.sub(r"(?s)<[^>]+>", "\n", s))
    lines, out = [], []
    for l in (x.strip() for x in t.split("\n")):
        if l and (not out or out[-1] != l):
            out.append(l)

    res = {"npn": npn, "raw_lines": out}

    def after(label, n=1):
        for i, x in enumerate(out):
            if x.rstrip(":") == label.rstrip(":"):
                j = i + 1
                while j < len(out) and out[j] == ":":
                    j += 1
                return out[j] if j < len(out) else ""
            if x.startswith(label):
                return x[len(label):].lstrip(": ").strip()
        return ""

    res["market_status"] = after("Market status")
    res["licence_status"] = after("Licence Status")
    res["holder"] = after("Licence holder")
    res["dosage_form"] = after("Dosage Form")
    res["licensed"] = after("Date of licensing")
    res["revised"] = after("Revised date of licence")

    # 成分表：容错匹配（页面标题可能带冒号或空格差异）
    def find_idx(*needles):
        for i, x in enumerate(out):
            xn = x.rstrip(":").strip().lower()
            for nd in needles:
                if xn == nd.lower() or xn.startswith(nd.lower()):
                    return i
        return -1

    i_med = find_idx("List of medicinal ingredients")
    i_non = find_idx("List of non-medicinal ingredients")
    i_date = find_idx("Date of licensing")

    if i_med >= 0:
        end = i_non if i_non > i_med else (i_date if i_date > i_med else len(out))
        res["medicinal_ingredients"] = [x for x in out[i_med + 1:end] if x != ":"]
    else:
        res["medicinal_ingredients"] = []

    if i_non >= 0:
        end = i_date if i_date > i_non else len(out)
        res["non_medicinal_ingredients"] = [x for x in out[i_non + 1:end] if x != ":"]
    else:
        res["non_medicinal_ingredients"] = []
    return res


def main():
    ap = argparse.ArgumentParser(
        description="LNHPD（加拿大已许可天然健康产品数据库）检索",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--brand", help="品牌/产品名关键词（不区分大小写，子串匹配）")
    ap.add_argument("--company", help="许可持有人关键词")
    ap.add_argument("--npn", help="按 NPN 精确查询")
    ap.add_argument("--detail", action="store_true",
                    help="抓取详情页（含 Market status、官方成分剂量）")
    ap.add_argument("--summary-only", action="store_true", help="只输出按 NPN 汇总的表")
    ap.add_argument("--limit", type=int, default=40, help="详情抓取上限（默认 40）")
    ap.add_argument("--refresh", action="store_true", help="强制重下全量数据")
    ap.add_argument("--cache-dir", default=DEFAULT_CACHE)
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    if not (args.brand or args.company or args.npn):
        ap.print_help()
        return 1

    data = ensure_dataset(args.cache_dir, args.refresh)
    rows = data

    if args.npn:
        rows = [r for r in rows if str(r.get("licence_number")) == str(args.npn)]
    if args.brand:
        kw = args.brand.lower()
        rows = [r for r in rows if kw in str(r.get("product_name", "")).lower()]
    if args.company:
        kw = args.company.lower()
        rows = [r for r in rows if kw in str(r.get("company_name", "")).lower()]

    rows = unique_rows(rows)
    if not rows:
        print("\n❌ 未检索到任何记录。")
        print("   注意：加拿大 NHP 必须有 NPN 才能合法销售；查无记录本身是重要发现，")
        print("   但请确认关键词拼写（建议先用品牌名或公司名子串试）。\n")
        return 0

    groups = group_by_npn(rows)
    print(f"\n命中 {len(rows)} 行 / {len(groups)} 个 NPN\n")

    if args.summary_only and not args.detail:
        print(f"{'NPN':<11}{'许可日':<12}{'状态':<6}{'持证人':<38}品牌名")
        print("-" * 110)
        for npn, e in sorted(groups.items()):
            r = e["_first"]
            print(f"{npn:<11}{str(r.get('licence_date'))[:10]:<12}"
                  f"{str(r.get('flag_product_status')):<6}"
                  f"{'; '.join(sorted(e['_holders']))[:36]:<38}"
                  f"{'; '.join(e['_names'])[:60]}")
        print()
        return 0

    # ------------------------------------------------------------ 详情
    out_json = []
    for i, (npn, e) in enumerate(sorted(groups.items())):
        r = e["_first"]
        print("=" * 100)
        print(f"NPN {npn}")
        print(f"  品牌名      : {'; '.join(e['_names'])}")
        print(f"  许可持有人  : {'; '.join(sorted(e['_holders']))}")
        print(f"  许可日期    : {str(r.get('licence_date'))[:10]}"
              f"   修订: {str(r.get('revised_date'))[:10]}")
        print(f"  许可状态    : flag_product_status={r.get('flag_product_status')}"
              f"   (1 = active)")

        if args.detail and i < args.limit:
            d = parse_detail(npn)
            if "error" in d:
                print(f"  ⚠ 详情抓取失败: {d['error']}")
            else:
                print(f"  Market status: {d['market_status']}   "
                      f"Licence Status: {d['licence_status']}")
                if d.get("dosage_form"):
                    print(f"  剂型        : {d['dosage_form']}")
                if d.get("licensed"):
                    print(f"  许可日期(页): {d['licensed']}")
                mi = [x for x in d.get("medicinal_ingredients", []) if x]
                if mi:
                    print(f"  官方成分剂量: {' | '.join(mi[:24])}")
                nmi = [x for x in d.get("non_medicinal_ingredients", []) if x]
                if nmi:
                    print(f"  非药用成分  : {' | '.join(nmi[:20])}")
                if d["market_status"].strip().lower() == "not marketed":
                    print("  ℹ️  Not Marketed 为**自愿申报**，未申报即默认此状态，")
                    print("     不能单独证明『该国没有销售』，只能作辅证。")
                out_json.append(d)

    print("=" * 100)
    print("""
判读要点
--------
· 许可状态 active ≠ 在售；Market status 为自愿申报，默认 Not Marketed，**不可单独作否定证据**。
· 一个 NPN 挂多个品牌名 = 典型贴牌(白牌)结构。
· 许可日期与品牌宣称的历史对照 —— 宣称"1989 年创立"却 2024 年才首次拿证，即为矛盾。
· 把"官方成分剂量"与**包装上印的剂量**逐项对照 —— 不一致即标签虚标。
· 许可 NHP 标签**必须印 NPN**；包装上看不到 NPN 本身就是发现。
""")
    if args.json:
        print(json.dumps(out_json, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
