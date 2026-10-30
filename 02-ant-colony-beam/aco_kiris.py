"""Ders 2: Karınca kolonisiyle betonarme kiriş kesiti seçimi.
Eğitim modeli; gerçek proje veya TS 500/TBDY uygunluk hesabı değildir.
Python 3.9+, ek paket gerekmez. python aco_kiris.py --help
"""
import argparse
import csv
from dataclasses import dataclass, asdict
import itertools
import json
import math
from pathlib import Path
import random
import statistics


@dataclass(frozen=True)
class Problem:
    genislikler: tuple = (250, 300, 350, 400, 450)
    yukseklikler: tuple = (350, 400, 450, 500, 550, 600, 650, 700)
    adetler: tuple = (2, 3, 4, 5, 6)
    caplar: tuple = (12, 16, 20, 24, 28)
    fc: float = 30.0  # MPa
    fy: float = 420.0  # MPa
    es: float = 200000.0  # MPa
    aciklik: float = 6.0  # m
    dis_yuk: float = 30.0  # kN/m, katsayı uygulanmış; kiriş öz ağırlığı hariç
    beton_agirlik: float = 25.0  # kN/m³, betonarme öz ağırlık yaklaşımı
    ozagirlik_katsayi: float = 1.2  # Bu dersin yük varsayımı
    paspayi: float = 35.0  # mm, etriyenin DIŞ yüzüne kadar
    etriye_cap: float = 8.0  # mm, sadece geometrik yer ayırma
    agrega: float = 20.0  # mm
    beton_fiyat: float = 3000.0  # varsayımsal PB/m³
    celik_fiyat: float = 35.0  # varsayımsal PB/kg

    @property
    def secenekler(self):
        return (self.genislikler, self.yukseklikler, self.adetler, self.caplar)


def hesapla(x, p):
    """Tek sırada alt donatılı, pozitif eğilme altındaki dikdörtgen kesit.

    Çelik akması varsayımıyla deneme hesabı yapılır. Çekme kontrollü olmayan
    adayın model kapasitesi raporlanmaz; aday uygun kabul EDİLMEZ.
    """
    b, h, n, cap = x
    d = h - p.paspayi - p.etriye_cap - cap / 2
    ast = n * math.pi * cap**2 / 4
    beta = max(0.65, min(0.85, 0.85 - 0.05 * (p.fc - 28) / 7))
    a = ast * p.fy / (0.85 * p.fc * b)
    c = a / beta
    eps = 0.003 * (d - c) / c
    eps_sinir = p.fy / p.es + 0.003
    as_min = max(0.25 * math.sqrt(p.fc) / p.fy, 1.4 / p.fy) * b * d
    net = (b - 2 * (p.paspayi + p.etriye_cap) - n * cap) / (n - 1)
    net_min = max(25.0, cap, 4 * p.agrega / 3)
    cekme_kontrollu = eps >= eps_sinir - 1e-12
    m_deneme = 0.9 * ast * p.fy * (d - a / 2) / 1e6  # kNm
    # Değişen kesitin öz ağırlığı her adayda yeniden hesaplanır.
    w = p.dis_yuk + p.ozagirlik_katsayi * p.beton_agirlik * b * h * 1e-6
    mu = w * p.aciklik**2 / 8
    beton = (b * h - ast) * 1e-6 * p.aciklik
    celik = ast * 1e-6 * p.aciklik * 7850
    maliyet = p.beton_fiyat * beton + p.celik_fiyat * celik
    ihlaller = {
        'moment_ihlali': max(0.0, (mu - m_deneme) / mu),
        'min_donati_ihlali': max(0.0, (as_min - ast) / as_min),
        'suneklik_ihlali': max(0.0, (eps_sinir - eps) / eps_sinir),
        'yerlesim_ihlali': max(0.0, (net_min - net) / net_min),
    }
    ihlal = sum(ihlaller.values())
    uygun = ihlal <= 1e-12 and cekme_kontrollu
    return dict(b_mm=b, h_mm=h, adet=n, cap_mm=cap, d_mm=d, As_mm2=ast,
                As_min_mm2=as_min, beta1=beta, a_mm=a, c_mm=c,
                epsilon_t=eps, epsilon_sinir=eps_sinir,
                cekme_kontrollu=cekme_kontrollu,
                net_aralik_mm=net, gerekli_aralik_mm=net_min,
                toplam_yuk_kN_m=w, Mu_kNm=mu,
                M_model_kNm=m_deneme if cekme_kontrollu else None,
                beton_m3=beton, celik_kg=celik, maliyet_PB=maliyet,
                **ihlaller, toplam_ihlal=ihlal, uygun=uygun)


def sira(r):
    return (not r['uygun'], r['toplam_ihlal'], r['maliyet_PB'])


def olasiliklar(feromon, alpha=1.0, kesif=0.10):
    """%10 düzgün rastgele keşif + %90 feromona bağlı seçim."""
    agirlik = [t**alpha for t in feromon]
    toplam = sum(agirlik)
    return [(1-kesif)*w/toplam + kesif/len(agirlik) for w in agirlik]


def aco(p, seed=0, karinca=30, iterasyon=60, buharlasma=0.20):
    """Düğüm feromonu kullanan ayrık ACO öğretim varyantı.

    Ebeveyn, çaprazlama veya mutasyon yoktur. Çözüm dört aşamalı seçimle
    oluşturulur. Heuristik eta=1 olduğundan ayrı bir beta parametresi yoktur.
    Referans/tam tarama bilgisi bu fonksiyona verilmez.
    """
    rng = random.Random(seed)
    tau = [[1.0] * len(s) for s in p.secenekler]
    en_iyi = None
    en_iyi_indeks = None
    iz = []
    gorulen = set()
    for t in range(1, iterasyon + 1):
        olasilik = [olasiliklar(row) for row in tau]
        suru = []
        for _ in range(karinca):
            idx = tuple(rng.choices(range(len(s)), weights=q)[0]
                        for s, q in zip(p.secenekler, olasilik))
            x = tuple(s[j] for s, j in zip(p.secenekler, idx))
            gorulen.add(x)
            r = hesapla(x, p)
            suru.append((r, idx))
            if en_iyi is None or sira(r) < sira(en_iyi):
                en_iyi, en_iyi_indeks = r, idx
        # Feromon buharlaşması; bir seçeneğin olasılığı asla sıfırlanmaz.
        tau = [[max(0.05, (1-buharlasma)*v) for v in row] for row in tau]
        # En iyi beş FARKLI adaya sıra tabanlı feromon ödülü.
        elitler, indeksler = [], set()
        for r, idx in sorted(suru, key=lambda item: sira(item[0])):
            if idx not in indeksler:
                elitler.append((r, idx))
                indeksler.add(idx)
            if len(elitler) == 5:
                break
        for rank, (r, idx) in enumerate(elitler, start=1):
            kalite = 1.0 if r['uygun'] else 0.1/(1+r['toplam_ihlal'])
            odul = kalite / rank
            for j, k in enumerate(idx):
                tau[j][k] += odul
        # Şimdiye kadarki en iyi UYGUN adaya küçük ek ödül.
        if en_iyi['uygun']:
            for j, k in enumerate(en_iyi_indeks):
                tau[j][k] += 0.5
        tau = [[min(20.0, v) for v in row] for row in tau]
        iz.append(dict(seed=seed, iterasyon=t,
                       en_iyi_maliyet_PB=en_iyi['maliyet_PB'] if en_iyi['uygun'] else None,
                       en_iyi_ihlal=en_iyi['toplam_ihlal'],
                       bu_tur_uygun=sum(r['uygun'] for r, _ in suru),
                       degerlendirme=t*karinca, benzersiz_aday=len(gorulen)))
    return en_iyi, iz, tau


def tam_tarama(p):
    tumu = [hesapla(x, p) for x in itertools.product(*p.secenekler)]
    uygunlar = [r for r in tumu if r['uygun']]
    if not uygunlar:
        return None, tumu
    return min(uygunlar, key=lambda r: r['maliyet_PB']), tumu


def csv_yaz(path, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--yuk', type=float, default=30, help='Katsayılı dış yük, kN/m')
    parser.add_argument('--kosu', type=int, default=10)
    parser.add_argument('--karinca', type=int, default=30)
    parser.add_argument('--iterasyon', type=int, default=60)
    args = parser.parse_args()
    if args.yuk < 0 or min(args.kosu, args.karinca, args.iterasyon) < 1:
        parser.error('Yük negatif olamaz; koşu, karınca ve iterasyon en az 1 olmalıdır.')
    p = Problem(dis_yuk=args.yuk)
    out = Path(__file__).resolve().parent / 'sonuclar'
    out.mkdir(exist_ok=True)
    runs, history, pheromones = [], [], []
    # Önce ACO çalışır. Tam tarama sonucuna hiçbir aşamada erişmez.
    for seed in range(args.kosu):
        best, trace, tau = aco(p, seed, args.karinca, args.iterasyon)
        runs.append(dict(seed=seed, **best, degerlendirme=args.karinca*args.iterasyon,
                         benzersiz_aday=trace[-1]['benzersiz_aday']))
        history.extend(trace)
        pheromones.append(tau)
    ref, all_rows = tam_tarama(p)
    for r in runs:
        r['optimumdan_fark_yuzde'] = (100*(r['maliyet_PB']/ref['maliyet_PB']-1)
                                      if ref and r['uygun'] else None)
    success = sum(r['uygun'] and ref is not None and
                  abs(r['optimumdan_fark_yuzde']) < 1e-8 for r in runs)
    gaps = [r['optimumdan_fark_yuzde'] for r in runs if r['uygun'] and ref]
    summary = dict(problem=asdict(p), ayarlar=vars(args), referans=ref,
                   aday_sayisi=len(all_rows), uygun_aday=sum(r['uygun'] for r in all_rows),
                   basarili_kosu=success, ortalama_fark_yuzde=statistics.mean(gaps) if gaps else None,
                   son_feromonlar=pheromones)
    csv_yaz(out/'tum_adaylar.csv', all_rows)
    csv_yaz(out/'aco_kosular.csv', runs)
    csv_yaz(out/'yakinsama.csv', history)
    (out/'ozet.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print('EĞİTİM MODELİ — gerçek yapı tasarımında kullanmayınız.')
    print(f"Aday: {len(all_rows)}; modelde uygun: {summary['uygun_aday']}")
    if ref:
        print(f"Tam tarama: {ref['b_mm']}×{ref['h_mm']} mm, {ref['adet']}Ø{ref['cap_mm']}")
        print(f"Maliyet: {ref['maliyet_PB']:.2f} PB; Mu: {ref['Mu_kNm']:.3f} kNm; kapasite: {ref['M_model_kNm']:.3f} kNm")
        print(f"Optimuma ulaşan koşu: {success}/{args.kosu}; ortalama fark: {summary['ortalama_fark_yuzde']}")
    else:
        print('Seçenek kümesinde model koşullarını sağlayan tasarım yok.')
    print('Sonuç klasörü:', out)


if __name__ == '__main__':
    main()
