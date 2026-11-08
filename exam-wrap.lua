-- ============================================================
-- exam-wrap.lua
--   Pandoc Lua filter：让家规试卷里挤在同一行的题干/选项/答案自动换行
--
--   Pandoc 把 md 源里的全角空格 '　'（U+3000）原样保留在 Str.text 里，
--   不拆成独立 Space 元素；同时 md 源里的换行转成 SoftBreak，
--   但 LuaLaTeX 默认把 SoftBreak 当成普通空格让 TeX 自己断行。
--   本 filter 显式把全角空格和 SoftBreak 都升级成 LineBreak，
--   这样 PDF 渲染时才会真正换行。
--
-- 用法: pandoc ... --lua-filter=exam-wrap.lua input.md
-- ============================================================

local function process_inline(el)
  -- LineBreak / SoftBreak 直接保留（已经是换行标记）
  if el.t == "LineBreak" or el.t == "SoftBreak" then
    return { pandoc.LineBreak() }   -- 升级为强制换行
  end

  -- 只处理 Str（Str.text 里可能嵌全角空格）
  if el.t ~= "Str" then
    return { el }
  end

  local txt = el.text
  -- 不包含全角空格的 Str 直接返回
  if not txt:find("　") then
    return { el }
  end

  -- 按 '　　'（两个全角空格，试卷里的标准分隔符）拆分
  -- 同时处理单个全角空格（兼容元信息行里的单个 　）
  local parts = {}
  -- 先把 '　　' 替换成 '\n'，再把单个 '　' 也替换成 '\n'
  txt = txt:gsub("　　", "\n"):gsub("　", "\n")

  for piece in txt:gmatch("[^\n]+") do
    piece = piece:gsub("^%s+", ""):gsub("%s+$", "")
    if piece ~= "" then
      table.insert(parts, pandoc.Str(piece))
      table.insert(parts, pandoc.LineBreak())
    end
  end
  -- 去掉末尾多余的 LineBreak
  if #parts > 0 and parts[#parts].t == "LineBreak" then
    table.remove(parts)
  end
  return parts
end

function Para(p)
  local new = {}
  for _, el in ipairs(p.content) do
    for _, ne in ipairs(process_inline(el)) do
      table.insert(new, ne)
    end
  end
  return pandoc.Para(new)
end
