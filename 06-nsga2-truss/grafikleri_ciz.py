"""python grafikleri_ciz.py — hazır CSV/JSON sonuçlarından görseller."""
import csv,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path(__file__).resolve().parent/'sonuclar'
s=json.loads((OUT/'ozet.json').read_text(encoding='utf-8'))
def oku(name):
    with (OUT/name).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
allrows=oku('tum_kombinasyonlar.csv');exact=oku('tam_pareto.csv');approx=oku('nsga2_pareto.csv');hist=oku('yakinsama.csv')
if not exact or not approx:raise SystemExit('Uygun Pareto kümesi yok.')
reps=s['temsilciler'];seed0=[r for r in approx if int(r['seed'])==0]
NAVY,TEAL,ORANGE='#102b46','#087f8c','#df8b36'
colors=[ORANGE,TEAL,'#7057a4']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig=plt.figure(figsize=(13,8.5),facecolor='#f5f7fa')
fig.text(.055,.94,'DERS 06  /  NSGA-II İLE ÇOK AMAÇLI OPTİMİZASYON',fontsize=12,color=TEAL,weight='bold')
fig.text(.055,.885,'Daha hafif mi, daha az şekil değiştiren mi?',fontsize=24,color=NAVY,weight='bold')
fig.text(.055,.84,f"{s['kombinasyon']:,} kombinasyon • {s['uygun_kombinasyon']} uygun tasarım • {s['gercek_pareto_nokta']} farklı Pareto noktası",fontsize=12,color='#526479')
ax=fig.add_axes([.075,.25,.54,.51],facecolor='white')
valid=[r for r in allrows if r['uygun']=='True']
ax.scatter([float(r['kutle_kg']) for r in valid],[float(r['tepe_deplasman_mm']) for r in valid],s=10,color='#cdd6df',label='Uygun kombinasyonlar')
ordered=sorted(exact,key=lambda r:float(r['kutle_kg']))
ax.plot([float(r['kutle_kg']) for r in ordered],[float(r['tepe_deplasman_mm']) for r in ordered],color=NAVY,ls='--',lw=1.2,label='Tam tarama Pareto sınırı')
ax.scatter([float(r['kutle_kg']) for r in seed0],[float(r['tepe_deplasman_mm']) for r in seed0],s=27,facecolor='none',edgecolor=TEAL,lw=1,label='NSGA-II, seed 0')
ax.axhline(2,color=TEAL,ls=':',lw=1)
for label,r,color in zip('ABC',reps,colors):
    ax.scatter(r['kutle_kg'],r['tepe_deplasman_mm'],s=90,color=color,zorder=5)
    ax.annotate(label,(r['kutle_kg'],r['tepe_deplasman_mm']),xytext=(8,7),textcoords='offset points',color=color,weight='bold')
ax.set(xlabel='Toplam kütle (kg) — daha düşük istenir',ylabel='Tepe düşey hareketi (mm) — daha düşük istenir')
ax.grid(alpha=.12);ax.legend(frameon=False,fontsize=9,loc='upper right')
for y,label,r,color in zip((.72,.54,.36),'ABC',reps,colors):
    fig.text(.67,y,f"{label}  {r['tercih']}",fontsize=13,color=color,weight='bold')
    fig.text(.67,y-.05,f"{r['kutle_kg']:.2f} kg  |  {r['tepe_deplasman_mm']:.3f} mm",fontsize=18,color=NAVY,weight='bold')
    fig.text(.67,y-.09,f"Alanlar: {r['A1_mm2']:g} / {r['A2_mm2']:g} / {r['A3_mm2']:g} mm²",fontsize=10,color='#526479')
covered=sum(r['kapsama_yuzde']==100 for r in s['kosular'])
fig.text(.055,.158,f"{covered}/{s['ayarlar']['kosu']} koşu, tam taramadaki Pareto noktalarının tamamını buldu.",fontsize=13,color=TEAL,weight='bold')
fig.text(.055,.095,'2 mm çizgisi yalnız sonradan uygulanan bir tercih örneğidir; aramada yer değiştirme üst sınırı yoktur.',fontsize=10,color='#526479')
fig.text(.055,.057,'EĞİTİM MODELİ • Gerilme kontrolü var; burkulma, öz ağırlık ve bağlantı tasarımı dahil değildir.',fontsize=10,color='#526479')
fig.savefig(OUT/'pareto_ozeti.png',dpi=170,facecolor=fig.get_facecolor());plt.close(fig)
# Temsilci tasarımlar ve alan/kütle ilişkisi.
fig,axs=plt.subplots(1,len(reps),figsize=(13,4.7),squeeze=False)
xy=np.array([[0,0],[4,0],[2,3.]])
for ax,label,r,color in zip(axs.flat,'ABC',reps,colors):
    areas=[r[f'A{i}_mm2'] for i in (1,2,3)]
    for j,(a,b) in enumerate([(0,1),(0,2),(1,2)]):
        ax.plot(xy[[a,b],0],xy[[a,b],1],color=color,lw=1.5+areas[j]/500)
        mid=(xy[a]+xy[b])/2
        ax.text(mid[0],mid[1]+(.15 if j else -.28),f'E{j+1}: {areas[j]:g}',ha='center',fontsize=10,color=NAVY)
    ax.scatter(xy[:,0],xy[:,1],color=NAVY,s=25,zorder=4)
    ax.scatter([0,4],[-.1,-.1],marker='^',s=70,facecolor='white',edgecolor=NAVY,zorder=5)
    ax.plot([3.9,4.1],[-.24,-.24],'o',markersize=2,color=NAVY)
    ax.annotate('',xy=(2,3.05),xytext=(2,3.7),arrowprops=dict(arrowstyle='-|>',color=NAVY))
    ax.text(2.2,3.5,f"{s['problem']['yuk_N']/1000:g} kN",fontsize=9,color=NAVY)
    ax.set(xlim=(-.4,4.4),ylim=(-.5,4),aspect='equal');ax.axis('off')
    ax.set_title(f"{label}  {r['kutle_kg']:.2f} kg / {r['tepe_deplasman_mm']:.3f} mm",color=color,fontsize=12)
fig.suptitle('Aynı 4 m açıklık ve 3 m yükseklik — farklı kesit alanları (mm²)',fontsize=14)
fig.subplots_adjust(left=.03,right=.98,bottom=.10,top=.80,wspace=.15)
fig.text(.1,.035,'Çizgi kalınlıkları alanla ölçeklidir; gerçek profil biçimi veya burkulma yeterliliği göstermez.',fontsize=10,color='#526479')
fig.savefig(OUT/'temsilci_kafesler.png',dpi=170);plt.close(fig)
# Yakınsama ölçüsü: aynı referans noktasıyla normalize hypervolume oranı.
fig,ax=plt.subplots(figsize=(9,5),layout='constrained')
for seed in range(s['ayarlar']['kosu']):
    h=[r for r in hist if int(r['seed'])==seed and r['hypervolume_orani']]
    ax.plot([int(r['nesil']) for r in h],[float(r['hypervolume_orani']) for r in h],alpha=.6)
ax.axhline(1,color=NAVY,ls='--',label='Tam Pareto kümesinin değeri')
ax.set(xlabel='Nesil',ylabel='Hypervolume / tam Pareto hypervolume',title='Çözüm kümesinin yakınsaması — 10 bağımsız koşu')
ax.grid(alpha=.15);ax.legend(frameon=False)
fig.savefig(OUT/'yakinsama.png',dpi=170);plt.close(fig)
print('Üç görsel hazır.')
