# Ders 03 — Parçacık sürüsü optimizasyonu ile çelik kafes tasarımı

Bu örnekte üç çubuklu düzlem kafesin kesit alanlarını PSO ile seçiyoruz.
Amaç, örnek gerilme ve tepe düşey yer değiştirme sınırları altında toplam
kütleyi azaltmak. Kesit alanları sürekli değişken; katalog profili seçilmiyor.

**Eğitim modeli:** Lineer elastik malzeme, küçük yer değiştirme, ideal mafsallı
birleşimler ve yalnız eksenel kuvvet taşıyan çubuklar. Basınç çubuklarının
burkulması, sistemin düzlem dışı stabilitesi, öz ağırlık, birleşimler, yorulma,
deprem ve gerçek profil/standart kontrolleri dahil değildir. Özellikle basınç
çubuklarında yalnız gerilme kontrolünün sağlanması gerçek tasarım yeterliliği
anlamına gelmez. Çıktı bir imalat veya uygulama projesi değildir.

## 1. Çalıştırma

Python 3.9 veya üstü gerekir. ZIP'i çıkarıp `03-particle-swarm-truss` klasöründe terminal açın:

```bash
python -m pip install -r requirements.txt
python pso_kafes.py
python grafikleri_ciz.py
```

Hesap NumPy, görseller Matplotlib kullanır. Hazır sonuçlar ve PNG görselleri
pakette bulunur. Kontrolleri çalıştırmak için:

```bash
python -m unittest test_hesap.py -v
```

NumPy 2.3.5 ve Matplotlib 3.10.8 ile kontrol edilmiştir. Program `sonuclar`
klasöründeki aynı adlı çıktıları yeniler. Farklı deneyleri ayrı klasörlerde
saklayın. Hesabı değiştirdikten sonra grafikleri yeniden üretin; eski PNG
ve bu nottaki varsayılan sonuçlar kendiliğinden güncellenmez.

## 2. Taşıyıcı sistem

| Düğüm | x (mm) | y (mm) | Mesnet / yük |
|---|---:|---:|---|
| D1 | 0 | 0 | x ve y sabit, mafsal |
| D2 | 4.000 | 0 | y sabit, x serbest, hareketli mesnet |
| D3 | 2.000 | 3.000 | 120 kN aşağı yönde yük |

| Eleman | Bağlantı | Uzunluk |
|---|---|---:|
| E1 | D1–D2, alt yatay çubuk | 4.000 mm |
| E2 | D1–D3, sol eğik çubuk | 3.605,5513 mm |
| E3 | D2–D3, sağ eğik çubuk | 3.605,5513 mm |

| Kabul | Değer |
|---|---:|
| Elastisite modülü E | 200.000 MPa |
| Yoğunluk | 7.850 kg/m³ = 7,85×10^-6 kg/mm³ |
| Örnek gerilme sınırı | Çekme/basınç için mutlak 160 MPa |
| D3 düşey hareket sınırı | 2 mm |
| Her elemanın alan sınırı | 200–3.000 mm² |

160 MPa ve 2 mm öğretim amaçlı problem sınırlarıdır; belirli bir çelik
sınıfı veya tasarım standardının zorunlu değerleri olarak kullanılmamalıdır.
Yük tek ve sabit bir analiz yüküdür; yük birleşimi oluşturulmaz. Öz ağırlığın
yük hesabına dahil edilmemesi, bağımsız analitik referansın basit kalmasını
sağlar. Kütle amaç fonksiyonunda ise tüm çubukların kütlesi hesaba katılır.

## 3. Optimizasyon modeli

Tasarım vektörü x = [A1,A2,A3].

Amaç:

m(A) = yoğunluk × sum(A_i L_i) → minimum

Kısıtlar:

- Her elemanda |sigma_i| ≤ 160 MPa.
- Tepe düğümünde |uy_D3| ≤ 2 mm.
- Her alan 200 ≤ A_i ≤ 3.000 mm².

Yatay hareketler de hesaplanır ancak bu ders modelinde sınırlandırılmaz.

Her aday alan vektörü için global rijitlik matrisi yeniden oluşturulur.
Çubuğun doğrultu kosinüsleri c,s ise B=[−c,−s,c,s] ve

k_i = (E A_i / L_i) B^T B.

Eleman katkıları birleştirilir; mesnet koşulları uygulanır; K_ff u_f=F_f
çözülür. Gerilme sigma_i=(E/L_i) B_i u; eksenel kuvvet N_i=A_i sigma_i.
Reaksiyonlar R=K u−F ile hesaplanır. Eğilme dönmesi serbestlikleri yoktur.
Bu bir 2B çubuk modelidir; çerçeve veya kiriş elemanı modeli değildir.

## 4. PSO nasıl çalışır?

Bir parçacık bir olası alan vektörüdür. Örneğin [600,1000,1100] mm².
Her parçacığın bir konumu, hızı ve bulduğu en iyi kişisel konumu vardır.
Sürünün bulduğu en iyi konum da saklanır.

v(t+1) = w v(t) + c1 r1 [pbest−x(t)] + c2 r2 [gbest−x(t)]

x(t+1) = x(t) + v(t+1)

- w: önceki hareketi sürdürme etkisi; 0,9'dan 0,4'e doğrusal azalır.
- c1=1,7: parçacığın kendi deneyiminden öğrenmesi.
- c2=1,7: sürünün en iyi deneyiminden öğrenmesi.
- r1,r2: her parçacık ve alan bileşeni için yeni bağımsız [0,1) rastgele sayılar.
- pbest: parçacığın şimdiye kadar bulduğu en iyi aday.
- gbest: bütün parçacıkların kişisel en iyileri arasındaki en iyi aday.

40 parçacık, 300 güncelleme iterasyonu, 10 bağımsız tohum kullanılır. İlk
parçacık [3000,3000,3000] mm² olarak başlar; diğerleri sınırlar içinde düzgün
rastgeledir. En büyük alanlar her yükte uygun olmayabilir; uygunluk hesaplanır.
Hız her bileşende ±560 mm²/iterasyonla sınırlanır. Alan sınırına taşan bileşen
sınıra kırpılır ve o bileşenin hızı sıfırlanır. Gerilme veya deplasman için
ayrıca bir tasarım onarımı yapılmaz; koşulları sağlamayan aday uygunsuz kalır.

Başlangıç değerlendirmesi dahil bir koşuda 40×(300+1)=12.040 aday hesabı
vardır. 10 koşu toplam 120.400 değerlendirmedir. Tekrarlanan adaylar da sayılır.
NumPy, bir sürünün rijitlik sistemlerini toplu çözer; kullanılan hesap modeli
tekil analizle aynıdır. İterasyon 0, başlangıç popülasyonunun sonucudur.

### Kısıtlar nasıl ele alınıyor?

Uygun aday uygunsuz adaydan önce gelir. Uygun adaylarda küçük kütle;
uygunsuz adaylarda küçük boyutsuz ihlal toplamı tercih edilir.

İhlal toplamı:

sum(max(0,|sigma_i|/sigma_limit−1)) + max(0,|uy|/u_limit−1)

+ sum(max(0,A_min/A_i−1)) + sum(max(0,A_i/A_max−1)).

Sayısal uygunluk toleransı bu boyutsuz toplam için 10^-10'dur. Bu nedenle
son basamakta çok küçük sayısal farklar görülebilir. Uygunluk, görüntülenen
iki ondalığa yuvarlanmış değerlerden değil tam hassasiyetle hesaplanır.

## 5. Bağımsız referans neden mümkün?

Bu üç çubuklu sistem izostatiktir; yalnız verilen tepe yükü altında eleman
kuvvetleri alanlardan bağımsız olarak düğüm dengesiyle bulunur:

N1 = +40 kN; N2 = N3 = −72,1110255 kN.

Pozitif çekme, negatif basınçtır. Aynı yük yönündeki tepe yer değiştirmesi
sanal iş/enerji bağıntısından:

|uy| = sum(q_i/A_i), q_i = N_i² L_i / (E P).

Kütle katsayıları w_i = yoğunluk × L_i olsun. Böylece problem doğrusal bir
amaç ve pozitif alanlarda konveks sum(q_i/A_i) kısıtı içerir. Gerilme sınırları
alt alan sınırına dönüştürülebilir:

alt_i = max(A_min, |N_i|/sigma_limit).

KKT koşuluyla referans alanlar:

A_i = clip(sqrt(lambda q_i / w_i), alt_i, A_max).

Alt alanların deplasmanı yeterliyse doğrudan seçilir. Değilse lambda,
yer değiştirme sınırını sağlayacak şekilde ikiye bölme yöntemiyle bulunur.
En büyük alanlar dahi yeterli değilse uygun çözüm yoktur.

Varsayılan örnekte alan alt/üst sınırları optimumda aktif değildir. Bu durumda
Cauchy–Schwarz eşitsizliği ayrıca şu kütle alt sınırını verir:

m_min = [sum(sqrt(w_i q_i))]^2 / u_limit.

Bulunan referans bu alt sınıra erişir. Bu nedenle burada yalnızca başka bir
optimizasyon çalıştırmasının en iyi sonucuna değil, modelin global optimumuna
karşılaştırma yapılır. Referans PSO'ya verilmez; bütün PSO koşuları bittikten
sonra hesaplanır. Genel bir hiperstatik kafeste bu bağımsız kuvvet ve basit
referans formülü geçerli değildir.

## 6. Varsayılan sonuçlar

| Eleman | Eşit alanlı karşılaştırma | Analitik optimum | En iyi PSO |
|---|---:|---:|---:|
| E1 alanı (mm²) | 1.500 | 566,666667 | 566,025770 |
| E2 alanı (mm²) | 1.500 | 1.021,572861 | 1.021,394268 |
| E3 alanı (mm²) | 1.500 | 1.021,572861 | 1.022,464088 |
| Toplam kütle (kg) | 132,010733 | 75,621667 | 75,621713 |
| Tepe düşey hareket büyüklüğü (mm) | 1,219381 | 2,000000 | 1,999999993 |

Kütle azalması yaklaşık %42,7'dir. Eşit alanlı karşılaştırma tasarımı modelin
koşullarını sağlar; PSO'nun başlangıç sürüsündeki bütün parçacıkların bu
alanlarla başladığı anlamına gelmez.

10 koşunun tamamı uygun sonuç vermiş ve referans kütleye %0,1 içinde
ulaşmıştır. Ortalama fark %0,001473; en kötü fark %0,004521; en iyi fark
%0,00006073'tür. En iyi koşu seed=5'tir. PSO alanlarının tam simetrik
olmaması sayısal aramanın sonucudur; bu yük/geometride analitik optimum
simetriktir. Sonucun yalnızca kütlesini değil kısıtlarını da kontrol edin.

Bu küçük problemde analitik hesap PSO'dan çok daha doğrudandır. PSO'nun
hız üstünlüğü iddia edilmez; amaç yöntemi öğrenmek ve doğrulanabilir bir
örnekte test etmektir. Daha büyük modellerde başarı ve süre, aynı analiz
bütçesi ve koşullarla karşılaştırılmalıdır. Başka ayarlarda %0,1 yakınlık veya
10/10 başarı garanti değildir.

## 7. Dosyalar

| Dosya | İçerik |
|---|---|
| pso_kafes.py | Matris analizi, PSO, bağımsız referans |
| grafikleri_ciz.py | Sistem, yakınsama ve deforme şekil çizimi |
| test_hesap.py | Yedi doğrulama testi |
| requirements.txt | NumPy ve Matplotlib bağımlılıkları |
| sonuclar/pso_kosular.csv | 10 koşunun alanları, kütleleri ve referans farkları |
| sonuclar/yakinsama.csv | İterasyon bazında en iyi uygun kütle |
| sonuclar/eleman_kontrolleri.csv | En iyi PSO tasarımının eleman kuvvet ve gerilmeleri |
| sonuclar/dugum_sonuclari.csv | En iyi PSO tasarımının yer değiştirme ve reaksiyonları |
| sonuclar/ozet.json | Problem, ayarlar ve sonuç özeti |
| sonuclar/ders_ozeti.png | Sistem çizimi ve yakınsama grafikleri |
| sonuclar/deforme_sekil.png | Kuvvetler ve 100 kat büyütülmüş yer değiştirme |
| SONUC_KONTROLLERI.md | En iyi PSO tasarımının kontrol tablosu |

## 8. Yapılan doğrulamalar

1. OpenSees'in yayımlanmış üç çubuklu örneğinin düğüm hareketi ve kuvvetleriyle
   karşılaştırma. Bu doğrulama sistemi ders üçgeninden farklıdır: dört düğüm,
   üç mesnet, kip/inç birimleri kullanır. NumPy analiz rutininin birimden
   bağımsız tutarlılığı da kontrol edilir.
2. Serbest düğümlerde denge, toplam reaksiyonlar ve enerji eşitliği.
3. İzostatik kuvvetlerin kesit alanından bağımsız olması; sanal iş hareketi.
4. Analitik optimumun Cauchy–Schwarz alt sınırına erişmesi.
5. Uygunsuz aday, pozitif olmayan alan ve mümkün olmayan yük durumu.
6. PSO'nun sabit tohumla tekrarlanması, en iyi uygun kütlenin artmaması ve
   değerlendirme bütçesinin doğru sayılması.
7. Toplu sürü analizi ile tekil matris analizinin aynı sonuç vermesi.

Yedi test başarıyla geçti. Bunlar yazılım/model doğrulamasıdır; eksik tasarım
kontrollerini tamamlamaz.

## 9. Ders alıştırmaları

Daha sıkı deplasman sınırı:

```bash
python pso_kafes.py --deplasman-mm 1.5
python grafikleri_ciz.py
```

Yükü artırma:

```bash
python pso_kafes.py --yuk-kn 180
python grafikleri_ciz.py
```

Daha küçük arama bütçesi:

```bash
python pso_kafes.py --parcacik 15 --iterasyon 50 --kosu 20
```

Sorular: Hangi kısıt aktif hale geliyor? Alanlar yükle nasıl değişiyor?
Daha az parçacıkla koşuların sonuçları daha çok farklılaşıyor mu? PSO'nun
c1 veya c2 katsayısını değiştirmek yakınsamayı nasıl etkiliyor?
Her deneyde tek parametreyi değiştirin; yalnız en iyi koşuyu değil bütün
koşuların ortalama/en kötü farklarını ve analiz sayılarını karşılaştırın.

## 10. Kaynaklar ve koleksiyon

- Kennedy ve Eberhart (1995), *Particle swarm optimization*, ICNN'95.
  DOI: https://doi.org/10.1109/ICNN.1995.488968
  Bu kod, atalet ağırlığı ve sınır işlemleri belirtilmiş bir öğretim
  uygulamasıdır; özgün makaledeki kodun birebir yeniden üretimi değildir.
- OpenSees, *EXAMPLE 1 — Truss Example*: bağımsız yapısal analiz doğrulamasının
  yayımlanmış hareket ve kuvvet sonuçları:
  https://opensees.berkeley.edu/OpenSees/manuals/ExamplesManual/HTML/854.htm

Kaynak kontrol tarihi: 26 Ekim 2026. Üçgen ders probleminin geometrisi ve KKT
referans hesabı bu paket için oluşturuldu; yayımlanmış örneğin aynısı değildir.

Ders 01: GA + betonarme kolon. Ders 02: ACO + betonarme kiriş.
Ders 03: PSO + çelik kafes (bu paket).
Sonraki önerilen çalışma: Diferansiyel evrim; bu pakete dahil değildir.
