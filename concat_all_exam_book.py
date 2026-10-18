#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
concat_all_exam_book.py
-----------------------
把 29 个年龄文件夹下共 87 份试卷的题目，不区分年龄、按题型聚合整理到一张总试卷里。

题型聚合顺序（参考初高中语文/数学/英语/历史考试结构）:
  1. 选择题
  2. 填空题
  3. 判断题
  4. 连线题
  5. 排序题
  6. 计算题 / 数据分析题
  7. 材料分析题 / 案例分析题
  8. 英语翻译题
  9. 简答题
 10. 论述题 / 研究设计题

关键设计：
  - 题目和答案**共用同一套全局编号**（1、2、3、...，跨所有题型连续递增）
  - 每个 item 同时出现在题目区（按题型分组 + 全局编号）和答案区（按题型分组 + 同一全局编号）
  - 这样看到"第 123 题" → 答案区直接找 "123）" 即可

每题都带原始来源标记，例如：
    [来源: 16岁 · 难题试卷]
    第 123 题

输出: 试卷/家规试卷-按题型聚合.md

依赖: 标准库（Python 3.9+）
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXAM_ROOT = ROOT / "试卷"
OUT_FILE = EXAM_ROOT / "家规试卷-按题型聚合.md"

# ---- 题型识别与聚合顺序 ----
CATEGORY_ORDER = [
    "选择题",
    "填空题",
    "判断题",
    "连线题",
    "排序题",
    "计算题",
    "材料/案例分析题",
    "英语翻译题",
    "简答题",
    "论述/研究设计题",
]

SECTION_RE_NUM = re.compile(r"^##\s+[（(]\d+[）)](.+?)(?:[（(].*)?$")
SECTION_RE_ANSWER = re.compile(r"^##\s+参考答案与解析\s*$")

# 题目里的题号前缀（用于剥掉再重编号）
Q_PREFIX_RE = re.compile(r"^\s*\d+[）、.)]\s*")


def detect_category(title_text: str) -> str | None:
    title = title_text.strip()
    if "选择题" in title: return "选择题"
    if "填空题" in title: return "填空题"
    if "连线题" in title: return "连线题"
    if "排序题" in title: return "排序题"
    if "判断题" in title: return "判断题"
    if "计算题" in title or "数据分析" in title: return "计算题"
    if "材料分析" in title or "案例分析" in title: return "材料/案例分析题"
    if "翻译" in title: return "英语翻译题"
    if "简答题" in title: return "简答题"
    if "论述" in title or "研究设计" in title: return "论述/研究设计题"
    return None


def exam_label(file_path: Path) -> str:
    age_dir = file_path.parent.name
    stem = file_path.stem
    level = stem.split("-", 1)[1].replace("试卷", "") if "-" in stem else stem
    return f"{age_dir} · {level}"


def extract_block_until_next_header(lines: list[str], start_idx: int) -> list[str]:
    out = []
    i = start_idx + 1
    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            break
        out.append(line)
        i += 1
    return out


def split_block_into_single_items(block_lines: list[str]) -> list[list[str]]:
    """
    把一个 block（一个题型段落的所有行）按题号前缀 "1）" / "2、" / "3." 切成单题列表。
    每个单题是一个行列表（保留题目 + 多行内容）。
    """
    items: list[list[str]] = []
    current: list[str] = []

    for ln in block_lines:
        stripped = ln.lstrip()
        if Q_PREFIX_RE.match(stripped) or re.match(r"^\s*[①②③④⑤⑥⑦⑧⑨⑩]", stripped):
            # 新题开始：如果 current 非空，先保存
            if current:
                items.append(current)
            current = [ln]
        elif current:
            current.append(ln)
        # 如果 current 为空且不是题号开头（空行或说明行），丢弃

    if current:
        items.append(current)

    # 过滤空 item
    return [it for it in items if any(l.strip() for l in it)]


def parse_single_md(md_path: Path) -> list[dict]:
    """
    解析单份 md，返回题目 item 列表（已扁平化，每题一个 dict）。
    每个 dict: {
        "category": "选择题",     # 题型
        "label": "16岁 · 难题",   # 来源标记
        "question_lines": [...],  # 题目行（剥掉原始题号）
        "answer_lines": [...],    # 对应答案行（剥掉原始题号）
    }
    """
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    label = exam_label(md_path)

    # --- 第一步：按题型 block 切分，记录题型顺序 ---
    question_blocks: list[tuple[str, list[str]]] = []  # (category, block_lines)
    answer_block_lines: list[str] = []  # 整份 md 的答案区行（可能为空）
    categories_in_order: list[str] = []

    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        m_num = SECTION_RE_NUM.match(stripped)
        m_ans = SECTION_RE_ANSWER.match(stripped)

        if m_num:
            cat = detect_category(m_num.group(1))
            if cat:
                if cat not in categories_in_order:
                    categories_in_order.append(cat)
                block = extract_block_until_next_header(lines, i)
                question_blocks.append((cat, block))

        elif m_ans:
            answer_block_lines = extract_block_until_next_header(lines, i)

        i += 1

    # --- 第二步：把每个 question_block 切成单题 items ---
    question_items_by_cat: dict[str, list[dict]] = {}
    for cat, block in question_blocks:
        single_items = split_block_into_single_items(block)
        for item_lines in single_items:
            q_lines = [Q_PREFIX_RE.sub("", ln).lstrip() for ln in item_lines]
            question_items_by_cat.setdefault(cat, []).append({
                "category": cat,
                "label": label,
                "question_lines": q_lines,
            })

    # --- 第三步：把答案 block 切成单题，按题型顺序均匀分配 ---
    # 先按 "N）" 切答案
    answer_pieces: list[list[str]] = []
    cur: list[str] = []
    for ln in answer_block_lines:
        stripped = ln.lstrip()
        if Q_PREFIX_RE.match(stripped) or re.match(r"^\s*[①②③④⑤⑥⑦⑧⑨⑩]", stripped):
            if cur:
                answer_pieces.append(cur)
            cur = [ln]
        elif cur:
            cur.append(ln)
    if cur:
        answer_pieces.append(cur)

    # 答案均匀分配到各题型的题目里
    total_q = sum(len(v) for v in question_items_by_cat.values())
    if answer_pieces and total_q:
        # 把所有题型的 item 按 categories_in_order 拉平
        flat_items: list[dict] = []
        for cat in categories_in_order:
            flat_items.extend(question_items_by_cat.get(cat, []))

        # 答案一对一分配到题目
        assign_count = min(len(flat_items), len(answer_pieces))
        for idx in range(assign_count):
            raw = answer_pieces[idx]
            ans_clean = [Q_PREFIX_RE.sub("", ln).lstrip() for ln in raw]
            ans_clean = [ln for ln in ans_clean if ln.strip()]
            flat_items[idx]["answer_lines"] = ans_clean

    # 拉平返回
    result: list[dict] = []
    for cat in categories_in_order:
        result.extend(question_items_by_cat.get(cat, []))
    return result


def collect() -> list[dict]:
    """遍历所有 md，返回扁平化的题目 item 列表，已按年龄升序 + 难度升序。"""
    level_key = {"简单": 1, "中等": 2, "难题": 3}
    all_files = sorted(
        [p for p in EXAM_ROOT.rglob("*.md")
         if p.name not in {"目录.md", "家规试卷全集.md", "家规试卷-按题型聚合.md"}
         and len(p.relative_to(EXAM_ROOT).parts) >= 2],
        key=lambda p: (
            int(re.match(r"(\d+)", p.parent.name).group(1)),
            level_key.get(p.stem.split("-", 1)[1].replace("试卷", ""), 0)
            if "-" in p.stem else 0,
        ),
    )

    all_items: list[dict] = []
    for md in all_files:
        all_items.extend(parse_single_md(md))
    return all_items


def main() -> int:
    all_items = collect()

    # 给每个 item 分配全局编号（按出现顺序，1、2、3、...）
    for idx, item in enumerate(all_items, 1):
        item["num"] = idx

    # 按题型分组（保持 CATEGORY_ORDER 顺序）
    items_by_cat: dict[str, list[dict]] = {}
    for item in all_items:
        items_by_cat.setdefault(item["category"], []).append(item)

    question_order = [c for c in CATEGORY_ORDER if items_by_cat.get(c)]

    # 输出
    buf: list[str] = []
    buf.append("# 《家规试卷全集》按题型聚合\n")
    buf.append("> 依据《生活规范以及指导家规》编写，作者：邹九，邮箱：1069679911@qq.com")
    buf.append("> 一己之见仅供参考。")
    buf.append("> 本文件把 2-30 岁共 **87 份**试卷的题目和答案，不区分年龄、")
    buf.append("> 按题型重新聚合到一张总试卷里，每题保留原始来源标记。")
    buf.append("> 敏感词已用拼音驼峰代替。")
    buf.append("> 题目和答案共用同一套全局编号，例如**第 123 题** ↔ 答案区**123）** 可直接对应。")
    buf.append("\n---\n")

    total = len(all_items)
    answered = sum(1 for it in all_items if it.get("answer_lines"))
    buf.append(f"**题目总数**：{total} 道　　**附答案**：{answered} 道　　**无答案**：{total - answered} 道\n")

    # ====== 题目前部 ======
    buf.append("\n\n---\n")
    buf.append("# 题目部分（按题型分组，全局编号）\n")

    for i, cat in enumerate(question_order, 1):
        items = items_by_cat.get(cat, [])
        if not items:
            continue
        buf.append(f"\n\n## 第 {i} 部分 · {cat}（共 {len(items)} 题）\n")
        for item in items:
            buf.append(f"**第 {item['num']} 题**　**[来源: {item['label']}]**")
            buf.append("")
            buf.append("\n".join(item["question_lines"]).strip())
            buf.append("")

    # ====== 答案后部 ======
    buf.append("\n\n---\n")
    buf.append("# 参考答案与解析（按题型分组，全局编号）\n")
    buf.append("> 解析末尾的【章节号】指原书《生活规范以及指导家规》的对应章节。\n")

    for i, cat in enumerate(question_order, 1):
        items = items_by_cat.get(cat, [])
        if not items:
            continue
        buf.append(f"\n\n## 第 {i} 部分 · {cat} · 参考答案与解析（共 {len(items)} 题）\n")
        for item in items:
            if item.get("answer_lines"):
                ans_text = "\n".join(item["answer_lines"]).strip()
                buf.append(f"**{item['num']}）**　{ans_text}")
                buf.append("")
            else:
                buf.append(f"**{item['num']}）**　（无参考答案）　*来源: {item['label']}*")
                buf.append("")

    OUT_FILE.write_text("\n".join(buf), encoding="utf-8")
    print(f"✅ 已生成 {OUT_FILE}")
    print(f"   题目 {total} 道 / 有答案 {answered} 道 / 无答案 {total - answered} 道")
    return 0


if __name__ == "__main__":
    sys.exit(main())
