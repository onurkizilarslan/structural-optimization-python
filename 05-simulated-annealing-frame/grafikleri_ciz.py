"""python grafikleri_ciz.py"""
import csv,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path(__file__).resolve().parent/'sonuclar'
s=json.loads((OUT/'ozet.json').read_text(encoding='utf-8'))
r=s['en_iyi'];ref=s['referans']
if r is None:raise SystemExit('Uygun çözüm yok; sonuç görseli üretilemiyor.')
with (OUT/'tavlama_izi.csv').open(encoding='utf-8-sig') as f:history=list(csv.DictReader(f))
NAVY,TEAL,ORANGE='#102b46','#087f8c','#df8b36'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig=plt.figure(figsize=(13,8.5),facecolor='#f5f7fa')
fig.text(.055,.94,'DERS 05  /  BENZETİMLİ TAVLAMA',color=TEAL,fontsize=12,weight='bold')
fig.text(.055,.884,'Çelik çerçevede profil kombinasyonu seçimi',color=NAVY,fontsize=24,weight='bold')
fig.text(.055,.84,'8 ideal I kesiti • 3 tasarım değişkeni • 512 kombinasyon • Tam taramayla doğrulama',color='#526479',fontsize=12)
ax=fig.add_axes([.055,.405,.43,.36],facecolor='#f5f7fa')
xy=np.array([[0,0],[6,0],[0,3],[3,3],[6,3]],float)
for i,(a,b) in enumerate([(0,2),(1,4),(2,3),(3,4)]):
    idx=r['indeks'][[0,1,2,2][i]]
    ax.plot(xy[[a,b],0],xy[[a,b],1],lw=3+idx*.5,color=TEAL)
ax.scatter(xy[:,0],xy[:,1],s=30,color=NAVY,zorder=3)
for x in (0,6):
    ax.plot([x-.35,x+.35],[0,0],color=NAVY,lw=2)
    for q in np.linspace(x-.3,x+.3,6):ax.plot([q-.1,q],[ -.17,0],color=NAVY,lw=.7)
ax.annotate('',xy=(3,3.08),xytext=(3,3.95),arrowprops=dict(arrowstyle='-|>',color=ORANGE,lw=2))
ax.text(3.17,3.7,f"{s['problem']['dusey_N']/1000:g} kN",color=ORANGE,weight='bold')
for x in (0,6):
    ax.annotate('',xy=(x+.65,3.35),xytext=(x,3.35),arrowprops=dict(arrowstyle='-|>',color=ORANGE,lw=1.5))
    ax.text(x+.3,3.55,f"{s['problem']['yatay_N']/2000:g} kN",ha='center',fontsize=10,color=ORANGE)
ax.text(.2,1.5,r['sol_kolon'],ha='left',color=NAVY,weight='bold')
ax.text(6.18,1.5,r['sag_kolon'],color=NAVY,weight='bold')
ax.text(3,2.62,r['kiris'],ha='center',color=NAVY,weight='bold')
ax.annotate('',xy=(0,-.5),xytext=(6,-.5),arrowprops=dict(arrowstyle='<->',color=NAVY))
ax.text(3,-.8,'6,0 m',ha='center',color=NAVY)
ax.text(-.65,1.5,'3,0 m',rotation=90,va='center',color='#526479')
ax.set(xlim=(-1,7),ylim=(-1,4.2),aspect='equal');ax.axis('off')
ax2=fig.add_axes([.56,.445,.39,.30],facecolor='white')
for seed in range(s['ayarlar']['kosu']):
    h=[v for v in history if int(v['seed'])==seed and v['en_iyi_uygun_kutle_kg']]
    ax2.plot([int(v['adim']) for v in h],[float(v['en_iyi_uygun_kutle_kg']) for v in h],lw=1,alpha=.55)
ax2.axhline(ref['kutle_kg'],ls='--',color=NAVY,label='Tam tarama minimumu')
ax2.set(xlabel='Önerilen değişiklik sayısı',ylabel='En iyi uygun kütle (kg)');ax2.grid(alpha=.15);ax2.legend(frameon=False,fontsize=9)
fig.text(.055,.33,f"{s['baslangic']['kutle_kg']:.2f} → {r['kutle_kg']:.2f} kg",fontsize=23,color=TEAL,weight='bold')
fig.text(.055,.285,'Tüm elemanlar K8 iken başlayan tasarıma göre',fontsize=11,color=NAVY)
fig.text(.56,.33,f"{s['basari']}/{s['ayarlar']['kosu']} koşu optimumda",fontsize=21,color=TEAL,weight='bold')
fig.text(.56,.285,'Yalnız tanımlı katalog ve hesap modeli için',fontsize=11,color=NAVY)
fig.text(.055,.215,f"En büyük normal gerilme: {r['max_sigma_MPa']:.2f} / 160 MPa",fontsize=12,color=NAVY)
fig.text(.055,.17,f"Çatı yatay hareketi: {r['otelenme_mm']:.3f} / 10 mm     |     Göreli orta sehim: {r['goreli_orta_sehim_mm']:.3f} / 20 mm",fontsize=12,color=NAVY)
fig.text(.055,.095,'EĞİTİM MODELİ • K1–K8 gerçek IPE/HEA adları değildir; geometrileri tanımlı ideal I kesitleridir.',fontsize=10,color='#526479')
fig.text(.055,.057,'Burkulma, yanal burulmalı burkulma, ikinci mertebe ve bağlantı kontrolleri dahil değildir.',fontsize=10,color='#526479')
fig.savefig(OUT/'ders_ozeti.png',dpi=170,facecolor=fig.get_facecolor());plt.close(fig)
# İlk bağımsız koşu: yüksek enerjiye geçiş, sıcaklık ve en iyi tasarım.
h=[v for v in history if int(v['seed'])==0];x=np.array([int(v['adim']) for v in h])
energy=np.array([float(v['mevcut_enerji']) for v in h]);up=np.array([v['daha_kotu_kabul']=='True' for v in h])
fig,axs=plt.subplots(3,1,figsize=(11,8),sharex=True,layout='constrained')
axs[0].semilogy(x,[float(v['sicaklik']) for v in h],color=TEAL);axs[0].set_ylabel('Sıcaklık (boyutsuz)')
axs[1].plot(x,energy,color='#8294a6',lw=.7)
axs[1].scatter(x[up],energy[up],s=7,color=ORANGE,label='Daha yüksek enerjili aday kabul edildi')
axs[1].set_ylabel('Mevcut enerji');axs[1].legend(frameon=False,fontsize=9)
axs[2].plot(x,[float(v['en_iyi_uygun_kutle_kg']) if v['en_iyi_uygun_kutle_kg'] else np.nan for v in h],color=TEAL)
axs[2].axhline(ref['kutle_kg'],color=NAVY,ls='--');axs[2].set(ylabel='En iyi uygun kütle (kg)',xlabel='Önerilen değişiklik sayısı')
for ax in axs:ax.grid(alpha=.15)
fig.suptitle('Tavlamanın mantığı — seed 0: mevcut tasarım kötüleşebilir, en iyi kayıt korunur',fontsize=13)
fig.savefig(OUT/'tavlama_mantigi.png',dpi=170);plt.close(fig)
print('İki görsel hazır.')
