# Ders 02 — Karınca kolonisi ile betonarme kiriş optimizasyonu

Bu uygulama yapı tasarımında meta-sezgisel optimizasyon dersine yönelik bir
örnektir. Python'da her karınca bir kesit ve alt donatı seçer; iyi seçimlerin
feromonları artar. Amaç, tanımlı eğilme ve yerleşim koşulları altında örnek
malzeme maliyetini azaltmaktır.

**Kapsam:** Tek açıklıklı basit mesnetli kirişin pozitif moment kesiti; tek
sıra çekme donatısı; normal ağırlıklı beton. ACI tipi eşdeğer dikdörtgen basınç
bloğu ve çekme kontrollü kesit yaklaşımı kullanılır. TS 500/TBDY'ye göre tam
proje hesabı değildir. Sonuç bir uygulama/donatı projesi olarak kullanılamaz.

## 1. Hızlı başlangıç

ZIP dosyasını bir klasöre çıkarın. Python 3.9 veya üstüyle:

```bash
python aco_kiris.py
```

Ana hesap için ek kütüphane gerekmez. Hazır PNG ve sonuçlar pakette bulunur.
Grafikleri yeni sonuçlarınızla tekrar oluşturmak isterseniz:

```bash
python -m pip install matplotlib
python grafikleri_ciz.py
```

Hesap kontrolleri:

```bash
python -m unittest test_hesap.py -v
```

Komutları ZIP'in içindeki `02-ant-colony-beam` klasöründe çalıştırın. Program çıktıları
`sonuclar` klasöründeki aynı adlı dosyaların üzerine yazar. Farklı deneyleri
ayrı klasörlerde saklayın. Parametre değişikliğinden sonra grafikleri yeniden
çizin; aksi halde PNG dosyaları önceki deneyi gösterir.

## 2. Tasarım problemi

| Bilgi | Değer |
|---|---|
| Açıklık L | 6 m |
| Katsayılı dış yayılı yük | 30 kN/m; kiriş öz ağırlığı hariç |
| Öz ağırlık yaklaşımı | 25 kN/m³ × brüt kesit alanı |
| Öz ağırlık yük çarpanı | 1,2; ders varsayımı, yük birleşimi tasarımı değildir |
| Beton fc' | 30 MPa |
| Donatı fy / Es | 420 / 200.000 MPa |
| Pas payı | Dış etriye yüzüne 35 mm |
| Etriye çapı | 8 mm, sadece geometrik yer ayırma |
| En büyük agrega | 20 mm |
| Beton birim maliyeti | 3.000 PB/m³ |
| Çelik birim maliyeti | 35 PB/kg |

PB varsayımsal para birimidir; fiyatlar piyasa araştırması değildir.

Tasarım vektörü x=(b,h,n,çap):

- b: 250, 300, 350, 400, 450 mm.
- h: 350, 400, 450, 500, 550, 600, 650, 700 mm.
- n: 2, 3, 4, 5, 6 adet alt donatı.
- Çap: 12, 16, 20, 24, 28 mm.

Toplam 5×8×5×5 = 1.000 kombinasyon vardır. Donatı bir sırada ve eşit net
aralıklarla yerleştirilir. Boyutlar ve çaplar bu dersin seçenekleridir;
standartlara veya stok bulunabilirliğine dair genel kabul değildir.

## 3. Hesap mantığı

İç hesaplarda uzunluk mm, gerilme MPa=N/mm², moment kNm'dir.

1. Donatı alanı: As = n π çap² / 4.
2. Faydalı yükseklik: d = h − pas payı − etriye çapı − çap/2.
3. Eşdeğer basınç bloğu: a = As fy / (0,85 fc' b).
4. beta1 = max(0,65; min(0,85; 0,85 − 0,05(fc'−28)/7)); c=a/beta1.
5. Çekme şekil değiştirmesi: epsilon_t = 0,003(d−c)/c.
6. Bu modelde kabul: epsilon_t ≥ fy/Es + 0,003 = 0,0051.
7. Bu koşul sağlanırsa M_model = 0,90 As fy (d−a/2) / 10^6.
8. Minimum alan: As_min = max(0,25 sqrt(fc')/fy; 1,4/fy) b d.

Bu formüller çekme çeliğinin akması varsayımıyla başlar. 6. koşul sağlanmayan
adaylar reddedilir; onlar için kapasite sütunu boş bırakılır. Çekme kontrollü
olmayan kesitlere otomatik olarak 0,90 katsayısı uygulanıp uygun denmez.

Yerleşim için:

net_aralık = [b − 2(pas payı + etriye çapı) − n çap] / (n−1)

gerekli_aralık = max(25 mm; çap; 4 agrega / 3)

Yük ve moment her aday için yeniden hesaplanır:

w = dış_yük + 1,2 × 25 × b h × 10^-6  (kN/m)

Mu = w L² / 8  (kNm)

Bu nedenle daha büyük kesitin moment talebi de biraz daha yüksektir.

Maliyet:

Vb = (bh − As) × 10^-6 × L  (m³)

ms = As × 10^-6 × L × 7850  (kg)

C = 3000 Vb + 35 ms  (PB)

Yalnızca net beton ve düz alt donatı miktarı hesaplanır. Üst/montaj donatısı,
etriye miktarı, kanca, ankraj, bindirme, fire, işçilik ve kalıp maliyeti yoktur.
Etriye çizgisi yalnızca yerleşim sınırını gösterir; çap ve aralık tasarlanmaz.
Kesme, sehim, çatlak, deprem, burulma, yangın, dayanıklılık ve tam donatı
ayrıntıları kontrol edilmez. Kiriş boyu bu örnekte moment ve miktar hesabına
girer; sehim açısından yeterlilik anlamına gelmez.

## 4. Karınca bir çözümü nasıl oluşturur?

Örnek yol: 300 mm genişlik → 500 mm yükseklik → 4 donatı → 20 mm çap.
Bu yol, 300×500 mm ve 4Ø20 alt donatılı tek bir aday üretir.

Her seçenek başlangıçta eşit feromona (tau=1) sahiptir. Bir aşamadaki m
seçenekten j seçeneğinin olasılığı:

p_j = 0,90 × tau_j^alpha / sum(tau_k^alpha) + 0,10 / m

alpha=1'dir. Son terim keşif payıdır; zayıf feromonlu bir seçenek tamamen
unutulmaz. Sezgisel bilgi eta=1 seçilmiştir; ayrı bir beta ayarı kullanılmaz.
Bu bir **düğüm feromonlu ayrık ACO öğretim varyantıdır**; başka ACO
varyantları farklı güncelleme veya geçiş kuralları kullanabilir.

Bir iterasyon:

1. 30 karınca bağımsız olarak dört seçim yapar.
2. Kesit hesaplanır ve kısıt ihlalleri bulunur.
3. Feromonun %20'si buharlaştırılır.
4. En iyi beş farklı aday, sıralarına göre ödüllendirilir.
5. Şimdiye kadarki en iyi uygun adaya küçük ek ödül verilir.
6. Feromon [0,05;20] aralığında tutulur.

Bu işlemler 60 iterasyon tekrarlanır. Genetik algoritmadaki ebeveyn,
çaprazlama ve mutasyon işlemleri burada yoktur.

### Uygunluk ve feromon ödülü

Uygun aday her zaman uygunsuzdan önce gelir. Uygunlar maliyete göre;
uygunsuzlar boyutsuz ihlal toplamına göre sıralanır. İhlaller:

- moment: max(0,(Mu−M_deneme)/Mu)
- minimum donatı: max(0,(As_min−As)/As_min)
- süneklik: max(0,(epsilon_sınır−epsilon_t)/epsilon_sınır)
- yerleşim: max(0,(gerekli_aralık−net_aralık)/gerekli_aralık)

M_deneme, akma varsayımıyla hesaplanan deneme momentidir. Çekme kontrollü
olmayan adayın değerlendirmesi için bir arama sinyali sağlar; o adaya geçerli
bir kapasite atfetmez. Sünekliğin sağlanmaması zaten adayı uygunsuz yapar.

En iyi beş farklı adaydan sırası r olan uygun aday 1/r feromon ekler.
Uygunsuz adaya 0,1/[r(1+toplam_ihlal)] eklenir. Şimdiye kadarki en iyi uygun
aday ayrıca 0,5 ekler. Her ödül o adayın seçtiği dört seçeneğe uygulanır.

## 5. Tam taramayla doğrulama

Önce ACO çalıştırılır; sonra tüm 1.000 aday tek tek hesaplanır. ACO,
referans optimumu arama sırasında bilmez. Aynı hesap fonksiyonu iki yöntemde
de kullanılır; ek bağımsız sayısal örnek ve hata durumları test dosyasındadır.

Her ACO koşusu 30×60=1.800 aday değerlendirmesi yapar; tekrarlar bu bütçeye
dahildir. 10 koşu toplam 18.000 değerlendirmedir. Tam tarama 1.000
kombinasyonu hesaplar. **Bu küçük problemde ACO'nun daha hızlı veya daha
az hesap yaptığı iddia edilmez.** Amaç algoritmayı anlaşılır bir problemde
öğrenmek ve sonucunu doğrulamaktır. Büyük ve pahalı modellerde karşılaştırma
aynı değerlendirme bütçesiyle ayrıca yapılmalıdır.

Varsayılan çalıştırmanın sonuçları:

| Çıktı | Sonuç |
|---|---:|
| Tüm adaylar | 1.000 |
| Model koşullarını sağlayanlar | 385 |
| Ayrık modelin optimum kesiti | 250×550 mm |
| Alt donatı | 2Ø24 |
| Maliyet | 3.950,24 PB |
| Moment talebi | 153,5625 kNm |
| Model kapasitesi | 159,0998 kNm |
| Optimum maliyete ulaşan bağımsız koşu | 10/10 |

Bu sonuç tanımlı aralıklar ve model içindir; küresel optimum garantisi
meta-sezgisel algoritmadan değil, bu sonlu kümenin tamamının taranmasından
gelir. Başka yük ve ayarlar için 10/10 başarı garanti değildir. Uygun çözüm
yoksa program bunu bildirir; uygunsuz adayı çözüm diye sunmaz.

## 6. Dosyalar

| Dosya | İşlev |
|---|---|
| aco_kiris.py | Kesit hesabı, ACO ve tam tarama |
| grafikleri_ciz.py | PNG görsellerini yeniden üretme |
| test_hesap.py | Altı hesap/algoritma kontrolü |
| sonuclar/tum_adaylar.csv | 1.000 adayın koşulları ve maliyetleri |
| sonuclar/aco_kosular.csv | Her tohumun sonucu ve optimumdan farkı |
| sonuclar/yakinsama.csv | Her iterasyonun en iyi uygun maliyeti |
| sonuclar/ozet.json | Girdiler, ayarlar, referans ve son feromonlar |
| sonuclar/ders_ozeti.png | Kesit ve 10 koşunun yakınsama grafiği |
| sonuclar/feromon_olasiliklari.png | İlk koşunun son seçim olasılıkları |
| SONUC_KONTROLLERI.md | Optimum adayın sayısal kısıt kontrolleri |

## 7. Ders alıştırmaları

Yükün etkisi:

```bash
python aco_kiris.py --yuk 40
python grafikleri_ciz.py
```

Daha düşük arama bütçesi:

```bash
python aco_kiris.py --karinca 10 --iterasyon 15 --kosu 20
```

Sorular:

1. Yük artınca kesit ve donatı nasıl değişiyor?
2. Bütçe azalınca optimuma ulaşan koşu oranı nasıl değişiyor?
3. `aco()` içindeki buharlaşmayı 0,20 yerine 0,50 yapmak neyi değiştiriyor?
4. Beton/çelik maliyet oranı değişince tercih edilen tasarım değişiyor mu?
5. Keşif payı sıfırlanırsa sonuçların farklı başlangıçlara duyarlılığı artıyor mu?

Her deneyde tek parametreyi değiştirin. Başarı oranı, ortalama optimumdan
fark ve değerlendirme sayısını birlikte yorumlayın. Yalnızca en iyi koşuyu
raporlamak yerine bütün koşuları kullanın.

## 8. Hesap kaynakları

- Mento geliştirici dokümantasyonu, “Beam — ACI 318-19”, eşdeğer basınç bloğu,
  tek donatılı kesit, minimum donatı ve çekme kontrollü kesit ifadeleri:
  https://mento-docs.readthedocs.io/en/latest/theory/beam_aci_318_19.html
- StructurePoint, spColumn teknik el kitabı, ACI 318-19 şekil değiştirmeye
  bağlı dayanım azaltma katsayıları:
  https://structurepoint.org/pdfs/manuals/spColumn/spColumn%20manual%20v10.20.pdf

Kaynaklar 26 Ekim 2026 tarihinde kontrol edildi. Bunlar kullanılan hesap
modelinin arka planıdır; yazılım bir standardın bütün hükümlerini uygulamaz.

## 9. Koleksiyonun devamı

Ders 01: Genetik algoritma + betonarme kolon (önceki paket).
Ders 02: Karınca kolonisi + betonarme kiriş (bu paket).
Sonraki önerilen çalışma: PSO + düzlem kafes sistemde minimum kütle;
daha sonra DE ve benzetimli tavlama. Bunlar bu pakette henüz uygulanmadı.
