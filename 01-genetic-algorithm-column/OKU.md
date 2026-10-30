# Betonarme kolon optimizasyonu — ders örneği 1

Amaç: Genetik algoritmayı, betonarme kesit seçimi üzerinden öğrenmek.
Bu dosyalar bir proje hesabı değildir. TS 500/TBDY uygunluğu iddia edilmez.

## Çalıştırma

Python 3.9 veya üstü yeterlidir; ek kütüphane gerekmez.
ZIP'i çıkarın, dosyanın bulunduğu klasörde terminal açın:

```bash
python kolon_optimizasyonu.py
```

Program aynı klasörde üç CSV dosyası üretir; tekrar çalıştırma bunların
üzerine yazar. Değişikliklerinizi başka klasörde saklayabilirsiniz.

## Problem tanımı

- Eksenel basınç talebi: 2000 kN. Bu, yük katsayıları uygulanmış ve öz ağırlık
  dahil kabul edilmiş varsayımsal toplam taleptir. Yük birleşimi üretilmez.
- Beton basınç dayanımı fc'=30 MPa; çelik akma dayanımı fy=420 MPa.
- Kolon uzunluğu: 3 m; yalnızca malzeme miktarı hesabında kullanılır.
- Kısa kolon kabulü yapılır fakat narinlik kontrol edilmez.
- b,h = 300,350,400,450,500,550,600 mm.
- Boyuna donatı adedi n = 4,8,12; çap d = 16,20,24,28 mm.
- 7×7×3×4 = 588 aday. b/h yer değiştirmiş kesitler ayrı adaydır;
  bu eksenel modelde eşdeğer sonuç verirler.
- Donatı oranı sınırı %1–%4: bu problem için seçilmiş sınırlar.
- Dış etriye yüzüne pas payı 40 mm, etriye çapı 8 mm kabul edilir.
- Donatılar çevreye simetrik, her yüzde eşit adette yerleştirilir.
  n=4/8/12 için her yüzde köşeler dahil 2/3/4 çubuk bulunur.
- Komşu çubukların net açıklığı en az max(40 mm, donatı çapı) seçilir.
  Bu, eğitim amaçlı geometrik bir filtredir; tam detaylandırma değildir.

## Hesap modeli ve birimler

Ag = b h (mm²)

As = n π d² / 4 (mm²)

rho = As / Ag

P0 = 0.85 fc' (Ag-As) + fy As (N)

N_model = 0.80 × 0.65 × P0 / 1000 (kN)

Buradaki nominal eksenel basınç ifadesi ve kapasite katsayıları, ACI tipi
etriyeli kolon eksenel kapasite üst sınırı yaklaşımına dayanır. 0.85 beton
basınç katsayısı, 0.65 dayanım azaltma katsayısı ve 0.80 eksenel üst sınır
çarpanıdır. Bunlar TS 500 katsayıları olarak yorumlanmamalıdır. Bu tek
ifadenin sağlanması gerçek bir kolonun güvenli olduğunu göstermez.

Kaynak: StructurePoint, Tied Reinforced Concrete Column Design Strength,
ACI 318-19, 2022:
https://structurepoint.org/publication/pdf/Interaction-Diagram-Tied-Reinforced-Concrete-Column-Design-Strength-ACI-318-19.pdf

Vb = (Ag-As) × 10^-6 × L (m³)

ms = As × 10^-6 × L × 7850 (kg)

C = 3000 Vb + 35 ms (varsayımsal para birimi, PB)

3000 PB/m³ ve 35 PB/kg öğretim için seçilmiştir; güncel piyasa fiyatları
değildir. Maliyet yalnızca net beton ve düz boyuna donatı içindir.
Etriye/çiroz miktarı, kanca, bindirme, ankraj, fire, kalıp ve işçilik dahil
değildir. Etriye çapı sadece boyuna donatı yerleşim geometrisinde kullanılır.

Kısıtlar: N_model >= 2000 kN, 0.01 <= rho <= 0.04 ve net açıklık sınırı.
Moment, kesme, minimum dışmerkezlik, deprem, sargılama, donatıların yanal
tutulması, yangın, dayanıklılık ve ikinci mertebe etkileri kontrol edilmez.

## Genetik algoritmanın mantığı

Kromozom: (b,h,n,d). Başlangıçta 50 rastgele aday üretilir.
Üç adaylı turnuva ile iki ebeveyn seçilir. Her gen iki ebeveynden birinden
alınır (üniform çaprazlama). Her gen %15 olasılıkla kendi seçenek listesinden
yeniden seçilir (mutasyon). En iyi iki aday değişmeden korunur (elitizm).
100 nesil boyunca işlem tekrarlanır. Nesil 0 başlangıç popülasyonudur.

Bu sürümde keyfi bir ceza katsayısı yerine uygunluk öncelikli sıralama vardır:
1. Uygun tasarım, uygun olmayan tasarımdan daima üstündür.
2. Uygunlar arasında maliyeti düşük olan tercih edilir.
3. Uygun olmayanlarda toplam boyutsuz kısıt ihlali küçük olan tercih edilir.

Kapasite ihlali max(0,2000/N_model-1), alt donatı oranı ihlali
max(0,0.01/rho-1), üst donatı oranı ihlali max(0,rho/0.04-1),
açıklık ihlali max(0,(gerekli-mevcut)/gerekli) olarak hesaplanır.

Genetik algoritmaya tam tarama sonucu verilmez. Karşılaştırma yalnızca
arama tamamlandıktan sonra yapılır. 0–9 rastgele tohumlarıyla 10 koşu yapılır.

## Doğrulanmış örnek çıktı

588 adayın 328'i model kısıtlarını sağlar. Ayrık seçenek kümesinin en düşük
maliyeti 2526.325906 PB'dir. Bir optimum 300×450 mm, 8Ø16'dır; 450×300 mm
eşdeğerdir. As=1608.495439 mm², oran=%1.1915, N_model=2120.066754 kN,
minimum net açıklık=78 mm, net beton=0.400175 m³, boyuna çelik=37.880068 kg.
10 koşunun 10'u aynı optimum maliyete ulaşmıştır. Bu, başka yük ve seçenekler
için garanti değildir. “Optimum” yalnızca tanımlı ayrık model için geçerlidir.

Bu küçük problemde tam tarama daha doğrudan bir yöntemdir. Genetik algoritma
burada öğrenmek ve doğrulamak için kullanılır; hız üstünlüğü iddia edilmez.

## Çıktılar ve alıştırmalar

- tum_adaylar.csv: Tüm adaylar, maliyetler ve kısıt sonuçları.
- ga_sonuclari.csv: Her tohumun sonucu ve referans maliyetten yüzde farkı.
- yakinsama.csv: Her neslin en iyi uygun maliyeti; uygun aday yoksa boş.

Excel'de yakinsama.csv dosyasını açıp tek bir seed seçin; yatay eksene nesil,
düşey eksene en_iyi_uygun_maliyet_PB sütununu koyarak yakınsama grafiği çizin.

Alıştırmalar:
1. Yükü 2500 kN yapın; optimum kesit ve donatı nasıl değişiyor?
2. Çelik birim maliyetini 50 PB/kg yapın; sonuç ne oluyor?
3. Mutasyonu %15 yerine %1 yapın; 10 koşunun başarısını karşılaştırın.
4. Popülasyonu 50 yerine 10 yapın; erken yakınsamayı inceleyin.

Sonraki aşama: seçilen standardı belirleyip N–M etkileşimi ve gerçek
detaylandırma koşullarını eklemek; daha sonra aynı problemde PSO karşılaştırması.
