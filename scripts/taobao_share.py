#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
taobao_share.py — 解析电商「分享文本」，产出可用的商品简报。

为什么需要它
------------
淘宝/天猫/京东的**商品页需要登录态**（无头浏览器也会被重定向到 login.taobao.com，
页面含 baxia 反爬），纯 HTTP 抓不到正文。但**分享文本本身**含有用信息：
短链、商品 ID、标价、以及完整标题——而标题通常已包含品牌、品类、宣称、成分。

本脚本把分享文本解析成结构化简报，避免把「抓不到商品页」误判为「查不到品牌」。

支持：淘宝 / 天猫 / 京东 / 拼多多 分享文本与短链

示例
----
python3 taobao_share.py '【淘宝】https://e.tb.cn/h.8s02e3CGG7FyVPS?tk=xxx CZ321 「Oppuland活性叶酸…」'
python3 taobao_share.py --file share.txt --json
python3 taobao_share.py --url 'https://e.tb.cn/h.8s02e3CGG7FyVPS?tk=xxx'

仅依赖标准库。
"""

import argparse
import html
import json
import re
import sys
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")

SHORT_HOSTS = ("e.tb.cn", "m.tb.cn", "tb.cn", "u.jd.com", "3.cn")

# URL 中「不是分隔符」的字符类。用三引号原始字符串，避免 \' 这种
# 「在原始串里是两字符、在正则里又等价于单引号」的绕人写法。
NOT_URL = r"""[^\s"'<>]"""

FULL_ITEM_RE = re.compile(
    r"https?://" + NOT_URL + r"*?(?:item\.taobao\.com|detail\.tmall\.com|"
    r"item\.jd\.com|item\.m\.jd\.com|mobile\.yangkeduo\.com|yangkeduo\.com)"
    + NOT_URL + r"*")
SHORT_RE = re.compile(r"https?://(?:" + "|".join(h.replace(".", r"\.") for h in SHORT_HOSTS) +
                      r")/[A-Za-z0-9._\-]+(?:\?" + NOT_URL + r"*)?")

# 商品标题通常用「」『』包裹；【】/[] 里往往是平台名或营销词（如【淘宝】【双十一大促】），
# 因此**强模式优先**，且同类里取**最右**一个（标题一般在链接之后）。
TITLE_PATTERNS_STRONG = [re.compile(r"[「『]([^」』]{4,200})[」』]")]
TITLE_PATTERNS_WEAK = [re.compile(r"[【\[]([^】\]]{4,200})[】\]]")]

# 明显是平台名/营销词的片段，不作为标题
TITLE_NOISE = ("淘宝", "天猫", "京东", "拼多多", "抖音", "唯品会", "小红书",
               "大促", "价保", "限时", "特价", "抢购", "秒杀", "优惠", "补贴",
               "包邮", "百亿", "官方", "旗舰", "正品", "分享", "打开")

# 平台特征
PLATFORMS = [
    ("taobao", r"淘宝|taobao\.com|e\.tb\.cn|m\.tb\.cn"),
    ("tmall", r"天猫|tmall\.com"),
    ("jd", r"京东|jd\.com|jd\.hk|u\.jd\.com|3\.cn"),
    ("pdd", r"拼多多|yangkeduo|pinduoduo"),
]


def _decompress(data, enc):
    """按 Content-Encoding 解压。

    deflate 有两种实际形态，必须都试：
      · zlib 包装（RFC1950，带 2 字节头）→ zlib.decompress(data)
      · 原始 deflate（RFC1951，无头）    → zlib.decompress(data, -zlib.MAX_WBITS)
    只写前者会报 "incorrect header check"；只写后者遇到前者也会失败。
    """
    enc = (enc or "").strip().lower()
    if enc == "gzip":
        import gzip
        return gzip.decompress(data)
    if enc == "deflate":
        import zlib
        try:
            return zlib.decompress(data)                          # RFC1950
        except zlib.error:
            return zlib.decompress(data, -zlib.MAX_WBITS)         # RFC1951
    if enc == "br":
        raise RuntimeError("服务器返回 br 压缩，本脚本不支持（请改用截图或 --url）")
    return data


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept-Encoding": "gzip, deflate",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = _decompress(r.read(), r.headers.get("Content-Encoding"))
        return data.decode("utf-8", "replace"), r.geturl()


def detect_platform(text):
    for name, pat in PLATFORMS:
        if re.search(pat, text, re.I):
            return name
    return "unknown"


def resolve_short(url):
    """短链 → (真实 URL, 商品 ID, 标价)。淘宝短链页内嵌 `var url = '...'`。"""
    out = {"short_url": url, "resolved_url": None, "item_id": None,
           "price_hint": None, "reachable": False, "note": ""}
    try:
        body, final = fetch(url)
        out["reachable"] = True
    except Exception as e:                                    # noqa: BLE001
        out["note"] = f"短链请求失败：{type(e).__name__}: {e}"
        return out

    m = re.search(r"var\s+url\s*=\s*'([^']+)'", body)
    target = None
    if m:
        target = m.group(1).replace("\\/", "/")
    else:
        m2 = re.compile(r"https?://" + NOT_URL + r"*?(?:item\.taobao\.com|detail\.tmall\.com|"
                        r"item\.jd\.com)" + NOT_URL + r"*").search(body)
        if m2:
            target = html.unescape(m2.group(0))
    if not target:
        target = final
        out["note"] = "未在短链页中解析到内嵌商品 URL，已回退为最终跳转地址"

    out["resolved_url"] = target
    if target:
        idm = re.search(r"[?&](?:id|itemId|sku|wareId)=(\d{6,})", target)
        if idm:
            out["item_id"] = idm.group(1)
        pm = re.search(r"[?&](?:price|priceStr)=([\d.]+)", target)
        if pm:
            out["price_hint"] = pm.group(1)
    return out


def extract_title(text):
    """提取商品标题。

    强模式（「」『』）优先于弱模式（【】[]），同类里取**最右**一个：
    分享文本形如「【淘宝】<营销语> <链接> <口令> 「<商品标题>」」，
    标题在最后，而【】里是平台名或营销词。
    """
    for pats in (TITLE_PATTERNS_STRONG, TITLE_PATTERNS_WEAK):
        for pat in pats:
            for raw in reversed(pat.findall(text)):
                t = re.sub(r"https?://\S+", "", raw).strip()
                if len(t) < 4:
                    continue
                # 短且全是平台名/营销词 → 不是标题
                if len(t) <= 14 and any(n in t for n in TITLE_NOISE):
                    continue
                return t
    return None


def canonical_url(platform, item_id):
    if not item_id:
        return None
    return {
        "taobao": f"https://item.taobao.com/item.htm?id={item_id}",
        "tmall": f"https://detail.tmall.com/item.htm?id={item_id}",
        "jd": f"https://item.jd.com/{item_id}.html",
        "pdd": f"https://mobile.yangkeduo.com/goods.html?goods_id={item_id}",
    }.get(platform)


def main():
    ap = argparse.ArgumentParser(
        description="解析电商分享文本，产出商品简报",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("text", nargs="*", help="分享文本（可直接粘贴整段）")
    ap.add_argument("--url", help="只给一个链接")
    ap.add_argument("--file", help="从文件读取分享文本")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--lang", choices=["zh", "en"], default="zh")
    args = ap.parse_args()

    raw = " ".join(args.text) if args.text else ""
    if args.url:
        raw = (raw + " " + args.url).strip()
    if args.file:
        try:
            raw += " " + open(args.file, encoding="utf-8").read()
        except OSError as e:
            print(f"❌ 无法读取 --file {args.file}：{e}", file=sys.stderr)
            return 2
    if not raw.strip():
        ap.print_help()
        return 1

    platform = detect_platform(raw)
    title = extract_title(raw)

    # 分享文本里可能直接带完整商品链接
    full = FULL_ITEM_RE.search(raw)
    short = SHORT_RE.search(raw)

    result = {
        "platform": platform,
        "title": title,
        "item_id": None,
        "price_hint": None,
        "canonical_url": None,
        "source": None,
        "access": {},
    }

    if full:
        result["source"] = "full_url"
        u = html.unescape(full.group(0))
        result["access"]["full_url"] = u
        idm = re.search(r"[?&](?:id|itemId|wareId)=(\d{6,})", u)
        if idm:
            result["item_id"] = idm.group(1)
        pm = re.search(r"[?&](?:price|priceStr)=([\d.]+)", u)
        if pm:
            result["price_hint"] = pm.group(1)
    elif short:
        result["source"] = "short_url"
        r = resolve_short(html.unescape(short.group(0)))
        result["access"].update(r)
        result["item_id"] = r["item_id"]
        result["price_hint"] = r["price_hint"]
    else:
        result["access"]["note"] = "分享文本中未找到可识别的商品链接"

    result["canonical_url"] = canonical_url(platform, result["item_id"])

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    zh = args.lang == "zh"
    print()
    print("商品简报 / Product brief" if zh else "Product brief")
    print("=" * 72)
    print(f"  平台        : {result['platform']}")
    print(f"  商品 ID     : {result['item_id'] or '（未解析出）'}")
    print(f"  标价提示    : {result['price_hint'] or '—'}   （来自短链跳转参数，非实时价）")
    print(f"  商品标题    : {result['title'] or '（分享文本中无标题）'}")
    print(f"  规范链接    : {result['canonical_url'] or '—'}")
    print(f"  解析来源    : {result['source']}")
    if result["access"].get("note"):
        print(f"  备注        : {result['access']['note']}")

    print()
    print("-" * 72)
    print("⚠️  商品页正文**取不到是正常的**，不是故障：" if zh else "Note:")
    print("    淘宝/天猫/京东商品页需要**登录态**；无头浏览器也会被重定向到")
    print("    login.taobao.com（页面含 baxia 反爬）。纯 HTTP 只会拿到 JS 壳页。")
    print()
    print("✅  但**你不需要商品页**。按下面顺序取证即可：")
    print()
    print("  ① 【最强】让用户发**商品页截图 / 包装实拍图**")
    print("     —— 图片由视觉模型直接读取，能拿到标签原文，是最硬的证据。")
    print("  ② 用上面的**标题 + 商品 ID** 直接开始核查：")
    print("     标题里通常已含 品牌 / 品类 / 宣称 / 成分，足够定位品牌与国家。")
    print("  ③ 交叉检索**同款在其他平台**的页面（京东/天猫国际/Walmart/亚马逊），")
    print("     这些站点多半可抓；同款标题可互为佐证。")
    print("  ④ 第三方聚合站（ziyimall、315jiage、chanmama 等）常已索引商品详情，")
    print("     可作为补充，但**必须标注来源与证据强度**。")
    print()
    print("❌ 不要做的：不要把「商品页抓不到」写成「品牌查不到」——")
    print("   这两件事无关。前者是访问限制，后者才是核查结论。")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
