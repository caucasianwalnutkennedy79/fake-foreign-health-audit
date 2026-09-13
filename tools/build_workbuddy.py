#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_workbuddy.py — 从 master 生成 Windows WorkBuddy（CodeBuddy Code）变体。

为什么需要它
------------
两个平台的 skill 约定不同，差异是**机械的**，手工维护两份必然会漂移：

| 项目 | OpenClaw | WorkBuddy (CodeBuddy Code) |
|---|---|---|
| 脚本路径占位符 | `{baseDir}` | `${CODEBUDDY_SKILL_DIR}` |
| 依赖声明 | `metadata.openclaw.requires.bins` | `allowed-tools:` |
| 安装目录 | `~/.openclaw/workspace/<agent>/skills/` | `~/.codebuddy/skills/` 或 `<项目>/.codebuddy/skills/` |
| Python 命令 | `python3` | `python`（Windows 常见；`py -3` 为兜底） |

用法
----
    python3 tools/build_workbuddy.py [--out DIR]

默认输出到仓库同级的 `workbuddy-fake-foreign-health-audit/`。

仅依赖标准库。
"""

import argparse
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MASTER = os.path.dirname(HERE)
DEFAULT_OUT = os.path.join(os.path.dirname(MASTER), "workbuddy-fake-foreign-health-audit")

# master 上要排除的（版本库 / OpenClaw 专属元数据 / 生成物）
EXCLUDE_DIRS = {".git", ".openclaw", ".cache", "__pycache__", "tools", "dist"}
EXCLUDE_FILES = {".gitignore", ".DS_Store"}

# ---------------------------------------------------------------- frontmatter
WB_FRONTMATTER = """---
name: fake-foreign-health-audit
description: 鉴别药品/保健品是否为"假洋货"（伪造洋品牌身份）。当用户给出商品链接、包装图片或品牌名，问"是不是假洋货""是不是真进口""XX国品牌是真的吗"，或需要核验某"进口"保健品的产地、资质、宣称国本土在售情况时使用。覆盖加拿大 NPN/LNHPD、德国欧盟工商登记与健康宣称合规、美国 FDA/商标、澳洲 TGA、中国蓝帽子与 GACC 备案。
allowed-tools: Read, Write, Bash, WebFetch
---

<!--
  本文件由 master 仓库的 tools/build_workbuddy.py 自动生成。
  请勿直接修改此仓库——改动请提到 master：
  https://github.com/longppai68-ai/fake-foreign-health-audit
-->

"""

# ---------------------------------------------------------------- 文本替换
def convert_text(text: str, relpath: str) -> str:
    """把 OpenClaw 写法转成 WorkBuddy + Windows 写法。"""
    is_py = relpath.endswith(".py")

    # 1) 路径占位符
    text = text.replace("{baseDir}", "${CODEBUDDY_SKILL_DIR}")

    if not is_py:
        # 2) Python 命令名：Windows 上通常是 python（py -3 为兜底）
        #    逐词替换，覆盖行首 / 引用块(> ) / 表格(| ) 等所有位置
        text = re.sub(r"\bpython3\b", "python", text)

        # 3) 临时路径 → 跨平台写法
        text = text.replace('/tmp/zoom.png', 'zoom.png')
        text = text.replace('read_image /tmp/zoom.png', 'read_image zoom.png')
        text = text.replace(
            "open('/tmp/nrv.html',encoding='utf-8',errors='replace')",
            "open('nrv.html',encoding='utf-8',errors='replace')")
        text = text.replace('--cache-dir /tmp/lnhpd', '--cache-dir "%TEMP%\\\\lnhpd"')
    else:
        # .py：保留 shebang（跨平台正确），但把 --help 里的用法示例改成 python
        lines = text.splitlines(keepends=True)
        out = []
        for ln in lines:
            if not ln.startswith("#!") and "python3 " in ln:
                ln = ln.replace("python3 ", "python ")
            out.append(ln)
        text = "".join(out)

    return text


def convert_skill_md(text: str) -> str:
    """SKILL.md 额外处理：换 frontmatter + 注入 Windows 须知。"""
    # 替换 frontmatter（自第一个 --- 到第二个 ---）
    m = re.match(r"(?s)^---\n.*?\n---\n", text)
    if not m:
        raise SystemExit("SKILL.md 未找到 frontmatter")
    text = WB_FRONTMATTER + text[m.end():].lstrip("\n")

    windows_note = """
## ⚠️ Windows / WorkBuddy 环境须知（先读）

本变体面向 **Windows 上的 WorkBuddy（CodeBuddy Code）**。开始前先确认两件事：

**1) 确认 Python 命令名**

```bash
python --version     # 首选
py -3 --version      # 若上一条失败，用 Windows Python 启动器
```

本文档中的命令一律写成 `python`。若你的环境只有 `py -3`，**自行替换**即可——
四个脚本都只用标准库，任何 Python 3.8+ 都能跑。

**2) 路径分隔符**

脚本路径用 `${CODEBUDDY_SKILL_DIR}` 占位符，由 WorkBuddy 自动替换为该 skill 的绝对路径，
**不要**手写成 `scripts/x.py` 这种相对路径——那取决于当前工作目录，会找不到文件。

**3) 抓取命令**

文档里的 `curl` 命令在 Windows 10 1803+ 自带 `curl.exe`，可直接用。
若在 PowerShell 里执行，注意引号规则与 bash 不同；建议在 WorkBuddy 的 Bash 中执行。

**4) 缓存目录**

`lnhpd_search.py` 默认把约 140 MB 的加拿大数据库缓存到用户主目录下的 `.cache/lnhpd`。
Windows 上即 `%USERPROFILE%\\.cache\\lnhpd`。若该位置不可写，加参数指定：

```bash
python ${CODEBUDDY_SKILL_DIR}/scripts/lnhpd_search.py --brand "LOEON" --cache-dir "%TEMP%\\lnhpd"
```

---

"""
    # 插到 "# 假洋货鉴别（药品 / 保健品）" 标题之后、正文之前
    anchor = "# 假洋货鉴别（药品 / 保健品）\n"
    i = text.find(anchor)
    if i < 0:
        return text
    j = i + len(anchor)
    return text[:j] + windows_note + text[j:].lstrip("\n")


def convert_readme(text: str) -> str:
    """README 额外处理：换安装段落、去掉 OpenClaw 专属的维护章节。"""
    # 目录结构树里的 SKILL.md 注释
    text = text.replace(
        "├── SKILL.md                      # 主文件：工作流、原则、红旗清单、输出契约（面向 agent）",
        "├── SKILL.md                      # 主文件：工作流、原则、红旗清单、输出契约（面向 agent）")

    # 安装章节整体替换
    install_new = """## 安装

### 方式一：放到用户级 skills 目录（推荐）

Windows：

```bat
mkdir "%USERPROFILE%\\.codebuddy\\skills"
xcopy /E /I fake-foreign-health-audit "%USERPROFILE%\\.codebuddy\\skills\\fake-foreign-health-audit"
```

macOS / Linux：

```bash
mkdir -p ~/.codebuddy/skills
cp -R fake-foreign-health-audit ~/.codebuddy/skills/
```

### 方式二：放到项目级 skills 目录

在项目根目录下：

```bat
mkdir ".codebuddy\\skills"
xcopy /E /I fake-foreign-health-audit ".codebuddy\\skills\\fake-foreign-health-audit"
```

> WorkBuddy 支持**项目级**（`.codebuddy/skills/`）与**用户级**（`~/.codebuddy/skills/`）两种位置，见[官方文档](https://www.workbuddy.cn/docs/cli/skills)。

### 验证安装

在 WorkBuddy 里直接提问即可，skill 会按 `description` 自动匹配：

> "这个淘宝链接是不是假洋货？"（附链接或包装图）

或手动确认命令能跑：

```bat
python "%USERPROFILE%\\.codebuddy\\skills\\fake-foreign-health-audit\\scripts\\nrv_check.py" --help
```
"""
    # 注意：用 lambda 作替换，否则 install_new 里的 \\. 与 \\s 会被 re 当成转义序列
    text = re.sub(r"(?s)## 安装\n.*?(?=\n## )", lambda m: install_new + "\n", text, count=1)

    # 本仓库是生成物，不该在这里维护——把「开发与维护」换成回主仓库的指引
    dev_new = """## 开发与维护

> ⚠️ **本仓库是自动生成的产物，请勿直接修改。**

它是 master 仓库的 **Windows WorkBuddy 变体**：

**https://github.com/longppai68-ai/fake-foreign-health-audit**

改动流程：

1. 在 master 仓库修改源文件
2. 运行 `python3 tools/build_workbuddy.py` 重新生成本变体
3. 将生成结果推送到本仓库

Issue、PR、讨论请一律提到 **master 仓库**，提到这里无法被处理。

### 两个平台的差异（由构建脚本自动转换）

| 项目 | master（OpenClaw） | 本仓库（WorkBuddy） |
|---|---|---|
| 脚本路径占位符 | `{baseDir}` | `${CODEBUDDY_SKILL_DIR}` |
| 依赖声明 | `metadata.openclaw.requires.bins` | `allowed-tools` |
| 安装目录 | `~/.openclaw/workspace/<agent>/skills/` | `~/.codebuddy/skills/` 或 `<项目>/.codebuddy/skills/` |
| Python 命令 | `python3` | `python`（`py -3` 兜底） |

### 本地校验

```bat
python scripts\\nrv_check.py --help
python scripts\\ean_check.py 4262366230132
```
"""
    text = re.sub(r"(?s)## 开发与维护\n.*?(?=\n## )", lambda m: dev_new + "\n", text, count=1)

    return text


def main():
    ap = argparse.ArgumentParser(description="生成 Windows WorkBuddy 变体")
    ap.add_argument("--out", default=DEFAULT_OUT, help="输出目录")
    args = ap.parse_args()

    if os.path.exists(args.out):
        shutil.rmtree(args.out)
    os.makedirs(args.out)

    n_files = 0
    for root, dirs, files in os.walk(MASTER):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        rel = os.path.relpath(root, MASTER)
        rel = "" if rel == "." else rel
        for f in files:
            if f in EXCLUDE_FILES or f.endswith(".pyc"):
                continue
            src = os.path.join(root, f)
            dst_dir = os.path.join(args.out, rel) if rel else args.out
            os.makedirs(dst_dir, exist_ok=True)
            dst = os.path.join(dst_dir, f)

            if f.endswith((".md", ".py")):
                with open(src, encoding="utf-8") as fh:
                    txt = fh.read()
                relpath = os.path.join(rel, f) if rel else f
                txt = convert_text(txt, relpath)
                if f == "SKILL.md":
                    txt = convert_skill_md(txt)
                elif f == "README.md":
                    txt = convert_readme(txt)
                with open(dst, "w", encoding="utf-8") as fh:
                    fh.write(txt)
            else:
                shutil.copy2(src, dst)
            n_files += 1

    print(f"✅ 已生成 {n_files} 个文件 → {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
