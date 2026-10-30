"""python grafikleri_ciz.py — önceden üretilen sonuçları çizer."""
import csv,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle

OUT=Path(__file__).resolve().parent/'sonuclar'
s=json.loads((OUT/'ozet.json').read_text(encoding='utf-8'))
b=s['en_iyi'];d=s['donusturulen'];k=s['katalog_en_iyi'];ref=s['izgara_referansi']
if b is None or k is None:raise SystemExit('Görsel için uygun sürekli ve katalog sonucu gerekiyor.')
with (OUT/'yakinsama.csv').open(encoding='utf-8-sig') as f:history=list(csv.DictReader(f))
NAVY,TEAL,ORANGE='#102b46','#087f8c','#dd8d38'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,
                     'axes.spines.top':False,'axes.spines.right':False})
fig=plt.figure(figsize=(13,8.5),facecolor='#f5f7fa')
fig.text(.055,.94,'DERS 04  /  DİFERANSİYEL EVRİM',fontsize=12,weight='bold',color=TEAL)
fig.text(.055,.885,'Sürekli çözümden donatı seçimine',fontsize=26,weight='bold',color=NAVY)
fig.text(.055,.84,'DE/rand/1/bin • 3 değişken • Yuvarlama sonrası yeniden hesap ve katalog taraması',fontsize=12,color='#526479')
items=[('SÜREKLİ DE',b,'#087f8c'),('YUKARI YUVARLAMA',d,ORANGE),('KATALOG TARAMASI',k,TEAL)]
for left,(name,r,color) in zip((.055,.365,.675),items):
    fig.text(left,.755,name,fontsize=11,color=color,weight='bold')
    if r:
        fig.text(left,.707,f"{r['maliyet_PB']:.2f} PB",fontsize=23,color=NAVY,weight='bold')
        dim=f"{r['b_mm']/10:.2f} × {r['h_mm']/10:.2f} cm"
        steel=f"{r['adet']}Ø{r['cap_mm']}" if 'adet' in r else f"As = {r['As_mm2']:.2f} mm²"
        fig.text(left,.66,dim+'\n'+steel,fontsize=12,color=NAVY,va='top',linespacing=1.6)
ax=fig.add_axes([.075,.195,.25,.34],facecolor='#f5f7fa')
bw,hh=k['b_mm'],k['h_mm'];p=s['problem'];cc=p['paspayi'];tie=p['etriye'];dia=k['cap_mm'];n=k['adet']
ax.add_patch(Rectangle((0,0),bw,hh,facecolor='#e2e8ee',edgecolor=NAVY,lw=2))
ax.add_patch(Rectangle((cc+tie/2,cc+tie/2),bw-2*cc-tie,hh-2*cc-tie,fill=False,ls='--',edgecolor='#8b98a5',lw=1.2))
xc=cc+tie+dia/2
for i in range(n):ax.add_patch(Circle((xc+i*(bw-2*xc)/(n-1),xc),dia/2,color=TEAL))
ax.text(bw/2,hh+25,'Katalogdaki en iyi aday',ha='center',fontsize=11,color=NAVY)
ax.annotate('',xy=(0,-30),xytext=(bw,-30),arrowprops=dict(arrowstyle='<->',color=NAVY))
ax.text(bw/2,-62,f'{bw/10:g} cm',ha='center',color=NAVY)
ax.annotate('',xy=(-30,0),xytext=(-30,hh),arrowprops=dict(arrowstyle='<->',color=NAVY))
ax.text(-55,hh/2,f'{hh/10:g} cm',rotation=90,va='center',color=NAVY)
ax.set(xlim=(-85,bw+50),ylim=(-85,hh+65),aspect='equal');ax.axis('off')
ax2=fig.add_axes([.43,.25,.51,.29],facecolor='white')
for seed in range(s['ayarlar']['kosu']):
    rows=[r for r in history if int(r['seed'])==seed and r['en_iyi_uygun_maliyet_PB']]
    ax2.plot([int(r['nesil']) for r in rows],[float(r['en_iyi_uygun_maliyet_PB']) for r in rows],alpha=.5,lw=1)
if ref:ax2.axhline(ref['maliyet_PB'],ls='--',color=NAVY,label='0,5 mm ızgara referansı')
ax2.set(xlabel='Nesil',ylabel='En iyi uygun maliyet (PB)');ax2.grid(alpha=.16);ax2.legend(frameon=False,fontsize=9)
fig.text(.43,.165,f"{s['referansa_yuzde01_yakin']}/{s['ayarlar']['kosu']} DE koşusu ızgara referansına %0,1 içinde yaklaştı.",color=TEAL,weight='bold',fontsize=11)
fig.text(.055,.095,'EĞİTİM MODELİ • Yalnız eğilme ve seçili kesit koşulları • Kesme, sehim ve tam detaylandırma dahil değildir.',color='#526479',fontsize=10)
fig.text(.055,.057,'PB: varsayımsal para birimi. Izgara bir sayısal referanstır; sürekli global optimum ispatı değildir.',color='#526479',fontsize=10)
fig.savefig(OUT/'ders_ozeti.png',dpi=170,facecolor=fig.get_facecolor());plt.close(fig)
# Katalog alternatifi kontrol grafiği: boyutsuz talep/kapasite oranları.
fig,ax=plt.subplots(figsize=(9,5),layout='constrained')
ratios=[k['Mu_kNm']/k['M_model_kNm'],k['As_min_mm2']/k['As_mm2'],k['epsilon_min']/k['epsilon_t'],k['gerekli_aralik_mm']/k['net_aralik_mm']]
labels=['Eğilme','Minimum donatı','Süneklik','Net aralık']
bars=ax.bar(labels,ratios,color=TEAL,width=.55)
ax.axhline(1,color=ORANGE,ls='--',label='Üst sınır: 1,00')
for bar,r in zip(bars,ratios):ax.text(bar.get_x()+bar.get_width()/2,r+.035,f'{r:.3f}',ha='center',color=NAVY)
ax.set(ylim=(0,1.2),ylabel='Talep / sağlanan değer',title=f"Katalog adayı: {k['b_mm']/10:g} × {k['h_mm']/10:g} cm, {n}Ø{dia}")
ax.legend(frameon=False);ax.grid(axis='y',alpha=.12)
fig.savefig(OUT/'kisit_kontrolleri.png',dpi=170);plt.close(fig)
print('İki görsel hazır.')
