"""python grafikleri_ciz.py — Matplotlib gerektirir."""
import csv,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pso_kafes import Problem,Kafes,lineer_analiz

OUT=Path(__file__).resolve().parent/'sonuclar'
s=json.loads((OUT/'ozet.json').read_text(encoding='utf-8'))
best=s['en_iyi'];ref=s['referans']
if best is None:raise SystemExit('Uygun PSO sonucu yok; grafik üretilemedi.')
p=Problem(**s['problem']);m=Kafes(p)
A=np.array([best[f'A{i}_mm2'] for i in (1,2,3)])
with (OUT/'yakinsama.csv').open(encoding='utf-8-sig') as f:hist=list(csv.DictReader(f))
NAVY,TEAL,ORANGE='#102b46','#087f8c','#df8b36'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,
                     'axes.spines.top':False,'axes.spines.right':False})
fig=plt.figure(figsize=(13,8.5),facecolor='#f5f7fa')
fig.text(.055,.94,'DERS 03  /  PARÇACIK SÜRÜSÜ OPTİMİZASYONU',fontsize=12,color=TEAL,weight='bold')
fig.text(.055,.884,'Çelik kafeste daha az malzemeyle tasarım',fontsize=24,color=NAVY,weight='bold')
fig.text(.055,.835,'3 çubuk • Sürekli kesit alanları • Gerilme ve tepe deplasmanı kısıtları',fontsize=12,color='#526479')
ax=fig.add_axes([.055,.40,.40,.37],facecolor='#f5f7fa')
xy=m.nodes/1000
for i,(a,b) in enumerate(m.elements):
    ax.plot(xy[[a,b],0],xy[[a,b],1],color=TEAL,lw=2+3*A[i]/max(A))
    mid=(xy[a]+xy[b])/2
    offset=[(0,-.30),(-.32,.1),(.32,.1)][i]
    ax.text(mid[0]+offset[0],mid[1]+offset[1],f'E{i+1}',ha='center',va='center',weight='bold',color=NAVY)
ax.scatter(xy[:,0],xy[:,1],s=45,color=NAVY,zorder=4)
ax.scatter([0,4],[-.12,-.12],s=110,marker='^',facecolor='white',edgecolor=NAVY,zorder=5)
ax.plot([3.9,4.1],[-.28,-.28],'o',color=NAVY,markersize=3)
ax.annotate('',xy=(2,3.06),xytext=(2,3.8),arrowprops=dict(arrowstyle='-|>',color=ORANGE,lw=2))
ax.text(2.18,3.65,f'{p.yuk_N/1000:g} kN',color=ORANGE,weight='bold')
for i,(x,y) in enumerate(xy):ax.text(x+.13,y+.06,f'D{i+1}',color=NAVY,fontsize=10)
ax.annotate('',xy=(0,-.65),xytext=(4,-.65),arrowprops=dict(arrowstyle='<->',color='#526479'))
ax.text(2,-.92,'4,0 m',ha='center',color='#526479')
ax.annotate('',xy=(4.65,0),xytext=(4.65,3),arrowprops=dict(arrowstyle='<->',color='#526479'))
ax.text(4.85,1.5,'3,0 m',rotation=90,va='center',color='#526479')
ax.set(xlim=(-.5,5.25),ylim=(-1,4.1),aspect='equal');ax.axis('off')
ax2=fig.add_axes([.55,.45,.40,.30],facecolor='white')
for seed in range(s['ayarlar']['kosu']):
    h=[r for r in hist if int(r['seed'])==seed and r['en_iyi_uygun_kutle_kg']]
    ax2.plot([int(r['iterasyon']) for r in h],[float(r['en_iyi_uygun_kutle_kg']) for r in h],alpha=.5,lw=1.1)
if ref:ax2.axhline(ref['mass'],ls='--',color=NAVY,lw=1.4,label='Analitik referans')
ax2.set(xlabel='İterasyon',ylabel='En iyi uygun kütle (kg)');ax2.grid(alpha=.15);ax2.legend(frameon=False,fontsize=9)
reduction=100*(1-best['kutle_kg']/s['baslangic_kutle_kg'])
fig.text(.055,.33,f"{s['baslangic_kutle_kg']:.2f} → {best['kutle_kg']:.2f} kg",fontsize=22,color=TEAL,weight='bold')
fig.text(.055,.287,f'1.500 mm² eşit kesitli tasarıma göre %{reduction:.1f} azalma',fontsize=11,color=NAVY)
fig.text(.55,.33,f"{s['yuzde_01_yakin_kosu']}/{s['ayarlar']['kosu']} koşu",fontsize=22,color=TEAL,weight='bold')
fig.text(.55,.287,'referans kütleye %0,1 içinde yaklaştı',fontsize=11,color=NAVY)
fig.text(.055,.215,f"PSO alanları:  E1 {A[0]:.2f}   |   E2 {A[1]:.2f}   |   E3 {A[2]:.2f} mm²",color=NAVY,fontsize=12)
fig.text(.055,.172,f"Tepe düşey hareketi: {abs(best['uy_mm']):.6f} mm   /   sınır {p.deplasman_sinir_mm:g} mm",color=NAVY,fontsize=12)
fig.text(.055,.095,'EĞİTİM MODELİ • Basınç çubuklarında burkulma, öz ağırlık ve bağlantı kontrolleri dahil değildir.',fontsize=10,color='#526479')
fig.text(.055,.057,'Kesit alanları ideal sürekli değişkenlerdir; sonuçlar uygulama projesi veya hazır profil seçimi değildir.',fontsize=10,color='#526479')
fig.savefig(OUT/'ders_ozeti.png',dpi=170,facecolor=fig.get_facecolor());plt.close(fig)
# İkinci görsel: tepki ve deformasyon; büyütme açıkça belirtilir.
sol=lineer_analiz(m.nodes,m.elements,p.E_MPa,A,m.loads,m.fixed)
scale=100
original=m.nodes/1000
moved=(m.nodes+scale*sol['u'].reshape(-1,2))/1000
fig,ax=plt.subplots(figsize=(9,6))
fig.subplots_adjust(left=.11,right=.97,bottom=.18,top=.90)
for i,(a,b) in enumerate(m.elements):
    ax.plot(original[[a,b],0],original[[a,b],1],color='#a4afbb',ls='--',lw=2,label='Başlangıç' if i==0 else None)
    ax.plot(moved[[a,b],0],moved[[a,b],1],color=ORANGE,lw=2,label='Deforme şekil (100×)' if i==0 else None)
    mid=(original[a]+original[b])/2
    ax.text(mid[0],mid[1]+.12,f"E{i+1}: {sol['force'][i]/1000:.2f} kN",ha='center',color=NAVY)
ax.scatter(original[:,0],original[:,1],color=NAVY,s=35)
ax.set(title='En iyi PSO tasarımı — eksenel kuvvetler ve şekil değiştirme',xlabel='x (m)',ylabel='y (m)',aspect='equal',ylim=(-.5,3.7))
ax.grid(alpha=.15);ax.legend(loc='upper right',frameon=False)
fig.text(.12,.025,'Pozitif: çekme • Negatif: basınç • Yer değiştirmeler 100 kat büyütülmüştür.',fontsize=10,color='#526479')
fig.savefig(OUT/'deforme_sekil.png',dpi=170);plt.close(fig)
print('Görseller hazır.')
