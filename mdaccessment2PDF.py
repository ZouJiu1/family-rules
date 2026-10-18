#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mdaccessment2PDF.py - 批量将 试卷/ 目录下的 Markdown 试卷转为独立 PDF

用法:
    python3 mdaccessment2PDF.py                     # 全部试卷（不含目录.md）
    python3 mdaccessment2PDF.py 试卷/16岁/16岁-难题试卷.md   # 只转一份

依赖安装（Ubuntu 24.04）:
    sudo apt install texlive-luatex texlive-lang-chinese \
        texlive-lang-japanese fonts-noto-cjk fonts-noto-color-emoji \
        fonts-symbola pandoc texlive-xetex texlive-fonts-recommended

模板与辅助文件复用 md2PDF.sh:
    eisvogel-template/eisvogel.latex
    metadata.yaml
    header-inc.tex
"""
from __future__ import annotations

import sys
import subprocess
from pathlib import Path
from multiprocessing import Pool, cpu_count

# ============ 配置（与 md2PDF.sh 保持一致）============
PROJECT_ROOT = Path(__file__).resolve().parent
TEMPLATE = PROJECT_ROOT / "eisvogel-template" / "eisvogel.latex"
METADATA = PROJECT_ROOT / "metadata.yaml"
HEADER_INC = PROJECT_ROOT / "header-inc.tex"

PANDOC_COMMON_ARGS = [
    "--template", str(TEMPLATE),
    "--pdf-engine", "lualatex",
    "--lua-filter", str(PROJECT_ROOT / "exam-wrap.lua"),
    "-V", "lang=zh-CN",
    "-V", "mainfont=Noto Sans",
    "-V", "watermark=邹九1069679911@qq",
    "-V", "mainfontfallback=NotoColorEmoji:mode=harf",
    "-V", "monofont=Noto Sans Mono CJK SC",
    "-V", "monofontfallback=NotoColorEmoji:mode=harf",
    "-V", "CJKmainfont=Noto Sans CJK SC",
    "-V", "CJKsansfont=Noto Sans CJK SC",
    "-V", "CJKmonofont=Noto Sans CJK SC",
    "-V", "mathfont=Noto Sans Math",
    "--include-in-header", str(HEADER_INC),
    "-V", "geometry:margin=1in",
]

PANDOC_COMMON_ARGS_NO_WATERMARK = [
    "--template", str(TEMPLATE),
    "--pdf-engine", "lualatex",
    "--lua-filter", str(PROJECT_ROOT / "exam-wrap.lua"),
    "-V", "lang=zh-CN",
    "-V", "mainfont=Noto Sans",
    # "-V", "watermark=邹九1069679911@qq",
    "-V", "mainfontfallback=NotoColorEmoji:mode=harf",
    "-V", "monofont=Noto Sans Mono CJK SC",
    "-V", "monofontfallback=NotoColorEmoji:mode=harf",
    "-V", "CJKmainfont=Noto Sans CJK SC",
    "-V", "CJKsansfont=Noto Sans CJK SC",
    "-V", "CJKmonofont=Noto Sans CJK SC",
    "-V", "mathfont=Noto Sans Math",
    "--include-in-header", str(HEADER_INC),
    "-V", "geometry:margin=1in",
]
# =====================================================


def find_all_exam_mds(root: Path) -> list[Path]:
    """递归查找试卷目录下的 Markdown 试卷。

    只处理 **某个年龄子目录里** 的试卷 md，跳过:
      - 试卷/目录.md
      - 试卷/试卷.md
    """
    EXCLUDE_NAMES = {"目录.md", "试卷.md"} #, "家规试卷全集.md", "家规试卷-按题型聚合.md"}
    mds = []
    for p in sorted(root.rglob("*.md")):
        if p.name in EXCLUDE_NAMES:
            continue
        # 必须位于"年龄子目录"里（试卷/XX岁/xxx.md），至少 1 层
        if len(p.relative_to(root).parts) >= 1:
            mds.append(p)
    return sorted(mds)


def check_env() -> None:
    """检查依赖，缺失则给出友好提示。"""
    if not TEMPLATE.exists():
        sys.exit(f"❌ 找不到 Eisvogel 模板: {TEMPLATE}")
    if not METADATA.exists():
        sys.exit(f"❌ 找不到 metadata.yaml: {METADATA}")
    if not HEADER_INC.exists():
        sys.exit(f"❌ 找不到 header-inc.tex: {HEADER_INC}")

    def which(cmd: str) -> bool:
        return subprocess.run(["which", cmd], capture_output=True).returncode == 0

    missing = [c for c in ("pandoc", "lualatex") if not which(c)]
    if missing:
        sys.exit(f"❌ 缺少依赖: {', '.join(missing)}\n   安装: sudo apt install pandoc texlive-luatex")


def md_to_pdf(md_path: Path, no_watermark: bool = False, out_pdf: Path | None = None) -> Path | None:
    """调用 pandoc + lualatex 把单份 md 转成 pdf。失败返回 None。"""
    out_pdf = out_pdf or md_path.with_suffix(".pdf")
    out_pdf = out_pdf.with_suffix(".有水印.pdf")
    cmd = ["pandoc", str(md_path), "-o", str(out_pdf)] + (PANDOC_COMMON_ARGS_NO_WATERMARK if no_watermark else PANDOC_COMMON_ARGS)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not out_pdf.exists():
        # 打印最后一段错误，便于定位
        print(f"    ⚠️  失败: {md_path.relative_to(PROJECT_ROOT)}")
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-10:]
        for line in tail:
            print(f"       {line}")
        return None
    return out_pdf

def md_to_pdf_no_watermark(md_path: Path, no_watermark: bool = True, out_pdf: Path | None = None) -> Path | None:
    """调用 pandoc + lualatex 把单份 md 转成 pdf。失败返回 None。"""
    out_pdf = out_pdf or md_path.with_suffix(".pdf")
    cmd = ["pandoc", str(md_path), "-o", str(out_pdf)] + (PANDOC_COMMON_ARGS_NO_WATERMARK if no_watermark else PANDOC_COMMON_ARGS)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not out_pdf.exists():
        # 打印最后一段错误，便于定位
        print(f"    ⚠️  失败: {md_path.relative_to(PROJECT_ROOT)}")
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-10:]
        for line in tail:
            print(f"       {line}")
        return None
    return out_pdf


def main() -> int:
    check_env()
    exams_root = PROJECT_ROOT / "试卷"

    if len(sys.argv) > 1:
        # 指定了单份 md
        targets = [Path(sys.argv[1]).resolve()]
    else:
        targets = find_all_exam_mds(exams_root)

    print(f"📋 共 {len(targets)} 份试卷待转换")
    ok = 0
    fail = 0

    # Pool 大小: CPU 核数的一半，至少 1，避免单核机器 Pool(0) 报错
    pool_size = max(1, cpu_count() // 2)
    print(f"🧵 使用 {pool_size} 个进程并行转换（CPU 核数={cpu_count()}）")

    with Pool(pool_size) as pool:
        results = pool.map(md_to_pdf, targets)
    with Pool(pool_size) as pool:
        results = pool.map(md_to_pdf_no_watermark, targets)
    for i, pdf in enumerate(results, 1):
        rel = targets[i - 1].relative_to(PROJECT_ROOT)
        print(f"[{i}/{len(targets)}] {rel}")
        if pdf:
            ok += 1
            print(f"    ✅ {pdf.relative_to(PROJECT_ROOT)}")
        else:
            fail += 1

    print(f"\n🎉 完成: 成功 {ok} 份，失败 {fail} 份")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
