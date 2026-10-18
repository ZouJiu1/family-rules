#!/bin/bash
# ============================================================
# mdaccessment2PDF.sh  -  批量把 试卷/ 目录下的 Markdown 试卷
#                         转为独立 PDF（LuaLaTeX + Eisvogel）
#
# 复用 md2PDF.sh 的 Eisvogel 模板、metadata.yaml、header-inc.tex
# 调用 Python 脚本 mdaccessment2PDF.py
#
# 用法:
#   ./mdaccessment2PDF.sh                 # 全部 87 份试卷
#   ./mdaccessment2PDF.sh 试卷/16岁/16岁-难题试卷.md   # 只转一份
# ============================================================
set -e

./concat_all_exam_book.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# ---- 复用 md2PDF.sh 的依赖检查 ----
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

if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ 找不到 python3"
  exit 1
fi

echo "🛠  正在批量转换 Markdown 试卷 -> PDF ..."
python3 mdaccessment2PDF.py "$@"
