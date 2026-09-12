# 各国核查路径

## 目录
- [判定框架](#判定框架)
- [加拿大](#加拿大)
- [澳大利亚](#澳大利亚)
- [中国](#中国)
- [美国](#美国)
- [德国 / 欧盟](#德国--欧盟)
- [英国 / 香港](#英国--香港)
- [通用：条码](#通用条码)

---

## 判定框架

**三层**：身份层（主体在不在宣称国）→ 实质层（有无该国资质）→ 存在层（该国本土是否真在售）

**四级**：A 真洋品牌 / B 合法授权贴牌 / **C 伪造洋身份（假洋货）** / D 三无假货

**关键认知：最难也最常见的争议是 C 类。** 很多假洋货**手里握着真实的境外注册号**（因为注册号是可以合法申请的），问题出在：主体是空壳、本土无销售、叙事虚构、标签与注册不符。

> 因此：**"查到了注册号"不等于"是真洋品牌"；"查不到注册号"也不一定就是假的**（有些国家本就不要求注册）。必须结合主体与渠道一起判。

---

## 加拿大

### 监管结构
天然健康产品（NHP）**上市前必须取得许可**，标签必须印 **NPN**（Natural Product Number，8 位）或 **DIN-HM**。
→ **这是全球最好用的一击命中式核查。**

### 主查：LNHPD（Licensed Natural Health Products Database）

- 网页查询：`https://health-products.canada.ca/lnhpd-bdpsnh/info?licence=<NPN>&lang=eng`
- 全量数据 API：见 `endpoints.md`（**资源名必须首字母大写**，这是踩坑点）

一键检索：`python3 {baseDir}/scripts/lnhpd_search.py --brand "品牌名"`

### 字段解读（都很关键）

| 字段 | 含义 | 怎么用 |
|---|---|---|
| `licence_number` | NPN | 与包装上印的是否一致 |
| `company_name` | **许可持有人** | 是不是宣称国主体？是不是空壳？ |
| `licence_date` | 许可日期 | **与品牌宣称的历史对照**（实战：官网称"1989 年创立"，许可却始于 2025 年） |
| `flag_product_status` | 许可状态（1=active） | 有效≠在售 |
| **Market status** | `Marketed` / `Not Marketed` | ⚠️ **自愿申报**，未申报默认显示 Not Marketed。**不能单独证明"本国没卖"**，只能作辅证 |
| Brand name(s) | 一个许可可挂**多个品牌名** | **一个配方挂 5 个牌子 = 典型贴牌结构** |
| List of medicinal ingredients | 官方登记的**成分与剂量** | **与包装标注逐项对照** |
| Recommended use or purpose | 官方批准的功效表述 | 广告宣称超出此范围即为违规 |

### 高价值套路

**① 剂量不符。** 实战：包装标 Folate **2000 µg**，官方许可仅 **1000 µg** → 标签虚标一倍。
（附带的硬知识：加拿大成人叶酸 UL = **1000 µg/日**，2000 µg 本身就超上限，正常不会获批。）

**② 一个许可多品牌。** 实战：NPN 80146614 的品牌名同时含 LOEON / Caitlyn / Dr. Nom / SIAC / TOFO 五个牌子。

**③ 批量注册。** 实战：某持证人 100 条许可**全部集中在 2024–2026 年**，之前一条没有 → 与"老牌"叙事矛盾。

**④ 品牌名曾被不同主体使用。** 检索到 2011–2014 年带该品牌名的许可时，注意其**主品牌名可能是别家**（实战：主品牌实为 Bill®，"LOEON"仅作并列品牌名）。

### 标签要求
许可 NHP 标签**必须印 NPN**。**包装上没有 NPN，本身就是重要发现。**

---

## 澳大利亚

治疗性商品由 **TGA** 管理。补充剂多为"listed medicines"，有 **AUST L** 编号（格式 `AUST L 123456`），可在 **ARTG**（Australian Register of Therapeutic Goods）公开查询。

- 查包装有无 `AUST L` → 查 ARTG 核对**申办人（sponsor）**是谁、是否澳洲主体
- TGA 对listed medicine的**许可声称（permitted indications）**有清单，超出即违规

---

## 中国

### 境内生产/销售
保健食品需**"蓝帽子"**（注册号或备案号，格式如 `国食健注G2021xxxxx` / `食健备G2021xxxxx`），可在**国家市场监督管理总局特殊食品信息查询平台**核对：
- 产品名称、保健功能、**申报企业**、**生产企业**、批准日期

### 进口
- **GACC 备案**：自 2022-01-01 起，境外食品生产企业/出口商须在中国海关总署备案。可查某境外公司是否真有对华出口资格、**备案国别**、备案年份
- ⚠️ 注意 2024-09 起旧 11 位 AQSIQ 号切换为 **18 位 GACC 号**，旧号会显示"失效（Inactive）"——**这是制度切换，不是公司出问题**，不要误判
- 中文标签须有**中文**；进口预包装食品须有境内进口商信息

### 企业信息
用天眼查/企查查或本机可用的企业信息工具核查：
- **注册资本**（实战：某"国际品牌"运营方注册资本仅 **50 万**）
- **注册地址**（"**集群注册**"= 虚拟/共享地址，是空壳特征）
- **经营范围**（是否含生产？还是只有批发/进出口/广告）
- 成立日期、股东、年报

---

## 美国

**无上市前审批**（DSHEA）。所以**不能靠"有没有注册号"判断**。

主攻：
1. **公司注册**：查宣称州的 Secretary of State 企业库（成立日期、注册代理地址、状态）
2. **FDA**：
   - **Warning Letters** 数据库（搜品牌/公司名）
   - **CAERS**（Center for Food Safety and Applied Nutrition Adverse Event Reporting System）
   - **Inspections/Compliance** 记录
3. **USPTO 商标状态**：`DEAD / Abandoned` 是强信号（实战：某品牌 USPTO 申请 2021 年因未答复审查意见而放弃）
   - 官方 TSDR API 需 key（401）；可用 Justia / TrademarkElite 等第三方，但常被 Cloudflare 拦截 → 标注置信度
4. **FTC** 对虚假宣称的执法记录

---

## 德国 / 欧盟

### 监管结构（关键差异）
膳食补充剂（Nahrungsergänzungsmittel）**按食品管理，上市前无需审批**，**没有**类似加拿大 NPN 的公开产品库。
→ 所以**不能用"查不到注册号"当结论**，必须换打法。

### 主攻一：工商登记的「经营范围」（Gegenstand）★最致命
德国公司登记必须写明 `Unternehmensgegenstand`。

> **问自己：这个"保健品品牌"背后的公司，法定经营范围是不是生产保健品？**
> 实战命中：某标着 `Made in Germany` 的叶酸，责任企业登记范围是"**食品、尤其各类饮料的进出口**"——一家葡萄酒/饮料贸易商。**贸易商不可能是胶囊的生产企业。**

查询入口见 `endpoints.md`（North Data 的 **JSON-LD 里直接含 `foundingDate` 和 `member`（董事）**，非常好用）。

同时看：
- 成立日期
- 董事姓名（是否本国人）
- 资本额
- 第三方对 SIC/WZ 的分类（如 `Grosshandel mit Getränken` = 饮料批发）

### 主攻二：零售实测
- `amazon.de`、`rossmann.de`、`dm.de`、`shop-apotheke.com`、`docmorris.de`、`mueller.de`
- **PZN**（Pharmazentralnummer）：进入德国药房数据体系才有。**有 PZN ≠ 广泛在售**
- ⚠️ 药房条目标"**zur Zeit nicht bestellbar**"（暂不可订购）、且缺 LMIV 强制信息（配料/用法）→ 只是**为留下德国痕迹铺的条目**

### 主攻三：合规硬指标
| 检查项 | 依据 | 常见破绽 |
|---|---|---|
| **标签语言** | (EU) 1169/2011 **Art. 15** | 在德国卖却**全英文** → 不是给德国人买的 |
| **健康宣称** | (EC) 1924/2006 | "调节代谢紊乱""治疗耳鸣"等**疾病宣称=违法**；"cerebrovascular health"等未授权宣称 |
| **%NRV** | (EU) 1169/2011 **Annex XIII** | 用 `{baseDir}/scripts/nrv_check.py` 核对 |
| **剂量上限 UL** | EFSA | 用 `{baseDir}/scripts/nrv_check.py --ul` |
| **强制标示** | 1169/2011 + NemV | 缺配料表、保质期、批号、三条警示语 |

### 付钱就能拿的"奖项"
**Monde Selection**（布鲁塞尔）等属**企业付费送评**：官网首页即为 "**Submit a Product**"，且 "Country of origin" 由**申报方自报、机构不核验**。
→ 出现在中文营销里时，**不构成"该国权威认证"**。

---

## 日本

### 监管结构
- **FOSHU（特定保健用食品）**：需厚生劳动省审批，有"特定保健用食品"标识和许可编号
- **FFC（机能性表示食品）**：企业自主备案，需向消费者厅（CAA）提交**机能性表示食品届出番号**（格式如 `A123`）
- **一般食品**：无特殊标识，不得做功能宣称

### 查询路径
- **FFC 备案**：消费者厅官网 `https://www.caa.go.jp/` → 机能性表示食品数据库（日文）
- **公司登记**：法务局登記情報提供サービス（需付费），或第三方 **Musubu** / **Bizmap** / **Houritsu Soudan**
- **渠道实测**：Amazon.co.jp、Rakuten、@cosme

### 红旗
- 宣称"日本药妆"却无 PMDA 或 CAA 任何备案号
- 公司名带"Japan"但登记地址在第三国
- 日文标签机翻痕迹（如「お召し上がりください」写成「食べてください」的粗暴命令形）

---

## 韩国

### 监管结构
- **健康功能食品（건강기능식품）**：需 MFDS（食品药品安全部）备案。多数产品走**品目製造申告**（制造申报），取得**申告受理编号**；个别功能性认证产品才有**健康功能食品认证书**
- **一般食品**：不得做功能宣称

### 查询路径
- **MFDS 备案**：`https://www.mfds.go.kr` → 식품안전나라 → 건강기능식품 정보（韩文）
- **公司登记**：法院登记信息公开系统 `https://www.iros.go.kr`（需韩国手机号），或第三方 **Saramin** / **JobKorea**
- **渠道实测**：Coupang、Naver Smart Store、Olive Young

### 红旗
- 宣称"韩国进口"却无 MFDS 健康功能食品编号
- 公司名带"Korea"但登记地址在第三国
- 韩文标签机翻痕迹

---

## 新西兰

### 监管结构
- **膳食补充剂（Dietary Supplements）**：由 MPI（Ministry for Primary Industries）监管，上市前无需审批
- **与澳洲互认**：Trans-Tasman Mutual Recognition 协定下，澳洲 TGA 产品可在新西兰销售

### 查询路径
- **公司登记**：New Zealand Companies Register `https://companies-register.companiesoffice.govt.nz/`（免费）
- **渠道实测**：HealthPost、Chemist Warehouse NZ、Amazon NZ

### 红旗
- 宣称"新西兰制造"但公司注册在第三国
- 无 MPI 备案（虽非强制，但正规厂商通常有）

---

## 英国 / 香港

### 英国 Companies House
`https://find-and-update.company-information.service.gov.uk/company/<公司号>`

网页正文里直接可读：
- **Registered office address** — 注意**批量注册地址**（如 Croydon 一带）是空壳特征
- **Incorporated on** — 成立日期
- **Nature of business (SIC)** — ⚠️ **`99999 - Dormant Company`（休眠公司）是极强的红旗**
- **Confirmation statement overdue**（年报逾期）
- Officers / Persons with significant control

### 香港公司注册处
查成立日期、公司编号、注册地址、现状（Live）。
实战意义：某"加拿大品牌"的许可持有人是**2020 年才在香港成立**的公司。

### 常见"假洋"命名手法
公司名**字面上带国家名**，实际注册在第三国。
> 实战：商标持有人叫 "**Switzerland** SIAC Health Ltd"，登记地址却在**英国 Croydon**。

---

## 通用：条码

`python3 {baseDir}/scripts/ean_check.py <条码>`

**能读出什么 / 不能读出什么：**
- ✅ 校验位是否正确（正确 = 号码是规范生成的，不是随手编的）
- ✅ GS1 国家前缀（400–440 = 德国；690–699 = 中国；00–13 = 美国/加拿大…）
- ❌ **不能**证明产地！**前缀只表示号码由哪个 GS1 成员组织分配**
- ⚠️ **200–299 是"受限流通/店内码"号段，不是正常零售条码** → 若商品条码落在此段，说明它**不是为开放零售渠道注册的**

**别被"外国前缀"唬住**：任何国家的公司只要加入对应 GS1 组织就能拿到该前缀。
