# 可直接复制的端点与命令（含踩坑记录）

> 全部命令均在本机实测通过。**通用前提**：很多站点靠 UA / 压缩 / JS 判断爬虫，加 `--compressed` 和真实 UA 能救回一大半。
> 约定：`UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"`

---

## 0. 通用抓取骨架

```bash
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
curl -sSL --compressed -m 45 -A "$UA" -H "Accept-Language: zh-CN,zh;q=0.9" "<URL>" -o page.html -w "http:%{http_code} size:%{size_download}\n"
```

**先看 `http` 与 `size` 再下结论：**

| 现象 | 含义 | 处理 |
|---|---|---|
| `403` / `size≈3KB` 且含 "Just a moment" / "Enable JavaScript" | Cloudflare / 反爬拦截 | **标注"未获证据"，不得算作"不存在"** |
| `200` 但 `size` 很小（<10KB）且无标题 | **JS 壳页** | 换 API / 移动端接口，或标注未取证 |
| `200` 但内容乱码 | 未解压 | 加 `--compressed` |
| `000` / timeout | 网络不可达 | 检查是否是沙箱 DNS 代理（见文末） |

**JS 壳页识别**：`<title>` 为空、body 里只有 `g.alicdn.com`、`window.__INITIAL_STATE__`、`ali_analytics` 之类 → 淘宝/京东/Tmall 基本都是壳页，**取不到商品正文属正常**。

---

## 0.5 源纪律（**先读这一节，能省掉大半无用功**）

### 规则一：只用本文件列出的源

本文件里的每个端点都是**实测过**的，并标注了可用性。**不要临场另找站点**——那类站点（药品库、商标聚合站、企业黄页）绝大多数上了反爬，试了也是白试。

> **反例（真实发生）**：为查一个德国保健品，去查了 `gelbe-liste.de`——那是**德国药品**数据库（Arzneimittel），
> 对膳食补充剂本就没什么收录，而且**不在本 skill 的任何推荐列表里**。结果超时被 SIGTERM 杀掉，白耗一轮。

### 规则二：单个源最多试一次，失败就走退路链

```
官方库 → 官方库的移动端/API → 搜索引擎摘要 → 第三方聚合（标注置信度）
```

**不要对同一个站点反复重试、换 UA、加超时**。本文件对每个源都写了已知状态与退路，照着换下一条即可。

### 规则三：给足超时预算，但别把超时当结论

| 场景 | 建议 |
|---|---|
| 单次 curl | `-m 45`（大文件如下载 LNHPD 全量数据用 `-m 300`） |
| **整个任务的执行预算** | 查 3–5 个源通常要 **2–5 分钟**；若你的 exec 超时更短，**会被 SIGTERM 杀掉**——那是**你的超时**，不是站点不可用 |
| 被 SIGTERM 时 | 在报告里写「**未完成**」，**不要**写「该源不存在 / 未查到」 |

> 🔴 **SIGTERM ≠ 未获证据**。前者是本地超时中断，后者是真的查过了。两者在报告里的措辞完全不同。

### 规则四：失败必须原样记录，不得升级为结论

| 实际发生 | 可以写 | **不可以**写 |
|---|---|---|
| 403 / Cloudflare | 「该渠道被拦截，未获证据」 | 「该品牌不存在」 |
| TLS/连接失败 | 「端点不可达，改用搜索引擎摘要」 | 「查无此商标」 |
| 本地 SIGTERM | 「本轮未完成，需延长超时重试」 | 「未查到相关信息」 |

### 已实测**不可靠**的端点（别再试）

| 端点 | 状态 |
|---|---|
| `trademark.trademarkia.com` | 🔴 TLS 层失败，完全不可达 |
| `companyhouse.de` | ❌ 403 |
| `handelsregister.ai` | ❌ 403（但 URL 路径自带行业分类，可作旁证） |
| `docmorris.de` | ❌ 403 |
| `well.ca` | ❌ 403 |
| `walmart.ca` | ❌ 人机验证 |
| `shoppersdrugmart.ca` | ❌ 403 |
| `tsdrapi.uspto.gov` | ❌ 401（需 API key） |

---

## 1. 加拿大 LNHPD（最高价值）

### 1.1 全量许可 JSON（资源名首字母**必须大写**）

```bash
# 正确（大写 ProductLicence）
curl -sSL -m 300 "https://health-products.canada.ca/api/natural-licences/ProductLicence/?lang=en&type=json" -o lnhpd.json

# 错误写法会 500 "Configuration Error"：
#   /api/natural-licences/?lang=en&type=json
```

- 文件约 **140 MB / 30 万行**（一行一个「许可 × 品牌名」）
- 其他可用资源（同样大写）：`MedicinalIngredient`、`NonMedicinalIngredient`、`ProductDose`、`ProductPurpose`、`ProductRisk`、`ProductRoute`
- ❌ **没有** `Company` 资源（404）

建议直接用封装脚本：

```bash
python3 {baseDir}/scripts/lnhpd_search.py --brand "LOEON"
python3 {baseDir}/scripts/lnhpd_search.py --company "Bethune Health Develops Limited" --summary-only
```

数据集元信息（含全部资源 URL）：

```bash
curl -sSL "https://open.canada.ca/data/api/3/action/package_show?id=ef546c83-43a8-4404-943e-ab324164eeb3" \
 | python3 -c "import json,sys; [print(r['name'],'|',r['url']) for r in json.load(sys.stdin)['result']['resources']]"
```

### 1.2 单条许可详情页（**含 Market status**）

```bash
curl -sSL -A "$UA" "https://health-products.canada.ca/lnhpd-bdpsnh/info?licence=80145377&lang=eng" -o d.html
```

用 Python 剥标签阅读（比肉眼快，且能同时拿到成分表）：

```bash
python3 - <<'PY'
import re, html
s = open('d.html', encoding='utf-8', errors='replace').read()
s = re.sub(r'(?is)<(script|style|nav|header|footer).*?</\1>', ' ', s)
t = html.unescape(re.sub(r'(?s)<[^>]+>', '\n', s))
out = []
for l in (x.strip() for x in t.split('\n')):
    if l and (not out or out[-1] != l):
        out.append(l)
i = next((k for k, x in enumerate(out) if x.startswith('Natural Product Number')), 0)
print('\n'.join(out[i:i+80]))
PY
```

关键字段：`Market status`、`Licence Status`、`Brand name(s)`、`Licence holder`、`List of medicinal ingredients`、`Recommended dose`、`Recommended use or purpose`、`Date of licensing`。

### 1.3 field 含义
- `flag_product_status`：**1 = active**（不表示"在售"）
- Market status：**自愿申报**，未申报默认 `Not Marketed` → **不可单独作为"本国没卖"的证据**

---

## 2. 德国工商登记

### 2.1 North Data ★推荐（JSON-LD 里直接有干货）

```bash
curl -sSL --compressed -A "$UA" -H "Accept-Language: de-DE,de;q=0.9" \
  "https://www.northdata.de/Caretechion+GmbH,+D%C3%BCsseldorf" -o nd.html
```

**关键技巧**：不要只看可见文本，**提取内嵌的 `application/ld+json`**，里面有 `foundingDate`、`member`（董事姓名）、`address`：

```bash
python3 - <<'PY'
import re, json, html
s = open('nd.html', encoding='utf-8', errors='replace').read()
print('TITLE:', (re.search(r'(?is)<title>(.*?)</title>', s) or [None, '?'])[1].strip())
for m in re.finditer(r'(?is)<script[^>]*application/ld\+json[^>]*>(.*?)</script>', s):
    d = m.group(1)
    if '"foundingDate"' in d or '"member"' in d:
        print(d[:1600])
# 经营范围（Gegenstand）在可见文本里
t = re.sub(r'\s+', ' ', html.unescape(re.sub(r'(?s)<[^>]+>', ' ', s)))
i = t.find('Gegenstand')
print('GEGENSTAND:', t[i:i+400] if i >= 0 else '?')
PY
```

**标题本身就含关键信息**：`<名称>, <城市>, Amtsgericht <法院> HRB <号>`

### 2.2 其他入口（常被 Cloudflare 拦，备选）
- `https://www.companyhouse.de/<Name>-<Stadt>`  → 常 403
- `https://handelsregister.ai/...` → 常 403（但其 **URL 路径里自带分类**，如 `grosshandel-mit-getraenken`（饮料批发），本身就是证据）
- `https://www.handelsregister.de` → 需 JS

### 2.3 德国药房查 PZN
```bash
curl -sSL --compressed -A "$UA" "https://apotheke-am-theater.de/shop/<slug>-<PZN>" -o apo.html
```
页面会给出：`Firma:`（负责公司）、`PZN`、`EAN/GTIN`、`UVP`、**`der Artikel ist in unserem Shop zur Zeit nicht bestellbar`**（是否可订购）。
⚠️ `apotheke-am-theater.de` 与 `internet-apotheke-freiburg.de` **是同一家弗莱堡药房**，别当两个渠道计数。

---

## 3. 英国 Companies House

```bash
curl -sSL --compressed -A "$UA" "https://find-and-update.company-information.service.gov.uk/company/14414045" -o ch.html
python3 - <<'PY'
import re, html
s = open('ch.html', encoding='utf-8', errors='replace').read()
t = re.sub(r'\s+', ' ', html.unescape(re.sub(r'(?s)<[^>]+>', ' ', re.sub(r'(?is)<(script|style).*?</\1>', ' ', s))))
i = t.find('Registered office address')
print(t[i:i+600])
PY
```

**重点看**：`Registered office address`、`Incorporated on`、`Nature of business (SIC)`、`Confirmation statement overdue`。
⚠️ **`99999 - Dormant Company` = 休眠公司**，是极强的空壳信号。

---

## 4. 香港公司注册处（第三方镜像）

```bash
curl -sSL --compressed -A "$UA" "https://hongkongcompanysearch.com/company/<id>.html" -o hk.html
```
可读到：成立日期、公司编号、中英文名、注册地址、现状（Live）。

---

## 5. GACC 中国海关境外出口商备案

```bash
curl -sSL --compressed -A "$UA" "https://transcustoms.cn/GACC/GACC_exporter_summary.asp?GACC=<编号>&country=<国家>&company=<公司名>" -o gacc.html
```
可读到：公司名、GACC 号、备案类型（境外出口商）、**备案国别**、签发年份、失效日期。
⚠️ 输出常为 GBK 乱码，直接抓 `Company:` / `Country:` / `Issue Year:` 等英文锚点即可。
⚠️ **2024-09 起旧 11 位号切换为 18 位号**，旧号显示 `Inactive Date` 属**制度切换，不是公司问题**。

---

## 6. 欧盟法规依据（引用时用这些原始出处）

| 内容 | 出处 |
|---|---|
| **NRV 参考量** | (EU) 1169/2011 **Annex XIII Part A** |
| 纯文本可抓： | `https://www.legislation.gov.uk/eur/2011/1169/annex/XIII/part/A/division/1/data.htm?view=plain` |
| **标签语言要求** | (EU) 1169/2011 **Art. 15** |
| **健康宣称** | (EC) 1924/2006（禁止疾病宣称；仅授权清单内宣称可用） |
| **维生素/矿物质 UL** | EFSA（如维生素 B6：2023 年由 25 mg 下调至 **12 mg/日**） |

```bash
curl -sSL --compressed -A "$UA" "https://www.legislation.gov.uk/eur/2011/1169/annex/XIII/part/A/division/1/data.htm?view=plain" -o nrv.html
python3 -c "
import re,html
t=re.sub(r'\s+',' ',html.unescape(re.sub(r'(?s)<[^>]+>',' ',open('/tmp/nrv.html',encoding='utf-8',errors='replace').read())))
for k in ['Vitamin B6','Folic acid','Vitamin B12']:
    m=re.search(re.escape(k)+r'[^0-9]*([0-9,]+)',t)
    print(k,'=',m.group(1) if m else '?')
"
```

---

## 7. 电商检索（判"有商品页"vs"可下单"）

### Amazon（ca / de / com 通用）
```bash
curl -sSL --compressed -m 45 -A "$UA" -H "Accept-Language: en-CA,en;q=0.9" "https://www.amazon.ca/s?k=<关键词>" -o amz.html
python3 - <<'PY'
import re, html
s = open('amz.html', encoding='utf-8', errors='replace').read()
m = re.search(r'"totalResultCount":(\d+)', s)
print('totalResultCount:', m.group(1) if m else '(未拿到，可能被拦)')
for b in re.split(r'(?=data-component-type="s-search-result")', s)[1:13]:
    h = re.search(r'(?is)<h2[^>]*>(.*?)</h2>', b)
    asin = (re.search(r'data-asin="([^"]+)"', b) or [None, '?'])[1]
    print(' ', asin, html.unescape(re.sub('<[^>]+>', '', h.group(1))).strip()[:100] if h else '?')
PY
```
⚠️ **务必逐条看标题**：命中的往往是**无关商品**（模糊匹配），别把 `totalResultCount>0` 当成"有卖"。
⚠️ Amazon 有时返回 1–2 KB 的验证页 → 标注未取证。

### 其他
- Walmart.ca / Shoppers / Well.ca：**常见人机验证或 403** → 标注未取证
- 德国：`rossmann.de`、`shop-apotheke.com` 通常可抓；`docmorris.de` 常 403
- CHFA（加拿大保健品协会）：`https://www.chfa.ca/?s=<品牌>` → **命中数全在 meta/搜索词回显里就说明无内容**

### 中国电商（实测结论：**商品页需要登录态**）

**先把话说清楚，避免误判：**

| 说法 | 事实 |
|---|---|
| ❌ "淘宝短链被拦截" | **错**。`e.tb.cn` 短链 **HTTP 200 可取**，页内嵌 `var url = '...'`，能解析出**商品 ID 与标价** |
| ✅ "淘宝商品页取不到正文" | **对**。`item.taobao.com/item.htm?id=…` 返回 **~1.7 KB JS 壳页**，无商品数据 |
| ✅ 无头浏览器也拿不到 | **对**。Playwright + Chromium（真实 UA/locale）会被**重定向到 `login.taobao.com`**，页面含 `baxia`（阿里反爬） |

实测数据（同一商品 ID）：

| 路径 | 大小 | 结果 |
|---|---|---|
| `item.taobao.com/item.htm?id=…` | ~1.7 KB | JS 壳页，无数据 |
| `detail.tmall.com/item.htm?id=…` | ~1.8 KB | JS 壳页，无数据 |
| `h5.m.taobao.com/awp/core/detail.htm?id=…` | ~49 KB | 仍是 **JS 加载器**（只有 `mtop.taobao.detail.getdetail` 的调用骨架） |
| `h5api.m.taobao.com/h5/mtop.taobao.detail.getdetail/6.0` | — | **JS 挑战**：返回 `set_x5referer` 跳转 + `x5secdata` cookie，纯 HTTP 走不通 |
| Playwright headless → `item.taobao.com` | 255 KB | **跳到登录页**，`title='登录'` |

> ⚠️ **`mtop` 接口不是可用的退路**。它用 `_m_h5_tk` 签名机制，但前置有 JS 挑战；
> 试图用脚本绕过反爬既不稳定，也可能违反平台条款。**不要在这上面耗时间。**

### ✅ 正确的取证阶梯（按强度排序）

```
① 商品页截图 / 包装实拍图   ← 最强。视觉模型直接读标签原文，证据等级最高
② 分享文本的标题 + 商品 ID  ← 标题通常已含 品牌/品类/宣称/成分，足够定位品牌与国家
③ 同款在其他平台的页面      ← 京东/天猫国际/Walmart/Amazon 多半可抓，可互为佐证
④ 第三方聚合站              ← ziyimall / 315jiage / chanmama 等，常已索引详情；
                              可用，但**必须标注来源与证据强度**
```

**一键产出简报**（短链解析 + 标题提取 + 后续动作提示）：

```bash
python3 {baseDir}/scripts/taobao_share.py '【淘宝】https://e.tb.cn/xxxx CZ321 「商品标题…」'
python3 {baseDir}/scripts/taobao_share.py --json '…'      # 结构化输出
```

脚本会解析：短链 → 真实 URL / 商品 ID / 标价提示、分享文本里的标题、规范链接。

### 🔴 最容易犯的错

> **不要把「商品页抓不到」写成「品牌查不到」。**
> 前者是**访问限制**，后者才是**核查结论**。两者毫无关系。
> 若某次核查以"链接被拦截"收尾，说明流程用错了——应该走上面的阶梯。

### 传统爬取要点（仍然适用）

- 短链解析：抓 `e.tb.cn` / `m.tb.cn` 的 HTML，正则 `var\s+url\s*=\s*'([^']+)'`
- 商品页取不到时**不要编造**；改用第三方转载页并标注来源与证据强度
- 用户给的分享文本里，标题在 `「…」` / `【…】` 中，往往比页面信息更全

---

## 8. 商标

> ⚠️ **商标是最容易白费功夫的一环**：几乎所有免费聚合站都上 Cloudflare / 反爬。**别在单个站点上反复重试**，按下面选路，失败就换下一条。

| 库 | 端点 | 可用性（实测） |
|---|---|---|
| **加拿大 CIPO ★推荐** | `https://ised-isde.canada.ca/opic/recherche-marques/<申请号>-00?lang=eng` | ✅ **200，可直接抓**（加拿大是本案最强法域，优先用它） |
| ~~旧 CIPO 入口~~ | ~~`https://www.ic.gc.ca/app/opic-cipo/trdmrks/...`~~ | 🔴 **已失效**：SSL 握手失败（`tlsv1 alert internal error`）。改用上面的 `ised-isde` 新域名 |
| **USPTO 官方检索** | `https://tmsearch.uspto.gov/` | ✅ 200，但**需 JS** |
| **USPTO TSDR（官方）** | `https://tsdrapi.uspto.gov/ts/cd/casestatus/sn<号>/status.json` | ❌ **401，需 API key** |
| Justia | `https://trademarks.justia.com/owners/<owner>-<id>/` | ❌ 常被 Cloudflare 拦 |
| TrademarkElite | `https://www.trademarkelite.com/...` | ❌ 常 403；但**搜索引擎摘要**常已含状态 |
| ~~Trademarkia~~ | ~~`trademark.trademarkia.com`~~ | 🔴 **已废弃，勿用**：TLS 层直接失败（连接超时 / `SSL_ERROR_SYSCALL`），实测完全不可达 |
| 德国 DPMA | `https://register.dpma.de/DPMAregister/marke/...` | ⚠️ **需 JavaScript** |
| 瑞士 IGE | `https://www.swissreg.ch/...` | ⚠️ **需 JavaScript** |
| 第三方镜像 | `markenmeldungen.ch` | ⚠️ 可抓，但**页面有模板瑕疵**（如年份字段明显错误），必须标注置信度 |

### ✅ 推荐做法：不要死磕官网，直接走「搜索摘要」退路

商标核查里**性价比最高的其实是搜索引擎摘要**——聚合站自己被拦，但它们的页面**已被搜索引擎索引**，摘要里常常就带着关键状态：

```
"<商标名>" trademark owner
"<商标名>" Marke Inhaber
"<商标名>" trademark DEAD abandoned
site:trademarks.justia.com "<商标名>"
site:trademarkelite.com "<商标名>"
```

**实战案例**：查 `COVO COYO` 的 USPTO 状态时，`trademarkelite.com` 本体被 403 拦死，但搜索摘要直接给出了：

> `COVO COYO Trademark (USPTO Serial 90015702) | ... DEAD On 8/21/2021 - Abandoned`

→ 状态、序列号、日期全都拿到了，**根本不需要打开那个站**。

**报告写法**：走摘要路径获取的信息，一律标注「**来自第三方聚合站，未能直连核实，置信度中**」，并给出序列号/日期等可复核要素。

---

## 9. 环境陷阱

### 沙箱 DNS 代理
若 `dig` 对**任何**域名都返回 `198.18.x.x` 这类地址，说明本机有 DNS 拦截/代理层：
→ **此时"域名解析失败/连接超时"不能作为"网站不存在"的证据。**
（`198.18.0.0/15` 是 RFC 2544 基准测试保留段，被部分沙箱用作 DNS 劫持占位。）

### 失效链接
黑猫投诉（`tousu.sina.com.cn`）等投诉平台**会在数月后删除/改号**，返回"页面不存在"。
→ **不要把"链接失效"写成"投诉不存在"**；搜索摘要里出现过就标注"曾见投诉记录，原链接已失效"。

### 图片小字
直接看原图必然看错。**必须裁剪 + 放大 4–14 倍 + autocontrast**（见 SKILL.md 第 0 步）。
条码数字常被**中央分隔条**干扰（会把分隔条误读成数字）→ 用 `ean_check.py` 的校验位反推验证。

---

## 10. 日本

### FFC 备案查询
```bash
# 消费者厅机能性表示食品数据库（日文，可英文搜索公司名）
curl -sSL --compressed -A "$UA" "https://www.caa.go.jp/policies/policy/food_labeling/food_labeling_2016/functional_foods/" -o ffc.html
# 页面为 JS 渲染，建议用搜索引擎 site: 限定
# Google: site:caa.go.jp "届出番号" "<品牌名>"
```

### 公司登记（第三方）
```bash
# Musubu（免费基础信息）
curl -sSL --compressed -A "$UA" "https://musubu.jp/<公司名>"
# Bizmap
curl -sSL --compressed -A "$UA" "https://bizmap.jp/<公司名>"
```

---

## 11. 韩国

### MFDS 健康功能食品备案
```bash
# MFDS 官网（韩文）
# https://www.mfds.go.kr → 식품안전나라 → 건강기능식품 정보
# 搜索引擎退路：site:mfds.go.kr "<品牌名>" 건강기능식품
```

### 渠道实测
- Coupang: `https://www.coupang.com/np/search?q=<关键词>`
- Naver Smart Store: `https://search.shopping.naver.com/search/all?query=<关键词>`

---

## 12. 美国州级公司查询

### 常用州 Secretary of State 端点
```bash
# Delaware（特拉华，最常见的注册地）
curl -sSL --compressed -A "$UA" "https://icis.corp.delaware.gov/ecorp/entitysearch/NameSearch.aspx" -o de.html

# California
curl -sSL --compressed -A "$UA" "https://bizfileonline.sos.ca.gov/search/business" -o ca.html

# Wyoming（低税州，空壳常选）
curl -sSL --compressed -A "$UA" "https://wyobiz.wyo.gov/Business/FilingSearch.aspx" -o wy.html

# Florida
sunbiz.org（可直接网页查询）

# Texas
sos.state.tx.us（可直接网页查询）
```

**判读要点**：
- **Delaware** 是空壳公司最爱（隐私好、年费低），看到 Delaware 注册要额外警惕
- **注册代理地址**（Registered Agent）是批量地址 → 空壳特征
- **状态**：Active vs Forfeited vs Dissolved

---

## 13. GMP 证书核查

### 查询路径
```bash
# Health Canada GMP 证书查询（加拿大厂商）
# https://health-products.canada.ca/gmp-gpp/index-eng.php

# EU GMP 证书（EudraGMDP）
# https://eudragmdp.ema.europa.eu/（需注册）

# 美国 FDA 药品 GMP 检查记录
# https://www.fda.gov/inspections-compliance-enforcement-and-criminal-investigations/compliance-actions-and-activities/warning-letters
```

**判读要点**：
- "GMP compliant" ≠ "GMP certified" —— 前者是自我声明，后者是第三方认证
- 要求卖方提供 **GMP 证书编号**，然后向发证机构核实
- 注意证书有效期和覆盖范围（是否覆盖该产品的生产）

---

## 14. 反向图片搜索

### 用途
- 识别盗图（同一包装图出现在多个不相关品牌）
- 识别 AI 生成图（无真实产品照片）

### 工具
- **Google Lens**: `https://lens.google.com/uploadbyurl?url=<图片URL>`
- **TinEye**: `https://tineye.com/api/v1/result_json/?url=<图片URL>`（需 API key）
- **Google 图片搜索**: 上传图片或粘贴图片 URL

**判读要点**：
- 同一包装图出现在 3 个以上不相关品牌 → 共用模板，典型贴牌
- 只有渲染图、无实拍图 → 可能无真实产品

---

## 15. 瑞士 IGE 商标查询（补充）

```bash
# 官方 swissreg.ch 需 JavaScript，纯 HTTP 无用（实测返回 "IPI Database Application startup failed"）
#   官方入口: https://www.swissreg.ch/  （需浏览器 / JS）

# 退路 1：搜索引擎（推荐，性价比最高）
#   site:swissreg.ch "<商标名>"
#   "<商标名>" Marke Inhaber Schweiz

# 退路 2：第三方镜像（可抓，但有模板瑕疵，务必标注置信度）
curl -sSL --compressed -A "$UA" "https://www.markenmeldungen.ch/marke.cfm?marke=<商标名>" -o tm.html
```

> 🔴 **不要用 `trademark.trademarkia.com`** —— 那是美国商标聚合站，**既不是瑞士官方镜像**，
> 又已实测 TLS 层不可达（连接超时 / `SSL_ERROR_SYSCALL`）。此前版本误将其列在此处，已移除。
> 查瑞士商标**只认** `swissreg.ch`（官方）或其搜索摘要。

---
