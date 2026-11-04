import fitz,io,math
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
root=Path('tmp/erc-review');target=Path('docs/CORE_Rev1.0_原理图检查报告_2026-11-04.pdf')
src=fitz.open(root/'schematic.pdf');doc=fitz.open(target);doc.select(list(range(7)))
# Source coordinates are PDF points, measured on the vector schematic exported by KiCad.
views=[
('图 1 / Storage：FT2232HL 电源与复位',3,(45,225,610,555),[
((369,230,395,274),'VCORE 错接 3.3V','U3.12、37、64 必须从 +3.3V 分离。建议连接到独立 FTDI_1V8 网络，由 VREGOUT 提供 1.8V。',False),
((300,260,350,280),'VREGOUT 悬空','将 U3.49 接到上述 FTDI_1V8；补 ≥3.3µF 滤波电容及各 VCORE 的 100nF 去耦。不得并接另一颗稳压器输出。',False),
((300,345,349,368),'RESET# 悬空','U3.14 不使用外部复位时接 VCCIO 3.3V；可按官方参考电路增加上拉。',False),
((343,229,430,275),'补齐电源去耦','核对 VCCIO、VPHY、VPLL、VREGIN 的本地去耦；USB 的 VBUS 电容不能替代这些电容。',True),
((55,265,248,352),'确认 USB 自供电配置','USB1 的 VBUS 只接电容，未供电给 U3。若需只插该口即可运行，应重新设计供电；否则按自供电方式核对检测及配置。',True)
]),
('图 2 / Comm_Periph：网口保护器件两侧未贯通',2,(105,100,470,320),[
((169,125,222,180),'D10 四通道断开','每对引脚应显式连接：1↔10、2↔9、4↔7、5↔6。左侧 PHY 与右侧 RJ1 对应信号必须成为同一网络。',False),
((169,185,227,232),'D11 四通道断开','D11 同样添加上述四组连接。NC 端并没有芯片内部直通，不能当作串联器件使用。',False),
((276,179,312,250),'中心抽头接法待确认','RJ1.P5/P6 当前通过 C1 到地。需拿到核心板 PHY 型号及推荐电路后确认，不能直接认定必须接电源。',True)
]),
('图 3 / Comm_Periph：IO8、IO9 未接外部接口',2,(290,425,475,550),[
((354,515,387,541),'IO8 / IO9 悬空','这两个层次标签未连接器件。若需要使用，应接到连接器；若不用，清理对应层次端口/父页导线，在模块引脚处明确标为未使用。',False)
]),
('图 4 / Display：悬空线与符号定义',4,(85,90,410,425),[
((205,157,229,172),'检查背光侧悬空线端','ERC 报告 Display 横线末端未连接（UUID b56ea5d5…）。确认是否为多画的短线，或补齐需要的连接。',False),
((313,147,331,164),'检查另一处悬空线端','ERC 报告另一条横线末端未连接（UUID c0070011…）。应按连通关系处理，不要只隐藏告警。',False),
((168,190,210,230),'修正 Q1 的引脚类型','G/D/S 当前为 Unspecified，导致三条警告。先核对编号，再将 G 设为 Input、D/S 设为合适的 Passive 类型。',True),
((321,375,351,395),'触摸 I²C 上拉待确认','底板未见独立上拉。先查屏模组或核心板是否已有上拉，并确认接口电压。',True)
]),
('图 5 / Power：重复电源输出标记',6,(75,50,420,165),[
((354,76,395,106),'删除多余 PWR_FLAG','U5 输出端已有 Power output，#FLG06 再声明电源输出会形成 ERC 冲突。删除这一个多余标记即可。',False),
((281,72,340,126),'此处不是实际电源短路','该 ERC 是标记与稳压器输出之间的类型冲突；不能因此断开正常的 +1.8V 供电。',True)
]),
('图 6 / Signal：明确 LVDS 阻抗与终端条件',5,(40,35,790,475),[
((90,73,205,130),'“100 OHM TRACE”含义待确认','同类注释分布于多路 P/N 线路。若 P/N 分别走常见 50Ω 同轴，单根应匹配其单端阻抗，100Ω通常指差分阻抗。先确定线缆与接口条件。',True),
((40,35,430,465),'接收端终端待确认','底板未展示差分终端。需要核对核心板已有终端或 FPGA 内部终端配置，避免漏装或重复终端；此项不是已确认缺失。',True)
])]
W,H=1190.55,841.89
for vi,(title,si,clip,marks) in enumerate(views):
 page=doc.new_page(width=W,height=H)
 # Diagram occupies the left pane; right pane contains readable annotations.
 cr=fitz.Rect(clip);area=fitz.Rect(35,110,820,730);scale=min(area.width/cr.width,area.height/cr.height)
 dw,dh=cr.width*scale,cr.height*scale;dest=fitz.Rect(area.x0,area.y0+(area.height-dh)/2,area.x0+dw,area.y0+(area.height+dh)/2)
 page.show_pdf_page(dest,src,si,clip=cr)
 buf=io.BytesIO();c=canvas.Canvas(buf,pagesize=(W,H))
 c.setFillColorRGB(.07,.14,.22);c.setFont('STSong-Light',22);c.drawString(35,H-45,title)
 c.setFont('STSong-Light',11);c.drawString(35,H-70,'红色：确认的问题或 ERC 项；橙色：需核对条件。图纸、框线、箭头和文字均保留为矢量对象。')
 c.setStrokeColorRGB(.8,.83,.86);c.setLineWidth(.8);c.line(839,95,839,H-95)
 for mi,(box,head,body,conditional) in enumerate(marks):
  color=(.78,.36,.02) if conditional else (.8,.06,.1);c.setStrokeColorRGB(*color);c.setFillColorRGB(*color);c.setLineWidth(1.7)
  r=fitz.Rect(box);x=dest.x0+(r.x0-cr.x0)*scale;y=dest.y0+(r.y0-cr.y0)*scale;rw=r.width*scale;rh=r.height*scale
  c.rect(x,H-y-rh,rw,rh,stroke=1,fill=0)
  # Short arrow ends at the highlighted box's top-right corner.
  ex,ey=x+rw,H-y;sx,sy=min(ex+33,823),ey+24
  c.line(sx,sy,ex,ey);a=math.atan2(ey-sy,ex-sx)
  for da in [-.45,.45]:c.line(ex,ey,ex-8*math.cos(a+da),ey-8*math.sin(a+da))
  c.circle(sx,sy,10,stroke=1,fill=1);c.setFillColorRGB(1,1,1);c.setFont('Helvetica-Bold',10);c.drawCentredString(sx,sy-3,str(mi+1))
  ty=H-125-mi*132
  c.setFillColorRGB(*color);c.setFont('STSong-Light',13);c.drawString(858,ty,f'{mi+1}. {head}')
  st=ParagraphStyle('n',fontName='STSong-Light',fontSize=11,leading=18,wordWrap='CJK',textColor='#253747')
  para=Paragraph(body,st);pw,ph=para.wrap(290,130);para.drawOn(c,858,ty-15-ph)
 c.setFillColorRGB(.4,.4,.4);c.setFont('STSong-Light',10);c.drawString(35,30,'CORE Rev1.0 | 原理图问题位置标注 | 2026-11-04');c.drawRightString(W-35,30,'附图 '+str(vi+1))
 c.save();overlay=fitz.open(stream=buf.getvalue(),filetype='pdf');page.show_pdf_page(page.rect,overlay,0)
 page.get_pixmap(matrix=fitz.Matrix(.85,.85)).save(root/f'annotated-{vi+1}.png')
tmp=root/'report-vector.pdf';doc.save(tmp,garbage=4,deflate=True);doc.close();src.close()
target.write_bytes(tmp.read_bytes())
d=fitz.open(target);print('pages:',len(d),'vector drawing counts:',[(i+1,len(d[i].get_drawings()),len(d[i].get_images())) for i in range(7,len(d))])
from PIL import Image
sheet=Image.new('RGB',(1600,1740),'#cccccc')
for i in range(6):
 im=Image.open(root/f'annotated-{i+1}.png');im.thumbnail((790,560));sheet.paste(im,((i%2)*800,(i//2)*580))
sheet.save(root/'annotations-contact.png')

