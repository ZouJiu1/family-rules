#!/bin/bash
# ============================================================
# md2PDF.sh  -  Markdown 转 PDF（LuaLaTeX 引擎 + Eisvogel）
#   支持: 封面 / 目录 / 章节编号 / 中文 / 彩色 emoji / 特殊符号
#   符号全部由 header-inc.tex 的 newunicodechar 处理
# 用法: ./md2PDF.sh ["你的markdown文件名.md"]
#
# 依赖安装（Ubuntu 24.04）:
#   sudo apt install texlive-luatex texlive-lang-japanese fonts-noto-color-emoji pandoc
#   sudo apt install fonts-symbola fonts-noto-cjk texlive-lang-chinese texlive-xetex  # 推荐，■ ≥ 等符号兜底
# ============================================================
set -e

INPUT_MD="${1:-full version 完整版.md}"
OUTPUT_PDF="${INPUT_MD%.md}.pdf"
OUTPUT_PDF="fullversion生活规范以及指导家规.pdf"
TEMPLATE_DIR="./eisvogel-template"

if [ ! -f "${TEMPLATE_DIR}/eisvogel.latex" ]; then
  echo "❌ 错误: 找不到 ${TEMPLATE_DIR}/eisvogel.latex"
  echo "   请确认 eisvogel-template/ 目录完整"
  exit 1
fi

if ! kpsewhich luaotfload.sty >/dev/null 2>&1; then
  echo "❌ 缺少 luaotfload（LuaLaTeX 加载字体必需）"
  echo "   安装: sudo apt install texlive-luatex"
  exit 1
fi

echo "📄 输入: ${INPUT_MD}"
echo "📄 输出: ${OUTPUT_PDF}"
echo "🛠  正在用 pandoc + lualatex + Eisvogel 编译..."

pandoc metadata.yaml "${INPUT_MD}" \
  -o "${OUTPUT_PDF}" \
  --template="${TEMPLATE_DIR}/eisvogel.latex" \
  --pdf-engine=lualatex \
  --top-level-division=chapter \
  --toc \
  --toc-depth=3 \
  -V lang=zh-CN \
  -V mainfont="Noto Sans" \
  -V mainfontfallback="NotoColorEmoji:mode=harf" \
  -V monofont="Noto Sans Mono CJK SC" \
  -V monofontfallback="NotoColorEmoji:mode=harf" \
  -V CJKmainfont="Noto Sans CJK SC" \
  -V CJKsansfont="Noto Sans CJK SC" \
  -V CJKmonofont="Noto Sans CJK SC" \
  -V mathfont="Noto Sans Math" \
  --include-in-header=./header-inc.tex \
  -V geometry:margin=1in \
  > md2PDF.log 2>&1

if [ -f "${OUTPUT_PDF}" ]; then
  echo "✅ 完成: ${OUTPUT_PDF}"
else
  echo "❌ 编译失败，错误日志已保存到 md2PDF.log，最后 30 行如下："
  tail -30 md2PDF.log
  exit 1
fi
