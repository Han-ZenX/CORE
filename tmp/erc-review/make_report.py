from pathlib import Path
import json,re,html
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Image,KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib import colors
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
out=Path('docs/CORE_Rev1.0_原理图检查报告_2026-11-04.pdf')
styles={k:ParagraphStyle(k,fontName='STSong-Light',fontSize=z,leading=l,textColor=colors.HexColor('#172534'),spaceAfter=sp,wordWrap='CJK') for k,z,l,sp in [('title',22,30,16),('h',14,21,10),('body',10.5,17,9),('small',9,14,7)]}
story=[]
def p(t,k='body'):story.append(Paragraph(t,styles[k]))
def h(t):p(t,'h')
def page():story.append(PageBreak())
p('CORE Rev1.0 原理图检查报告','title')
p('检查日期：2026-11-04　｜　KiCad 10.0.4　｜　仅检查原理图','small')
p('对象：hardware/schematic/v1.0/CORE_Rev1.0/CORE_Rev1.0.kicad_sch，以及其引用的六张子页。检查方式：完整层次 ERC、XML 网表逐引脚核对、七页图面审阅及关键器件官方数据手册比对。FMC_LPC.kicad_sch 未被根图引用，不属于本次七页有效电路。')
h('结论：存在必须修正的硬件连接问题')
p('最优先处理 U3（FT2232HL）的 VCORE 错接 3.3V，以及 D10/D11（AZ1143-04F）前后网络未贯通。随后处理 U3 复位、供电去耦及 IO8/IO9 悬空。普通 ERC 无法判断电源电压是否适合器件，也无法识别保护器件 NC 引脚被误当作内部直通端口。')
p('原始 ERC：8 条 error、13 条 warning，共 21 条；未配置排除项。工程关闭了 single_global_label、four_way_junction、simulation_model_issue、footprint_filter 四类检查，因此 21 条并非所有可疑设计问题的总数。')
h('边界与资料缺口')
p('本次不修改原理图，也不包含 PCB 评价。M1 是核心板模块符号，不是 Zynq 芯片完整原理图；无法据此确认模块内部 PHY 型号、Bank 电压、核心板接口定义、终端匹配和启动绑带。报告将确定错误与需要补充核心板/外设资料的核对项分开。')
h('建议修改顺序')
p('1. 修正 U3 核心供电，补齐复位及去耦。<br/>2. 将 D10/D11 各通道的两侧显式接为同一网络。<br/>3. 处理 IO8/IO9、Display 悬空线和库定义。<br/>4. 核对核心板电平、网口中心抽头、LVDS 终端及外部接口。<br/>5. 重跑 ERC，并用网表再次确认关键引脚。')
page();h('01 / U3：核心电压错接（已确认，最高优先级）')
p('位置：Storage 子页，U3 FT2232HL。网表显示 U3.12、U3.37、U3.64（VCORE）全部接到 +3.3V。官方规定 VCORE 正常工作范围为 1.62～1.98V，典型 1.8V。当前连接有器件损坏风险，不能作为正确电路上电。[1，表 5.2]')
p('建议采用官方内部稳压方案：将上述三个 VCORE 从 +3.3V 分离，接入独立网络 FTDI_1V8；将 U3.49（VREGOUT）连接到 FTDI_1V8，U3.50（VREGIN）保留 +3.3V。FTDI_1V8 增加不小于 3.3µF 的滤波电容，并在各 VCORE 引脚就近配置 100nF 去耦。不得再与 AMS1117 的 +1.8V 输出直接并联。')
p('也可使用外部 1.8V 方案，但必须完整遵循官方外部稳压参考电路，不能将两个稳压输出并接。当前 U3.49 既悬空又被符号误定义为 Power input，应修正为 Power output。VCCIO、VPHY、VPLL、VREGIN 维持各自要求的 3.3V 供电，不要整体改为 1.8V。[1，第 6 节]')
h('02 / U3：复位、去耦与 USB 工作方式')
p('U3.14 RESET# 在网表中为独立未连接网络。官方明确要求不用外部复位时接 VCCIO（3.3V）；建议按参考电路增加上拉（例如 1kΩ）到 3.3V，若要外部控制则接可靠的复位驱动。[1，第 4 节]')
p('现有 U3 电源直接汇在 3.3V 上，图面未见完整的各供电脚本地去耦组。VBUS 上的 C20～C23 不能代替 U3 各供电脚的去耦。按参考电路补齐 VCCIO、VPHY、VPLL、VREGIN 的去耦，并核对模拟供电滤波。[1，第 6 节]')
p('USB1 的 +VBUS 仅接 C20～C23，没有给 U3 提供供电；U3 使用系统 +3.3V。这意味着此 USB 是自供电连接，需要按官方自供电配置核对插拔检测及 EEPROM 配置。若希望只插 USB1 就能运行下载器，当前供电网络不支持。USB1 直接挂有两颗 10µF，建议另外核算插入时的输入电容/浪涌预算；此项不是已确认的断线错误。')
p('验收：网表中 +3.3V 不再包含 U3.12/37/64；三个 VCORE 与 U3.49 同网；RESET# 有明确高电平/复位路径；电源引脚及去耦逐项有对应关系。')
page();h('03 / 网口：保护阵列两侧断开（已确认）')
p('位置：Comm_Periph 子页，D10/D11 AZ1143-04F。保护阵列不是内部直通的串联器件；1/2/4/5 是保护线，10/9/7/6 为 NC。厂家要求用外部导线连接成对端子。[2，第 1、5 页]')
p('当前示例：M1.J2_3 → D10.1 属于 PHY1_MDI0_P；D10.10 → RJ1.P1 却属于 Net-(D10-NC-Pad10)。两个网络没有连接。D10/D11 四通道均存在同类问题，网口八根信号都未在原理图网表中形成完整通路。')
p('修改：D10 和 D11 分别添加 1↔10、2↔9、4↔7、5↔6 的显式连接，或者采用单端分支形式表示保护器件，使对应 PHY 与 RJ45 管脚直接处于同一网络。3、8 保持接地。不要依赖器件内部或隐藏的封装铜连接来补原理图网表。')
p('验收：每条 MDI 网络同时包含 M1 接口引脚、D10/D11 对应保护引脚以及 RJ1 对应引脚；不再出现只有 NC 和 RJ1 的八条孤立网。')
h('04 / IO8、IO9：接口标签悬空（已确认）')
p('Comm_Periph 页底部的 IO8/IO9 层次标签悬空；对应网表只有 M1.J2_59、M1.J2_61，未接外部负载或连接器。若要引出，增加实际连接器并连接；若明确不用，删除对应层次标签及父页两端相关层次引脚/导线，在真正不用的模块引脚处使用明确的未连接标记。不要只抑制 ERC。')
h('05 / 工程和符号定义问题')
p('U5 的 +1.8V 已有稳压器 Power output，又放了 #FLG06，导致电源输出冲突：删除多余的输出电源标记即可，不代表两颗实际稳压器相互短接。GND（#PWR02）及 USB1 +VBUS（#PWR031）的未驱动告警，应在确认真实供电来源后，用恰当的 PWR_FLAG/源引脚类型处理。')
p('Q1 的 G/D/S 被定义为 Unspecified，造成 3 条类型警告：核对实际引脚顺序后，G 设 Input、D/S 设 Passive 等合适类型。U6、X1、U2、RGB TFTLCD1 的库与图内符号不一致，应逐项比对编号/引脚/封装，不要未经核对一键覆盖。CN1、F2 的封装链接缺失是工程库问题，恢复实际封装或修正链接。')
page();h('06 / 需进一步确认的设计条件')
p('核心板与电平：M1 的引脚名大多只是连接器编号，ERC 无法证明这些编号与真实核心板吻合。需要该核心板原理图/接口表核对全部 J1/J2 引脚、正反面编号、Bank35 电压、PS MIO 电压、5V 输入能力及启动模式。SD 电平转换器 U1 的 A 侧固定 1.8V，只有核心板 SD 对应 MIO 确为 1.8V 时才正确。')
p('SD 卡：U1.SEL 由 R15 下拉，选 B0；卡数据接 B0，该选择关系与 TI 功能表一致。[3] SD_CD 经 R17/R16 连接卡座，并由 R18 上拉 3.3V，需要确认该信号进入的核心板引脚是否允许 3.3V。')
p('网口：RJ1 的 P5/P6 中心抽头只通过 C1 接地，是否正确取决于核心板 PHY 的具体型号及该磁性接口方案；缺少 PHY 资料，不能武断改接 3.3V。补充 PHY 型号后对照参考电路核查。')
p('LVDS：Signal 页每根独立 IPEX 线标注为“100 OHM TRACE”。若使用常见 50Ω 同轴分别传输 P/N，两根独立走线应按相应单端阻抗设计；标准 LVDS 的 100Ω通常指差分阻抗。[4] 应明确注释含义及线缆型号，并确认接收端有 100Ω 差分终端（核心板已有/FPGA 内部使能/外置择其适用方式），不能仅凭当前底板图确认缺失。普通 LVDS 同对 P/N 对调可在逻辑中补偿，但应写清每对映射。')
p('触摸与显示：CTP_SCL/CTP_SDA 当前底板未见独立上拉，需查屏模组/核心板是否已有上拉及允许电压。RGB TFTLCD1 是通用连接器，屏供电、背光电流和 FPC 顺序必须用所选屏规格确认。Q1 为低端开关且带下拉，结构本身不因 Unspecified 警告而被判定错误。')
p('XADC：J26 通过 49.9Ω 串阻接 XADC_VP/VN，没有电压缩放或输入钳位；必须明确外部模拟信号范围，并查核心板内是否已有调理电路。当前图无法证明外接 3.3V 信号可直接输入 XADC。')
h('修改后的验收要求')
p('ERC 不保留未说明的 error；所有 warning 逐项修正或记录理由。重新导出网表检查 U3 电源、复位、八根 MDI 与 IO8/IO9。补齐核心板与显示屏资料后，才能完成接口电压、管脚映射和外设兼容性的最终签核。本报告不是全板功能或电气性能验证通过证明。')
page();h('附录 A / ERC 全部 21 条原始结果')
p('位置按违规项 UUID 在实际文件中重新定位；工具部分层次路径归属与文件不一致，因此以下以实际文件为准。坐标字段存在比例异常，本报告不以其数值定位。','small')
r=json.loads(Path('tmp/erc-review/erc.json').read_text(encoding='utf8')); base=Path('hardware/schematic/v1.0/CORE_Rev1.0'); ss={f.name:f.read_text(encoding='utf8') for f in base.glob('*.kicad_sch')}
i=0
for sh in r['sheets']:
 for v in sh['violations']:
  i+=1; uid=v['items'][0]['uuid'];fn=next((f for f,s in ss.items() if uid in s),sh['path']); items='；'.join(x['description'] for x in v['items'])
  p(f'{i:02d}. {v["severity"].upper()} | {html.escape(fn)} | {html.escape(v["type"])}<br/>{html.escape(v["description"])}<br/>{html.escape(items)}','small')
page();h('附录 B / 资料来源与复核方法')
sources=[('1. FTDI FT2232H 数据手册，v2.9。核对表 5.2、复位说明及第 6 节供电参考设计。','https://www.ftdichip.cn/Support/Documents/DataSheets/ICs/DS_FT2232H.pdf'),('2. Amazing AZ1143-04F 数据手册，2014/10/02。核对引脚定义和外部连通要求。','https://www.amazingic.com/uploads/images/products/PDF/AZ1/AZ1143-04F.pdf'),('3. TI TXS02612 数据手册。核对 SEL 与 B0/B1 选择关系。','https://www.ti.com/lit/gpn/TXS02612'),('4. Analog Devices：High Speed Converter Survival Guide: Digital Data Outputs。核对 LVDS 差分与单端阻抗说明。','https://www.analog.com/en/resources/technical-articles/high-speed-converter-survival-guide-digital-data-outputs.html')]
for t,u in sources:p(t);p(f'<link href="{u}" color="#175AA0">{u}</link>','small')
p('可复现检查：使用 KiCad CLI 对根原理图执行 sch erc --format json --severity-all，并执行 sch export netlist --format kicadxml；后者用于确认真实网络，而非依赖图形外观。检查时工程原理图及项目文件已有用户未提交修改，本次读取其当前磁盘版本，未覆盖任何设计修改。')
def footer(c,d):
 c.setFont('STSong-Light',9);c.setFillColor(colors.grey);c.drawString(42,25,'CORE Rev1.0 | 原理图检查 | 2026-11-04');c.drawRightString(553,25,str(d.page))
SimpleDocTemplate(str(out),pagesize=(595.28,841.89),rightMargin=42,leftMargin=42,topMargin=40,bottomMargin=42).build(story,onFirstPage=footer,onLaterPages=footer)
import fitz
d=fitz.open(str(out));print('REPORT',out,'pages',len(d))
for i in range(len(d)):d[i].get_pixmap(matrix=fitz.Matrix(1,1)).save('tmp/erc-review/report-%d.png'%(i+1))
