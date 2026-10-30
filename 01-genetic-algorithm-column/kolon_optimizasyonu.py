"""Betonarme kolon optimizasyonu — eğitim modeli, Python 3.9+.

Çalıştırma: python kolon_optimizasyonu.py
Harici paket gerekmez. CSV çıktıları bu dosyanın yanına yazılır.
Gerçek proje tasarımı veya TS 500/TBDY uygunluk kontrolü DEĞİLDİR.
Model ve kapsam için OKU.md dosyasına bakınız.
"""
import csv
import itertools
import math
import random
from pathlib import Path

# Birimler: mm, MPa=N/mm², kN; maliyet: varsayımsal para birimi (PB).
BOYUTLAR = (300, 350, 400, 450, 500, 550, 600)
ADETLER = (4, 8, 12)
CAPLAR = (16, 20, 24, 28)
SECENEKLER = (BOYUTLAR, BOYUTLAR, ADETLER, CAPLAR)
YUK_KN = 2000.0  # Yük katsayıları uygulanmış varsayımsal talep; öz ağırlık dahil.
UZUNLUK_M = 3.0  # Bu sürümde yalnızca miktar hesabında kullanılır.
FC, FY = 30.0, 420.0
BETON_BIRIM = 3000.0  # PB/m³, piyasa fiyatı değildir.
CELIK_BIRIM = 35.0  # PB/kg, piyasa fiyatı değildir.
RHO_MIN, RHO_MAX = 0.01, 0.04  # Bu ders probleminin sınırları.
PAS_PAYI, ETRIYE_CAP = 40.0, 8.0  # Dış etriye yüzüne kadar örtü.
MIN_NET_ARALIK = 40.0  # Ders varsayımı; tam detaylandırma kontrolü değildir.


def hesapla(x):
    """x=(b,h,n,çap); her aday için aynı hesap ve kısıtlar kullanılır."""
    b, h, n, cap = x
    ag = b * h
    ast = n * math.pi * cap**2 / 4
    rho = ast / ag
    # ACI tipi bağlı kolon eksenel kapasite üst sınırı; tam tasarım değildir.
    kapasite = 0.80 * 0.65 * (0.85 * FC * (ag - ast) + FY * ast) / 1000
    beton_m3 = (ag - ast) * 1e-6 * UZUNLUK_M
    celik_kg = ast * 1e-6 * UZUNLUK_M * 7850
    maliyet = beton_m3 * BETON_BIRIM + celik_kg * CELIK_BIRIM
    # Her yüzde eşit sayıda çubuk; köşeler iki yüzde ortaktır.
    # n=4,8,12 için bir yüzde sırasıyla 2,3,4 çubuk bulunur.
    aralik_adedi = n // 4
    merkez_ortusu = PAS_PAYI + ETRIYE_CAP + cap / 2
    net_aralik = min((b - 2 * merkez_ortusu) / aralik_adedi - cap,
                    (h - 2 * merkez_ortusu) / aralik_adedi - cap)
    gerekli_aralik = max(MIN_NET_ARALIK, cap)
    # Boyutsuz pozitif ihlaller: sıfır = bu modeldeki bütün kısıtlar sağlanıyor.
    ihlaller = (
        max(0.0, YUK_KN / kapasite - 1),
        max(0.0, RHO_MIN / rho - 1),
        max(0.0, rho / RHO_MAX - 1),
        max(0.0, (gerekli_aralik - net_aralik) / gerekli_aralik),
    )
    ihlal = sum(ihlaller)
    return dict(b_mm=b, h_mm=h, adet=n, cap_mm=cap, As_mm2=ast,
                donati_orani=rho, kapasite_kN=kapasite,
                net_aralik_mm=net_aralik, beton_m3=beton_m3,
                celik_kg=celik_kg, maliyet_PB=maliyet, ihlal=ihlal,
                uygun=ihlal <= 1e-12)


def siralama(x):
    """Uygunluk öncelikli seçim: ceza katsayısını ayarlamak gerekmez.

    Önce uygun adaylar, sonra bunların ucuz olanı tercih edilir.
    Uygunsuz adaylar toplam boyutsuz ihlale göre sıralanır.
    """
    r = hesapla(x)
    return (not r['uygun'], r['ihlal'], r['maliyet_PB'])


def rastgele_aday(rng):
    return tuple(rng.choice(s) for s in SECENEKLER)


def genetik_algoritma(seed, populasyon=50, nesiller=100):
    rng = random.Random(seed)
    toplum = [rastgele_aday(rng) for _ in range(populasyon)]
    gecmis = []
    for nesil in range(nesiller + 1):
        toplum.sort(key=siralama)
        en_iyi = hesapla(toplum[0])
        gecmis.append(dict(seed=seed, nesil=nesil,
                           en_iyi_uygun_maliyet_PB=(en_iyi['maliyet_PB']
                                                    if en_iyi['uygun'] else ''),
                           en_iyi_ihlal=en_iyi['ihlal']))
        if nesil == nesiller:
            break
        # Elitizm: en iyi iki aday bir sonraki nesilde korunur.
        yeni = toplum[:2]
        while len(yeni) < populasyon:
            # Turnuva seçimi: üç rastgele adaydan en iyisini ebeveyn yap.
            anne = min(rng.sample(toplum, 3), key=siralama)
            baba = min(rng.sample(toplum, 3), key=siralama)
            # Üniform çaprazlama ve her gen için %15 mutasyon.
            cocuk = [rng.choice((a, b)) for a, b in zip(anne, baba)]
            for i, secenek in enumerate(SECENEKLER):
                if rng.random() < 0.15:
                    cocuk[i] = rng.choice(secenek)
            yeni.append(tuple(cocuk))
        toplum = yeni
    return toplum[0], gecmis


def csv_yaz(yol, satirlar):
    with yol.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(satirlar[0]))
        writer.writeheader()
        writer.writerows(satirlar)


def main():
    klasor = Path(__file__).resolve().parent
    adaylar = list(itertools.product(*SECENEKLER))
    uygunlar = [x for x in adaylar if hesapla(x)['uygun']]
    if not uygunlar:
        raise SystemExit('Tanımlı seçeneklerde uygun çözüm yok. Sınırları inceleyin.')
    kesin = min(uygunlar, key=lambda x: hesapla(x)['maliyet_PB'])
    referans = hesapla(kesin)
    sonuclar, gecmisler = [], []
    for seed in range(10):
        aday, gecmis = genetik_algoritma(seed)
        r = hesapla(aday)
        fark = (100 * (r['maliyet_PB'] / referans['maliyet_PB'] - 1)
                if r['uygun'] else None)
        sonuclar.append(dict(seed=seed, **r, optimumdan_fark_yuzde=fark))
        gecmisler.extend(gecmis)
    csv_yaz(klasor / 'tum_adaylar.csv', [hesapla(x) for x in adaylar])
    csv_yaz(klasor / 'ga_sonuclari.csv', sonuclar)
    csv_yaz(klasor / 'yakinsama.csv', gecmisler)
    basari = sum(r['uygun'] and abs(r['optimumdan_fark_yuzde']) < 1e-8
                 for r in sonuclar)
    print('EĞİTİM MODELİ — gerçek yapı tasarımı için kullanılamaz.')
    print(f'Aday sayısı: {len(adaylar)}, uygun aday: {len(uygunlar)}')
    print(f'Tam tarama optimumu: {kesin[0]} x {kesin[1]} mm, {kesin[2]}Ø{kesin[3]}')
    for anahtar in ('As_mm2', 'donati_orani', 'kapasite_kN', 'net_aralik_mm',
                    'beton_m3', 'celik_kg', 'maliyet_PB'):
        print(f'  {anahtar}: {referans[anahtar]:.6f}')
    print(f'GA, 10 bağımsız tohumun {basari} tanesinde tam tarama maliyetine ulaştı.')
    print('CSV dosyaları:', klasor)


if __name__ == '__main__':
    main()
