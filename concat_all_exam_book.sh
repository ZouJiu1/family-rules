#!/bin/bash
# 拼接所有试卷 -> 家规试卷全集.md
# 顺序: 按年龄文件夹升序；每个年龄内按 简单 -> 中等 -> 难题 顺序
set -e
cd "$(dirname "$0")"

OUT="试卷/家规试卷全集.md"
# 先写总封面
cat > "$OUT" <<'EOF'
# 《家规试卷全集》

> 依据《生活规范以及指导家规》（full version 完整版.md）编写，作者：邹九，邮箱：1069679911@qq.com
> 一己之见仅供参考。
> 本全集收录 2-30 岁共 29 个年龄段、每年龄段 3 份试卷（简单 ★ / 中等 ★★ / 难题 ★★★），合计 **87 份试卷**。
> 题型参考语文、数学、英语、历史等考试。敏感词一律用拼音驼峰代替。
> 每份试卷末尾均附【参考答案与解析】。

---

EOF

for age_dir in $(ls -d 试卷/[0-9]*岁* 2>/dev/null | sort); do
    for level in 简单 中等 难题; do
        f="${age_dir}/$(basename "$age_dir")-${level}试卷.md"
        if [ -f "$f" ]; then
            echo -e "\n\n---\n" >> "$OUT"
            cat "$f" >> "$OUT"
        fi
    done
done

echo "✅ 已生成 $OUT（$(wc -l < "$OUT") 行）"


#!/bin/bash
# ============================================================
# concat_all_exam_book.sh
#   把 29 个年龄文件夹下 87 份试卷，不区分年龄、按题型聚合，
#   生成一张总试卷: 试卷/家规试卷-按题型聚合.md
#
#   按题型顺序：选择 → 填空 → 判断 → 连线 → 排序 → 计算
#                → 材料/案例分析 → 英语翻译 → 简答 → 论述/研究设计
#   每份题目都带原始来源标记，答案与解析同样按题型分组置于文末。
#
# 用法: ./concat_all_exam_book.sh
# ============================================================
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ 找不到 python3"
  exit 1
fi

python3 concat_all_exam_book.py

echo ""
echo "🛠  若需要把聚合后的总试卷转为 PDF，可运行:"
echo "   pandoc metadata.yaml 试卷/家规试卷-按题型聚合.md \\"
echo "     -o 试卷/家规试卷-按题型聚合.pdf \\"
echo "     --template=eisvogel-template/eisvogel.latex --pdf-engine=lualatex \\"
echo "     --lua-filter=exam-wrap.lua --toc --toc-depth=2 \\"
echo "     -V lang=zh-CN -V geometry:margin=1in \\"
echo "     --include-in-header=header-inc.tex"
