#!/usr/bin/env python3
"""
md2pdf.py 的配套绘图模块：为硬件文档生成矢量示意图。

在 Markdown 中用 `@fig:名称 图题` 单独一行引用，例如:
    @fig:stackup 图 2　四层板叠层剖面（1.6 mm）

纯 reportlab.graphics 矢量绘制，不依赖外部图片文件。
"""

from reportlab.graphics.shapes import Drawing, Group, Line, PolyLine, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer

W = 170 * mm  # 与正文同宽

FONT, BOLD = 'NotoSC', 'NotoSC-Bold'
ACCENT = colors.HexColor('#1a5f9c')
DARK = colors.HexColor('#1a1a1a')
GREY = colors.HexColor('#666666')
COPPER = colors.HexColor('#c8801f')
DIEL = colors.HexColor('#d9e6c9')
CORE_C = colors.HexColor('#c3d6ae')
MASK = colors.HexColor('#2f7a4f')
RED = colors.HexColor('#c0392b')
AMBER = colors.HexColor('#d68910')
GREEN = colors.HexColor('#1e8449')

CAP = ParagraphStyle('cap', fontName=FONT, fontSize=8.5, leading=12.5,
                     textColor=GREY, alignment=1, spaceBefore=3, spaceAfter=10)


def _txt(d, x, y, s, size=8, font=FONT, fill=DARK, anchor='start'):
    d.add(String(x, y, s, fontName=font, fontSize=size,
                 fillColor=fill, textAnchor=anchor))


def _box(d, x, y, w, h, fill, stroke=None, sw=0.6, r=None):
    kw = dict(fillColor=fill, strokeColor=stroke or colors.HexColor('#94a7b8'),
              strokeWidth=sw)
    if r:
        kw['rx'] = kw['ry'] = r
    d.add(Rect(x, y, w, h, **kw))


def _arrow(d, x1, y1, x2, y2, color=ACCENT, sw=1.0, head=4):
    """带箭头的直线（仅支持水平/垂直方向的箭头）。"""
    d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=sw))
    if abs(x2 - x1) < 0.01:                       # 垂直
        s = -head if y2 < y1 else head
        d.add(Polygon([x2, y2, x2 - head * 0.6, y2 - s, x2 + head * 0.6, y2 - s],
                      fillColor=color, strokeColor=color))
    else:                                          # 水平
        s = -head if x2 < x1 else head
        d.add(Polygon([x2, y2, x2 - s, y2 - head * 0.6, x2 - s, y2 + head * 0.6],
                      fillColor=color, strokeColor=color))


# ---------------------------------------------------------------- 图：流程总览

def flow():
    """十阶段流程总览，边框颜色表示返工代价。"""
    d = Drawing(W, 250)
    stages = [
        ('一', '开工前决策', '层数 / 板厂 / 板框', RED),
        ('二', '原理图收尾', '批注 / 封装 / ERC', AMBER),
        ('三', '电路板配置', '叠层 / 规则 / 网络类', RED),
        ('四', '更新 PCB', '从原理图导入', GREEN),
        ('五', '板框与结构', 'Edge.Cuts / 安装孔', AMBER),
        ('六', '布局', '摆放 / 分区 / 锁定', RED),
        ('七', '布线', '优先级 / 阻抗 / 等长', AMBER),
        ('八', '铺铜与回流', '平面 / 缝合过孔', GREEN),
        ('九', '检查', 'DRC / 目视 / 3D', ACCENT),
        ('十', '制造输出', 'Gerber / 钻孔 / BOM', GREEN),
    ]
    bw, bh, gx, gy = 218, 38, 24, 8
    x0, y0 = 4, 250 - bh - 16
    for i, (num, name, sub, col) in enumerate(stages):
        cx = x0 + (i % 2) * (bw + gx)
        cy = y0 - (i // 2) * (bh + gy)
        _box(d, cx, cy, bw, bh, colors.white, col, 1.1, r=4)
        d.add(Rect(cx, cy, 4, bh, fillColor=col, strokeColor=col))
        _txt(d, cx + 12, cy + bh - 15, '阶段' + num, 8.5, BOLD, col)
        _txt(d, cx + 52, cy + bh - 15, name, 9.5, BOLD, DARK)
        _txt(d, cx + 12, cy + 8, sub, 7.5, FONT, GREY)
        if i % 2 == 0:                              # 左 -> 右
            _arrow(d, cx + bw + 3, cy + bh / 2, cx + bw + gx - 3, cy + bh / 2, GREY, .8)
        elif i < len(stages) - 1:                   # 右 -> 下一行左
            _arrow(d, cx + bw / 2, cy - 1, cx + bw / 2, cy - gy + 1, GREY, .8)

    ly = 12
    _txt(d, 4, ly, '返工代价：', 8, BOLD, DARK)
    for i, (c, t) in enumerate(((RED, '极高 / 高'), (AMBER, '高 / 中'),
                                (GREEN, '低'), (ACCENT, '检查环节'))):
        bx = 52 + i * 96
        d.add(Rect(bx, ly - 1, 16, 7, fillColor=colors.white, strokeColor=c, strokeWidth=1.1))
        _txt(d, bx + 21, ly, t, 8, FONT, GREY)
    return d


# ---------------------------------------------------------------- 图：叠层剖面

def stackup():
    """四层板 1.6 mm 叠层剖面（嘉立创 JLC04161H-7628）。"""
    d = Drawing(W, 232)
    layers = [
        ('阻焊 / Solder Mask', '0.01 mm', MASK, 7, ''),
        ('F.Cu  (1 oz)', '0.035 mm', COPPER, 11, '信号层：射频、差分时钟'),
        ('Prepreg 7628', '0.2104 mm', DIEL, 26, 'Dk 4.4　← 决定 F.Cu 阻抗'),
        ('In1.Cu  (0.5 oz)', '0.0152 mm', COPPER, 9, 'GND 完整平面（不可分割）'),
        ('Core', '1.065 mm', CORE_C, 52, 'Dk 4.2'),
        ('In2.Cu  (0.5 oz)', '0.0152 mm', COPPER, 9, 'PWR 电源平面'),
        ('Prepreg 7628', '0.2104 mm', DIEL, 26, 'Dk 4.4'),
        ('B.Cu  (1 oz)', '0.035 mm', COPPER, 11, '次信号层'),
        ('阻焊 / Solder Mask', '0.01 mm', MASK, 7, ''),
    ]
    lx, lw = 92, 210
    y = 232 - 26
    for name, th, col, h, note in layers:
        y -= h
        _box(d, lx, y, lw, h, col, colors.HexColor('#7d8f9e'), 0.5)
        _txt(d, lx - 6, y + h / 2 - 3, name, 7.5, FONT, DARK, 'end')
        _txt(d, lx + lw + 8, y + h / 2 - 3, th, 7.5, BOLD, ACCENT)
        if note:
            _txt(d, lx + lw + 62, y + h / 2 - 3, note, 7.5, FONT, GREY)

    top, bot = 232 - 26, y
    d.add(Line(lx - 76, top, lx - 76, bot, strokeColor=ACCENT, strokeWidth=0.8))
    for yy in (top, bot):
        d.add(Line(lx - 80, yy, lx - 72, yy, strokeColor=ACCENT, strokeWidth=0.8))
    _txt(d, lx - 84, (top + bot) / 2 - 3, '1.6 mm', 8, BOLD, ACCENT, 'end')

    # 高亮 F.Cu 与 In1.Cu 之间的关键间距
    ky1 = top - 7 - 11
    ky2 = ky1 - 26
    d.add(Line(lx + lw + 168, ky1, lx + lw + 168, ky2, strokeColor=RED, strokeWidth=0.9))
    for yy in (ky1, ky2):
        d.add(Line(lx + lw + 164, yy, lx + lw + 172, yy, strokeColor=RED, strokeWidth=0.9))
    _txt(d, lx + lw + 176, (ky1 + ky2) / 2 - 3, 'H', 8.5, BOLD, RED)

    _txt(d, 4, 8, '计算阻抗时 H 填这一段（0.2104 mm），不是板厚 1.6 mm', 8, BOLD, RED)
    return d


# ---------------------------------------------------------------- 图：微带线截面

def microstrip():
    """微带线截面与计算器参数对应关系。"""
    d = Drawing(W, 165)
    bx, bw2, by = 60, 300, 46
    d.add(Rect(bx, by, bw2, 42, fillColor=DIEL, strokeColor=colors.HexColor('#7d8f9e')))
    d.add(Rect(bx, by - 10, bw2, 10, fillColor=COPPER, strokeColor=colors.HexColor('#7d8f9e')))
    tw, tx = 54, bx + 120
    d.add(Rect(tx, by + 42, tw, 11, fillColor=COPPER, strokeColor=colors.HexColor('#7d8f9e')))

    _txt(d, bx - 6, by - 8, 'In1.Cu', 8, BOLD, DARK, 'end')
    _txt(d, bx - 6, by + 18, 'Prepreg', 8, FONT, DARK, 'end')
    _txt(d, bx + bw2 + 8, by - 8, '参考平面（完整 GND）', 8, FONT, GREY)
    _txt(d, tx + tw + 10, by + 45, '走线 (F.Cu)', 8, FONT, GREY)

    # W 标注
    d.add(Line(tx, by + 68, tx + tw, by + 68, strokeColor=ACCENT, strokeWidth=0.9))
    for xx in (tx, tx + tw):
        d.add(Line(xx, by + 64, xx, by + 72, strokeColor=ACCENT, strokeWidth=0.9))
    _txt(d, tx + tw / 2, by + 74, 'W 线宽', 8.5, BOLD, ACCENT, 'middle')
    # H 标注
    hx = bx + 40
    d.add(Line(hx, by, hx, by + 42, strokeColor=RED, strokeWidth=0.9))
    for yy in (by, by + 42):
        d.add(Line(hx - 4, yy, hx + 4, yy, strokeColor=RED, strokeWidth=0.9))
    _txt(d, hx + 8, by + 18, 'H 介质厚度', 8.5, BOLD, RED)
    # T 标注
    d.add(Line(tx + tw + 4, by + 42, tx + tw + 4, by + 53, strokeColor=GREEN, strokeWidth=0.9))
    _txt(d, tx + tw + 8, by + 44, 'T 铜厚', 8, BOLD, GREEN)

    _txt(d, 4, 22, 'KiCad 计算器对应：εr = 介质 Dk　|　H = 介质厚度（非板厚）　|　'
                   'T = 铜厚　|　W = 合成结果', 8, FONT, DARK)
    _txt(d, 4, 8, 'H(top) 保持 1e+20，表示走线上方为空气、无金属盖板', 8, FONT, GREY)
    return d


# ---------------------------------------------------------------- 图：布线优先级

def priority():
    """布线优先级阶梯。"""
    d = Drawing(W, 208)
    items = [
        ('1', '去耦电容 → 电源/地引脚', '环路面积最小'),
        ('2', '晶振、时钟源', '最短最直，远离干扰'),
        ('3', '阻抗控制线：射频、差分时钟', '线宽固定，无腾挪余地'),
        ('4', '其他差分对：以太网、USB', '需成对等距'),
        ('5', '敏感模拟信号', '远离数字与开关电源'),
        ('6', '高速数字总线', '需等长、成组'),
        ('7', '普通数字 I/O、LED、按键', '最灵活，随便绕'),
        ('8', '电源走线', '加宽即可，最后填空隙'),
    ]
    bh, gy = 20, 3.5
    y = 208 - 26
    for i, (n, name, why) in enumerate(items):
        y -= bh
        ratio = 1 - i * 0.055
        bw2 = 300 * ratio
        col = RED if i < 4 else (AMBER if i < 6 else GREEN)
        _box(d, 40, y, bw2, bh, colors.white, col, 1.0, r=3)
        d.add(Rect(40, y, 3.5, bh, fillColor=col, strokeColor=col))
        _txt(d, 22, y + 6, n, 10, BOLD, col, 'middle')
        _txt(d, 50, y + 6, name, 8.5, FONT, DARK)
        _txt(d, 352, y + 6, why, 7.5, FONT, GREY)
        y -= gy

    _arrow(d, 12, 208 - 30, 12, y + 14, ACCENT, 1.0)
    _txt(d, 4, 208 - 18, '先', 8, BOLD, ACCENT)
    _txt(d, 4, y + 4, '后', 8, BOLD, ACCENT)
    _txt(d, 40, 8, '越敏感、越难改的越先走；LED 按键这类线多晚布都能绕过去', 8, BOLD, DARK)
    return d


# ---------------------------------------------------------------- 图：回流路径

def refplane():
    """参考平面完整 vs 被割断时的回流路径对比。"""
    d = Drawing(W, 175)
    pw, ph = 218, 88
    for k, (px, title, ok) in enumerate((
            (6, '完整参考平面', True),
            (6 + pw + 24, '平面被走线割断', False))):
        py = 58
        _box(d, px, py, pw, ph, colors.HexColor('#f4f7fa'),
             GREEN if ok else RED, 1.1, r=3)
        # 信号走线（上方）
        sy = py + ph - 22
        d.add(Line(px + 20, sy, px + pw - 20, sy, strokeColor=COPPER, strokeWidth=2.4))
        _txt(d, px + 20, sy + 7, '信号走线 (F.Cu)', 7.5, FONT, GREY)
        # 参考平面（下方）
        gy2 = py + 26
        if ok:
            d.add(Rect(px + 14, gy2, pw - 28, 9, fillColor=COPPER,
                       strokeColor=colors.HexColor('#7d8f9e'), strokeWidth=0.4))
        else:
            gap = 34
            midx = px + pw / 2
            d.add(Rect(px + 14, gy2, midx - gap / 2 - (px + 14), 9, fillColor=COPPER,
                       strokeColor=colors.HexColor('#7d8f9e'), strokeWidth=0.4))
            d.add(Rect(midx + gap / 2, gy2, (px + pw - 14) - (midx + gap / 2), 9,
                       fillColor=COPPER, strokeColor=colors.HexColor('#7d8f9e'), strokeWidth=0.4))
            _txt(d, midx, gy2 - 12, '割缝', 7.5, BOLD, RED, 'middle')
        _txt(d, px + 14, gy2 + 14, 'In1.Cu (GND)', 7.5, FONT, GREY)

        # 回流路径
        if ok:
            d.add(PolyLine([px + 60, sy - 4, px + 60, gy2 + 13,
                            px + pw - 60, gy2 + 13, px + pw - 60, sy - 4],
                           strokeColor=GREEN, strokeWidth=1.3,
                           strokeDashArray=[3, 2]))
            _txt(d, px + pw / 2, gy2 + 18, '回流路径短', 7.5, BOLD, GREEN, 'middle')
        else:
            midx = px + pw / 2
            d.add(PolyLine([px + 60, sy - 4, px + 60, gy2 + 13, midx - 20, gy2 + 13,
                            midx - 20, py + 8, midx + 20, py + 8,
                            midx + 20, gy2 + 13, px + pw - 60, gy2 + 13,
                            px + pw - 60, sy - 4],
                           strokeColor=RED, strokeWidth=1.3, strokeDashArray=[3, 2]))
            _txt(d, midx, py + 1, '回流被迫绕行 → 阻抗突变、辐射、串扰', 7.5, BOLD, RED, 'middle')

        _txt(d, px + pw / 2, py + ph + 8, title, 9, BOLD,
             GREEN if ok else RED, 'middle')

    _txt(d, 6, 30, '高频回流电流总是走信号线正下方的最短路径。参考平面上任何割缝都会迫使回流绕行，',
         8, FONT, DARK)
    _txt(d, 6, 17, '同时破坏阻抗连续性并显著增加辐射。这是 In1.Cu 不允许走线的根本原因。',
         8, FONT, DARK)
    return d


# ---------------------------------------------------------------- 图：布局分区

def layout():
    """CORE 底板的布局分区示意。"""
    d = Drawing(W, 215)
    bx, by, bw2, bh2 = 30, 34, 420, 160
    _box(d, bx, by, bw2, bh2, colors.white, DARK, 1.2, r=3)
    _txt(d, bx, by + bh2 + 8, '板框 (Edge.Cuts)', 8, FONT, GREY)

    zones = [
        (bx + 8, by + 8, 130, 144, '#fdeaea', RED, '射频区', 'SMA ×8 输入\n50Ω 控制\n最短路径'),
        (bx + 146, by + 8, 150, 144, '#eaf1f8', ACCENT, '数字区', 'ZYNQ 核心板座\n差分时钟\n高速总线'),
        (bx + 304, by + 78, 108, 74, '#eaf6ee', GREEN, '电源区', '稳压器\n大电容'),
        (bx + 304, by + 8, 108, 62, '#fdf6e6', AMBER, '接口区', 'RJ45 / USB-C'),
    ]
    for zx, zy, zw, zh, fill, col, name, items in zones:
        _box(d, zx, zy, zw, zh, colors.HexColor(fill), col, 0.9, r=3)
        _txt(d, zx + 6, zy + zh - 13, name, 9, BOLD, col)
        for j, ln in enumerate(items.split('\n')):
            _txt(d, zx + 6, zy + zh - 27 - j * 11, ln, 7.5, FONT, GREY)

    # 板边接口标记
    for cy, lbl in ((by + 130, 'SMA'), (by + 100, 'SMA'), (by + 70, 'SMA'), (by + 40, 'SMA')):
        d.add(Rect(bx - 7, cy, 7, 12, fillColor=COPPER, strokeColor=DARK, strokeWidth=0.5))
    _txt(d, bx - 12, by + 12, 'SMA ×8', 7.5, BOLD, DARK, 'end')
    for cx, lbl in ((bx + 330, 'RJ45'), (bx + 386, 'USB-C')):
        d.add(Rect(cx, by - 7, 34, 7, fillColor=COPPER, strokeColor=DARK, strokeWidth=0.5))
        _txt(d, cx + 17, by - 17, lbl, 7.5, BOLD, DARK, 'middle')

    _txt(d, 6, 16, '三条原则：就近（去耦电容贴紧电源脚）　|　分区（模拟/数字/电源/射频分开）　|　'
                   '信号流向（避免来回穿越）', 8, FONT, DARK)
    return d


# ------------------------------------------------------- 图：原理图流程总览

def sch_flow():
    """原理图设计八阶段。"""
    d = Drawing(W, 212)
    stages = [
        ('一', '工程与图纸准备', '新建工程 / 页面设置 / 图框', GREEN),
        ('二', '符号库准备', '标准库 / 自建符号 / 库路径', AMBER),
        ('三', '绘制电路', '放符号 / 连线 / 标签', ACCENT),
        ('四', '层次化拆分', '按功能分图纸 / 层次标签', AMBER),
        ('五', '批注位号', '分配唯一 R1 C2 U3', GREEN),
        ('六', '分配封装', '与实际采购件对应', RED),
        ('七', 'ERC 检查', '引脚冲突 / 未连接 / 电源', RED),
        ('八', '输出', 'BOM / 网表 / 更新 PCB', GREEN),
    ]
    bw, bh, gx, gy = 218, 38, 24, 8
    x0, y0 = 4, 212 - bh - 14
    for i, (num, name, sub, col) in enumerate(stages):
        cx = x0 + (i % 2) * (bw + gx)
        cy = y0 - (i // 2) * (bh + gy)
        _box(d, cx, cy, bw, bh, colors.white, col, 1.1, r=4)
        d.add(Rect(cx, cy, 4, bh, fillColor=col, strokeColor=col))
        _txt(d, cx + 12, cy + bh - 15, '阶段' + num, 8.5, BOLD, col)
        _txt(d, cx + 52, cy + bh - 15, name, 9.5, BOLD, DARK)
        _txt(d, cx + 12, cy + 8, sub, 7.5, FONT, GREY)
        if i % 2 == 0:
            _arrow(d, cx + bw + 3, cy + bh / 2, cx + bw + gx - 3, cy + bh / 2, GREY, .8)
        elif i < len(stages) - 1:
            _arrow(d, cx + bw / 2, cy - 1, cx + bw / 2, cy - gy + 1, GREY, .8)
    _txt(d, 4, 10, '阶段六、七出错会直接导致板子报废或返工，是全流程的两个卡点',
         8, BOLD, RED)
    return d


# ------------------------------------------------------- 图：六种连接方式

def sch_connect():
    """原理图中六种建立连接的方式对比。"""
    d = Drawing(W, 268)
    rows = [
        ('导线 / Wire', 'W', '直接画线相连', '同一图纸内看得见的物理连接'),
        ('结点 / Junction', 'J', '交叉处的实心圆点', '无圆点的交叉线不相连'),
        ('网络标签 / Label', 'L', '同名 = 相连', '仅在本张图纸内生效'),
        ('全局标签 / Global Label', 'Ctrl+L', '同名 = 相连', '跨所有图纸生效'),
        ('层次标签 / Hier. Label', 'H', '对应父图纸的图纸引脚', '子图与父图的接口'),
        ('电源符号 / Power', 'P', '同名 = 自动相连', 'GND、+3V3 等全局连通'),
    ]
    rh = 38
    y = 268 - 24
    for name, key, how, note in rows:
        y -= rh
        _box(d, 4, y, W - 8, rh - 4, colors.HexColor('#f8fafb'),
             colors.HexColor('#d5dee7'), 0.6, r=3)
        _txt(d, 12, y + rh - 18, name, 9, BOLD, ACCENT)
        d.add(Rect(150, y + rh - 22, 34, 13, fillColor=colors.white,
                   strokeColor=ACCENT, strokeWidth=0.8, rx=2, ry=2))
        _txt(d, 167, y + rh - 18, key, 8, BOLD, ACCENT, 'middle')
        _txt(d, 12, y + 8, how, 7.5, FONT, DARK)
        _txt(d, 150, y + 8, note, 7.5, FONT, GREY)

        # 右侧小示意
        gx0, gy0 = 340, y + rh / 2 - 2
        if name.startswith('导线'):
            d.add(Line(gx0, gy0, gx0 + 60, gy0, strokeColor=GREEN, strokeWidth=1.4))
            for xx in (gx0, gx0 + 60):
                d.add(Rect(xx - 3, gy0 - 3, 6, 6, fillColor=DARK, strokeColor=DARK))
        elif name.startswith('结点'):
            d.add(Line(gx0, gy0, gx0 + 60, gy0, strokeColor=GREEN, strokeWidth=1.4))
            d.add(Line(gx0 + 30, gy0 - 14, gx0 + 30, gy0 + 14, strokeColor=GREEN, strokeWidth=1.4))
            d.add(Polygon([gx0 + 30, gy0 + 3.2, gx0 + 33.2, gy0, gx0 + 30, gy0 - 3.2,
                           gx0 + 26.8, gy0], fillColor=DARK, strokeColor=DARK))
        elif name.startswith('网络标签'):
            for k, off in ((0, 0), (1, 76)):
                d.add(Line(gx0 + off, gy0, gx0 + off + 26, gy0,
                           strokeColor=GREEN, strokeWidth=1.4))
                _txt(d, gx0 + off + 28, gy0 - 3, 'SDA', 7.5, BOLD, ACCENT)
            _txt(d, gx0 + 56, gy0 + 8, '=', 9, BOLD, GREY)
        elif name.startswith('全局标签'):
            for off, lbl in ((0, '图纸 A'), (76, '图纸 B')):
                d.add(Rect(gx0 + off, gy0 - 10, 52, 20, fillColor=colors.white,
                           strokeColor=GREY, strokeWidth=0.5, rx=2, ry=2))
                _txt(d, gx0 + off + 26, gy0 - 3, lbl, 7, FONT, GREY, 'middle')
            _arrow(d, gx0 + 54, gy0, gx0 + 74, gy0, ACCENT, 1.0, 3.5)
        elif name.startswith('层次标签'):
            d.add(Rect(gx0, gy0 - 12, 56, 24, fillColor=colors.white,
                       strokeColor=ACCENT, strokeWidth=0.9, rx=2, ry=2))
            _txt(d, gx0 + 28, gy0 - 3, '父图纸', 7, FONT, ACCENT, 'middle')
            d.add(Rect(gx0 + 54, gy0 - 3, 6, 6, fillColor=AMBER, strokeColor=AMBER))
            _arrow(d, gx0 + 62, gy0, gx0 + 84, gy0, AMBER, 1.0, 3.5)
            _txt(d, gx0 + 88, gy0 - 3, '子图', 7, FONT, AMBER)
        else:
            for off in (0, 60):
                d.add(Line(gx0 + off + 12, gy0 + 10, gx0 + off + 12, gy0,
                           strokeColor=GREEN, strokeWidth=1.4))
                d.add(Line(gx0 + off + 4, gy0, gx0 + off + 20, gy0,
                           strokeColor=GREEN, strokeWidth=1.6))
                _txt(d, gx0 + off + 12, gy0 - 11, 'GND', 7, BOLD, ACCENT, 'middle')
            _txt(d, gx0 + 40, gy0 + 2, '=', 9, BOLD, GREY)

    _txt(d, 4, 8, '常见错误：交叉处漏放结点导致该连的没连；用网络标签跨图纸连接（不生效，'
                  '需用全局标签）', 8, BOLD, RED)
    return d


# ------------------------------------------------------- 图：层次化结构

def sch_hierarchy():
    """层次化原理图的父子对应关系。"""
    d = Drawing(W, 226)
    # 顶层
    tx, ty, tw, th = 90, 150, 300, 60
    _box(d, tx, ty, tw, th, colors.HexColor('#eaf1f8'), ACCENT, 1.2, r=4)
    _txt(d, tx + 8, ty + th - 15, '顶层图纸 / Root Sheet', 9, BOLD, ACCENT)
    sheets = [('电源.kicad_sch', tx + 14), ('射频前端.kicad_sch', tx + 108),
              ('接口.kicad_sch', tx + 214)]
    pins = []
    for name, sx in sheets:
        d.add(Rect(sx, ty + 8, 78, 28, fillColor=colors.white,
                   strokeColor=DARK, strokeWidth=0.8))
        _txt(d, sx + 39, ty + 24, '图纸符号', 7, FONT, GREY, 'middle')
        _txt(d, sx + 39, ty + 13, name.replace('.kicad_sch', ''), 7.5, BOLD, DARK, 'middle')
        px, py = sx + 78, ty + 22
        d.add(Rect(px - 3, py - 3, 6, 6, fillColor=AMBER, strokeColor=AMBER))
        pins.append((px, py, sx + 39))
    _txt(d, tx + tw + 8, ty + 22, '图纸引脚', 7.5, BOLD, AMBER)
    _txt(d, tx + tw + 8, ty + 11, 'Sheet Pin', 7, FONT, GREY)

    # 子图
    cy = 44
    for i, (name, sx) in enumerate(sheets):
        cx = 24 + i * 152
        _box(d, cx, cy, 132, 62, colors.HexColor('#fdf6e6'), AMBER, 1.0, r=4)
        _txt(d, cx + 8, cy + 48, name.replace('.kicad_sch', '') + ' 子图', 8, BOLD, AMBER)
        d.add(Rect(cx + 8, cy + 26, 6, 6, fillColor=AMBER, strokeColor=AMBER))
        _txt(d, cx + 20, cy + 26, '层次标签 (H)', 7.5, FONT, DARK)
        _txt(d, cx + 8, cy + 10, '名称必须与图纸引脚一致', 7, FONT, GREY)
        _arrow(d, pins[i][2], ty - 2, cx + 66, cy + 64, ACCENT, 0.8, 3.5)

    _txt(d, 4, 20, '层次标签 (H) 与父图纸上的图纸引脚 **同名即相连**，是子图对外的唯一接口。',
         8, FONT, DARK)
    _txt(d, 4, 8, '快捷键：S 放置图纸　|　Ctrl+H 层次导航　|　Alt+Back 离开图纸　|　'
                  'PgUp / PgDn 翻页', 8, FONT, GREY)
    return d


# ------------------------------------------------------- 图：数据流

def sch_dataflow():
    """符号库 -> 原理图 -> 封装 -> PCB 的数据流。"""
    d = Drawing(W, 168)
    steps = [
        ('符号库', '.kicad_sym', '引脚定义\n电气类型', ACCENT),
        ('原理图', '.kicad_sch', '位号 Reference\n数值 Value\n封装 Footprint', GREEN),
        ('封装库', '.pretty', '焊盘尺寸\n实际外形', AMBER),
        ('PCB', '.kicad_pcb', '焊盘 + 飞线\n网络连接', RED),
    ]
    bw, gx = 104, 34
    x = 8
    y = 62
    for i, (name, ext, items, col) in enumerate(steps):
        _box(d, x, y, bw, 74, colors.white, col, 1.2, r=4)
        d.add(Rect(x, y + 58, bw, 16, fillColor=col, strokeColor=col,
                   rx=4, ry=4))
        _txt(d, x + bw / 2, y + 63, name, 9, BOLD, colors.white, 'middle')
        _txt(d, x + bw / 2, y + 46, ext, 7, FONT, GREY, 'middle')
        for j, ln in enumerate(items.split('\n')):
            _txt(d, x + 8, y + 32 - j * 11, ln, 7.5, FONT, DARK)
        if i < len(steps) - 1:
            _arrow(d, x + bw + 4, y + 37, x + bw + gx - 4, y + 37, ACCENT, 1.2, 4.5)
        x += bw + gx

    _txt(d, 118, 146, '分配封装', 7.5, BOLD, ACCENT)
    _txt(d, 256, 146, '引用', 7.5, BOLD, ACCENT)
    _txt(d, 388, 146, '从原理图更新 PCB', 7.5, BOLD, ACCENT)

    _txt(d, 8, 40, '关键：原理图里的「封装」字段只是一个名字字符串，它必须能在封装库里找到对应项。',
         8, FONT, DARK)
    _txt(d, 8, 27, '符号的引脚数与封装的焊盘数必须一一对应，否则更新 PCB 时报错。',
         8, FONT, DARK)
    _txt(d, 8, 12, '常见错误：符号画 0402、实物买 0603；连接器封装引脚顺序镜像。',
         8, BOLD, RED)
    return d


# ------------------------------------------------------- 图：ERC 引脚类型

def sch_erc():
    """ERC 引脚类型冲突矩阵（常见组合）。"""
    d = Drawing(W, 224)
    types = ['输出\nOutput', '输入\nInput', '双向\nBidir', '无源\nPassive',
             '电源输入\nPwr In', '电源输出\nPwr Out']
    # 0 = 正常, 1 = 警告, 2 = 错误
    m = [
        [2, 0, 0, 0, 0, 2],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [2, 0, 0, 0, 0, 2],
    ]
    cs, x0, y0 = 46, 96, 214 - 34
    for j, t in enumerate(types):
        for k, ln in enumerate(t.split('\n')):
            _txt(d, x0 + j * cs + cs / 2, y0 + 6 - k * 9, ln,
                 6.8, BOLD if k == 0 else FONT, DARK if k == 0 else GREY, 'middle')
    y = y0 - 12
    for i, t in enumerate(types):
        y -= cs * 0.62
        for k, ln in enumerate(t.split('\n')):
            _txt(d, x0 - 6, y + 14 - k * 9, ln, 6.8,
                 BOLD if k == 0 else FONT, DARK if k == 0 else GREY, 'end')
        for j in range(len(types)):
            v = m[i][j]
            fill = {0: colors.HexColor('#e8f5ec'), 1: colors.HexColor('#fdf6e6'),
                    2: colors.HexColor('#fdeaea')}[v]
            edge = {0: GREEN, 1: AMBER, 2: RED}[v]
            d.add(Rect(x0 + j * cs, y, cs - 3, cs * 0.62 - 3,
                       fillColor=fill, strokeColor=edge, strokeWidth=0.7))
            _txt(d, x0 + j * cs + (cs - 3) / 2, y + 8,
                 {0: '✓', 1: '!', 2: '✕'}[v], 9, BOLD, edge, 'middle')

    ly = 30
    for i, (c, t) in enumerate(((GREEN, '✓ 正常'), (AMBER, '! 警告'), (RED, '✕ 错误'))):
        _txt(d, 8 + i * 76, ly, t, 8, BOLD, c)
    _txt(d, 8, 16, '两个输出引脚直接相连是硬错误（会短路）；电源输出对电源输出同理。',
         8, FONT, DARK)
    _txt(d, 8, 4, '电源网络必须有至少一个「电源输出」或 PWR_FLAG，否则报「电源未驱动」。',
         8, BOLD, RED)
    return d


FIGURES = {
    'flow': flow,
    'stackup': stackup,
    'microstrip': microstrip,
    'priority': priority,
    'refplane': refplane,
    'layout': layout,
    'sch_flow': sch_flow,
    'sch_connect': sch_connect,
    'sch_hierarchy': sch_hierarchy,
    'sch_dataflow': sch_dataflow,
    'sch_erc': sch_erc,
}


def make(name, caption=''):
    """返回可插入 story 的 flowable 列表。"""
    if name not in FIGURES:
        raise SystemExit('[ERROR] 未定义的插图: %s（可用: %s）'
                         % (name, ', '.join(sorted(FIGURES))))
    out = [Spacer(1, 4), FIGURES[name]()]
    if caption:
        out.append(Paragraph(caption, CAP))
    else:
        out.append(Spacer(1, 8))
    return out


# ================================================================ FT2232HL 系列

def ft_arch():
    """FT2232HL 双通道架构：一个 USB 口如何分出 JTAG 与 UART。"""
    d = Drawing(W, 272)

    _box(d, 2, 158, 58, 46, colors.HexColor('#eef3f8'), ACCENT, 1.0, r=4)
    _txt(d, 31, 186, 'USB Type-C', 7.5, BOLD, ACCENT, 'middle')
    _txt(d, 31, 175, 'D+ / D-', 7, FONT, GREY, 'middle')
    _txt(d, 31, 164, 'CC 仅供电/方向', 6.5, FONT, GREY, 'middle')
    _arrow(d, 60, 181, 84, 181, ACCENT, 1.1)

    _box(d, 86, 96, 250, 160, colors.white, ACCENT, 1.2, r=5)
    d.add(Rect(86, 236, 250, 20, fillColor=ACCENT, strokeColor=ACCENT))
    _txt(d, 211, 242, 'FT2232HL   USB 复合设备   VID:PID = 0403:6010',
         8, BOLD, colors.white, 'middle')

    ch = [(172, 'Interface 0', 'Channel A', 'MPSSE 至 JTAG', 'ADBUS0-7 / ACBUS0-7', GREEN),
          (110, 'Interface 1', 'Channel B', 'UART', 'BDBUS0-7 / BCBUS0-7', AMBER)]
    for y, itf, name, mode, pins, col in ch:
        _box(d, 96, y, 230, 52, colors.white, col, 1.0, r=4)
        d.add(Rect(96, y, 4, 52, fillColor=col, strokeColor=col))
        _txt(d, 108, y + 37, name, 9.5, BOLD, DARK)
        _txt(d, 108, y + 22, itf, 7.5, FONT, GREY)
        _txt(d, 108, y + 8, mode, 8.5, BOLD, col)
        _arrow(d, 328, y + 26, 356, y + 26, col, 1.0)
        _box(d, 358, y + 8, 122, 36, colors.HexColor('#fafbfc'), col, 0.8, r=3)
        _txt(d, 419, y + 26, pins, 7, BOLD, DARK, 'middle')
        _txt(d, 419, y + 14, '目标板调试口', 6.5, FONT, GREY, 'middle')

    _txt(d, 211, 100, '两通道完全独立，同时工作，无需切换', 7.5, BOLD, ACCENT, 'middle')

    d.add(Line(4, 82, W - 4, 82, strokeColor=colors.HexColor('#d5dee7'), strokeWidth=0.6))
    _txt(d, 4, 68, '主机端枚举结果（EEPROM 按建议配置后）', 8.5, BOLD, DARK)
    rows = [(GREEN, 'Channel A', 'D2XX 驱动', '不产生 COM 口，OpenOCD / flashrom 独占'),
            (AMBER, 'Channel B', 'VCP 驱动', 'Windows: COM 口　Linux: /dev/ttyUSB0')]
    for i, (col, a, b, c) in enumerate(rows):
        y = 46 - i * 22
        d.add(Rect(4, y - 2, 4, 16, fillColor=col, strokeColor=col))
        _txt(d, 16, y + 2, a, 8, BOLD, col)
        _txt(d, 78, y + 2, b, 8, BOLD, DARK)
        _txt(d, 150, y + 2, c, 8, FONT, GREY)
    _txt(d, 4, 2, '识别靠 USB Interface 号，与 Type-C 接口本身无关；A 恒为 Interface 0。',
         7.5, BOLD, RED)
    return d


def ft_pinmux():
    """同一组数据引脚在四种模式下的功能对照。"""
    d = Drawing(W, 236)
    cols = [('UART', AMBER), ('MPSSE / JTAG', GREEN), ('MPSSE / SPI', GREEN),
            ('MPSSE / I2C', RED)]
    rows = [('xD0', ['TXD', 'TCK', 'SCK', 'SCL'], True),
            ('xD1', ['RXD', 'TDI', 'MOSI', 'SDA (out)'], True),
            ('xD2', ['RTS#', 'TDO', 'MISO', 'SDA (in)'], True),
            ('xD3', ['CTS#', 'TMS', 'CS#', '—'], True),
            ('xD4-7', ['DTR#/DSR#/DCD#/RI#', 'GPIOL0-3', 'GPIOL0-3', 'GPIOL0-3'], False),
            ('xCBUS0-7', ['—', 'GPIOH0-7', 'GPIOH0-7', 'GPIOH0-7'], False)]

    lx, cw, rh = 66, 103, 26
    top = 236 - 30
    for j, (name, col) in enumerate(cols):
        x = lx + j * cw
        d.add(Rect(x, top, cw - 4, 20, fillColor=col, strokeColor=col))
        _txt(d, x + (cw - 4) / 2, top + 6, name, 7.5, BOLD, colors.white, 'middle')

    for i, (pin, vals, mux) in enumerate(rows):
        y = top - (i + 1) * rh - 4
        _txt(d, lx - 8, y + 9, pin, 8, BOLD, DARK, 'end')
        for j, v in enumerate(vals):
            x = lx + j * cw
            fill = colors.HexColor('#fdf6e6') if mux else colors.HexColor('#f2f4f6')
            edge = cols[j][1] if mux else colors.HexColor('#c3ccd4')
            d.add(Rect(x, y, cw - 4, rh - 5, fillColor=fill, strokeColor=edge,
                       strokeWidth=0.8 if mux else 0.5))
            _txt(d, x + (cw - 4) / 2, y + 8, v, 7.5 if len(v) < 14 else 6.3,
                 BOLD if mux else FONT, DARK if mux else GREY, 'middle')

    ky = top - 4 * rh - 8
    d.add(Rect(lx - 3, ky - 1, 4 * cw - 1, 4 * rh + 1, fillColor=None,
               strokeColor=RED, strokeWidth=1.2))
    _txt(d, 4, 14, 'xD0-xD3 是复用冲突区：同一通道换模式，外部走线也必须跟着换。',
         8, BOLD, RED)
    _txt(d, 4, 2, 'x 代表 A（Channel A）或 B（Channel B）。xD4-7 与 xCBUS 在 MPSSE 下恒为 GPIO。',
         7.5, FONT, GREY)
    return d


def ft_i2c():
    """MPSSE 做 I2C 时的外部接线要求。"""
    d = Drawing(W, 198)
    _box(d, 4, 46, 104, 110, colors.white, ACCENT, 1.1, r=4)
    _txt(d, 56, 138, 'FT2232HL', 9, BOLD, ACCENT, 'middle')
    _txt(d, 56, 126, 'MPSSE', 7.5, FONT, GREY, 'middle')

    for y, p, f in ((108, 'AD0', 'SCL'), (86, 'AD1', 'DO'), (64, 'AD2', 'DI')):
        _txt(d, 100, y - 3, p, 7.5, BOLD, DARK, 'end')
        _txt(d, 112, y + 5, f, 6.5, FONT, GREY)

    d.add(Line(108, 108, 400, 108, strokeColor=DARK, strokeWidth=1.0))
    d.add(Line(108, 86, 196, 86, strokeColor=RED, strokeWidth=1.4))
    d.add(Line(108, 64, 196, 64, strokeColor=RED, strokeWidth=1.4))
    d.add(Line(196, 64, 196, 86, strokeColor=RED, strokeWidth=1.4))
    d.add(Line(196, 75, 400, 75, strokeColor=DARK, strokeWidth=1.0))
    for yy in (64, 86, 75):
        d.add(Polygon([196, yy, 192, yy - 2.8, 192, yy + 2.8],
                      fillColor=RED, strokeColor=RED))
    _txt(d, 202, 92, '外部短接后才是 SDA', 8, BOLD, RED)
    _txt(d, 202, 52, 'MPSSE 输入输出物理分离，', 7, FONT, GREY)
    _txt(d, 202, 42, '不短接读不到 ACK', 7, BOLD, RED)

    d.add(Line(300, 108, 300, 182, strokeColor=DARK, strokeWidth=1.0))
    d.add(Line(340, 75, 340, 182, strokeColor=DARK, strokeWidth=1.0))
    d.add(Line(276, 182, 364, 182, strokeColor=RED, strokeWidth=1.4))
    _txt(d, 370, 179, '3V3', 8, BOLD, RED)
    for x in (300, 340):
        d.add(Rect(x - 6, 132, 12, 22, fillColor=colors.white,
                   strokeColor=DARK, strokeWidth=0.9))
    _txt(d, 292, 143, '2.2k 至 4.7k 上拉', 7.5, BOLD, DARK, 'end')
    _txt(d, 294, 116, 'SCL', 7, FONT, GREY, 'end')
    _txt(d, 334, 82, 'SDA', 7, FONT, GREY, 'end')

    _box(d, 402, 58, 76, 68, colors.HexColor('#f2f4f6'),
         colors.HexColor('#94a7b8'), 0.8, r=3)
    _txt(d, 440, 102, 'I2C 从设备', 8, BOLD, DARK, 'middle')
    _txt(d, 440, 88, 'EEPROM /', 7, FONT, GREY, 'middle')
    _txt(d, 440, 78, '传感器', 7, FONT, GREY, 'middle')

    _txt(d, 4, 24, 'MPSSE 引脚不是真开漏，靠固件切输入态模拟高阻，上拉电阻必须外接。',
         8, BOLD, RED)
    _txt(d, 4, 12, '速率上限约 400 kHz（Fast mode），够用于配置类操作，不适合高速采集。',
         7.5, FONT, GREY)
    return d


def ft_eeprom():
    """93LC56B 配置 EEPROM 的接法与救砖点。"""
    d = Drawing(W, 194)
    _box(d, 4, 62, 118, 114, colors.white, ACCENT, 1.1, r=4)
    _txt(d, 63, 160, 'FT2232HL', 9, BOLD, ACCENT, 'middle')

    _box(d, 300, 62, 128, 114, colors.white, colors.HexColor('#7d8f9e'), 1.1, r=4)
    _txt(d, 364, 160, '93LC56BT-I/OT', 9, BOLD, DARK, 'middle')
    _txt(d, 364, 148, '2 Kbit　128 x 16　SOT-23-6', 7, FONT, GREY, 'middle')

    for y, l, r in ((132, 'EECS', 'CS'), (112, 'EECLK', 'CLK'), (92, 'EEDATA', 'DI')):
        _txt(d, 116, y - 3, l, 7.5, BOLD, DARK, 'end')
        _txt(d, 306, y - 3, r, 7.5, BOLD, DARK)
        d.add(Line(122, y, 300, y, strokeColor=ACCENT, strokeWidth=1.0))

    d.add(Line(122, 92, 122, 76, strokeColor=RED, strokeWidth=1.2))
    d.add(Line(122, 76, 190, 76, strokeColor=RED, strokeWidth=1.2))
    d.add(Rect(190, 69, 30, 14, fillColor=colors.white, strokeColor=RED, strokeWidth=1.1))
    _txt(d, 205, 57, '2.2k', 7.5, BOLD, RED, 'middle')
    d.add(Line(220, 76, 300, 76, strokeColor=RED, strokeWidth=1.2))
    _txt(d, 306, 73, 'DO', 7.5, BOLD, DARK)

    d.add(Polygon([250, 132, 245, 140, 255, 140], fillColor=AMBER, strokeColor=AMBER))
    d.add(Line(250, 140, 250, 152, strokeColor=AMBER, strokeWidth=1.1))
    d.add(Rect(243, 152, 14, 10, fillColor=colors.white, strokeColor=AMBER, strokeWidth=1.0))
    _txt(d, 262, 154, 'TP', 7.5, BOLD, AMBER)

    notes = [(44, RED, BOLD, '必须串 2.2k 电阻：DI/DO 合并成一根线，防双向驱动冲突。'),
             (32, AMBER, BOLD, 'TP 为救砖测试点：短接到 GND 可让芯片忽略 EEPROM，回退默认值重新枚举。'),
             (20, RED, BOLD, '必须用 B 版（x16 组织）。93LC56A 是 x8 组织，FT2232H 读不了。'),
             (8, GREY, FONT, '出厂空白（全 0xFF）时芯片回退片内默认值照常枚举，可直接用 FT_PROG 烧录。')]
    for y, col, fnt, txt in notes:
        _txt(d, 4, y, txt, 8 if fnt is BOLD else 7.5, fnt, col)
    return d


FIGURES.update({
    'ft_arch': ft_arch,
    'ft_pinmux': ft_pinmux,
    'ft_i2c': ft_i2c,
    'ft_eeprom': ft_eeprom,
})


# ================================================================ Power 电源系列

def _pwbox(d, x, y, w, h, title, sub='', col=ACCENT, fill=colors.white):
    _box(d, x, y, w, h, fill, col, 1.0, r=4)
    _txt(d, x + w / 2, y + h / 2 + (2 if sub else -3), title, 8, BOLD, DARK, 'middle')
    if sub:
        _txt(d, x + w / 2, y + h / 2 - 9, sub, 6.5, FONT, GREY, 'middle')


def _tag(d, x, y, n, col=RED):
    d.add(Rect(x - 7, y - 7, 14, 14, rx=7, ry=7, fillColor=col, strokeColor=col))
    _txt(d, x, y - 3, str(n), 7.5, BOLD, colors.white, 'middle')


def pw_now():
    """当前 Power 页网络现状：电源名不一致导致核心板无供电。"""
    d = Drawing(W, 250)
    # 主路径
    _pwbox(d, 4, 176, 78, 40, 'J10 USB-C', 'CC 5.1k 下拉')
    _arrow(d, 82, 196, 112, 196, ACCENT, 1.1)
    _txt(d, 97, 202, '+VBUS_5V', 6.5, BOLD, ACCENT, 'middle')
    _pwbox(d, 114, 176, 84, 40, 'TPS78633', 'LDO  SOT-223', AMBER)
    _arrow(d, 198, 196, 228, 196, ACCENT, 1.1)
    _txt(d, 213, 202, '+3.3V', 6.5, BOLD, ACCENT, 'middle')
    _pwbox(d, 230, 176, 84, 40, 'AMS1117-1.8', '3.3V 降 1.8V', AMBER)
    _arrow(d, 314, 196, 344, 196, ACCENT, 1.1)
    _txt(d, 329, 202, '+1.8V', 6.5, BOLD, ACCENT, 'middle')
    _pwbox(d, 346, 176, 132, 40, 'FT2232H / TXS02612', '1.8V 负载（待确认）', GREY)
    _tag(d, 88, 222, 3, AMBER); _tag(d, 156, 222, 4, AMBER); _tag(d, 272, 222, 9, AMBER)

    # 断开的 +5V
    d.add(Line(97, 176, 97, 142, strokeColor=RED, strokeWidth=1.1, strokeDashArray=[3, 2]))
    d.add(Line(91, 156, 103, 144, strokeColor=RED, strokeWidth=1.6))
    d.add(Line(91, 144, 103, 156, strokeColor=RED, strokeWidth=1.6))
    _txt(d, 108, 152, '网络名不同，不连通', 7.5, BOLD, RED)
    _pwbox(d, 4, 96, 150, 40, 'ZynqCore 核心板', '+5V 输入（无来源）', RED, colors.HexColor('#fdf0ee'))
    _pwbox(d, 166, 96, 150, 40, 'Comm_Periph', '+5V（无来源）', RED, colors.HexColor('#fdf0ee'))
    _tag(d, 10, 140, 1)

    # USB D± 悬空
    _tag(d, 236, 155, 2)
    _txt(d, 246, 152, 'J10 的 USB_D+ / USB_D- 为本地标签，未接任何器件', 7, BOLD, RED)
    _pwbox(d, 346, 96, 132, 40, 'J12 USB-C (Storage)', '独立网络 +VBUS', GREY)

    d.add(Line(4, 82, W - 4, 82, strokeColor=colors.HexColor('#d5dee7'), strokeWidth=0.6))
    rows = [(RED, '1', '+VBUS_5V 与 +5V 名称不同：核心板、Comm_Periph 均无 5V 供电'),
            (RED, '2', 'J10 的 D+/D- 没有去向，ERC 会报未连接'),
            (AMBER, '3', 'Rd=5.1k 只能拿到 USB 默认电流（电脑口 500 mA）'),
            (AMBER, '4', 'TPS78633 压差 1.7 V，0.8 A 时耗散约 1.4 W'),
            (AMBER, '9', 'AMS1117 压差余量仅 0.2~0.4 V，且 1.8V 可能可省')]
    for i, (c, n, t) in enumerate(rows):
        y = 66 - i * 14
        _tag(d, 10, y + 3, n, c)
        _txt(d, 22, y, t, 7.5, BOLD if c == RED else FONT, c if c == RED else DARK)
    return d


def pw_fix():
    """建议的电源路径。"""
    g = Group()
    d = g
    # 两路输入
    _pwbox(d, 4, 206, 70, 36, 'DC 圆座', '5V / 3A 主电源')
    _pwbox(d, 4, 152, 70, 36, 'J10 USB-C', 'CC 5.1k')
    for y in (224, 170):
        _arrow(d, 74, y, 92, y, ACCENT, 1.0)
        _pwbox(d, 94, y - 14, 44, 28, 'PPTC', '2A', GREEN)
        _arrow(d, 138, y, 154, y, ACCENT, 1.0)
        _pwbox(d, 156, y - 14, 50, 28, '肖特基', '或理想二极管', GREEN)
        d.add(Line(206, y, 222, y, strokeColor=ACCENT, strokeWidth=1.0))
        # TVS 到地
        d.add(Line(147, y, 147, y - 24, strokeColor=GREEN, strokeWidth=0.9))
        d.add(Rect(141, y - 34, 12, 10, fillColor=colors.white, strokeColor=GREEN, strokeWidth=0.9))
        _txt(d, 156, y - 32, 'TVS', 6.5, BOLD, GREEN)
    d.add(Line(222, 224, 222, 170, strokeColor=ACCENT, strokeWidth=1.0))
    _txt(d, 4, 106, 'TVS：SMBJ5.0A，放在 PPTC 之后，击穿短路时由 PPTC 断开', 6.8, FONT, GREY)

    _arrow(d, 222, 197, 240, 197, ACCENT, 1.1)
    _pwbox(d, 242, 180, 72, 34, '负载开关', 'TPS22918 / 拨动', GREEN)
    _arrow(d, 314, 197, 334, 197, ACCENT, 1.2)
    # +5V 母线
    d.add(Line(336, 250, 336, 110, strokeColor=RED, strokeWidth=2.2))
    _txt(d, 336, 255, '+5V 母线（统一网络名）', 8, BOLD, RED, 'middle')
    _txt(d, 322, 168, '10uF', 6.5, BOLD, AMBER, 'end')
    _txt(d, 322, 160, '限值', 6.5, FONT, GREY, 'end')

    for y, t, s, col in ((222, 'ZynqCore 核心板', '+5V 输入', ACCENT),
                         (178, 'Buck 3.3V', 'TPS62130 / SY8089', GREEN),
                         (124, 'Comm_Periph', '+5V 外设', ACCENT)):
        _arrow(d, 336, y, 356, y, ACCENT, 1.0)
        _pwbox(d, 358, y - 16, 120, 32, t, s, col)
    _arrow(d, 418, 162, 418, 148, ACCENT, 1.0)
    _txt(d, 424, 152, '+3.3V', 6.5, BOLD, ACCENT)
    _pwbox(d, 242, 116, 72, 34, '电源指示灯', 'LED + 限流电阻', GREY)
    d.add(Line(314, 133, 336, 133, strokeColor=GREY, strokeWidth=0.8))

    out = Drawing(W, 166)
    g.transform = (1, 0, 0, 1, 0, -102)
    out.add(g)
    return out


FIGURES.update({
    'pw_now': pw_now,
    'pw_fix': pw_fix,
})
