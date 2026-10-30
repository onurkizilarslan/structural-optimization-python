"""İsteğe bağlı görseller: pip install matplotlib; python grafikleri_ciz.py"""
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'sonuclar'
s = json.loads((OUT/'ozet.json').read_text(encoding='utf-8'))
r = s['referans']
if r is None:
    raise SystemExit('Uygun referans yok; optimum kesit çizilemez.')
with (OUT/'yakinsama.csv').open(encoding='utf-8-sig') as f:
    history = list(csv.DictReader(f))
with (OUT/'aco_kosular.csv').open(encoding='utf-8-sig') as f:
    runs = list(csv.DictReader(f))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,
                     'axes.spines.top':False,'axes.spines.right':False})
NAVY, TEAL, ORANGE = '#112943','#087f8c','#e79035'
fig = plt.figure(figsize=(13,8), facecolor='#f5f7fa')
fig.text(.06,.94,'DERS 02  /  KARINCA KOLONİSİ',color=TEAL,fontsize=12,weight='bold')
fig.text(.06,.885,'Betonarme kirişte optimum kesit arayışı',color=NAVY,fontsize=25,weight='bold')
fig.text(.06,.842,'1.000 aday • 4 tasarım değişkeni • 10 bağımsız başlangıç',color='#526479',fontsize=12)
ax = fig.add_axes([.06,.20,.30,.57],facecolor='#f5f7fa')
b,h,n,cap = [r[k] for k in ('b_mm','h_mm','adet','cap_mm')]
p = s['problem']
cover, tie = p['paspayi'],p['etriye_cap']
ax.add_patch(Rectangle((0,0),b,h,facecolor='#e1e7ed',edgecolor=NAVY,lw=2))
# Sadece etriyenin kapladığı yer gösterilir; etriye tasarımı yapılmaz.
ax.add_patch(Rectangle((cover+tie/2,cover+tie/2),b-2*cover-tie,h-2*cover-tie,
                       fill=False,edgecolor='#7b8998',lw=1.3,linestyle='--'))
xc = cover + tie + cap/2
for i in range(n):
    x = xc+i*(b-2*xc)/(n-1)
    ax.add_patch(Circle((x,xc),cap/2,color=TEAL))
ax.annotate('',(-30,0),(-30,h),arrowprops=dict(arrowstyle='<->',color=NAVY))
ax.text(-48,h/2,f'{h/10:g} cm',rotation=90,ha='center',va='center',color=NAVY)
ax.annotate('',(0,-40),(b,-40),arrowprops=dict(arrowstyle='<->',color=NAVY))
ax.text(b/2,-66,f'{b/10:g} cm',ha='center',color=NAVY)
ax.text(b/2,h+35,f'{n}Ø{cap} alt donatı',ha='center',weight='bold',color=TEAL)
ax.set(xlim=(-85,b+40),ylim=(-100,h+70),aspect='equal')
ax.axis('off')
ax2=fig.add_axes([.43,.43,.51,.33],facecolor='white')
for seed in range(s['ayarlar']['kosu']):
    rows=[v for v in history if int(v['seed'])==seed and v['en_iyi_maliyet_PB']]
    ax2.step([int(v['iterasyon']) for v in rows],
             [float(v['en_iyi_maliyet_PB']) for v in rows],where='post',alpha=.55,lw=1.4)
ax2.axhline(r['maliyet_PB'],color=NAVY,ls='--',lw=1.4,label='Tam tarama optimumu')
ax2.set(xlabel='İterasyon',ylabel='En iyi uygun maliyet (PB)')
ax2.grid(alpha=.16)
ax2.legend(frameon=False,fontsize=9)
fig.text(.43,.32,f"{s['basarili_kosu']}/{s['ayarlar']['kosu']} koşu optimuma ulaştı",fontsize=19,color=TEAL,weight='bold')
fig.text(.43,.27,f"Moment talebi     {r['Mu_kNm']:.2f} kNm\nModel kapasitesi  {r['M_model_kNm']:.2f} kNm\nÖrnek maliyet       {r['maliyet_PB']:.2f} PB",fontsize=12,color=NAVY,linespacing=1.65,va='top')
fig.text(.06,.10,'Yalnızca eğilme ve seçili kesit koşulları kontrol edilir. Kesme, sehim ve tam detaylandırma dahil değildir.',fontsize=10,color='#526479')
fig.text(.06,.062,'EĞİTİM MODELİ • TS 500/TBDY uygunluk hesabı değildir • PB: varsayımsal para birimi',fontsize=10,color='#526479')
fig.savefig(OUT/'ders_ozeti.png',dpi=170,facecolor=fig.get_facecolor())
plt.close(fig)
# Feromon çizimi: her aşamanın son seçim olasılıkları, seed=0.
from aco_kiris import olasiliklar
fig,axs=plt.subplots(2,2,figsize=(10,6),layout='constrained')
labels=['Genişlik b (mm)','Yükseklik h (mm)','Donatı adedi n','Donatı çapı (mm)']
keys=['genislikler','yukseklikler','adetler','caplar']
for ax,tau,label,key in zip(axs.flat,s['son_feromonlar'][0],labels,keys):
    values=olasiliklar(tau)
    ax.bar([str(x) for x in p[key]],values,color=TEAL)
    ax.set(title=label,ylabel='Seçim olasılığı',ylim=(0,1))
fig.suptitle('Öğrenilen seçim eğilimleri — seed 0, son güncelleme sonrası',fontsize=14)
fig.savefig(OUT/'feromon_olasiliklari.png',dpi=170)
plt.close(fig)
print('İki PNG hazır:',OUT)
