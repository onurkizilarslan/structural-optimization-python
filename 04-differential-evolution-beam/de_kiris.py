"""Ders 04 — DE/rand/1/bin ile betonarme kiriş optimizasyonu.
Eğitim modeli; TS 500/TBDY uygulama hesabı değildir. Python 3.9+, NumPy.
"""
import argparse
import csv
from dataclasses import dataclass, asdict
import itertools
import json
import math
from pathlib import Path
import numpy as np

ALT=np.array([250.,350.,200.])  # b, h (mm), As (mm²)
UST=np.array([450.,700.,4000.])
TOL=1e-10


@dataclass(frozen=True)
class Problem:
    fc: float=30.0
    fy: float=420.0
    Es: float=200000.0
    L: float=6.0
    dis_yuk: float=30.0  # kN/m, katsayılı; öz ağırlık hariç
    ozagirlik: float=25.0  # kN/m³
    ozagirlik_katsayi: float=1.2  # bu problem için varsayım
    merkez_ortusu: float=60.0  # sürekli model: alt yüzden donatı merkezine mm
    paspayi: float=35.0  # katalog modeli: etriyenin dış yüzüne mm
    etriye: float=8.0
    agrega: float=20.0
    beton_fiyat: float=3000.0  # varsayımsal PB/m³
    celik_fiyat: float=35.0  # varsayımsal PB/kg


def hesapla(x,p,ortusu=None):
    """Tek veya çok sayıda (b,h,As) adayı. Yerleşim bu fonksiyonda yoktur.

    Akma varsayımıyla deneme momenti; sünek olmayan kesit reddedilir.
    """
    x=np.asarray(x,float)
    if x.shape[-1]!=3 or not np.all(np.isfinite(x)) or np.any(x<=0):
        raise ValueError('Pozitif ve sonlu b, h, As gereklidir.')
    b,h,As=np.moveaxis(x,-1,0)
    d=h-(p.merkez_ortusu if ortusu is None else ortusu)
    beta=max(.65,min(.85,.85-.05*(p.fc-28)/7))
    a=As*p.fy/(.85*p.fc*b)
    c=a/beta
    eps=.003*(d-c)/c
    eps_min=p.fy/p.Es+.003
    As_min=max(.25*math.sqrt(p.fc)/p.fy,1.4/p.fy)*b*d
    mu=(p.dis_yuk+p.ozagirlik_katsayi*p.ozagirlik*b*h*1e-6)*p.L**2/8
    m_trial=.9*As*p.fy*(d-a/2)/1e6
    beton=(b*h-As)*1e-6*p.L
    celik=As*1e-6*p.L*7850
    cost=p.beton_fiyat*beton+p.celik_fiyat*celik
    moment=np.maximum(0,(mu-m_trial)/np.maximum(mu,1e-12))
    minimum=np.maximum(0,(As_min-As)/np.maximum(As_min,1e-12))
    ductility=np.maximum(0,(eps_min-eps)/eps_min)
    bounds=np.sum(np.maximum(0,(ALT-x)/(UST-ALT))+np.maximum(0,(x-UST)/(UST-ALT)),axis=-1)
    violation=moment+minimum+ductility+bounds
    return dict(cost=cost,violation=violation,feasible=violation<=TOL,
                d=d,As_min=As_min,eps=eps,eps_min=eps_min,mu=mu,
                m_trial=m_trial,m_model=np.where(eps>=eps_min-1e-12,m_trial,np.nan),
                beton=beton,celik=celik,moment_violation=moment,
                minimum_violation=minimum,ductility_violation=ductility)


def kayit(x,p,ortusu=None):
    r=hesapla(x,p,ortusu)
    return dict(b_mm=float(x[0]),h_mm=float(x[1]),As_mm2=float(x[2]),
                d_mm=float(r['d']),As_min_mm2=float(r['As_min']),
                epsilon_t=float(r['eps']),epsilon_min=float(r['eps_min']),
                Mu_kNm=float(r['mu']),M_model_kNm=float(r['m_model']) if np.isfinite(r['m_model']) else None,
                beton_m3=float(r['beton']),celik_kg=float(r['celik']),
                maliyet_PB=float(r['cost']),ihlal=float(r['violation']),uygun=bool(r['feasible']))


def daha_iyi(c,v,pc,pv):
    f,pf=v<=TOL,pv<=TOL
    return ((f&~pf)|(f&pf&(c<pc))|(~f&~pf&((v<pv)|((v==pv)&(c<pc)))))


def en_iyi(c,v):
    return min(range(len(c)),key=lambda i:(v[i]>TOL,0 if v[i]<=TOL else v[i],c[i]))


def deneme_uret(pop,rng,F=.7,CR=.9):
    """DE/rand/1/bin; donorlar birbirinden ve hedef indeksten farklıdır."""
    n,dim=pop.shape
    donor=np.empty((n,3),int)
    for i in range(n):
        donor[i]=rng.choice(np.delete(np.arange(n),i),size=3,replace=False)
    v=pop[donor[:,0]]+F*(pop[donor[:,1]]-pop[donor[:,2]])
    v=np.clip(v,0,1)
    mask=rng.random((n,dim))<CR
    mask[np.arange(n),rng.integers(0,dim,n)]=True  # en az bir donor bileşeni
    return np.where(mask,v,pop),donor,mask


def diferansiyel_evrim(p,seed=0,populasyon=40,nesil=300,F=.7,CR=.9):
    if populasyon<4 or nesil<1 or F<=0 or not 0<=CR<=1:
        raise ValueError('Popülasyon>=4, nesil>=1, F>0, 0<=CR<=1 olmalı.')
    rng=np.random.default_rng(seed)
    z=rng.random((populasyon,3))  # birimleri dengelemek için [0,1] normalizasyonu
    r=hesapla(ALT+z*(UST-ALT),p)
    costs,violations=r['cost'].copy(),r['violation'].copy()
    trace=[]
    for t in range(nesil+1):
        idx=en_iyi(costs,violations)
        trace.append(dict(seed=seed,nesil=t,en_iyi_uygun_maliyet_PB=float(costs[idx]) if violations[idx]<=TOL else None,
                          en_iyi_ihlal=float(violations[idx]),degerlendirme=(t+1)*populasyon))
        if t==nesil:break
        trial,_,_=deneme_uret(z,rng,F,CR)
        nr=hesapla(ALT+trial*(UST-ALT),p)
        better=daha_iyi(nr['cost'],nr['violation'],costs,violations)
        # Senkron nesil: bütün donorlar önceki popülasyondan geldi.
        z[better]=trial[better];costs[better]=nr['cost'][better];violations[better]=nr['violation'][better]
    return ALT+z[idx]*(UST-ALT),trace


def gerekli_alan(b,h,p):
    """Sabit b,h için eğilme denkleminden minimum gerekli As (kararlı küçük kök)."""
    b,h=np.broadcast_arrays(np.asarray(b,float),np.asarray(h,float))
    d=h-p.merkez_ortusu
    mu=(p.dis_yuk+p.ozagirlik_katsayi*p.ozagirlik*b*h*1e-6)*p.L**2/8
    k=mu*1e6/(.9*p.fy)
    coef=p.fy/(2*.85*p.fc*b)
    discriminant=d*d-4*coef*k
    root=2*k/(d+np.sqrt(np.maximum(discriminant,0)))
    amin=max(.25*math.sqrt(p.fc)/p.fy,1.4/p.fy)*b*d
    As=np.maximum(np.maximum(root,amin),ALT[2])
    return np.where(discriminant>=0,As,np.nan)


def izgara_referansi(p,adim=.5):
    """b,h ızgarasında As analitik çözülür. Sürekli global optimum ispatı DEĞİL."""
    bs=np.arange(ALT[0],UST[0]+adim/2,adim)
    hs=np.arange(ALT[1],UST[1]+adim/2,adim)
    b,h=np.meshgrid(bs,hs,indexing='ij')
    As=gerekli_alan(b,h,p)
    valid=np.isfinite(As)
    xs=np.column_stack((b[valid],h[valid],As[valid]))
    r=hesapla(xs,p)
    ok=np.flatnonzero(r['feasible'])
    if not len(ok):return None,len(bs)*len(hs)
    i=ok[np.argmin(r['cost'][ok])]
    return kayit(xs[i],p),len(bs)*len(hs)


def katalog_adayi(b,h,n,cap,p):
    As=n*math.pi*cap**2/4
    cover=p.paspayi+p.etriye+cap/2
    r=kayit([b,h,As],p,cover)
    net=(b-2*(p.paspayi+p.etriye)-n*cap)/(n-1)
    needed=max(25.,cap,4*p.agrega/3)
    r.update(adet=n,cap_mm=cap,merkez_ortusu_mm=cover,net_aralik_mm=net,gerekli_aralik_mm=needed)
    extra=max(0,(needed-net)/needed)
    r['ihlal']+=extra;r['uygun']=r['uygun'] and extra<=TOL
    return r


def katalog_tara(p):
    rows=[katalog_adayi(b,h,n,cap,p) for b,h,n,cap in itertools.product(
        range(250,451,25),range(350,701,25),range(2,7),(12,16,20,24,28))]
    ok=[r for r in rows if r['uygun']]
    return (min(ok,key=lambda r:r['maliyet_PB']) if ok else None),rows


def donustur(x,p,rows):
    """b,h yukarı 25 mm adımına; +0,+25,+50 mm komşuluk.
    As, DE hedefinden az olmayacak. Her aday GERÇEK merkez örtüsüyle hesaplı.
    """
    b0=25*math.ceil((x[0]-1e-8)/25)
    h0=25*math.ceil((x[1]-1e-8)/25)
    near=[dict(r) for r in rows if r['b_mm'] in (b0,b0+25,b0+50)
          and r['h_mm'] in (h0,h0+25,h0+50) and r['As_mm2']>=x[2]-1e-8]
    ok=[r for r in near if r['uygun']]
    return (min(ok,key=lambda r:r['maliyet_PB']) if ok else None),near


def csv_yaz(path,rows):
    if not rows:
        path.unlink(missing_ok=True);return
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--yuk',type=float,default=30)
    parser.add_argument('--populasyon',type=int,default=40)
    parser.add_argument('--nesil',type=int,default=300)
    parser.add_argument('--kosu',type=int,default=10)
    args=parser.parse_args()
    if not np.isfinite(args.yuk) or args.yuk<=0 or args.populasyon<4 or min(args.nesil,args.kosu)<1:
        parser.error('Yük pozitif/sonlu, popülasyon>=4, nesil/koşu>=1 olmalı.')
    p=Problem(dis_yuk=args.yuk)
    runs,history=[],[]
    # Aramada ızgara/katalog sonucu kullanılmaz.
    for seed in range(args.kosu):
        x,tr=diferansiyel_evrim(p,seed,args.populasyon,args.nesil)
        runs.append(dict(seed=seed,**kayit(x,p),degerlendirme=(args.nesil+1)*args.populasyon))
        history.extend(tr)
    feasible=[r for r in runs if r['uygun']]
    best=min(feasible,key=lambda r:r['maliyet_PB']) if feasible else None
    ref,grid_n=izgara_referansi(p)
    catalog,rows=katalog_tara(p)
    converted,near=(donustur([best['b_mm'],best['h_mm'],best['As_mm2']],p,rows) if best else (None,[]))
    for r in runs:
        r['izgara_farki_yuzde']=(100*(r['maliyet_PB']/ref['maliyet_PB']-1) if ref and r['uygun'] else None)
    summary=dict(problem=asdict(p),ayarlar=vars(args),en_iyi=best,izgara_referansi=ref,
                 izgara_adim_mm=.5,izgara_nokta=grid_n,donusturulen=converted,
                 katalog_en_iyi=catalog,katalog_aday=len(rows),katalog_uygun=sum(r['uygun'] for r in rows),
                 donusum_aday=len(near),uygun_kosu=len(feasible),
                 referansa_yuzde01_yakin=sum(r['uygun'] and r['izgara_farki_yuzde'] is not None
                                           and abs(r['izgara_farki_yuzde'])<=.1 for r in runs))
    out=Path(__file__).resolve().parent/'sonuclar';out.mkdir(exist_ok=True)
    csv_yaz(out/'de_kosular.csv',runs);csv_yaz(out/'yakinsama.csv',history)
    csv_yaz(out/'katalog_taramasi.csv',rows);csv_yaz(out/'donusum_adaylari.csv',near)
    (out/'ozet.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print('EĞİTİM MODELİ: Kesme, sehim ve tam detaylandırma dahil değildir.')
    print('En iyi sürekli DE:',best)
    print('0.5 mm ızgara referansı:',ref)
    print('Dönüştürülen aday:',converted)
    print('Tüm katalogdaki en iyi:',catalog)
    print('Yakın koşu:',summary['referansa_yuzde01_yakin'],'/',args.kosu)


if __name__=='__main__':main()
