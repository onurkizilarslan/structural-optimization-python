"""Ders 03 — PSO ile üç çubuklu düzlem kafeste kesit optimizasyonu.
Python 3.9+ / NumPy. Eğitim modeli: burkulma ve gerçek profil tasarımı yoktur.
"""
import argparse
import csv
from dataclasses import dataclass, asdict
import json
from pathlib import Path
import numpy as np


@dataclass(frozen=True)
class Problem:
    aciklik_mm: float = 4000.0
    yukseklik_mm: float = 3000.0
    yuk_N: float = 120000.0
    E_MPa: float = 200000.0
    yogunluk_kg_mm3: float = 7.85e-6
    gerilme_sinir_MPa: float = 160.0
    deplasman_sinir_mm: float = 2.0  # Yalnız tepe düğümünün düşey hareketi
    alan_min_mm2: float = 200.0
    alan_max_mm2: float = 3000.0


def rijitlik_hazirla(nodes, elements, E, fixed):
    """Genel 2B çubuk: k_e=(EA/L) B^T B, B=[-c,-s,c,s]."""
    nodes = np.asarray(nodes, dtype=float)
    elements = np.asarray(elements, dtype=int)
    ndof = 2*len(nodes)
    delta = nodes[elements[:,1]]-nodes[elements[:,0]]
    L = np.linalg.norm(delta, axis=1)
    yon = delta/L[:,None]
    B = np.zeros((len(elements),ndof))
    for i, ((a,b), (c,s)) in enumerate(zip(elements,yon)):
        B[i,[2*a,2*a+1,2*b,2*b+1]] = [-c,-s,c,s]
    free = np.setdiff1d(np.arange(ndof), fixed)
    # Her elemanın birim kesit alanına ait global rijitlik katkısı.
    K0 = E/L[:,None,None]*B[:,:,None]*B[:,None,:]
    return L,B,K0,free


def lineer_analiz(nodes, elements, E, areas, loads, fixed):
    """Genel tek analiz; doğrulama örnekleri ve reaksiyon hesabı için."""
    areas = np.asarray(areas,dtype=float)
    L,B,K0,free = rijitlik_hazirla(nodes,elements,E,fixed)
    K = np.einsum('i,ijk->jk',areas,K0)
    u = np.zeros(2*len(nodes))
    u[free] = np.linalg.solve(K[np.ix_(free,free)],np.asarray(loads)[free])
    stress = E/L*(B@u)
    return dict(u=u,stress=stress,force=areas*stress,
                reaction=K@u-loads,K=K,length=L)


class Kafes:
    def __init__(self,p):
        self.p=p
        self.nodes=np.array([[0,0],[p.aciklik_mm,0],
                             [p.aciklik_mm/2,p.yukseklik_mm]],dtype=float)
        self.elements=np.array([[0,1],[0,2],[1,2]])
        self.fixed=np.array([0,1,3])  # Sol: x,y sabit; sağ: y sabit, x serbest.
        self.loads=np.array([0,0,0,0,0,-p.yuk_N],dtype=float)
        self.L,self.B,self.K0,self.free=rijitlik_hazirla(
            self.nodes,self.elements,p.E_MPa,self.fixed)
        self.Kfree=self.K0[:,self.free][:,:,self.free]
        self.Bfree=self.B[:,self.free]

    def degerlendir(self,areas):
        """Bir veya çok sayıda aday için aynı matris çözümü; onarım yapılmaz."""
        A=np.asarray(areas,dtype=float)
        if A.shape[-1]!=3 or np.any(A<=0) or not np.all(np.isfinite(A)):
            raise ValueError('Üç pozitif, sonlu kesit alanı gereklidir.')
        K=np.einsum('...i,ijk->...jk',A,self.Kfree)
        rhs=np.broadcast_to(self.loads[self.free],A.shape[:-1]+(len(self.free),))
        uf=np.linalg.solve(K,rhs[...,None])[...,0]
        stress=self.p.E_MPa/self.L*np.einsum('ij,...j->...i',self.Bfree,uf)
        uy=uf[...,list(self.free).index(5)]
        mass=np.sum(A*self.L*self.p.yogunluk_kg_mm3,axis=-1)
        violation=(np.sum(np.maximum(np.abs(stress)/self.p.gerilme_sinir_MPa-1,0),axis=-1)
                   +np.maximum(np.abs(uy)/self.p.deplasman_sinir_mm-1,0)
                   +np.sum(np.maximum(self.p.alan_min_mm2/A-1,0),axis=-1)
                   +np.sum(np.maximum(A/self.p.alan_max_mm2-1,0),axis=-1))
        return dict(mass=mass,violation=violation,feasible=violation<=1e-10,
                    stress=stress,uy=uy,uf=uf)


def daha_iyi(m,v,pm,pv):
    """Uygunluk önceliği: uygunlar kütleye, uygunsuzlar ihlale göre."""
    feasible,pfeasible=v<=1e-10,pv<=1e-10
    return ((feasible & ~pfeasible) |
            (feasible & pfeasible & (m<pm)) |
            (~feasible & ~pfeasible & ((v<pv)|((v==pv)&(m<pm)))))


def en_iyi_indeks(m,v):
    return min(range(len(m)),key=lambda i:(v[i]>1e-10,0 if v[i]<=1e-10 else v[i],m[i]))


def pso(model,seed=0,parcacik=40,iterasyon=300):
    p=model.p
    rng=np.random.default_rng(seed)
    lo,hi=p.alan_min_mm2,p.alan_max_mm2
    x=rng.uniform(lo,hi,(parcacik,3))
    x[0]=hi  # En büyük kesitli bir başlangıç; her yükte uygun olmak zorunda değil.
    v=rng.uniform(-.1,.1,(parcacik,3))*(hi-lo)
    r=model.degerlendir(x)
    pb=x.copy(); pm=r['mass'].copy(); pv=r['violation'].copy()
    g=en_iyi_indeks(pm,pv)
    gb=pb[g].copy()
    history=[]
    for t in range(iterasyon+1):
        history.append(dict(seed=seed,iterasyon=t,
                            en_iyi_uygun_kutle_kg=float(pm[g]) if pv[g]<=1e-10 else None,
                            en_iyi_ihlal=float(pv[g]),degerlendirme=(t+1)*parcacik))
        if t==iterasyon:
            break
        # w atalet, c1 kişisel öğrenme, c2 sürüden öğrenme.
        w=.9-.5*t/max(iterasyon-1,1)
        r1,r2=rng.random(x.shape),rng.random(x.shape)
        v=w*v+1.7*r1*(pb-x)+1.7*r2*(gb-x)
        v=np.clip(v,-.2*(hi-lo),.2*(hi-lo))
        proposal=x+v
        hit=(proposal<lo)|(proposal>hi)
        x=np.clip(proposal,lo,hi)
        v[hit]=0  # Sınıra çarpan bileşenin hızını sıfırla.
        r=model.degerlendir(x)
        better=daha_iyi(r['mass'],r['violation'],pm,pv)
        pb[better]=x[better]; pm[better]=r['mass'][better]; pv[better]=r['violation'][better]
        g=en_iyi_indeks(pm,pv)
        gb=pb[g].copy()
    return gb,history


def analitik_referans(model):
    """Bu izostatik üçgen için global konveks referans (KKT).

    N_i kesitten bağımsızdır. Tepe düşey hareketi sum(q_i/A_i),
    q_i=N_i² L_i/(E P). Kütle sum(w_i A_i).
    KKT: A_i=clip(sqrt(lambda*q_i/w_i), alt_i, üst).
    """
    p=model.p
    half=p.aciklik_mm/2
    force=np.array([p.yuk_N*half/(2*p.yukseklik_mm),
                    -p.yuk_N*model.L[1]/(2*p.yukseklik_mm),
                    -p.yuk_N*model.L[2]/(2*p.yukseklik_mm)])
    q=force**2*model.L/(p.E_MPa*p.yuk_N)
    weight=model.L*p.yogunluk_kg_mm3
    lower=np.maximum(p.alan_min_mm2,np.abs(force)/p.gerilme_sinir_MPa)
    upper=p.alan_max_mm2
    if np.any(lower>upper) or np.sum(q/upper)>p.deplasman_sinir_mm:
        return None
    if np.sum(q/lower)<=p.deplasman_sinir_mm:
        A=lower
    else:
        def alan(lam):
            return np.clip(np.sqrt(lam*q/weight),lower,upper)
        left,right=0.,1.
        while np.sum(q/alan(right))>p.deplasman_sinir_mm:
            right*=2
        for _ in range(100):
            mid=(left+right)/2
            if np.sum(q/alan(mid))>p.deplasman_sinir_mm:
                left=mid
            else:
                right=mid
        A=alan(right)
    return dict(areas=A,mass=float(np.sum(weight*A)),
                uy=float(-np.sum(q/A)),force=force)


def csv_yaz(path,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--yuk-kn',type=float,default=120)
    parser.add_argument('--deplasman-mm',type=float,default=2)
    parser.add_argument('--parcacik',type=int,default=40)
    parser.add_argument('--iterasyon',type=int,default=300)
    parser.add_argument('--kosu',type=int,default=10)
    a=parser.parse_args()
    if (not np.isfinite(a.yuk_kn) or not np.isfinite(a.deplasman_mm) or
        min(a.yuk_kn,a.deplasman_mm,a.parcacik,a.iterasyon,a.kosu)<=0):
        parser.error('Bütün parametreler pozitif ve sonlu olmalıdır.')
    p=Problem(yuk_N=a.yuk_kn*1000,deplasman_sinir_mm=a.deplasman_mm)
    model=Kafes(p)
    runs,trace=[],[]
    # Referans çözüm PSO'ya verilmez; aramadan sonra hesaplanır.
    for seed in range(a.kosu):
        x,h=pso(model,seed,a.parcacik,a.iterasyon)
        r=model.degerlendir(x)
        runs.append(dict(seed=seed,A1_mm2=float(x[0]),A2_mm2=float(x[1]),A3_mm2=float(x[2]),
                         kutle_kg=float(r['mass']),uy_mm=float(r['uy']),uygun=bool(r['feasible']),
                         toplam_ihlal=float(r['violation']),
                         degerlendirme=(a.iterasyon+1)*a.parcacik))
        trace.extend(h)
    ref=analitik_referans(model)
    for row in runs:
        row['referanstan_fark_yuzde']=(100*(row['kutle_kg']/ref['mass']-1)
                                      if ref and row['uygun'] else None)
    feasible=[r for r in runs if r['uygun']]
    best=min(feasible,key=lambda r:r['kutle_kg']) if feasible else None
    baseline=model.degerlendir([1500,1500,1500])
    summary=dict(problem=asdict(p),ayarlar=vars(a),referans=ref,en_iyi=best,
                 uygun_kosu=len(feasible),
                 yuzde_01_yakin_kosu=sum(r['uygun'] and r['referanstan_fark_yuzde'] is not None
                                       and abs(r['referanstan_fark_yuzde'])<=.1 for r in runs),
                 baslangic_kutle_kg=float(baseline['mass']),
                 baslangic_uy_mm=float(baseline['uy']),baslangic_uygun=bool(baseline['feasible']))
    out=Path(__file__).resolve().parent/'sonuclar';out.mkdir(exist_ok=True)
    csv_yaz(out/'pso_kosular.csv',runs);csv_yaz(out/'yakinsama.csv',trace)
    if best:
        x=np.array([best[f'A{i}_mm2'] for i in (1,2,3)])
        sol=lineer_analiz(model.nodes,model.elements,p.E_MPa,x,model.loads,model.fixed)
        csv_yaz(out/'eleman_kontrolleri.csv',[
            dict(eleman=i+1,baslangic_dugum=int(e[0]+1),bitis_dugum=int(e[1]+1),
                 L_mm=float(L),A_mm2=float(A),N_kN=float(N/1000),
                 sigma_MPa=float(sig),gerilme_kullanim=abs(float(sig))/p.gerilme_sinir_MPa)
            for i,(e,L,A,N,sig) in enumerate(zip(model.elements,model.L,x,sol['force'],sol['stress']))])
        csv_yaz(out/'dugum_sonuclari.csv',[
            dict(dugum=i+1,ux_mm=float(sol['u'][2*i]),uy_mm=float(sol['u'][2*i+1]),
                 Rx_kN=float(sol['reaction'][2*i]/1000),Ry_kN=float(sol['reaction'][2*i+1]/1000))
            for i in range(3)])
    else:
        # Eski koşuya ait uygun tasarım tabloları yeni deneyle karışmasın.
        for name in ('eleman_kontrolleri.csv','dugum_sonuclari.csv'):
            (out/name).unlink(missing_ok=True)
    (out/'ozet.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,
                     default=lambda v:v.tolist() if isinstance(v,np.ndarray) else v),encoding='utf-8')
    print('EĞİTİM MODELİ: Burkulma, bağlantı ve gerçek profil tasarımı dahil değildir.')
    if best:
        print('En iyi PSO:',best)
    else:
        print('PSO uygun çözüm bulamadı.')
    print('Analitik referans:',ref)
    print('Referansa %0,1 içinde yaklaşan koşu:',summary['yuzde_01_yakin_kosu'],'/',a.kosu)
    print('Çıktı:',out)


if __name__=='__main__':
    main()
