#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ean_check.py — 校验商品条码校验位，并解读 GS1 国家前缀。

能读出什么 / 不能读出什么
------------------------
✅ 校验位是否正确  → 正确说明号码是规范生成的，不是随手编的
✅ GS1 国家前缀    → 号码由哪个 GS1 成员组织分配
❌ 不能证明产地！ 任何国家的公司只要加入对应 GS1 组织就能拿到该前缀
⚠️ 200–299 是"受限流通/店内码"号段，**不是**正常零售条码

示例
----
python3 ean_check.py 4262366230132
python3 ean_check.py 4262366230132 6901234567892 --lang zh
python3 ean_check.py --batch codes.txt

仅依赖标准库。
"""

import argparse
import re
import sys

# GS1 前缀 -> 国家/地区（覆盖主要号段）
PREFIXES = [
    ((0, 19), "US / CA", "美国 / 加拿大"),
    ((20, 29), "Restricted distribution (in-store)", "受限流通（店内码，非零售）"),
    ((30, 39), "US", "美国"),
    ((40, 49), "Restricted distribution (in-store)", "受限流通（店内码，非零售）"),
    ((50, 59), "Coupons", "优惠券"),
    ((60, 139), "US", "美国"),
    ((200, 299), "Restricted distribution (in-store)", "受限流通（店内码，非零售）"),
    ((300, 379), "France", "法国"),
    ((380, 380), "Bulgaria", "保加利亚"),
    ((383, 383), "Slovenia", "斯洛文尼亚"),
    ((385, 385), "Croatia", "克罗地亚"),
    ((387, 387), "Bosnia and Herzegovina", "波黑"),
    ((389, 389), "Montenegro", "黑山"),
    ((400, 440), "Germany", "德国"),
    ((450, 459), "Japan", "日本"),
    ((460, 469), "Russia", "俄罗斯"),
    ((471, 471), "Taiwan", "台湾"),
    ((474, 474), "Estonia", "爱沙尼亚"),
    ((475, 475), "Latvia", "拉脱维亚"),
    ((477, 477), "Lithuania", "立陶宛"),
    ((479, 479), "Sri Lanka", "斯里兰卡"),
    ((480, 480), "Philippines", "菲律宾"),
    ((481, 481), "Belarus", "白俄罗斯"),
    ((482, 482), "Ukraine", "乌克兰"),
    ((484, 484), "Moldova", "摩尔多瓦"),
    ((485, 485), "Armenia", "亚美尼亚"),
    ((486, 486), "Georgia", "格鲁吉亚"),
    ((487, 487), "Kazakhstan", "哈萨克斯坦"),
    ((489, 489), "Hong Kong", "中国香港"),
    ((490, 499), "Japan", "日本"),
    ((500, 509), "United Kingdom", "英国"),
    ((520, 520), "Greece", "希腊"),
    ((528, 528), "Lebanon", "黎巴嫩"),
    ((529, 529), "Cyprus", "塞浦路斯"),
    ((531, 531), "North Macedonia", "北马其顿"),
    ((535, 535), "Malta", "马耳他"),
    ((539, 539), "Ireland", "爱尔兰"),
    ((540, 549), "Belgium / Luxembourg", "比利时 / 卢森堡"),
    ((560, 560), "Portugal", "葡萄牙"),
    ((569, 569), "Iceland", "冰岛"),
    ((570, 579), "Denmark", "丹麦"),
    ((590, 590), "Poland", "波兰"),
    ((594, 594), "Romania", "罗马尼亚"),
    ((599, 599), "Hungary", "匈牙利"),
    ((600, 601), "South Africa", "南非"),
    ((603, 603), "Ghana", "加纳"),
    ((609, 609), "Mauritius", "毛里求斯"),
    ((611, 611), "Morocco", "摩洛哥"),
    ((613, 613), "Algeria", "阿尔及利亚"),
    ((615, 615), "Nigeria", "尼日利亚"),
    ((616, 616), "Kenya", "肯尼亚"),
    ((618, 618), "Ivory Coast", "科特迪瓦"),
    ((619, 619), "Tunisia", "突尼斯"),
    ((620, 620), "Tanzania", "坦桑尼亚"),
    ((621, 621), "Syria", "叙利亚"),
    ((622, 622), "Egypt", "埃及"),
    ((623, 623), "Brunei", "文莱"),
    ((624, 624), "Libya", "利比亚"),
    ((625, 625), "Jordan", "约旦"),
    ((626, 626), "Iran", "伊朗"),
    ((627, 627), "Kuwait", "科威特"),
    ((628, 628), "Saudi Arabia", "沙特阿拉伯"),
    ((629, 629), "United Arab Emirates", "阿联酋"),
    ((640, 649), "Finland", "芬兰"),
    ((690, 699), "China", "中国大陆"),
    ((700, 709), "Norway", "挪威"),
    ((729, 729), "Israel", "以色列"),
    ((730, 739), "Sweden", "瑞典"),
    ((740, 745), "Central America", "中美洲"),
    ((746, 746), "Dominican Republic", "多米尼加"),
    ((750, 750), "Mexico", "墨西哥"),
    ((754, 755), "Canada", "加拿大"),
    ((759, 759), "Venezuela", "委内瑞拉"),
    ((760, 769), "Switzerland", "瑞士"),
    ((770, 770), "Colombia", "哥伦比亚"),
    ((773, 773), "Uruguay", "乌拉圭"),
    ((775, 775), "Peru", "秘鲁"),
    ((777, 777), "Bolivia", "玻利维亚"),
    ((778, 779), "Argentina", "阿根廷"),
    ((780, 780), "Chile", "智利"),
    ((784, 784), "Paraguay", "巴拉圭"),
    ((786, 786), "Ecuador", "厄瓜多尔"),
    ((789, 790), "Brazil", "巴西"),
    ((800, 839), "Italy", "意大利"),
    ((840, 849), "Spain", "西班牙"),
    ((850, 850), "Cuba", "古巴"),
    ((858, 858), "Slovakia", "斯洛伐克"),
    ((859, 859), "Czech Republic", "捷克"),
    ((860, 860), "Serbia", "塞尔维亚"),
    ((865, 865), "Mongolia", "蒙古"),
    ((867, 867), "North Korea", "朝鲜"),
    ((868, 869), "Turkey", "土耳其"),
    ((870, 879), "Netherlands", "荷兰"),
    ((880, 880), "South Korea", "韩国"),
    ((884, 884), "Cambodia", "柬埔寨"),
    ((885, 885), "Thailand", "泰国"),
    ((888, 888), "Singapore", "新加坡"),
    ((890, 890), "India", "印度"),
    ((893, 893), "Vietnam", "越南"),
    ((896, 896), "Pakistan", "巴基斯坦"),
    ((899, 899), "Indonesia", "印度尼西亚"),
    ((900, 919), "Austria", "奥地利"),
    ((930, 939), "Australia", "澳大利亚"),
    ((940, 949), "New Zealand", "新西兰"),
    ((950, 950), "GS1 Global Office", "GS1 全球总部"),
    ((955, 955), "Malaysia", "马来西亚"),
    ((958, 958), "Macau", "中国澳门"),
    ((977, 977), "ISSN (periodicals)", "ISSN（期刊）"),
    ((978, 979), "ISBN (books)", "ISBN（图书）"),
    ((980, 980), "Refund receipts", "退款收据"),
    ((981, 984), "GS1 coupons", "GS1 优惠券"),
    ((990, 999), "Coupons", "优惠券"),
]


def lookup_prefix(code):
    """解读 GS1 前缀。UPC-A (12位) 与 EAN-13 (13位) 前缀逻辑不同。GTIN-14 需剥离首位包装指示符。"""
    n = len(code)
    if n == 12:
        # UPC-A: 前缀是前 1-2 位（0-1 = US/CA）
        p1 = int(code[0])
        if p1 in (0, 1):
            return "US / CA (UPC-A)", "美国 / 加拿大（UPC-A）"
        elif p1 == 2:
            return "Restricted distribution (in-store)", "受限流通（店内码，非零售）"
        elif p1 == 3:
            return "US (UPC-A)", "美国（UPC-A）"
        elif p1 == 4:
            return "Restricted distribution (in-store)", "受限流通（店内码，非零售）"
        elif p1 == 5:
            return "Coupons", "优惠券"
        else:
            return "US (UPC-A)", "美国（UPC-A）"
    elif n == 14:
        # GTIN-14: 首位是包装指示符（0-9），不是条码本体的一部分
        # 剥离首位后，剩余 13 位按 EAN-13 逻辑查询前缀
        inner = code[1:]
        p = int(inner[:3])
        for (lo, hi), en, zh in PREFIXES:
            if lo <= p <= hi:
                return en + " (GTIN-14)", zh + "（GTIN-14）"
        return "Unknown / unassigned", "未知 / 未分配"
    else:
        # EAN-13/EAN-8: 前缀是前 3 位
        p = int(code[:3])
        for (lo, hi), en, zh in PREFIXES:
            if lo <= p <= hi:
                return en, zh
        return "Unknown / unassigned", "未知 / 未分配"


def check(code):
    """返回 (是否合法, 说明, 国家en, 国家zh)"""
    code = re.sub(r"[\s\-]", "", code)
    if not code.isdigit():
        return False, "含非数字字符", "", ""
    n = len(code)
    if n not in (8, 12, 13, 14):
        return False, f"长度 {n} 不是 EAN-8/UPC-A/EAN-13/GTIN-14", "", ""
    body, check_digit = code[:-1], int(code[-1])
    if n in (12, 13):          # UPC-A / EAN-13：从右往左 3,1,3,1...
        total = sum(int(d) * (3 if (len(body) - i) % 2 == 1 else 1)
                    for i, d in enumerate(body))
    else:                       # EAN-8 / GTIN-14
        total = sum(int(d) * (3 if (len(body) - i) % 2 == 1 else 1)
                    for i, d in enumerate(body))
    expected = (10 - total % 10) % 10
    en, zh = lookup_prefix(code if n != 12 else code)
    if expected == check_digit:
        return True, f"校验位正确（应为 {expected}）", en, zh
    return False, f"校验位错误：末位是 {check_digit}，应为 {expected}", en, zh


def main():
    ap = argparse.ArgumentParser(
        description="校验商品条码校验位并解读 GS1 国家前缀",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("codes", nargs="*", help="条码（可多个）")
    ap.add_argument("--batch", metavar="FILE", help="从文件逐行读取条码")
    ap.add_argument("--lang", choices=["zh", "en"], default="zh")
    args = ap.parse_args()

    codes = list(args.codes)
    if args.batch:
        with open(args.batch, encoding="utf-8") as f:
            codes += [l.strip() for l in f if l.strip() and not l.startswith("#")]
    if not codes:
        ap.print_help()
        return 1

    zh = args.lang == "zh"
    restrict_seen = False
    bad_seen = False

    for raw in codes:
        ok, msg, en, zhs = check(raw)
        country = zhs if zh else en
        print(f"\n条码 {raw}")
        print(f"  校验：{'✅ ' if ok else '🔴 '}{msg}")
        print(f"  前缀：{raw[:3]} → {country}")
        if "Restricted" in en or "受限" in zhs:
            restrict_seen = True
            print("  🔴 该号段为『受限流通/店内码』，**不是**面向开放零售的条码。")
            print("     → 正常零售商品不会用这个号段，属于红旗。")
        if not ok:
            bad_seen = True
        if "GS1 Global" in en:
            print("  ℹ️  950 为 GS1 全球总部号段，通常用于内部/特殊用途。")

    print()
    print("=" * 70)
    if bad_seen:
        print("🔴 存在校验位不正确的条码 → 该条码为不规范生成（可能随手编造或抄错）。")
    if restrict_seen:
        print("🔴 存在受限流通号段 → 该商品并非按开放零售渠道注册。")
    if not bad_seen and not restrict_seen:
        print("✅ 所检条码均为规范条码。")
    print()
    print("⚠️ 重要：GS1 前缀**只表示号码由哪个 GS1 成员组织分配**，")
    print("   **不能证明产地或制造地**。任何国家的公司加入对应 GS1 组织即可获得该前缀。")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
