from pptx import Presentation
from pptx.util import Mm, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
import sys

OUT = sys.argv[1]
W, H = 210, 297
M = 14  # margin mm
FONT = "Yu Gothic"
INK = RGBColor(0x1A, 0x1A, 0x1A)
GRAY = RGBColor(0x88, 0x88, 0x88)
LIGHT = RGBColor(0xE6, 0xE6, 0xE6)
PH = RGBColor(0xD4, 0xD4, 0xD4)
PH_DRAW = RGBColor(0xDC, 0xE3, 0xEA)
ACC = RGBColor(0xC8, 0x4B, 0x1E)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

WORKS = [
    ("01", "大型ソフトクリーム サイン造形", "2021", "図面"),
    ("02", "ロックワーク（擬岩）", "2022", "CAD"),
    ("03", "地形ジオラマ（古墳）", "2022", "図面"),
    ("04", "石室 断面模型", "2022", "図面"),
    ("05", "全身骨格レプリカ", "2022", "資料・3Dデータ"),
    ("06", "土器 復元レプリカ", "2022", "図面"),
    ("07", "円形モニュメントサイン", "2023", "図面"),
    ("08", "方形墳 分割組立模型", "2023", "図面"),
    ("09", "巨大柑橘オブジェ", "2023", "図面"),
    ("10", "串焼き型ライト × ツリー装飾", "2023", "図面"),
    ("11", "鍾乳洞ジオラマ ボックス", "2024", "図面"),
    ("12", "屋内遊具施設", "2024", "図面"),
    ("13", "コンテナハウス 縮尺模型", "2025", "図面"),
    ("14", "大型頭部造形", "2025", "原寸造形データ"),
]
KEY = {"01", "02", "05", "08", "12", "14"}  # 詳細見開きを持つ主力作品

prs = Presentation()
prs.slide_width, prs.slide_height = Mm(W), Mm(H)
BLANK = prs.slide_layouts[6]


def box(s, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE, name=None, lw=0.5):
    sh = s.shapes.add_shape(shape, Mm(x), Mm(y), Mm(w), Mm(h))
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line; sh.line.width = Pt(lw)
    sh.shadow.inherit = False
    if name:
        sh.name = name
    return sh


def text(s, x, y, w, h, t, size=9, bold=False, color=INK, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, spacing=None, ls=None):
    tb = s.shapes.add_textbox(Mm(x), Mm(y), Mm(w), Mm(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    for i, line in enumerate(t.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if ls:
            p.line_spacing = ls
        r = p.add_run(); r.text = line
        f = r.font; f.size = Pt(size); f.bold = bold; f.color.rgb = color; f.name = FONT
        rPr = r._r.get_or_add_rPr()
        ea = rPr.makeelement("{http://schemas.openxmlformats.org/drawingml/2006/main}ea", {"typeface": FONT})
        rPr.append(ea)
        if spacing is not None:
            rPr.set("spc", str(int(spacing * 100)))
    return tb


def hline(s, x1, y, x2, color=INK, w=0.5):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Mm(x1), Mm(y), Mm(x2), Mm(y))
    c.line.color.rgb = color; c.line.width = Pt(w)
    return c


def photo(s, x, y, w, h, name, label, fill=PH):
    """写真差し替え枠。PowerPointで右クリック→図の変更／塗りつぶし→図 で差し替え"""
    b = box(s, x, y, w, h, fill=fill, name=name)
    c1 = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Mm(x), Mm(y), Mm(x + w), Mm(y + h))
    c2 = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Mm(x + w), Mm(y), Mm(x), Mm(y + h))
    for c in (c1, c2):
        c.line.color.rgb = WHITE; c.line.width = Pt(0.5)
    text(s, x, y + h / 2 - 8, w, 16, f"{label}\n{w:.0f} × {h:.0f} mm", 8, color=GRAY,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    return b


def folio(s, n, section, dark=False):
    left = n % 2 == 1  # 奇数ページ=見開き左（A3で p1|p2, p3|p4 ...）
    col = WHITE if dark else GRAY
    if left:
        text(s, M, H - 10, 60, 5, f"{n:02d}   {section}", 7, color=col, spacing=1)
    else:
        text(s, W - M - 60, H - 10, 60, 5, f"{section}   {n:02d}", 7, color=col,
             align=PP_ALIGN.RIGHT, spacing=1)


def caption_band(s, y, h, kind_en, kind_jp, no, title, notes, n, left, dark_fill=RGBColor(0x14, 0x14, 0x14)):
    band = box(s, 0, y, W, h, fill=dark_fill)
    # 透過（60%不透明）
    from lxml import etree
    sf = band.fill._xPr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}solidFill")
    clr = sf[0]
    a = etree.SubElement(clr, "{http://schemas.openxmlformats.org/drawingml/2006/main}alpha"); a.set("val", "78000")
    text(s, M, y + 6, 80, 5, kind_en, 8, bold=True, color=ACC, spacing=3)
    text(s, M, y + 11, 120, 8, f"{kind_jp}", 15, bold=True, color=WHITE)
    text(s, W - M - 90, y + 6, 90, 5, f"{no}  {title}", 8, color=WHITE, align=PP_ALIGN.RIGHT)
    text(s, M, y + 21, W - 2 * M, h - 28, notes, 8, color=WHITE, ls=1.35)
    text(s, (M if left else W - M - 60), H - 10, 60, 5,
         f"{n:02d}   {no} {title}" if left else f"{no} {title}   {n:02d}", 7,
         color=RGBColor(0xBB, 0xBB, 0xBB), align=(PP_ALIGN.LEFT if left else PP_ALIGN.RIGHT))


pages = []  # (builder, args)


# ---------------- front ----------------
def p_cover(s, n):
    box(s, 0, 0, W, H, fill=RGBColor(0x14, 0x14, 0x14))
    text(s, M + 4, 40, 150, 8, "PORTFOLIO 2026", 10, color=ACC, bold=True, spacing=6)
    text(s, M + 4, 70, 180, 60, "描いたものを、\nそのまま立たせる。", 30, bold=True, color=WHITE, ls=1.25)
    hline(s, M + 4, 140, M + 44, ACC, 1.5)
    text(s, M + 4, 148, 180, 30, "図面 × 実物", 16, color=WHITE)
    text(s, M + 4, 230, 180, 12, "的場 道雄", 20, bold=True, color=WHITE)
    text(s, M + 4, 244, 180, 6, "MICHIO MATOBA", 9, color=GRAY, spacing=4)
    text(s, M + 4, 252, 180, 6, "空間デザイン / 美術造形・FRP / 施工管理 / 3D（Rhino・Vectorworks・ZBrush）", 8, color=GRAY)


def p_keyvisual(s, n):
    photo(s, 0, 0, W, H, "IMG_COVER", "表紙キービジュアル（代表作の実物写真・全面）")
    text(s, W - M - 100, H - 22, 100, 6, "【代表作名】 / 【年】", 8, color=INK, align=PP_ALIGN.RIGHT)


def p_profile(s, n):
    text(s, M, 22, 100, 5, "PROFILE", 9, bold=True, color=ACC, spacing=4)
    text(s, M, 30, 150, 12, "的場 道雄", 22, bold=True)
    text(s, M, 44, 180, 6, "空間デザイン × 美術造形 × 施工管理　｜　京都在住", 9, color=GRAY)
    hline(s, M, 54, W - M, LIGHT)
    photo(s, M, 62, 60, 75, "IMG_PORTRAIT", "顔写真 / 作業風景")
    text(s, M + 68, 62, W - 2 * M - 68, 75,
         "展示会・商業施設・テーマパークの空間制作に15年以上。\n"
         "図面（Rhinoceros / Vectorworks / ZBrush）で製作可能な仕様に落とし込み、"
         "FRP造形・3D制作・現場施工・品質確認まで一気通貫で担当。\n\n"
         "設計と現場の中間に立ち、複数業者を調整して納期内に納めることが強み。\n\n"
         "【志望先に合わせた2〜3行を記入】", 9.5, ls=1.5)
    text(s, M, 150, 80, 5, "SKILLS", 8, bold=True, color=ACC, spacing=3)
    skills = [("設計・3D", "Rhinoceros / Vectorworks / ZBrush / AutoCAD"),
              ("造形・製作", "FRP造形・成形 / 型取り / 3Dプリント / CNC / 塗装"),
              ("計測", "3Dスキャン / フォトグラメトリ / 点群処理"),
              ("管理", "積算・見積 / 工程・品質・安全管理 / 協力会社調整")]
    y = 158
    for k, v in skills:
        hline(s, M, y, W - M, LIGHT)
        text(s, M, y + 3, 35, 6, k, 9, bold=True)
        text(s, M + 38, y + 3, W - 2 * M - 38, 6, v, 9)
        y += 13
    text(s, M, 218, 80, 5, "HIGHLIGHTS", 8, bold=True, color=ACC, spacing=3)
    hl = [("約1億円 / 約1年", "大型テーマパーク ライド装飾"),
          ("FRP 1,000㎡超", "海外IPテーマエリア（終盤90日）"),
          ("約3.5億円規模", "制作進行・協力会社調整")]
    cw = (W - 2 * M - 8) / 3
    for i, (a, b) in enumerate(hl):
        x = M + i * (cw + 4)
        box(s, x, 226, cw, 34, line=LIGHT)
        text(s, x + 4, 231, cw - 8, 10, a, 12, bold=True)
        text(s, x + 4, 245, cw - 8, 12, b, 8, color=GRAY)
    folio(s, n, "PROFILE")


def p_method(s, n):
    text(s, M, 22, 100, 5, "HOW I WORK", 9, bold=True, color=ACC, spacing=4)
    text(s, M, 30, 180, 24, "図面で決めて、\n実物で応える。", 20, bold=True, ls=1.2)
    text(s, M, 58, W - 2 * M, 12,
         "本ポートフォリオは各作品を見開きで構成。左ページ＝図面、右ページ＝実物。\n同じ位置・同じ大きさで並べ、図面どおりに納めた精度を比較で見せます。", 9, color=GRAY, ls=1.4)
    steps = [("01", "ヒアリング", "予算・納期・設置条件・安全を数値に置き換える"),
             ("02", "図面", "製作できる寸法・分割・構造を決める"),
             ("03", "CG・検証", "形と見え方を関係者と先に合わせる"),
             ("04", "製作", "FRP・切削・3Dプリント・塗装を使い分ける"),
             ("05", "施工・検品", "現場で納め、仕上がりと安全を確認する")]
    y = 82
    for no, t, d in steps:
        box(s, M, y, 14, 14, fill=INK)
        text(s, M, y, 14, 14, no, 9, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        text(s, M + 20, y + 1, 50, 6, t, 11, bold=True)
        text(s, M + 20, y + 8, W - 2 * M - 20, 6, d, 8.5, color=GRAY)
        y += 22
    # 見開き構成図
    text(s, M, 200, 100, 5, "LAYOUT", 8, bold=True, color=ACC, spacing=3)
    bx, by, bw, bh = M + 20, 210, 60, 70
    box(s, bx, by, bw, bh, fill=PH_DRAW, line=GRAY)
    box(s, bx + bw, by, bw, bh, fill=PH, line=GRAY)
    text(s, bx, by, bw, bh, "左：図面\nA4縦", 10, bold=True, color=INK, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, bx + bw, by, bw, bh, "右：実物\nA4縦", 10, bold=True, color=INK, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, bx, by + bh + 2, bw * 2, 5, "見開き A3（420 × 297 mm）", 7.5, color=GRAY, align=PP_ALIGN.CENTER)
    folio(s, n, "HOW I WORK")


def p_index(s, n, pagemap):
    text(s, M, 22, 100, 5, "INDEX", 9, bold=True, color=ACC, spacing=4)
    text(s, M, 30, 150, 12, "掲載作品", 20, bold=True)
    y = 52
    for no, title, yr, _ in WORKS:
        hline(s, M, y, W - M, LIGHT)
        text(s, M, y + 3.5, 12, 6, no, 10, bold=True, color=ACC)
        text(s, M + 14, y + 3.5, 120, 6, title + ("  ●" if no in KEY else ""), 10, bold=True)
        text(s, W - M - 45, y + 3.5, 20, 6, yr, 9, color=GRAY)
        text(s, W - M - 22, y + 3.5, 22, 6, f"p.{pagemap[no]:02d}", 9, color=GRAY, align=PP_ALIGN.RIGHT)
        y += 15
    hline(s, M, y, W - M, LIGHT)
    text(s, M, y + 4, 180, 5, "● 詳細ページ（工程・部分比較）あり", 7.5, color=GRAY)
    folio(s, n, "INDEX")


def p_numbers(s, n):
    text(s, M, 22, 100, 5, "NUMBERS", 9, bold=True, color=ACC, spacing=4)
    text(s, M, 30, 150, 12, "数字で見る実績", 20, bold=True)
    items = [("15+", "年", "空間制作・美術造形の実務"),
             ("1,000+", "㎡", "FRP施工面積（最大案件）"),
             ("3.5", "億円", "最大の案件規模"),
             ("【  】", "件", "担当案件数（要記入）"),
             ("【  】", "社", "同時調整した協力会社数（要記入）"),
             ("【  】", "%", "納期遵守率（要記入）")]
    cw, ch = (W - 2 * M - 6) / 2, 62
    for i, (v, u, d) in enumerate(items):
        x = M + (i % 2) * (cw + 6); y = 55 + (i // 2) * (ch + 6)
        box(s, x, y, cw, ch, line=LIGHT)
        text(s, x + 6, y + 14, cw - 12, 22, f"{v}", 30, bold=True)
        text(s, x + 6, y + 34, cw - 12, 8, u, 11, bold=True, color=ACC)
        text(s, x + 6, y + 46, cw - 12, 8, d, 8.5, color=GRAY)
    folio(s, n, "NUMBERS")


# ---------------- works ----------------
def p_drawing(s, n, w):
    no, title, yr, dkind = w
    photo(s, 0, 0, W, H, f"IMG_{no}_DRAWING", f"{dkind}（A4縦・全面）", fill=PH_DRAW)
    caption_band(s, H - 54, 54, "DRAWING", dkind, no, title,
                 "縮尺：【1/○】　使用ソフト：【Rhino / Vectorworks】\n"
                 "図面で決めたこと：【寸法・分割・構造を1行】\n"
                 "制約：【予算・納期・設置条件を1行】", n, True)


def p_real(s, n, w):
    no, title, yr, _ = w
    photo(s, 0, 0, W, H, f"IMG_{no}_REAL", "実物写真（A4縦・全面）※左の図面と同アングル")
    caption_band(s, H - 54, 54, "RESULT", "実物", no, f"{title}  {yr}",
                 "規模：【W×D×H mm】　期間：【○ヶ月】　担当：【設計／製作管理／施工】\n"
                 "素材・工法：【FRP／発泡／3Dプリント 等】\n"
                 "成果：【数字で1行（例：工期○日短縮／手戻り0）】", n, False)


def p_process(s, n, w):
    no, title, yr, _ = w
    text(s, M, 18, 100, 5, "PROCESS", 9, bold=True, color=ACC, spacing=4)
    text(s, M, 25, 180, 10, f"{no}  {title}　制作工程", 14, bold=True)
    gw, gh = (W - 2 * M - 5) / 2, 105
    for i in range(4):
        x = M + (i % 2) * (gw + 5); y = 42 + (i // 2) * (gh + 12)
        photo(s, x, y, gw, gh - 18, f"IMG_{no}_STEP{i+1}", f"工程写真 STEP{i+1}")
        text(s, x, y + gh - 15, 20, 5, f"STEP {i+1}", 8, bold=True, color=ACC)
        text(s, x + 18, y + gh - 15, gw - 18, 5, "【工程名】", 9, bold=True)
        text(s, x, y + gh - 8, gw, 8, "【ポイント・工夫を1行】", 8, color=GRAY)
    folio(s, n, f"{no} {title}")


def p_compare(s, n, w):
    no, title, yr, dkind = w
    text(s, M, 18, 100, 5, "DETAIL", 9, bold=True, color=ACC, spacing=4)
    text(s, M, 25, 180, 10, "部分比較　図面 → 実物", 14, bold=True)
    ph = 95
    photo(s, M, 42, W - 2 * M, ph, f"IMG_{no}_DETAIL_DRAWING", f"{dkind}（部分拡大）", fill=PH_DRAW)
    text(s, M, 42 + ph + 2, 80, 5, "DRAWING", 7.5, bold=True, color=GRAY, spacing=2)
    photo(s, M, 42 + ph + 10, W - 2 * M, ph, f"IMG_{no}_DETAIL_REAL", "実物（同部位・同アングル）")
    text(s, M, 42 + 2 * ph + 12, 80, 5, "RESULT", 7.5, bold=True, color=GRAY, spacing=2)
    y = 42 + 2 * ph + 20
    box(s, M, y, W - 2 * M, 22, fill=RGBColor(0xF4, 0xF4, 0xF4))
    text(s, M + 5, y + 4, 30, 5, "POINT", 8, bold=True, color=ACC, spacing=2)
    text(s, M + 5, y + 10, W - 2 * M - 10, 10, "【図面上の意図が実物でどう再現されたか／許容誤差・現場での調整を1〜2行】", 8.5)
    folio(s, n, f"{no} {title}")


# ---------------- back ----------------
def p_tools_timeline(s, n):
    text(s, M, 22, 100, 5, "TOOLS", 9, bold=True, color=ACC, spacing=4)
    tools = [("図面・3D", "Rhinoceros 8 / Grasshopper / ZBrush / Vectorworks / AutoCAD / Illustrator / Photoshop"),
             ("計測・取込", "3Dスキャン / フォトグラメトリ / 点群処理"),
             ("製作", "3Dプリント（DLP / FDM） / CNC加工 / FRP成形・型取り / 塗装・エイジング"),
             ("AI", "画像生成 / Image-to-3D / ChatGPT・Claude・Gemini")]
    y = 32
    for k, v in tools:
        hline(s, M, y, W - M, LIGHT)
        text(s, M, y + 3, 30, 6, k, 9, bold=True)
        text(s, M + 32, y + 3, W - 2 * M - 32, 12, v, 8.5, ls=1.3)
        y += 17
    text(s, M, 110, 100, 5, "TIMELINE", 9, bold=True, color=ACC, spacing=4)
    years = {}
    for no, t, yr, _ in WORKS:
        years.setdefault(yr, []).append(f"{no} {t}")
    y = 122
    hline(s, M + 18, y - 2, M + 18, GRAY)
    for yr, ts in years.items():
        text(s, M, y, 16, 6, yr, 10, bold=True, color=ACC)
        text(s, M + 24, y, W - 2 * M - 24, 6 * len(ts), "\n".join(ts), 9, ls=1.35)
        y += 6.2 * len(ts) + 6
    folio(s, n, "TOOLS / TIMELINE")


def p_contact(s, n):
    box(s, 0, 0, W, H, fill=RGBColor(0x14, 0x14, 0x14))
    text(s, M + 4, 90, 180, 10, "THANK YOU", 12, bold=True, color=ACC, spacing=6)
    text(s, M + 4, 105, 180, 20, "描いたものを、そのまま立たせる。", 18, bold=True, color=WHITE)
    text(s, M + 4, 200, 180, 12, "的場 道雄", 18, bold=True, color=WHITE)
    text(s, M + 4, 214, 180, 20, "MAIL　【メール】\nTEL　 【電話】\n京都府【市区】", 9, color=GRAY, ls=1.6)


# ---------------- page sequence ----------------
seq = [("cover", None), ("kv", None), ("profile", None), ("method", None), ("index", None), ("numbers", None)]
for w in WORKS:
    seq += [("drawing", w), ("real", w)]
    if w[0] in KEY:
        seq += [("process", w), ("compare", w)]
seq += [("tools", None), ("contact", None)]
assert len(seq) == 48, len(seq)

pagemap = {}
for i, (k, w) in enumerate(seq, 1):
    if k == "drawing":
        pagemap[w[0]] = i
        assert i % 2 == 1, f"図面ページは見開き左（奇数）であること: {w} p{i}"

F = dict(cover=p_cover, kv=p_keyvisual, profile=p_profile, method=p_method, numbers=p_numbers,
         tools=p_tools_timeline, contact=p_contact)
for i, (k, w) in enumerate(seq, 1):
    s = prs.slides.add_slide(BLANK)
    if k == "index":
        p_index(s, i, pagemap)
    elif k in F:
        F[k](s, i)
    else:
        {"drawing": p_drawing, "real": p_real, "process": p_process, "compare": p_compare}[k](s, i, w)

prs.save(OUT)
for i, (k, w) in enumerate(seq, 1):
    print(i, k, w[1] if w else "")
