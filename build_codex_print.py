"""Generate separate printable A4 Codex volumes from the website's content."""
from pathlib import Path
from html.parser import HTMLParser
from html import escape
import re
from reportlab.platypus import SimpleDocTemplate, KeepTogether, Paragraph, Spacer, PageBreak, Image, Table, TableStyle
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import portal, codex_core, codex_expansions, codex_homebrew, codex_2014

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'print'
OUT.mkdir(exist_ok=True)
for name,file in [('Book','georgia.ttf'),('Book-Bold','georgiab.ttf'),('Book-Italic','georgiai.ttf')]:
    pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+file))
pdfmetrics.registerFontFamily('Book',normal='Book',bold='Book-Bold',italic='Book-Italic',boldItalic='Book-Bold')
styles=getSampleStyleSheet()
for n in ('BodyText','Normal','Heading1','Heading2','Heading3','Title'):
    styles[n].fontName='Book'
styles['BodyText'].fontSize=10
styles['BodyText'].leading=14
styles['BodyText'].spaceAfter=8
styles['Heading2'].textColor=colors.HexColor('#653d28')
styles.add(ParagraphStyle('Cell',fontName='Book',fontSize=7.5,leading=10,spaceAfter=0))
styles.add(ParagraphStyle('Foot',fontName='Book',fontSize=8,leading=11,spaceAfter=5))

class Node:
    def __init__(self,tag='',attrs=()):self.tag=tag;self.attrs=dict(attrs);self.children=[]
    def text(self):return ''.join(c if isinstance(c,str) else c.text() for c in self.children)

class Parser(HTMLParser):
    def __init__(self):super().__init__();self.root=Node();self.stack=[self.root]
    def handle_starttag(self,tag,attrs):
        n=Node(tag,attrs);self.stack[-1].children.append(n)
        if tag not in ('img','input','br','hr','meta','link'):self.stack.append(n)
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag:self.stack=self.stack[:i];break
    def handle_data(self,data):self.stack[-1].children.append(data)

def inline(node):
    if isinstance(node,str):return escape(node).replace('↩','').replace('←','').replace('→','')
    t=''.join(inline(c) for c in node.children)
    if node.tag in ('b','strong'):return '<b>'+t+'</b>'
    if node.tag in ('i','em'):return '<i>'+t+'</i>'
    if node.tag=='br':return '<br/>'
    if node.tag=='a' and node.attrs.get('href','').startswith('https://'):
        return '<link href="'+escape(node.attrs['href'],quote=True)+'" color="#653d28">'+t+'</link>'
    return t

def rows(node):
    found=[]
    for c in node.children:
        if isinstance(c,Node):
            if c.tag=='tr':found.append(c)
            else:found.extend(rows(c))
    return found

def convert(node, story):
    if isinstance(node,str):return
    tag=node.tag
    if tag in ('form','script','style','button','input','caption'):return
    if tag=='img':
        src=node.attrs.get('src','')
        path=ROOT/'assets/codex'/Path(src).name
        if src=='/media/orc.png':path=ROOT/'assets/codex/orc-cartographer.png'
        if path.is_file():story.append(Image(str(path),width=360,height=540,kind='proportional'))
        return
    if tag=='table':
        data=[[Paragraph(inline(c),styles['Cell']) for c in r.children if isinstance(c,Node) and c.tag in ('th','td')] for r in rows(node)]
        if data:
            n=len(data[0]); widths=[495/n]*n
            if n==2:widths=[160,335]
            elif 3 <= n <= 8 and 'Merkmale' in data[0][2].getPlainText():
                widths=[30,60,405-55*(n-3)]+[55]*(n-3)
            table=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7d8b9')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f7f3e9')]),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#c5b497')),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
            story.extend([table,Spacer(1,10)])
        return
    if tag in ('h1','h2','h3','p','li','dt','dd'):
        text=inline(node).strip()
        if not text or any(x in node.text() for x in ('Buch schließen','Inhaltsverzeichnis','KI-Entwurf')):return
        st=styles['Heading2' if tag in ('h1','h2') else 'Heading3' if tag=='h3' else 'BodyText']
        if tag=='li':text='• '+text
        story.append(Paragraph(text,st));return
    is_art='codex-art-page' in node.attrs.get('class','')
    for c in node.children:convert(c,story)
    if is_art:story.append(PageBreak())

def page_footer(canvas,doc):
    canvas.setStrokeColor(colors.HexColor('#b39a72'));canvas.line(50,40,545,40)
    canvas.setFont('Book',8);canvas.setFillColor(colors.HexColor('#6b5746'))
    canvas.drawString(50,27,'Tormentor Codex · Version 2.1 · 16.09.2026')
    canvas.drawRightString(545,27,str(doc.page))

class BookDoc(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if hasattr(flowable, '_toc_key'):
            self.canv.bookmarkPage(flowable._toc_key)
            self.canv.addOutlineEntry(flowable._toc_name,flowable._toc_key,level=0)
            self.notify('TOCEntry',(0,flowable._toc_name,self.page,flowable._toc_key))

def build(filename,title,chapters,notice):
    story=[Spacer(1,100),Image(str(ROOT/'Tormentor_Android/app/src/main/res/mipmap-xxxhdpi/ic_tormentor.png'),width=100,height=100),Spacer(1,35),Paragraph('Tormentor’s Rassen und Klassen',styles['Title']),Spacer(1,20),Paragraph(title,styles['Heading2']),Spacer(1,30),Paragraph(notice,styles['BodyText']),Paragraph('Version 2.1 created with ChatGPT/Kodex',styles['Foot']),PageBreak(),Paragraph('Inhaltsverzeichnis',styles['Heading1'])]
    toc=TableOfContents();toc.levelStyles=[styles['BodyText']];story.append(toc)
    story.append(PageBreak())
    for index,(name,body) in enumerate(chapters):
        if index:story.append(PageBreak())
        heading=Paragraph(escape(name),styles['Heading1']);heading._toc_name=name;heading._toc_key=f'chapter-{index}';story.append(heading)
        parser=Parser();parser.feed(body);convert(parser.root,story)
    doc=BookDoc(str(OUT/filename),pagesize=A4,leftMargin=50,rightMargin=50,topMargin=48,bottomMargin=55,title=title,author='Tormentor · ChatGPT/Kodex')
    doc.multiBuild(story,onFirstPage=page_footer,onLaterPages=page_footer)

def main():
    catalogue=codex_expansions.catalogue(portal.EXTRA_SPECIES)
    chapters=[(d['name'],codex_core.class_page(k)) for k,d in codex_core.CLASSES.items()]
    chapters += [(d[0],codex_core.species_page(k)) for k,d in codex_core.SPECIES.items()]+[('Ork',portal.orc_page())]
    chapters += [(codex_expansions.german(e['name']),codex_expansions.detail(e,catalogue)) for e in catalogue if e['edition']=='2024']
    build('Tormentor-Codex-2024.pdf','Band I · 2024 / SRD 5.2.1',chapters,'Druckfassung des aktuellen Codex. Klassenübersichten und Stufentabellen, Spezies sowie getrennt gekennzeichnete Quellen-Steckbriefe. Einzelne Merkmalsbeschreibungen bleiben in den verlinkten Quellen. Kein vollständiger Ersatz der Regelbücher. A4 mit weißen Rändern; noch keine druckereispezifische PDF/X-Datei.')
    chapters=[(d[0],codex_2014.class_page(k)) for k,d in codex_2014.CLASSES.items()]
    chapters += [(d[0],codex_2014.species_page(k)) for k,d in codex_2014.SPECIES.items()]
    chapters += [(codex_expansions.german(e['name']),codex_expansions.detail(e,catalogue)) for e in catalogue if e['edition']=='2014']
    build('Tormentor-Codex-2014-Quellen.pdf','Band II · 2014 · Klassen und Völker',chapters,'Zwölf SRD-Grundklassen mit Stufentabellen, neun Völker und getrennte Quellen-Steckbriefe zu Zusatzbüchern. Deutsche Regelübersichten und Beispiele nach SRD 5.1, CC BY 4.0. Vollständige Einzelmerkmale und Zauberbeschreibungen bleiben in der verlinkten Quelle. Keine Vermischung mit 2024.')
    build('Tormentor-Codex-Homebrew.pdf','Band III · Homebrew · Spieltestfassung',[(codex_homebrew.TITLE,codex_homebrew.render())],'Eigene Hausregeln, getrennt von offiziellen D&D-Spieloptionen. Vor Verwendung mit dem DM abstimmen. Nicht durch Spieltests ausbalanciert.')
    print('Drei getrennte A4-PDFs erstellt.')

if __name__=='__main__':main()
