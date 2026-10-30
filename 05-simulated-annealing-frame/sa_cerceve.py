"""Ders 05 — Benzetimli tavlama ile 2B çerçevede öğretim profili seçimi.
Python 3.9+, NumPy. Gerçek çelik yapı standardı kontrolü değildir.
"""
import argparse,csv,itertools,json,math
from dataclasses import dataclass,asdict
from pathlib import Path
import numpy as np

@dataclass(frozen=True)
class Problem:
    E: float=200000.0  # MPa
    rho: float=7.85e-6  # kg/mm³
    dusey_N: float=100000.0
    yatay_N: float=20000.0
    sigma_sinir: float=160.0  # ders sınırı, MPa
    otelenme_sinir: float=10.0  # çatı düğümlerinde |ux|, mm
    sehim_sinir: float=20.0  # kiriş orta düğümünün uçlara göre hareketi, mm


def katalog():
    # Gerçek IPE/HEA tablosu DEĞİL: ideal keskin köşeli simetrik kaynaklı I geometrileri.
    dims=[(180,100,6,8),(220,110,6,9),(260,130,7,10),(300,150,8,12),
          (340,170,8,14),(380,190,9,16),(420,210,10,18),(460,230,10,20)]
    rows=[]
    for i,(h,b,tw,tf) in enumerate(dims):
        A=2*b*tf+(h-2*tf)*tw
        I=(b*h**3-(b-tw)*(h-2*tf)**3)/12
        rows.append(dict(profil=f'K{i+1}',h_mm=h,b_mm=b,tw_mm=tw,tf_mm=tf,
                         A_mm2=float(A),I_mm4=float(I),W_mm3=float(I/(h/2))))
    return rows


def eleman_matrisleri(x1,x2,E,A,I):
    delta=np.asarray(x2)-np.asarray(x1);L=float(np.linalg.norm(delta));c,s=delta/L
    k=np.zeros((6,6));a=E*A/L
    k[np.ix_([0,3],[0,3])]=[[a,-a],[-a,a]]
    f=E*I/L**3
    k[np.ix_([1,2,4,5],[1,2,4,5])]=f*np.array([
        [12,6*L,-12,6*L],[6*L,4*L*L,-6*L,2*L*L],
        [-12,-6*L,12,-6*L],[6*L,2*L*L,-6*L,4*L*L]])
    R=np.array([[c,s,0],[-s,c,0],[0,0,1.]])
    T=np.zeros((6,6));T[:3,:3]=R;T[3:,3:]=R
    return k,T,L


def analiz(nodes,elements,sections,E,loads,fixed):
    """Düğümde (ux,uy,theta); Euler–Bernoulli, lineer ve birinci mertebe."""
    ndof=3*len(nodes);K=np.zeros((ndof,ndof));parts=[]
    for (i,j),sec in zip(elements,sections):
        k,T,L=eleman_matrisleri(nodes[i],nodes[j],E,sec['A_mm2'],sec['I_mm4'])
        dofs=np.r_[np.arange(3*i,3*i+3),np.arange(3*j,3*j+3)]
        K[np.ix_(dofs,dofs)]+=T.T@k@T
        parts.append((k,T,L,dofs))
    free=np.setdiff1d(np.arange(ndof),fixed)
    u=np.zeros(ndof);u[free]=np.linalg.solve(K[np.ix_(free,free)],loads[free])
    forces=[k@T@u[dofs] for k,T,L,dofs in parts]
    return dict(u=u,R=K@u-loads,K=K,forces=forces,parts=parts,free=free)


class Cerceve:
    def __init__(self,p):
        self.p=p;self.cat=katalog()
        self.nodes=np.array([[0,0],[6000,0],[0,3000],[3000,3000],[6000,3000]],float)
        self.elements=[(0,2),(1,4),(2,3),(3,4)]
        self.groups=[0,1,2,2]  # kiriş iki sonlu eleman, tek profil değişkeni
        self.loads=np.zeros(15)
        self.loads[3*2]=p.yatay_N/2;self.loads[3*4]=p.yatay_N/2
        self.loads[3*3+1]=-p.dusey_N
        self.fixed=np.arange(6)  # iki tabanda ux,uy,theta sabit
        self.max_mass=self.cat[-1]['A_mm2']*12000*p.rho
        self.cache={};self.solves=0

    def hesapla(self,x):
        key=tuple(int(i) for i in x)
        if len(key)!=3 or any(i<0 or i>=len(self.cat) for i in key):raise ValueError('Üç katalog indeksi (0–7) gerekir.')
        if key in self.cache:return self.cache[key]
        secs=[self.cat[key[g]] for g in self.groups]
        a=analiz(self.nodes,self.elements,secs,self.p.E,self.loads,self.fixed)
        rows=[];mass=0.
        for n,(sec,f,part) in enumerate(zip(secs,a['forces'],a['parts'])):
            L=part[2];N=max(abs(f[0]),abs(f[3]));M=max(abs(f[2]),abs(f[5]))
            sigma=N/sec['A_mm2']+M/sec['W_mm3']
            mass+=L*sec['A_mm2']*self.p.rho
            rows.append(dict(eleman=n+1,profil=sec['profil'],L_mm=L,
                             N_mutlak_kN=float(N/1000),M_mutlak_kNm=float(M/1e6),
                             sigma_MPa=float(sigma),oran=float(sigma/self.p.sigma_sinir)))
        U=a['u'].reshape(-1,3)
        drift=float(np.max(np.abs(U[[2,3,4],0])))
        deflection=float(abs(U[3,1]-(U[2,1]+U[4,1])/2))
        ratios=[r['oran'] for r in rows]+[drift/self.p.otelenme_sinir,deflection/self.p.sehim_sinir]
        violation=sum(max(0,r-1) for r in ratios)
        feasible=violation<=1e-10
        # Uygun tasarım enerji <=1; uygunsuz enerji >2. En iyi UYGUN ayrı tutulur.
        energy=mass/self.max_mass+(0 if feasible else 2+violation)
        r=dict(indeks=list(key),sol_kolon=self.cat[key[0]]['profil'],
               sag_kolon=self.cat[key[1]]['profil'],kiris=self.cat[key[2]]['profil'],
               kutle_kg=float(mass),max_sigma_MPa=max(v['sigma_MPa'] for v in rows),
               otelenme_mm=drift,goreli_orta_sehim_mm=deflection,ihlal=float(violation),
               uygun=feasible,enerji=float(energy),elemanlar=rows,
               u=a['u'].tolist(),reaksiyon=a['R'].tolist())
        self.solves+=1;self.cache[key]=r
        return r


def komsu(x,rng,n=8):
    y=list(x);j=int(rng.integers(0,len(x)))
    # Değiştirilen profil, kalan n-1 profil arasından eşit olasılıkla seçilir.
    k=int(rng.integers(0,n-1));y[j]=k+(k>=y[j])
    return tuple(y)


def kabul_olasiligi(delta,T):
    if T<=0:raise ValueError('Sıcaklık pozitif olmalı.')
    return 1.0 if delta<=0 else math.exp(-delta/T)


def tavlama(model,seed=0,adim=3000,T0=.5,Tson=.002):
    if adim<1 or not 0<Tson<=T0:raise ValueError('adim>=1 ve 0<Tson<=T0 gerekir.')
    rng=np.random.default_rng(seed)
    current=model.hesapla((7,7,7));best=current if current['uygun'] else None
    initial_solves=model.solves
    uphill=0;trace=[]
    for step in range(1,adim+1):
        T=T0*(Tson/T0)**((step-1)/max(adim-1,1))
        proposal=model.hesapla(komsu(current['indeks'],rng))
        delta=proposal['enerji']-current['enerji']
        prob=kabul_olasiligi(delta,T)
        accepted=delta<=0 or rng.random()<prob
        if accepted:
            current=proposal
            if delta>0:uphill+=1
        # En iyi bulunan uygun tasarım, kabul edilmese de arşivlenir.
        if proposal['uygun'] and (best is None or proposal['kutle_kg']<best['kutle_kg']):best=proposal
        trace.append(dict(seed=seed,adim=step,sicaklik=T,kabul=accepted,
                          daha_kotu_kabul=accepted and delta>0,kabul_olasiligi=prob,
                          aday_enerji=proposal['enerji'],mevcut_enerji=current['enerji'],
                          mevcut_kutle_kg=current['kutle_kg'],mevcut_uygun=current['uygun'],
                          en_iyi_uygun_kutle_kg=best['kutle_kg'] if best else None,
                          degerlendirme=step+1))
    return best,trace,dict(kotu_kabul=uphill,analiz_cozumu=model.solves-initial_solves+1,
                           benzersiz_aday=len(model.cache),degerlendirme=adim+1)


def ozet_satir(r):
    return {k:v for k,v in r.items() if k not in ('indeks','elemanlar','u','reaksiyon')}


def csv_yaz(path,rows):
    if not rows:path.unlink(missing_ok=True);return
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--adim',type=int,default=3000);ap.add_argument('--kosu',type=int,default=10)
    ap.add_argument('--yatay-kn',type=float,default=20);ap.add_argument('--dusey-kn',type=float,default=100)
    args=ap.parse_args()
    if min(args.adim,args.kosu)<1 or not all(np.isfinite(v) and v>=0 for v in (args.yatay_kn,args.dusey_kn)):
        ap.error('Adım/koşu pozitif; yükler sonlu ve negatif olmayan değerler olmalı.')
    p=Problem(dusey_N=args.dusey_kn*1000,yatay_N=args.yatay_kn*1000)
    runs,history,bests=[],[],[]
    for seed in range(args.kosu):
        model=Cerceve(p)  # bağımsız, boş önbellek; önceden tarama bilgisi yok
        best,trace,stats=tavlama(model,seed,args.adim)
        runs.append(dict(seed=seed,uygun_bulundu=best is not None,
                         sol_kolon=best['sol_kolon'] if best else '',
                         sag_kolon=best['sag_kolon'] if best else '',kiris=best['kiris'] if best else '',
                         kutle_kg=best['kutle_kg'] if best else None,**stats))
        history.extend(trace)
        if best:bests.append(best)
    # Referans SA koşularından SONRA, farklı model/önbellekle hesaplanır.
    exact_model=Cerceve(p)
    all_rows=[exact_model.hesapla(x) for x in itertools.product(range(8),repeat=3)]
    valid=[r for r in all_rows if r['uygun']]
    ref=min(valid,key=lambda r:r['kutle_kg']) if valid else None
    for r in runs:
        r['optimumdan_fark_yuzde']=(100*(r['kutle_kg']/ref['kutle_kg']-1) if ref and r['uygun_bulundu'] else None)
    best=min(bests,key=lambda r:r['kutle_kg']) if bests else None
    summary=dict(problem=asdict(p),ayarlar=vars(args),referans=ref,en_iyi=best,
                 katalog=katalog(),kombinasyon=len(all_rows),uygun_kombinasyon=len(valid),
                 basari=sum(r['uygun_bulundu'] and r['optimumdan_fark_yuzde'] is not None and
                            abs(r['optimumdan_fark_yuzde'])<1e-8 for r in runs),
                 baslangic=exact_model.hesapla((7,7,7)))
    out=Path(__file__).resolve().parent/'sonuclar';out.mkdir(exist_ok=True)
    csv_yaz(out/'kosular.csv',runs);csv_yaz(out/'tavlama_izi.csv',history)
    csv_yaz(out/'tum_kombinasyonlar.csv',[ozet_satir(r) for r in all_rows])
    csv_yaz(out/'profil_katalogu.csv',katalog())
    csv_yaz(out/'eleman_kontrolleri.csv',best['elemanlar'] if best else [])
    (out/'ozet.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print('EĞİTİM MODELİ — Stabilite ve tam çelik tasarımı kapsam dışı.')
    print('Uygun kombinasyon:',len(valid),'/512')
    print('Referans:',ozet_satir(ref) if ref else None)
    print('SA en iyi:',ozet_satir(best) if best else None)
    print('Optimuma ulaşan koşu:',summary['basari'],'/',args.kosu)
    print('Kötü kabul sayıları:',[r['kotu_kabul'] for r in runs])

if __name__=='__main__':main()
