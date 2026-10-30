"""Ders 06 — Ayrık kesit alanlarıyla NSGA-II, kütle–deplasman Pareto araması.
Python 3.9+, NumPy. Eğitim modeli; burkulma ve gerçek profil tasarımı yoktur.
"""
import argparse,csv,itertools,json
from dataclasses import dataclass,asdict
from pathlib import Path
import numpy as np

ALANLAR=np.array([200,300,400,500,650,800,1000,1250,1500,2000,2500,3000],float)
TOL=1e-10

@dataclass(frozen=True)
class Problem:
    yuk_N: float=120000.0
    E: float=200000.0
    rho: float=7.85e-6
    sigma_sinir: float=160.0

class Kafes:
    def __init__(self,p):
        self.p=p;self.nodes=np.array([[0,0],[4000,0],[2000,3000]],float)
        self.elements=np.array([[0,1],[0,2],[1,2]])
        self.free=np.array([2,4,5]);self.F=np.array([0,0,0,0,0,-p.yuk_N],float)
        delta=self.nodes[self.elements[:,1]]-self.nodes[self.elements[:,0]]
        self.L=np.linalg.norm(delta,axis=1)
        self.B=np.zeros((3,6))
        for i,((a,b),(c,s)) in enumerate(zip(self.elements,delta/self.L[:,None])):
            self.B[i,[2*a,2*a+1,2*b,2*b+1]]=[-c,-s,c,s]
        self.K0=p.E/self.L[:,None,None]*self.B[:,:,None]*self.B[:,None,:]
        self.cache={};self.solves=0;self.queries=0

    def analiz(self,A):
        A=np.asarray(A,float)
        if A.shape!=(3,) or not np.all(np.isfinite(A)) or np.any(A<=0):raise ValueError('Üç pozitif alan gerekir.')
        K=np.einsum('i,ijk->jk',A,self.K0);u=np.zeros(6)
        u[self.free]=np.linalg.solve(K[np.ix_(self.free,self.free)],self.F[self.free])
        stress=self.p.E/self.L*(self.B@u)
        violation=float(np.sum(np.maximum(np.abs(stress)/self.p.sigma_sinir-1,0)))
        return dict(mass=float(np.sum(A*self.L*self.p.rho)),disp=float(abs(u[5])),
                    violation=violation,feasible=violation<=TOL,
                    stress=stress.tolist(),u=u.tolist(),reactions=(K@u-self.F).tolist())

    def degerlendir(self,pop,count=True):
        data=[]
        for row in pop:
            key=tuple(int(i) for i in row)
            if len(key)!=3 or any(i<0 or i>=len(ALANLAR) for i in key):raise ValueError('Geçersiz katalog indeksi.')
            if count:self.queries+=1
            if key not in self.cache:
                self.cache[key]=self.analiz(ALANLAR[list(key)]);self.solves+=1
            data.append(self.cache[key])
        F=np.array([[r['mass'],r['disp']] for r in data],float).reshape(-1,2)
        v=np.array([r['violation'] for r in data],float)
        return F,v


def yuvarla(F):
    """Simetrik tasarımlardaki son-basamak farklarını tutarlı biçimde kaldır."""
    return np.round(np.asarray(F,float),decimals=8)


def sirala(F,v):
    """Kısıtlı baskınlık ve O(N²) baskın olmayan sıralama."""
    F=yuvarla(F);n=len(F);feasible=np.asarray(v)<=TOL
    pareto=np.all(F[:,None,:]<=F[None,:,:],axis=2)&np.any(F[:,None,:]<F[None,:,:],axis=2)
    D=((feasible[:,None]&feasible[None,:]&pareto)|
       (feasible[:,None]&~feasible[None,:])|
       (~feasible[:,None]&~feasible[None,:]&(v[:,None]<v[None,:]-TOL)))
    np.fill_diagonal(D,False)
    count=np.sum(D,axis=0);rank=np.full(n,-1,int);fronts=[]
    front=np.flatnonzero(count==0);level=0
    while len(front):
        fronts.append(front);rank[front]=level
        count-=np.sum(D[front],axis=0)
        front=np.flatnonzero((count==0)&(rank<0));level+=1
    if np.any(rank<0):raise RuntimeError('Sıralama tamamlanmadı.')
    return rank,fronts


def kalabalik(F,fronts):
    """Her amaç aralığına normalize komşu uzaklıkları; uçlar korunur."""
    F=yuvarla(F);distance=np.zeros(len(F))
    for ids in fronts:
        if len(ids)<=2:distance[ids]=np.inf;continue
        for j in range(F.shape[1]):
            order=ids[np.argsort(F[ids,j],kind='stable')]
            span=F[order[-1],j]-F[order[0],j]
            if span<=0:continue
            distance[order[[0,-1]]]=np.inf
            distance[order[1:-1]]+=(F[order[2:],j]-F[order[:-2],j])/span
    return distance


def turnuva(rank,distance,rng):
    a,b=rng.choice(len(rank),2,replace=False)
    if rank[a]!=rank[b]:return a if rank[a]<rank[b] else b
    if distance[a]!=distance[b]:return a if distance[a]>distance[b] else b
    return int(rng.choice([a,b]))


def cevre_secimi(pop,model,size):
    # Aynı tasarımın çoğalmasını önleyen öğretim uyarlaması.
    pop=np.unique(pop,axis=0)
    F,v=model.degerlendir(pop,count=False);rank,fronts=sirala(F,v)
    crowd=kalabalik(F,fronts);chosen=[]
    for ids in fronts:
        if len(chosen)+len(ids)<=size:chosen.extend(ids.tolist())
        else:
            order=ids[np.argsort(-crowd[ids],kind='stable')]
            chosen.extend(order[:size-len(chosen)].tolist());break
    return pop[chosen]


def ilk_cephe(pop,model):
    F,v=model.degerlendir(pop,count=False)
    _,fronts=sirala(F,v)
    ids=fronts[0] if fronts else np.array([],int)
    ids=ids[v[ids]<=TOL]
    # Raporlamada eşdeğer amaç noktaları bir kez sayılır; indeks temsili korunur.
    if len(ids):
        _,loc=np.unique(yuvarla(F[ids]),axis=0,return_index=True)
        ids=ids[loc]
    return pop[ids],F[ids]


def nsga2(model,seed=0,size=100,generations=80):
    if not 4<=size<=len(ALANLAR)**3 or generations<1:raise ValueError('4<=popülasyon<=1728; nesil>=1 gerekir.')
    rng=np.random.default_rng(seed)
    codes=rng.choice(len(ALANLAR)**3,size,replace=False)
    pop=np.array(np.unravel_index(codes,(len(ALANLAR),)*3)).T
    model.degerlendir(pop)
    history=[]
    for gen in range(generations+1):
        fp,ff=ilk_cephe(pop,model)
        history.append(dict(seed=seed,nesil=gen,pareto_nokta=len(ff),
                            degerlendirme=model.queries,benzersiz_analiz=model.solves,
                            _front=ff.tolist()))
        if gen==generations:break
        F,v=model.degerlendir(pop,count=False);rank,fronts=sirala(F,v);crowd=kalabalik(F,fronts)
        children=[];seen=set()
        while len(children)<size:
            a=pop[turnuva(rank,crowd,rng)];b=pop[turnuva(rank,crowd,rng)]
            # Ayrık alanlara uygun üniform çaprazlama, her gende 1/3 mutasyon.
            child=np.where(rng.random(3)<.5,a,b).copy()
            mutate=rng.random(3)<1/3
            for j in np.flatnonzero(mutate):child[j]=rng.integers(len(ALANLAR))
            key=tuple(child)
            if key in seen:continue
            seen.add(key);children.append(child)
        children=np.array(children)
        model.degerlendir(children)
        pop=cevre_secimi(np.vstack([pop,children]),model,size)
    return fp,ff,history


def tam_tarama(model):
    pop=np.array(list(itertools.product(range(len(ALANLAR)),repeat=3)))
    F,v=model.degerlendir(pop)
    front,ff=ilk_cephe(pop,model)
    return pop,F,v,front,ff


def hypervolume(F,lo,span,ref=(1.1,1.1)):
    """İki amaçta, normalize uzayda referans noktasına baskın alan."""
    if len(F)==0:return 0.
    z=(yuvarla(F)-lo)/span;z=z[np.argsort(z[:,0])]
    area=0.;prev=ref[1]
    for x,y in z:
        if x<ref[0] and y<prev:
            area+=(ref[0]-x)*(prev-y);prev=y
    return float(area)


def keyset(F):return {tuple(x) for x in yuvarla(F)}


def kayit(row,model):
    A=ALANLAR[row];r=model.cache.get(tuple(row))
    if r is None:model.degerlendir([row],count=False);r=model.cache[tuple(row)]
    return dict(A1_mm2=float(A[0]),A2_mm2=float(A[1]),A3_mm2=float(A[2]),
                kutle_kg=r['mass'],tepe_deplasman_mm=r['disp'],uygun=r['feasible'],
                max_gerilme_MPa=max(abs(s) for s in r['stress']))


def csv_yaz(path,rows):
    if not rows:path.unlink(missing_ok=True);return
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--kosu',type=int,default=10);ap.add_argument('--populasyon',type=int,default=100)
    ap.add_argument('--nesil',type=int,default=80);ap.add_argument('--yuk-kn',type=float,default=120)
    args=ap.parse_args()
    if args.kosu<1 or args.nesil<1 or not 4<=args.populasyon<=1728 or not np.isfinite(args.yuk_kn) or args.yuk_kn<=0:
        ap.error('Koşu/nesil/yük pozitif; 4<=popülasyon<=1728 gerekir.')
    p=Problem(yuk_N=args.yuk_kn*1000)
    results=[]
    for seed in range(args.kosu):
        model=Kafes(p);pop,F,trace=nsga2(model,seed,args.populasyon,args.nesil)
        results.append((model,pop,F,trace))
    # Arama bittikten sonra bağımsız tam tarama; aramaya referans bilgisi verilmez.
    exact=Kafes(p);allpop,allF,allv,epop,eF=tam_tarama(exact)
    exact_keys=keyset(eF)
    lo=np.min(eF,axis=0) if len(eF) else np.zeros(2)
    span=np.maximum(np.ptp(eF,axis=0),1e-12) if len(eF) else np.ones(2)
    hvref=hypervolume(eF,lo,span)
    runs,front_rows,history=[],[],[]
    for seed,(model,pop,F,trace) in enumerate(results):
        keys=keyset(F);matches=len(keys&exact_keys)
        hv=hypervolume(F,lo,span)
        runs.append(dict(seed=seed,son_pareto_nokta=len(F),gercek_pareto_eslesme=matches,
                         kapsama_yuzde=100*matches/len(eF) if len(eF) else 0.,
                         dogruluk_yuzde=100*matches/len(F) if len(F) else 0.,
                         hypervolume_orani=hv/hvref if hvref else None,
                         degerlendirme=model.queries,benzersiz_analiz=model.solves))
        for row,f in zip(pop,F):
            front_rows.append(dict(seed=seed,**kayit(row,model),tam_taramada_pareto=tuple(yuvarla([f])[0]) in exact_keys))
        for t in trace:
            ff=np.array(t.pop('_front')).reshape(-1,2)
            t['hypervolume_orani']=hypervolume(ff,lo,span)/hvref if hvref else None
            history.append(t)
    # Temsilciler: önceden sabitlenen seed 0'ın doğrulanmış Pareto noktaları.
    sample=[r for r in front_rows if r['seed']==0 and r['tam_taramada_pareto']]
    reps=[]
    if sample:
        reps.append(dict(tercih='En hafif',**min(sample,key=lambda r:r['kutle_kg'])))
        target=[r for r in sample if r['tepe_deplasman_mm']<=2+1e-10]
        if target:reps.append(dict(tercih='2 mm hedefinde en hafif',**min(target,key=lambda r:r['kutle_kg'])))
        reps.append(dict(tercih='En az yer değiştiren',**min(sample,key=lambda r:r['tepe_deplasman_mm'])))
    summary=dict(problem=asdict(p),ayarlar=vars(args),alanlar_mm2=ALANLAR.tolist(),
                 kombinasyon=len(allpop),uygun_kombinasyon=int(np.sum(allv<=TOL)),
                 gercek_pareto_nokta=len(eF),kosular=runs,temsilciler=reps,
                 hv_alt=lo.tolist(),hv_aralik=span.tolist(),hv_referans=[1.1,1.1])
    out=Path(__file__).resolve().parent/'sonuclar';out.mkdir(exist_ok=True)
    csv_yaz(out/'kosular.csv',runs);csv_yaz(out/'yakinsama.csv',history)
    csv_yaz(out/'nsga2_pareto.csv',front_rows)
    csv_yaz(out/'tam_pareto.csv',[kayit(row,exact) for row in epop])
    csv_yaz(out/'tum_kombinasyonlar.csv',[kayit(row,exact) for row in allpop])
    csv_yaz(out/'temsilci_tasarimlar.csv',reps)
    (out/'ozet.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print('EĞİTİM MODELİ — Burkulma/öz ağırlık/bağlantı tasarımı yoktur.')
    print('Kombinasyon / uygun / gerçek Pareto noktası:',len(allpop),int(np.sum(allv<=TOL)),len(eF))
    print('Koşular:',runs)
    print('Temsilciler:',reps)

if __name__=='__main__':main()
