#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nrv_check.py — 核对营养标签的 %NRV 算术，并比对安全上限 (UL)。

用途：识别"抄模板"标签。正经标签的 %NRV 按法规算；抄来的会算错——
尤其是"标签引用了法规却算错"，几乎可断定是拼凑的。

示例
----
# 看某产品的实际数值与应有 %NRV，并做 UL 检查
python3 nrv_check.py --label folate=1000ug --label b6=50mg --label b12=500ug --ul

# 与标签上印的 %NRV 对比（找出算错的那一行）
python3 nrv_check.py --label folate=1000ug --claimed folate=270
python3 nrv_check.py --label b6=50mg --claimed b6=3571
python3 nrv_check.py --label b12=500ug --claimed b12=20000

# 覆盖参考量
python3 nrv_check.py --label folate=1000ug --nrv folate=200ug

仅依赖标准库。
"""

import argparse
import re
import sys

# ---------------------------------------------------------------- 参考量表
# 欧盟 (EU) No 1169/2011 Annex XIII Part A
EU_NRV = {
    "vitamin_a": (800, "ug"), "vitamin_d": (5, "ug"), "vitamin_e": (12, "mg"),
    "vitamin_k": (75, "ug"), "vitamin_c": (80, "mg"), "thiamin": (1.1, "mg"),
    "riboflavin": (1.4, "mg"), "niacin": (16, "mg"), "b6": (1.4, "mg"),
    "folate": (200, "ug"), "b12": (2.5, "ug"), "biotin": (50, "ug"),
    "pantothenic_acid": (6, "mg"), "calcium": (800, "mg"), "magnesium": (375, "mg"),
    "iron": (14, "mg"), "zinc": (10, "mg"), "iodine": (150, "ug"),
    "selenium": (55, "ug"), "copper": (1, "mg"), "manganese": (2, "mg"),
    "potassium": (2000, "mg"), "chloride": (800, "mg"), "phosphorus": (700, "mg"),
}

# 美国 Daily Value (21 CFR 101.9)，仅作对照
US_DV = {
    "folate": (400, "ug"), "b6": (1.7, "mg"), "b12": (2.4, "ug"),
    "vitamin_c": (90, "mg"), "vitamin_d": (20, "ug"), "calcium": (1300, "mg"),
    "iron": (18, "mg"), "zinc": (11, "mg"),
}

# 成人可耐受最高摄入量 (UL)
UL = {
    "b6": (12, "mg", "EFSA 2023（此前为 25 mg）；长期超量可致周围神经病变；超 UL 的补充剂在欧盟须加警示标示"),
    "folate": (1000, "ug", "SCF/EFSA（合成叶酸）；可掩盖维生素 B12 缺乏"),
    "vitamin_a": (3000, "ug", "SCF；肝毒性、骨密度下降、致畸"),
    "vitamin_d": (100, "ug", "EFSA；高钙血症"),
    "vitamin_e": (300, "mg", "SCF；出血倾向"),
    "selenium": (300, "ug", "SCF；硒中毒（脱发、指甲变形）"),
    "zinc": (25, "mg", "SCF；铜缺乏、免疫抑制"),
    "copper": (5, "mg", "SCF"),
    "iodine": (600, "ug", "SCF"),
    "niacin": (900, "mg", "SCF（烟酸形式）；US IOM 为 35 mg（潮红反应）"),
    "vitamin_c": (2000, "mg", "SCF"),
    "iron": (45, "mg", "US IOM；胃肠刺激、铁过载；女性经期外补充需谨慎"),
    "manganese": (11, "mg", "US IOM"),
    "phosphorus": (4000, "mg", "US IOM"),
    "chloride": (3600, "mg", "US IOM"),
    "calcium": (2500, "mg", "US IOM；高钙血症、肾结石风险"),
    "magnesium": (350, "mg", "US IOM（补充剂形式，非食物来源）；腹泻"),
}

# ⚠️ 以下**不是 UL**。这些营养素 IOM / EFSA 均**未设定**可耐受最高摄入量(UL)。
# 表中数值取自各国「参考上限 / 指导水平」(英国 EVM SRL、欧盟/法国建议上限等)，
# 其含义与法律效力都不同于 UL —— **不得**据此判定"超标需警示"或"产品不安全"。
# 用途：仅当剂量明显高于该参考值时，提示"值得留意"，并注明非监管限值。
SOFT_LIMITS = {
    # 值, 单位, 出处与说明
    "potassium":        (4700, "mg", "⚠️ 非 UL：4700 mg 是 IOM 的『适宜摄入量(AI)』，不是 UL；美国膳食钾未设 UL"),
    "biotin":           (900,  "ug", "⚠️ 非 UL：IOM(1998) 与 EFSA 均未为生物素设定 UL；900 µg 为欧盟/法国建议上限"),
    "pantothenic_acid": (200,  "mg", "⚠️ 非 UL：IOM 与 EFSA 均未设定 UL；200 mg 为欧盟/法国建议上限"),
    "thiamin":          (100,  "mg", "⚠️ 非 UL：IOM 未设定 UL；100 mg 为英国 EVM 指导水平 / 欧盟建议上限"),
    "riboflavin":       (43,   "mg", "⚠️ 非 UL：IOM(1998) 未设定 UL；43 mg 为欧盟/法国建议上限（EVM 为 40 mg）"),
    "vitamin_k":        (200,  "ug", "⚠️ 非 UL：IOM 未设定 UL（LPI 明确 'no UL has been established'）；200 µg 为欧盟/法国建议上限"),
}

# 无 UL、亦无公认参考上限的营养素：仅提示"该国未设定 UL"，不参与任何超限判定
NO_UL = {"b12"}

ALIASES = {
    "folate": "folate", "folicacid": "folate", "folic": "folate",
    "vitaminb9": "folate", "b9": "folate", "叶酸": "folate",
    "b6": "b6", "vitaminb6": "b6", "pyridoxine": "b6", "维生素b6": "b6",
    "b12": "b12", "vitaminb12": "b12", "cobalamin": "b12",
    "methylcobalamin": "b12", "维生素b12": "b12",
    "b1": "thiamin", "thiamin": "thiamin", "thiamine": "thiamin",
    "b2": "riboflavin", "riboflavin": "riboflavin",
    "b3": "niacin", "niacin": "niacin", "nicotinamide": "niacin",
    "b5": "pantothenic_acid", "pantothenicacid": "pantothenic_acid",
    "b7": "biotin", "biotin": "biotin",
    "vitamina": "vitamin_a", "vitamind": "vitamin_d", "d3": "vitamin_d",
    "vitamine": "vitamin_e", "vitamink": "vitamin_k", "k2": "vitamin_k",
    "vitaminc": "vitamin_c",
    "calcium": "calcium", "钙": "calcium",
    "magnesium": "magnesium", "镁": "magnesium",
    "iron": "iron", "铁": "iron",
    "zinc": "zinc", "锌": "zinc",
    "iodine": "iodine", "碘": "iodine",
    "selenium": "selenium", "硒": "selenium",
    "copper": "copper", "铜": "copper",
    "manganese": "manganese", "锰": "manganese",
    "potassium": "potassium", "钾": "potassium",
    "phosphorus": "phosphorus", "磷": "phosphorus",
    "chloride": "chloride",
}

UNIT_G = {"g": 1.0, "mg": 1e-3, "ug": 1e-6, "mcg": 1e-6, "µg": 1e-6,
          "μg": 1e-6, "ng": 1e-9}

AMOUNT_RE = re.compile(r"^\s*([0-9]+(?:[.,][0-9]+)?)\s*([a-zA-Zµμ]+)\s*$")


def norm_key(name):
    k = re.sub(r"[\s_\-()（）]+", "", name.strip().lower())
    k = k.replace("vit.", "vitamin")
    if k in ALIASES:
        return ALIASES[k]
    m = re.fullmatch(r"(?:vitamin)?([a-z]?\d{1,2})", k)
    if m and m.group(1) in ALIASES:
        return ALIASES[m.group(1)]
    return k


def parse_amount(text):
    """'1000ug' / '50 mg' / '1,4mg' -> 克（float）；不是含量则返回 None"""
    m = AMOUNT_RE.match(text)
    if not m:
        return None
    unit = m.group(2).lower().replace("μ", "µ")
    if unit not in UNIT_G:
        return None
    return float(m.group(1).replace(",", ".")) * UNIT_G[unit]


def to_unit(grams, unit):
    return grams / UNIT_G[unit]


def fmt(v):
    if v >= 1000:
        return f"{v:,.0f}"
    if v >= 10:
        return f"{v:.0f}"
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s if s else "0"


def parse_kv(items, want_amount):
    """返回 {key: 克 或 数字}"""
    out = {}
    for it in items or []:
        if "=" not in it:
            print(f"  ⚠ 忽略无法解析的参数: {it}", file=sys.stderr)
            continue
        k, v = it.split("=", 1)
        key = norm_key(k)
        if want_amount:
            g = parse_amount(v)
            if g is None:
                print(f"  ⚠ 忽略无法解析的含量: {it}", file=sys.stderr)
                continue
            out[key] = g
        else:
            try:
                out[key] = float(v.replace(",", ".").replace("%", "").strip())
            except ValueError:
                print(f"  ⚠ 忽略无法解析的百分比: {it}", file=sys.stderr)
    return out


def main():
    ap = argparse.ArgumentParser(
        description="核对营养标签 %NRV 算术，并比对安全上限 UL",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--label", action="append", metavar="NUTRIENT=AMOUNT",
                    help="每份实际含量，如 folate=1000ug（可重复）")
    ap.add_argument("--claimed", action="append", metavar="NUTRIENT=PCT",
                    help="标签上印的 %%NRV，如 folate=270（可重复）")
    ap.add_argument("--nrv", action="append", metavar="NUTRIENT=AMOUNT",
                    help="覆盖参考量，如 folate=200ug（可重复）")
    ap.add_argument("--standard", choices=["eu", "us"], default="eu",
                    help="参考量标准（默认 eu）")
    ap.add_argument("--ul", action="store_true", help="做安全上限 UL 检查")
    ap.add_argument("--lang", choices=["zh", "en"], default="zh")
    args = ap.parse_args()

    labels = parse_kv(args.label, True)
    claimed = parse_kv(args.claimed, False)
    if not labels:
        ap.print_help()
        return 1

    # 参考量统一为 {key: (显示值, 显示单位, 克)}
    table = EU_NRV if args.standard == "eu" else US_DV
    nrv = {k: (v, u, v * UNIT_G[u]) for k, (v, u) in table.items()}
    for k, g in parse_kv(args.nrv, True).items():
        nrv[k] = (to_unit(g, "mg"), "mg", g)

    std_name = "EU 1169/2011 Annex XIII" if args.standard == "eu" else "US Daily Value"
    print()
    print(f"参考量标准 / Standard: {std_name}")
    print("=" * 86)
    print(f"{'营养素':<18}{'每份含量':>14}{'应有%NRV':>11}{'标签所标':>11}   {'判定':<22}参考量")
    print("-" * 86)

    problems = []
    for key, grams in labels.items():
        if key not in nrv:
            print(f"{key:<18}{fmt(to_unit(grams,'mg'))+' mg':>14}{'—':>11}{'—':>11}"
                  f"   {'（无参考量，跳过）':<22}")
            continue
        nv, nu, ng = nrv[key]
        pct = grams / ng * 100.0
        shown = f"{fmt(to_unit(grams, nu))} {nu}"
        cl = claimed.get(key)
        if cl is None:
            print(f"{key:<18}{shown:>14}{fmt(pct)+'%':>11}{'—':>11}"
                  f"   {'（标签未提供）':<22}{fmt(nv)}{nu}")
        else:
            rel = abs(cl - pct) / pct * 100 if pct else 0
            if rel <= 2:
                verdict = "✅ 吻合"
            else:
                verdict = f"❌ 不符(差{cl-pct:+.0f})"
                problems.append((key, pct, cl))
            print(f"{key:<18}{shown:>14}{fmt(pct)+'%':>11}{fmt(cl):>11}"
                  f"   {verdict:<22}{fmt(nv)}{nu}")

    if args.ul:
        print()
        print("-" * 86)
        print("安全上限 (UL) 检查")
        print("-" * 86)
        any_ul = False
        for key, grams in labels.items():
            if key not in UL:
                continue
            any_ul = True
            uv, uu, note = UL[key]
            ug = uv * UNIT_G[uu]
            ratio = grams / ug
            flag = "✅ 低于 UL" if ratio <= 1 else ("⚠️ 超 UL" if ratio <= 2 else "🔴 显著超 UL")
            print(f"  {key:<14} 本品 {fmt(to_unit(grams,uu))} {uu} / UL {fmt(uv)} {uu}"
                  f"  → UL 的 {ratio*100:.0f}%   {flag}")
            if ratio > 1:
                print(f"      ↳ {note}")
                print(f"      ↳ 提示：超 UL 的补充剂在该国通常须加警示标示，请核对标签是否印有警示。")
        if not any_ul:
            print("  （所测营养素均无可查 UL）")

        # ---- 非 UL 的参考上限（仅提示，不构成监管判定）----
        soft = [(k, g) for k, g in labels.items() if k in SOFT_LIMITS]
        if soft:
            print()
            print("非 UL 的『参考上限』（informational only — 不是监管限值，不得据此判定违规）")
            print("-" * 86)
            for key, grams in soft:
                sv, su, note = SOFT_LIMITS[key]
                sg = sv * UNIT_G[su]
                ratio = grams / sg
                mark = "（高于参考值，值得留意）" if ratio > 1 else "（低于参考值）"
                print(f"  {key:<14} 本品 {fmt(to_unit(grams,su))} {su} / 参考 {fmt(sv)} {su}"
                      f"  → 参考值的 {ratio*100:.0f}%   {mark}")
                print(f"      ↳ {note}")
            print("  ⚠️ 这些营养素在 IOM/EFSA 均**无 UL**；上表数值来自各国建议上限/指导水平，")
            print("     与 UL 含义不同。**不可**据此写『超标』或『产品不安全』。")

        for key in labels:
            if key in NO_UL:
                print(f"  ℹ️  {key}：该国未设定 UL（IOM/EFSA 均未建立），不做超限判定。")

    print()
    print("=" * 86)
    if problems:
        print("🔴 结论：标签自报的 %NRV 与按法规计算不一致 → 强烈的『抄模板』信号。")
        print("   若标签同时注明『according to Regulation (EU) no 1169/2011』，")
        print("   则属『引用了法规却算错法规』，是贴牌套模板的典型痕迹。")
        for k, should, got in problems:
            print(f"     - {k}: 应为 {should:.0f}%，标签标 {got:.0f}%")
    else:
        print("✅ 结论：所检项目的 %NRV 与计算结果一致（该标签在算术层面是规范的）。")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
