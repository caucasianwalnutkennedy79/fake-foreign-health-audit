# fake-foreign-health-audit

> 鉴别「药品 / 保健品」是不是**假洋货**（伪造洋品牌身份）的 OpenClaw 技能。

[![OpenClaw](https://img.shields.io/badge/OpenClaw-%E2%89%A52026.9.3-4B5563)](https://openclaw.ai)
[![Skill](https://img.shields.io/badge/type-agent--skill-2563EB)](#安装)
[![GitHub](https://img.shields.io/badge/github-longppai68--ai%2Ffake--foreign--health--audit-181717?logo=github)](https://github.com/longppai68-ai/fake-foreign-health-audit)
[![Release](https://img.shields.io/github/v/release/longppai68-ai/fake-foreign-health-audit?label=release)](https://github.com/longppai68-ai/fake-foreign-health-audit/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/longppai68-ai/fake-foreign-health-audit/total?label=downloads)](https://github.com/longppai68-ai/fake-foreign-health-audit/releases)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776AB)](https://www.python.org/)
[![Dependencies](https://img.shields.io/badge/dependencies-none%20(stdlib)-brightgreen)](#依赖)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

给它一个商品链接、包装照片或品牌名，它去查**宣称国的官方数据库、工商登记和本土渠道**，出一份带证据分级的鉴定报告。

**不做医疗建议，只做身份与合规核查。**

---

## 目录

- [为什么需要它](#为什么需要它)
- [核心框架](#核心框架)
- [亮点](#亮点)
- [下载](#下载)
- [安装](#安装)
- [快速开始](#快速开始)
- [目录结构](#目录结构)
- [脚本](#脚本)
- [参考文档](#参考文档)
- [真实案例](#真实案例)
- [红旗清单](#红旗清单)
- [设计原则](#设计原则)
- [依赖](#依赖)
- [FAQ](#faq)
- [开发与维护](#开发与维护)
- [变更记录](#变更记录)
- [局限](#局限)
- [许可](#许可)
- [免责声明](#免责声明)

---

## 为什么需要它

"XX国进口""XX国品牌"是保健品电商最常见的溢价理由，也是最容易造假的标签。但**判断它真假并不需要专业背景**——只是需要知道去**哪里查**，以及**怎么读查到的结果**。

难点在两个地方：

1. **各国的监管结构完全不同，打法必须换。** 加拿大有上市前强制许可（NPN），查一下就知道持证人是谁、剂量多少；德国**没有**产品级审批，查注册号这条路根本不存在，得改查**工商登记的「经营范围」**。
2. **"查不到"和"不存在"是两回事。** 大量站点有反爬（403 / 人机验证 / JS 壳页）。把"没查到"当成"没有"，会冤枉真实品牌；反过来，把"有个注册号"当成"是真洋品牌"，会放过假洋货——**注册号是可以合法申请的**。

这个 skill 把这两件事都固化成了流程：按国家切换核查路径，并且强制标注证据强度。

---

## 核心框架

### 三层分开验

| 层次 | 要回答的问题 | 若为否 |
|---|---|---|
| **身份层** | 品牌的控制主体，在不在它宣称的国家？ | 洋品牌身份是包装出来的 |
| **实质层** | 是否取得该国合法资质、按当地标准生产？ | 可能连合法身份都没有 |
| **存在层** | 在该国本土是否真有渠道、消费者、口碑？ | 属于"只对某个市场销售的洋品牌" |

### 四级判定

| 级别 | 含义 |
|---|---|
| **A 真洋品牌** | 本土主体 + 本土资质 + 本土在售 + 本土口碑 |
| **B 合法授权贴牌** | 境外主体真实持有并授权，本国确有销售（规模小） |
| **C 伪造洋身份（假洋货）** | 境外空壳/贸易壳承载品牌，本土几无市场，叙事虚构 |
| **D 三无假货** | 任何国家/地区监管资质都没有 |

> ⚠️ **C ≠ D，这是本 skill 最想纠正的认知偏差。**
> 大量争议产品**手里握着真实、可查的境外注册号**，却依然是假洋货。反之，某些国家（美国、德国、新西兰）本就不要求产品注册，"查不到编号"完全正常。
> **只答"是/否"必然出错；必须落到具体级别并给出依据。**

---

## 亮点

- 🎯 **按国家切换打法** — 加拿大 / 澳洲 / 中国 / 美国 / 德国欧盟 / 英国香港 / 日本 / 韩国 / 新西兰，每个国家给出对应的一击命中路径
- 🔍 **查「工商登记的经营范围」** — 一个"保健品品牌"背后的公司，法定范围写的是**饮料进出口**，答案就出来了（真实的命中案例）
- 🧮 **%NRV 算术核对** — 正经标签按法规算，抄模板的会算错；**"引用了法规却算错法规"**几乎可当定案证据
- 💊 **剂量 vs 安全上限（UL）** — 并**严格区分 UL 与"建议上限/指导水平"**，避免把正常的 B 族产品误判为超标
- 🧾 **标签法证九项** — 语言、注册号、剂量一致性、违法宣称、机翻痕迹、伪造认证章、付费送评奖项
- 🛒 **正面处理"电商页抓不到"** — 淘宝/天猫/京东商品页需登录态，本 skill 不在这上面耗时间，而是解析分享文本 + 给出取证阶梯
- 🧰 **四个零依赖脚本** — 仅用标准库，直接跑，不用装任何包
- ⚖️ **诚实性硬约束** — 被拦截的渠道一律标「未获证据」，不混入否定证据；报告必写「证据边界」

---

## 下载

| 下载 | 链接 | 说明 |
|---|---|---|
| **最新发布包** | [`fake-foreign-health-audit-v1.0.0.zip`](https://github.com/longppai68-ai/fake-foreign-health-audit/releases/latest/download/fake-foreign-health-audit-v1.0.0.zip) | 开箱可用，含全部文件 |
| 源码 zip | [`v1.0.0.zip`](https://github.com/longppai68-ai/fake-foreign-health-audit/archive/refs/tags/v1.0.0.zip) | GitHub 自动打包 |
| 源码 tar.gz | [`v1.0.0.tar.gz`](https://github.com/longppai68-ai/fake-foreign-health-audit/archive/refs/tags/v1.0.0.tar.gz) | 同上 |
| 全部版本 | [Releases](https://github.com/longppai68-ai/fake-foreign-health-audit/releases) | 版本历史 |

> ℹ️ 版本号只存在于 **git tag** 层面——OpenClaw 的 `SKILL.md` frontmatter **不接受 `version` 字段**（`quick_validate.py` 会报错），所以文件里不写版本号。

---

## 安装

### 方式一：从 GitHub 安装（推荐）

```bash
openclaw skills install git:https://github.com/longppai68-ai/fake-foreign-health-audit --agent <agent-id>
```

### 方式二：下载发布包后本地安装

```bash
# 下载并解压上面的「最新发布包」，然后：
openclaw skills install ./fake-foreign-health-audit --agent <agent-id>
```

### 方式三：克隆后本地安装

```bash
git clone https://github.com/longppai68-ai/fake-foreign-health-audit.git
openclaw skills install ./fake-foreign-health-audit --agent <agent-id>
```

### 方式四：手动放置

把整个目录放进目标 agent 的 workspace skills 目录：

```bash
# 生效位置（2026.9.3 起为 agent 作用域目录）
cp -R fake-foreign-health-audit ~/.openclaw/workspace/<agent>/skills/
```

> ⚠️ 手动放置时**不要**把 `.git/` 一并拷贝——多 agent 同步请参考 [开发与维护](#开发与维护) 里的 `rsync` 命令（已排除 `.git`）。

### 验证安装

```bash
openclaw skills info fake-foreign-health-audit --agent <agent-id>
openclaw skills check --agent <agent-id>
```

期望输出：

```
fake-foreign-health-audit ✓ Ready
  Visible to model: yes
  Available as command: yes
  Binaries: ✓ curl, ✓ python3
```

用 OpenClaw 内置校验器做严格格式校验：

```bash
python3 ~/.nvm/versions/node/*/lib/node_modules/openclaw/skills/skill-creator/scripts/quick_validate.py \
  ~/.openclaw/workspace/<agent>/skills/fake-foreign-health-audit
# → Skill is valid!
```

---

## 快速开始

直接在对话里描述需求即可，skill 会按 `description` 自动触发：

> "这个淘宝链接是不是假洋货？"
> "德国COVO这个牌子是真的吗？"
> "帮我看看这瓶叶酸的包装有没有问题"（附图）

也可以手动调用脚本：

```bash
cd ~/.openclaw/workspace/<agent>/skills/fake-foreign-health-audit

# 1) 查加拿大 NPN（最强证据）
python3 scripts/lnhpd_search.py --brand "LOEON"
python3 scripts/lnhpd_search.py --npn 80145377 --detail

# 2) 核对标签 %NRV 算术 + 安全上限
python3 scripts/nrv_check.py --label folate=1000ug --claimed folate=270 --ul

# 3) 校验条码
python3 scripts/ean_check.py 4262366230132
```

---

## 目录结构

```
fake-foreign-health-audit/
├── README.md                     # 本文件（面向人）
├── SKILL.md                      # 主文件：工作流、原则、红旗清单、输出契约（面向 agent）
├── references/
│   ├── jurisdictions.md          # 各国核查路径与数据库字段含义
│   ├── endpoints.md              # 可直接复制的命令与端点（含踩坑记录）
│   └── label-forensics.md        # 标签法证九项 + NRV / UL 对照表
└── scripts/
    ├── lnhpd_search.py           # 加拿大 LNHPD 全量检索
    ├── nrv_check.py              # %NRV 算术核对 + UL 检查
    ├── ean_check.py              # 条码校验 + GS1 前缀解读
    └── taobao_share.py           # 电商分享文本解析（CN 商品页需登录态时用）
```

> 📌 **面向 agent 还是面向人？**
> `SKILL.md` 与 `references/*.md` 由 agent 读取，其中引用自带文件一律用 OpenClaw 的 **`{baseDir}/`** 占位符（由 agent 解析到 skill 自身目录），**不写相对路径**——否则 agent 从别的目录执行就会失败。
> `README.md` 面向人，保留相对路径。细则见 [开发与维护](#开发与维护)。

---

## 脚本

### `lnhpd_search.py` — 加拿大 LNHPD 检索

加拿大天然健康产品**上市前必须取得许可**，标签必须印 **NPN**；持证人、成分剂量、许可日期、市场状态全部公开可查。这是全球最好用的一击命中式核查。

```bash
python3 scripts/lnhpd_search.py --brand "LOEON"                      # 按品牌
python3 scripts/lnhpd_search.py --company "Bethune Health Develops"  # 按持证人
python3 scripts/lnhpd_search.py --npn 80145377 --detail              # 详情页（含 Market status）
python3 scripts/lnhpd_search.py --brand LOEON --summary-only --json  # 结构化输出
```

| 参数 | 说明 |
|---|---|
| `--brand` / `--company` / `--npn` | 检索条件（三选一或组合） |
| `--detail` | 抓取详情页，含 `Market status`、官方成分剂量 |
| `--summary-only` | 只输出按 NPN 汇总的表 |
| `--limit` | 详情抓取上限（默认 40） |
| `--cache-dir` | 数据缓存目录（默认 `~/.cache/lnhpd`） |
| `--refresh` | 强制重下全量数据（约 140 MB，首次自动下载） |

**关键字段怎么读：**

| 字段 | 含义 | 用法 |
|---|---|---|
| `company_name` | 许可持有人 | 是不是宣称国主体？是不是空壳？ |
| `licence_date` | 许可日期 | **与品牌宣称的历史对照** |
| Brand name(s) | 一个许可可挂**多个品牌名** | 一个配方挂 5 个牌子 = 典型贴牌 |
| medicinal ingredients | 官方登记的**成分与剂量** | **与包装标注逐项对照** |
| `Market status` | `Marketed` / `Not Marketed` | ⚠️ **自愿申报**，未申报默认 Not Marketed，**不可单独证明"该国没卖"** |

### `nrv_check.py` — %NRV 算术核对 + UL 检查

```bash
# 按法规算出应有 %NRV，并与标签所标对比
python3 scripts/nrv_check.py --label folate=1000ug --claimed folate=270 --ul

# 只看数值 + UL 检查
python3 scripts/nrv_check.py --label b6=50mg --label b12=500ug --ul

# 覆盖参考量 / 切换标准
python3 scripts/nrv_check.py --label folate=1000ug --nrv folate=200ug --standard eu
```

> 🔴 **本脚本严格区分两类限值**，这是它区别于网上各种"UL 速查表"的地方：
> - **`UL`（可耐受最高摄入量）** — 监管限值，超出可提示"超标/需警示"
> - **`SOFT_LIMITS`（建议上限 / 指导水平）** — **不是 UL**。维生素 B12、K、生物素、泛酸、B1、B2、钾在 IOM/EFSA **都没有 UL**；网上常见的"维生素 K 1000 µg""生物素 900 µg""B1 100 mg"是英国 EVM 指导水平 / 欧盟建议上限
>
> 把后者当 UL 用，会把**正常的复合 B 族、生物素产品误判为超标**——假阳性。脚本对两类**分开输出**。

### `ean_check.py` — 条码校验 + GS1 前缀

```bash
python3 scripts/ean_check.py 4262366230132
python3 scripts/ean_check.py --batch codes.txt --lang en
```

| 能读出 | 不能读出 |
|---|---|
| ✅ 校验位是否正确（正确 = 号码规范生成，不是随手编的） | ❌ **产地！** 前缀只表示号码由哪个 GS1 成员组织分配 |
| ✅ GS1 国家/地区前缀 | — |
| ⚠️ `200–299` 是**受限流通/店内码**号段，不是正常零售条码 | — |

### `taobao_share.py` — 电商分享文本解析

**淘宝/天猫/京东的商品页需要登录态**（无头浏览器也会被重定向到 `login.taobao.com`，页面含 `baxia` 反爬），纯 HTTP 只能拿到 JS 壳页。但**分享文本本身**已含足够信息。

```bash
# 直接粘贴整段分享文本
python3 scripts/taobao_share.py '【淘宝】https://e.tb.cn/xxxx CZ321 「商品标题…」'

# 结构化输出
python3 scripts/taobao_share.py --json '…'
python3 scripts/taobao_share.py --file share.txt
```

输出：**商品 ID**、**标题**、**标价提示**、规范链接，以及后续取证阶梯提示。

**支持的输入格式：** 淘宝 / 天猫 / 京东 / 拼多多的短链、完整商品链接，或直接粘贴整段分享文本；标题可来自 `「」`、`『』`、`【】`、`[]`。

**两处值得一提的实现细节：**

| 细节 | 说明 |
|---|---|
| **标题提取有优先级** | `「」『』`（强）优先于 `【】[]`（弱），同类取**最右**一个，并过滤短平台/营销词。否则 `【双十一狂欢大促】…「真实标题」` 会把营销词当成标题 |
| **deflate 解压走两条路** | 服务器可能发 **zlib 包装**（RFC1950）或**原始 deflate**（RFC1951）。只写 `zlib.decompress(d)` 遇后者报 `incorrect header check`；只写 `-zlib.MAX_WBITS` 遇前者也会失败。**必须两种都试** |
| **仅标准库** | HTTP 用 `urllib`，解压用 `gzip`/`zlib`，不引入任何第三方依赖 |

> ✅ **短链是可以解析的**（`e.tb.cn` 页内嵌 `var url = '…'`，HTTP 200）。
> ❌ **商品页正文是拿不到的**，这是访问限制，**不是**"品牌查不到"。
> 正确阶梯：**① 截图（最强）→ ② 标题 + 商品 ID → ③ 同款在其他平台 → ④ 第三方聚合站（标注强度）**。

---

## 参考文档

| 文件 | 内容 |
|---|---|
| `references/jurisdictions.md` | 九个国家/地区的监管结构与核查路径、数据库字段解读 |
| `references/endpoints.md` | 全部可复制的 `curl` 命令与端点，含**踩坑记录**（API 大小写、GBK 乱码、DNS 代理、失效链接） |
| `references/label-forensics.md` | 标签法证九项、EU/US %NRV 对照表、UL 速查 + **无 UL 营养素清单** |

---

## 真实案例

> 以下两案均为**真实执行记录**，也是本 skill 规则的来源。

### 案例一：加拿大「高端活性叶酸」→ **C 类**

| 发现 | 证据 |
|---|---|
| **有真实 NPN** — NPN 80145377，`Licence Status: Active` | Health Canada LNHPD |
| 但持证人是 **2020-01-13 在香港成立**的公司 | 香港公司注册处 |
| 品牌商标由名为 `Switzerland SIAC Health Ltd` 的实体持有，地址却在**英国 Croydon**；名下另一家英国公司为 **SIC 99999 休眠公司**且年报逾期 | 瑞士商标公告 + 英国 Companies House |
| **标签虚标一倍**：包装标 Folate **2000 µg**，官方许可仅 **1000 µg** | 标签 vs LNHPD 成分表 |
| 该持证人 **100 条品牌名注册 / 28 个 NPN，全部集中在 2024–2026 年**，此前一条都没有 | LNHPD 全量数据 |
| 一个 NPN 挂 **LOEON / Caitlyn / Dr. Nom / SIAC / TOFO** 五个品牌 | LNHPD |
| Amazon.ca 检索无货；CHFA 无任何记录；38 个 NPN 市场状态全部 `Not Marketed` | 渠道实测 |
| 官网自称"1989 年创立""过去 21 年"，却又称关联公司 `Canada Kelsen Health` ——LNHPD 全库检索 **0 条** | 官网 vs 官方库 |

**结论：有牌照的贴牌。** 不是"三无"，但"加拿大品牌"身份是营销建构的产物。

### 案例二：德国「进口活性叶酸」→ **C 类**

**决定性一击来自工商登记的「经营范围」：**

标签印着 `Made in Germany` + **Europesdoor GmbH**，而这家公司在德国登记的法定经营范围是：

> *Der Import und Export von Lebensmitteln, insbesondere **Getränke aller Art***
> （食品、**尤其各类饮料**的进出口）

—— 一家**葡萄酒/饮料贸易商**。而它的中方页面正把这家公司写成"**生产企业**"。溯源后发现，其幕后是**北京**一家以德国葡萄酒进口为主业的公司。

**标签法证的其它命中：**

| 检查项 | 结果 |
|---|---|
| **语言** | 宣称德国制造，**通篇英文、一个德文字都没有**（违反 (EU) 1169/2011 Art. 15）→ 不是给德国人买的 |
| **违法宣称** | "Regulates metabolic **disorders** of the body" ——(EC) 1924/2006 禁止疾病宣称，**在德国根本无法合法上市** |
| **%NRV 算错** | 标签注明 *according to Regulation (EU) no 1169/2011*，却把叶酸 1000 µg 标成 **270%**（按该法规应为 **500%**）。同表 B6、B12 却算对了 → **唯独那行是抄来的** |
| **超 UL** | 维生素 B6 **50 mg/日**——EFSA 2023 已将 UL 下调至 **12 mg/日**，**超 4 倍且无警示**（长期可致周围神经病变） |
| **伪造认证章** | 德国国旗配色圆章——**德国不存在官方 "Made in Germany" 印章** |
| **付费奖项** | Monde Selection "Gold 2026"，官网首页即 `Submit a Product`，**"原产国"由申报方自报、不核验** |

---

## 红旗清单

命中 **≥3 条**基本可定 C 类；**≥6 条**相当确凿。

- [ ] 品牌商标持有人是**与宣称国无关的空壳**
- [ ] 负责主体的**工商登记经营范围不是生产**（贸易/咨询/进出口/展会）
- [ ] **宣称国本土主流渠道查无在售**，或仅有"不可订购"的孤条目
- [ ] **成立日期与宣称历史矛盾**
- [ ] 官网自述的公司名在宣称国**官方库中查无此主体**
- [ ] 包装**缺该国语言**、缺强制标示
- [ ] **无该国注册号**，或注册号与标签剂量**不符**
- [ ] **%NRV 算错**（尤其"引用了法规却算错"）
- [ ] 剂量**超出该国安全上限（UL）且无警示**
- [ ] 带**违法疾病宣称**
- [ ] 机械翻译的中式外文
- [ ] **伪造认证章** / 用付费送评奖项冒充权威认证
- [ ] 商标**已放弃 / 驳回 / 失效**
- [ ] 有集中的软文投放，或**自辩式"鉴别攻略"**
- [ ] 宣称日本/韩国进口却**无 FFC / MFDS 备案**
- [ ] **GMP 证书无法核实**，或只有 "GMP compliant"（自我声明）
- [ ] **反向图片搜索**发现同一包装图出现在多个不相关品牌

---

## 设计原则

这几条是本 skill 区别于"网上鉴别攻略"的地方，也是它没翻车的原因：

1. **搜不到 ≠ 不存在。** 被反爬拦截（403 / 人机验证 / JS 壳页）的渠道**必须标注「未获证据」**，不得计入否定证据。
2. **区分"推论"与"证实"。** 没有实物标签时只能说"推论"；拿到实物才能写"证实"。
3. **举证责任在卖方。** 你不需要证明"它不是"，只需指出**其宣称未被证实，或与其自身注册信息矛盾**。
4. **不重复别人的结论。** 网上流传的"鉴别标准"本身可能就是软文——例：某话术称"支持本地医保积分抵扣"，而加拿大药房用的是 PC Optimum 等商业积分，**根本没有"医保积分"这一概念**。一切声称必须自己复核。
5. **报告必写「证据边界」。** 哪些渠道被拦截、哪些结论是推论、哪些未能直连核实——全部写清。

---

## 依赖

- **OpenClaw** ≥ 2026.9.3（已在 `2026.9.3 (1391f7c)` 验证）
- **Python** ≥ 3.8（三个脚本**仅用标准库**，无需 pip 安装任何包）
- **curl**（`endpoints.md` 中的抓取命令）

---

## FAQ

**Q：为什么德国/美国查不到注册号，是不是就说明是假的？**
不是。美国（DSHEA）、德国/欧盟、新西兰、英国**都不要求**膳食补充剂上市前审批，本就没有产品级公开数据库。这些国家要改查**工商登记的「经营范围」+ 本土零售实测 + 健康宣称合规**。只有加拿大（NPN）、澳洲（AUST L）、中国（蓝帽子）等才有产品注册号可查。

**Q：`Market status: Not Marketed` 是不是说明该国没卖？**
不能。Health Canada 明确该状态为**自愿申报**，未申报者默认显示 Not Marketed，**且不影响合法销售**。它只能作辅证。

**Q：标签上没有 NPN，能说明什么？**
在加拿大，许可 NHP 的标签**必须**印 NPN。**包装上看不到 NPN 本身就是发现**（除非照片没拍全）。

**Q：条码是德国前缀（4xx），能证明是德国产吗？**
不能。GS1 前缀只表示号码由**哪个 GS1 成员组织分配**——任何国家的公司加入对应 GS1 组织就能拿到该前缀。它只能说明"号码规范生成"，与产地无关。

**Q：第一次跑 `lnhpd_search.py` 很慢？**
它在下载 LNHPD 全量数据（约 **140 MB**）。之后会缓存（默认 `~/.cache/lnhpd`，14 天后提示刷新）。若默认目录无写权限，用 `--cache-dir /tmp/lnhpd`。

**Q：搜索结果里的站点打不开 / 返回 403？**
很常见（Cloudflare、人机验证、需 JS）。按设计原则，这属于**未获证据**，不是"不存在"。

**Q：给了淘宝链接，为什么读不到商品页？**
**这是正常的，不是故障。** 实测结论：

| 路径 | 结果 |
|---|---|
| `e.tb.cn` 短链 | ✅ **HTTP 200，可解析**出商品 ID 与标价 |
| `item.taobao.com/item.htm?id=…` | ❌ 仅 ~1.7 KB 的 **JS 壳页** |
| `h5.m.taobao.com/.../detail.htm` | ❌ ~49 KB，仍是 **JS 加载器** |
| `h5api.m.taobao.com`（`mtop.detail.getdetail`） | ❌ **JS 挑战**（`set_x5referer` + `x5secdata`） |
| Playwright 无头浏览器 | ❌ **被重定向到登录页**（页面含 `baxia`） |

**商品页需要登录态，而核查并不需要商品页。** 用 `taobao_share.py` 解析分享文本拿到标题与 ID 即可开工；最强证据是**商品页截图或包装实拍图**（视觉模型直接读标签原文）。

> 🔴 若某次核查以"链接被拦截"收尾，说明流程用错了。**「抓不到页面」和「查不到品牌」是两件事**，前者是访问限制，后者才是结论。

---

## 开发与维护

### 编辑约定

| 约定 | 原因 |
|---|---|
| **面向 agent 的文档里引用自带文件，必须写 `{baseDir}/…`** | OpenClaw 的 agent 会**解析 `{baseDir}` 到 skill 自身目录**（[官方文档](https://docs.openclaw.ai/tools/creating-skills)）。写成相对路径 `scripts/x.py` 依赖进程工作目录，agent 从别处执行会直接报 `No such file or directory` |
| **脚本仅用标准库** | 保证零安装、任何 Python ≥3.8 环境可直接跑 |
| **`README.md` 面向人，可保留相对路径** | 它是仓库说明，不是 agent 指令 |
| **不带入 `.DS_Store` / `__MACOSX` / `__pycache__` / 一次性补丁** | 发布物保持干净 |

涉及的文件：`SKILL.md` 与 `references/*.md` 用 `{baseDir}/`；`README.md` 不用。

### 校验（改完必做）

```bash
# 1) 官方格式校验器——必须输出 "Skill is valid!"
python3 ~/.nvm/versions/node/*/lib/node_modules/openclaw/skills/skill-creator/scripts/quick_validate.py \
  /path/to/fake-foreign-health-audit

# 2) 四个脚本的语法与冒烟
for f in scripts/*.py; do
  python3 -B -c "compile(open('$f',encoding='utf-8').read(),'$f','exec')" && echo "OK $f"
done
for s in lnhpd_search nrv_check ean_check taobao_share; do
  python3 -B scripts/$s.py --help >/dev/null && echo "OK $s"
done

# 3) agent 侧确认
openclaw skills check --agent <agent-id>      # Missing requirements 应为 0
openclaw skills info  fake-foreign-health-audit --agent <agent-id>
```

### 同步到多个 agent

```bash
SRC=/path/to/fake-foreign-health-audit
for D in ~/.openclaw/workspace/skills/fake-foreign-health-audit \
         ~/.openclaw/workspace/main/skills/fake-foreign-health-audit \
         ~/.openclaw/workspace-{cpp,pp1,pp6,pp8}/skills/fake-foreign-health-audit; do
  rsync -a --exclude='.git' --exclude='.openclaw' --exclude='.cache' \
        --exclude='__pycache__' --exclude='.DS_Store' "$SRC"/ "$D"/
done
```

> ⚠️ `--exclude='.openclaw'` 不能省——管理型副本里有 `.openclaw/source-origin.json` 溯源元数据，覆盖会破坏它。
> ⚠️ `--exclude='.git'` 也不能省——本仓库已 `git init`，不排除会把版本库整个拷进每个 agent 目录。
> ⚠️ 注意 **main agent 的路径是嵌套的** `workspace/main/skills/`，不是 `workspace-main/`。

### 发布打包

```bash
zip -rq fake-foreign-health-audit.zip fake-foreign-health-audit \
  -x '*.DS_Store' -x '__MACOSX/*' -x '*/.openclaw/*' \
  -x '*/__pycache__/*' -x '*.pyc'
```

### 本文档的准确性规则

README 里的每条事实都应**可被复核**。改动后请顺手检查：

- 目录结构树与实际 `find` 结果一致
- 脚本数量、参数名与实际 `--help` 一致
- 案例中的数字（NPN、剂量、百分比）与 `references/` 里的记录一致
- 相对链接与锚点可跳转

---

## 变更记录

> 本 skill 由两个真实案例的核查过程提炼而成，规则多来自"踩过的坑"。

### 2026-09-12

**新增**
- `scripts/taobao_share.py` — 电商分享文本解析，正面解决"商品页需登录态"的问题
- `README.md`（本文件）
- **输出契约** — 报告格式固定化，取代原先宽松的"报告模板"
- **定性强制单一类别** — 只允许 `C` / `B/C 之间` / `倾向 B，需补充证据` 三种写法，禁用"接近""存疑""疑似"等含糊限定
- **发布 v1.0.0** — 首个带 tag 的 Release，附开箱可用的发布包与自动生成的源码包
- `references/endpoints.md` 补日本 / 韩国 / 美国州级公司查询端点
- `references/jurisdictions.md` 补日本 / 韩国 / 新西兰三节
- 标签法证补：反向图片搜索、GMP 证书核查、3 条红旗
- SKILL.md 第 0 步补 CN 电商访问现实与反误判硬约束
- **源纪律**（0.5 节 + 核心原则 7/8 条）：只用文档列出的源、单源只试一次、SIGTERM ≠ 未获证据

**修复**
| 问题 | 影响 |
|---|---|
| **文档里写了一个从未实测的死端点** | `trademark.trademarkia.com` TLS 层根本不通，且被误放在「瑞士 IGE」节下（实为美国聚合站）→ 已删除并列入黑名单 |
| **报告格式在不同 run 之间漂移** | 原模板 12 个占位符中**有 4 个在章节标题里**，导致每次 `2.x` 标题都不一样 → 改为刚性输出契约 |
| SKILL.md/references 用相对路径引用脚本 | agent 从非 skill 目录执行会 `No such file or directory` → 全部改为 `{baseDir}/`（31 处） |
| `taobao_share.py` 标题提取会取到营销词 | `【双十一狂欢大促】…「真实标题」` 会把 `双十一狂欢大促` 当标题 → 改为强/弱模式 + 取最右 |
| `taobao_share.py` 无法解压原始 deflate | 服务器发 RFC1951 时 `incorrect header check` → 改为两路都试 |
| `nrv_check.py` 把非 UL 值当 UL | 生物素/维生素K/B1/B2/泛酸/钾在 IOM/EFSA **无 UL**，原表会导致**正常产品被误判超标** → 拆出 `SOFT_LIMITS` 并分开输出 |
| `ean_check.py` 未剥离 GTIN-14 包装指示符 | 14 位码前缀解析错误 → 新增 `elif n == 14` 分支 |
| `endpoints.md` 得州网址错误 | `comptroller.texas.gov` 是企业税，登记应为 `sos.state.tx.us` |
| `jurisdictions.md` 三处事实错误 | Olive Young 被列在日本项下（实为韩国）；韩国"认证书"（多数实为品目製造申告）；NZFSA 已于 2012 并入 MPI |
| `label-forensics.md` 判读口径写反 | "日剂量**超过** UL 即为安全信号" → 应为"**未超过**" |
| frontmatter 含 `version` 字段 | OpenClaw `quick_validate.py` 不接受（**ClawHub 文档与本地校验器不一致**） |

**清理**
- 移除 `.DS_Store`
- 一次性补丁移出 skill 目录
- 去除 `SHORT_HOSTS` 重复项与绕人的 `\'` 转义写法

---

## 局限

- **不做医疗建议。** 只做身份与合规核查；安全提示仅基于公开的 UL/NRV 数值，具体用药请咨询医生。
- **不能证明"非该国制造"。** 本 skill 主张的是**该宣称未被证实 / 与其自身注册信息矛盾**，而不是已证明产地造假。
- **实物标签可能拍不全。** 只拍到部分标签面时，"强制标示缺失"为**中等强度**证据。
- **官方库有滞后与自愿申报问题。** 见上文 FAQ。
- **`SOFT_LIMITS` 数值来自各国建议上限，会随监管更新变化。** 关键结论请回溯到 `endpoints.md` 给出的原始出处。

---

## 许可

MIT

---

## 免责声明

本 skill 输出的是**基于公开可查证据的鉴别意见**，不构成法律、医疗或投资建议，也不构成对任何厂商的指控。涉及产品安全或消费纠纷，请以监管机构的正式结论为准；如需用药指导，请咨询医生或药师。

核查结论会随官方数据库更新而变化，**请以核查当日的公开记录为准**。
