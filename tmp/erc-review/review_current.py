from pathlib import Path
import json,html
from reportlab.platypus import SimpleDocTemplate,Paragraph,PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.styles import ParagraphStyle
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
ss={f.name:f.read_text(encoding='utf8') for f in Path('hardware/schematic/v1.0/CORE_Rev1.0').glob('*.kicad_sch')}
r=json.loads(Path('tmp/erc-review/erc-current.json').read_text(encoding='utf8'))
st=[]
styles={k:ParagraphStyle(k,fontName='STSong-Light',fontSize=z,leading=l,spaceAfter=10,wordWrap='CJK') for k,z,l in [('title',20,28),('h',14,20),('p',10.5,17),('s',9,14)]}
def p(t,k='p'):st.append(Paragraph(t,styles[k]))
p('CORE Rev1.0 原理图复查','title');p('2026-11-05 | 当前磁盘保存版本 | 仅原理图，不修改设计','s')
p('结果：ERC 0 条 error、11 条 warning。仍有一项确认的网口断路，不能以 ERC 零错误作为电路功能正确的结论。已对七张有效原理图进行图面检查，并用导出的 XML 网表核对实际连接。FMC_LPC 页未被根图引用。')
p('已修正项目','h')
p('U3.49 与 U3.12/37/64 同属 VREG，已从 +3.3V 分离；C31 为 4.7µF，另有 C28/C29/C30 各 100nF。U3.14 经 R38=1kΩ 上拉 3.3V。IO8/IO9 已引出到 J2。USB2 输入已改为 C6=100nF、C7=4.7µF；U5 输出端多余 PWR_FLAG 已删除。')
p('1. 必须修改：D10/D11 两侧信号仍然断开','h')
p('器件为 AZ1143-04F。左侧 1/2/4/5 为保护引脚，右侧 10/9/7/6 为 NC，没有内部直通。当前网表例如 PHY1_MDI0_P 仅含 M1.J2_3、D10.1；D10.10 与 RJ1.P1 则是另一条网。其余七根 MDI 同样断开。')
p('修改：D10、D11 各显式连接 1↔10、2↔9、4↔7、5↔6；3/8 保持接地。验收时每个 MDI 网都应同时含核心板 M1、保护器件和 RJ1 对应管脚。[1，第 5 页] 附图 1 已标出位置。')
p('2. 建议补齐：U3 的 3.3V 去耦','h')
p('三个 VCORE 的 100nF 已正确配置，但 VCCIO 20/31/42/56、VPHY 4、VPLL 9、VREGIN 50 仍直接接 +3.3V，图面未展示对应的完整本地去耦组。按官方参考电路补齐各供电脚 100nF 去耦及相应滤波。USB VBUS 上的 C20～C23 不能替代这些本地去耦。[2，第 6 节]')
st.append(PageBreak());p('3. USB1 与 USB2 要分别核算','h')
p('USB1：Storage 页 C20=100nF、C21=10µF、C22=10µF、C23=100nF，直接并在 VBUS，合计标称 20.2µF。可先精简为一颗 4.7µF 与一颗 100nF，再核算接口总输入电容与浪涌。USB1 VBUS 当前仅接电容，U3 由系统 3.3V 供电；因此 USB1 单独插入并不能给下载器供电，需确认这是预期的自供电方式，并核对 USB 插拔检测和配置。[2][3]')
p('USB2：本地电容已为 4.8µF；不过 +VBUS_5V 经 D8、F2 到 +5V，后者还连接 U2 电源支路及核心板。R40=0Ω，使 C8=10µF 等效接在 +5V 输入上。二极管和保险丝不会隔离上电充电浪涌，因此不能只按接口旁 4.8µF 宣称满足浪涌要求。需结合核心板输入电容与负载，核算或增加带软启动/限流的电源开关。[3]')
p('4. 符号及 ERC 处理','h')
p('VREGOUT 49 脚在当前网表仍为 power_in，VREG 上的 PWR_FLAG 使未驱动告警消失。实际供电连接已正确，但应将 49 脚修正为 Power output，再删除 VREG 的 PWR_FLAG。')
p('Display 两条未连接线端分别在背光 LEDK 和屏连接器附近；网表确认 R26.2 与屏 2 脚已同网，因此不能把它直接判作背光断路。按图删除多余尾线或补齐实际遗漏连接。Q1 G/D/S 为 Unspecified，需核对脚号后设置恰当类型。')
p('四项库符号不一致：RGB TFTLCD1、U6、X1、U2。先比对引脚编号、功能、封装，再选择更新库或图内符号。两项封装链接缺失：CN1、F2，恢复对应封装文件或修正库链接。')
p('5. 尚不能确认的条件','h')
p('M1 是核心板模块符号，缺少其内部原理图，无法确认 Bank/MIO 电压、PHY 型号、接口真实引脚和核心板已有终端。需继续核对：SD 侧 1.8V 是否匹配 MIO；网口中心抽头方案；LVDS 100Ω 注释是否指差分阻抗及终端位置；触摸 I²C 是否已有上拉；XADC 外接电压范围；屏背光参数与电流。以上属于待确认条件，不能直接当作已证实错误。')
st.append(PageBreak());p('ERC 完整结果：11 条警告','h')
for i,v in enumerate([v for sh in r['sheets'] for v in sh['violations']],1):
 uid=v['items'][0]['uuid']; fn=next((f for f,s in ss.items() if uid in s),'未知');p(f'{i}. {html.escape(fn)} | {v["type"]}<br/>{html.escape(v["description"])}<br/>'+html.escape('；'.join(x['description'] for x in v['items'])),'s')
p('检查设置：single_global_label、four_way_junction、simulation_model_issue、footprint_filter 四类仍被工程关闭；当前未见 ERC 排除项。')
p('参考资料','h')
for t,u in [('1. AZ1143-04F 官方手册','https://www.amazingic.com/uploads/images/products/PDF/AZ1/AZ1143-04F.pdf'),('2. FT2232H 官方手册 v2.9','https://www.ftdichip.cn/Support/Documents/DataSheets/ICs/DS_FT2232H.pdf'),('3. TI：USB Type-C 供电电容与浪涌','https://www.ti.com/document-viewer/lit/html/SSZTA47')]:p(f'<link href="{u}">{t}</link>','s')
def footer(c,d):c.setFont('STSong-Light',9);c.drawString(40,25,'CORE 原理图复查 | 2026-11-05');c.drawRightString(552,25,str(d.page))
SimpleDocTemplate('docs/CORE_Rev1.0_原理图复查_2026-11-05.pdf',leftMargin=42,rightMargin=42,topMargin=38,bottomMargin=42).build(st,onFirstPage=footer,onLaterPages=footer)
# Reuse the verified vector annotation layout with only current outstanding issues.
s=Path('tmp/erc-review/annotate_report.py').read_text(encoding='utf-8-sig')
s=s.replace('CORE_Rev1.0_原理图检查报告_2026-11-04.pdf','CORE_Rev1.0_原理图复查_2026-11-05.pdf').replace("root/'schematic.pdf'","root/'schematic-current.pdf'").replace(';doc.select(list(range(7)))','').replace('2026-11-04','2026-11-05')
s=s.replace('W,H=1190.55,841.89',"views=[views[1],views[3]]\nW,H=1190.55,841.89")
s=s.replace("for i in range(6):","for i in range(2):").replace('range(7,len(d))','range(3,len(d))')
Path('tmp/erc-review/annotate_current.py').write_text(s,encoding='utf8')

