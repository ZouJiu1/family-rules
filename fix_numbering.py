#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_numbering.py
----------------
修复 87 份原始试卷的编号问题：
  - 题目区：把每个题型内部从 1 开始的分段编号，改成整张试卷全局连续编号 1,2,3,...N
  - 答案区：同步改成全局连续编号（如果已经是全局连续的就不动）
  - 同步修正 "本试卷共（X）道题" 那一行

不修改任何题目文字内容、选项、解析、章节引用。只改编号数字。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXAM_ROOT = ROOT / "试卷"

# 匹配题号行首：行首空白 + 数字 + 常见题目标点 + 内容
Q_NUM_RE = re.compile(r"^(\s*)(\d+)([）、.)])")

# 匹配答案区行首：行首空白 + 数字 + 右括号/全角右括号 + 内容
A_NUM_RE = re.compile(r"^(\s*)(\d+)([）)])")

# 答案区的小标题，如 "### （1）选择题"、"### （2）判断题" —— 这些不动
A_SUBHEADING_RE = re.compile(r"^###\s+[（(]\d+[）)]")

# 题目区的大标题，如 "## （1）选择题"、"## （2）判断题" —— 这些不动
Q_HEADING_RE = re.compile(r"^##\s+[（(]\d+[）)]")

# "本试卷共（X）道题"
Q_COUNT_RE = re.compile(r"本试卷共[（(]\s*\d+\s*[）)]道题")


def fix_one_file(md_path: Path) -> tuple[bool, int]:
    """修复单份文件。返回 (是否有改动, 题目总数)。"""
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # 找到答案区起点
    ans_idx = None
    for i, l in enumerate(lines):
        if "参考答案与解析" in l and l.strip().startswith("#"):
            ans_idx = i
            break
    if ans_idx is None:
        return False, 0

    # ----- 第一步：修复题目区 -----
    # 收集所有题号位置（哪些行需要改编号）
    q_line_indices = []
    q_new_nums = []  # 新的编号列表

    counter = 1
    for i in range(ans_idx):
        l = lines[i]
        if Q_HEADING_RE.match(l.strip()):
            continue  # 大标题不动
        m = Q_NUM_RE.match(l)
        if m:
            q_line_indices.append(i)
            q_new_nums.append(counter)
            counter += 1

    total_q = counter - 1
    q_changed = False

    # 执行替换
    for idx, new_num in zip(q_line_indices, q_new_nums):
        original = lines[idx]
        new_line = Q_NUM_RE.sub(lambda m: f"{m.group(1)}{new_num}{m.group(3)}", original, count=1)
        if new_line != original:
            lines[idx] = new_line
            q_changed = True

    # 同步修正 "本试卷共（X）道题"
    count_line_changed = False
    for i in range(ans_idx):
        if Q_COUNT_RE.search(lines[i]):
            original = lines[i]
            new_line = Q_COUNT_RE.sub(f"本试卷共（{total_q}）道题", original, count=1)
            if new_line != original:
                lines[i] = new_line
                count_line_changed = True

    # ----- 第二步：修复答案区 -----
    # 答案区可能有两种模式：
    #   A) 全局连续（好的）——直接用 1..total_q
    #   B) 分段（坏的）——需要按出现顺序重新编号为 1..total_q
    # 答案区不管原来是什么模式，直接按出现顺序 1..N 重排
    a_line_indices = []
    counter = 1
    for i in range(ans_idx + 1, len(lines)):
        l = lines[i]
        if A_SUBHEADING_RE.match(l.strip()):
            continue  # 小标题不动
        m = A_NUM_RE.match(l)
        if m:
            a_line_indices.append(i)
            lines[i] = A_NUM_RE.sub(lambda mm, c=counter: f"{mm.group(1)}{c}{mm.group(3)}", l, count=1)
            counter += 1
    # 答案行总数应该 == 题目总数
    _ = a_line_indices  # 仅用于后续 debug 检查

    # ----- 写回 -----
    changed = q_changed or count_line_changed
    if changed:
        md_path.write_text("\n".join(lines), encoding="utf-8")

    return changed, total_q


def main() -> int:
    total_files = 0
    fixed_files = 0
    skipped_files = 0
    report = []

    for md_path in sorted(EXAM_ROOT.rglob("*.md")):
        rel = md_path.relative_to(EXAM_ROOT)
        if len(rel.parts) < 2:
            continue
        if md_path.name in {"目录.md", "家规试卷全集.md", "家规试卷-按题型聚合.md"}:
            continue

        total_files += 1
        changed, total_q = fix_one_file(md_path)
        if changed:
            fixed_files += 1
            report.append(f"  ✅ {rel} — 共 {total_q} 题，编号已重排为全局连续")
        else:
            skipped_files += 1

    print(f"📝 扫描 {total_files} 份原始试卷")
    print(f"🛠  修复 {fixed_files} 份（题目区编号分段 → 全局连续）")
    print(f"⏭  跳过 {skipped_files} 份（编号已正确）\n")
    if report:
        print("修复清单：")
        for r in report:
            print(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
