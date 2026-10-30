# Ders 05 — Benzetimli tavlama ile çelik çerçevede profil seçimi

Amaç: tek katlı düzlem çerçevenin sol kolon, sağ kolon ve kiriş profillerini
seçerek kütleyi azaltmak. Benzetimli tavlama (Simulated Annealing, SA), daha
kötü bir adayı sıcaklığa bağlı olasılıkla kabul edebilir. Böylece arama yalnız
her adımda iyileşen seçeneklerle sınırlı kalmaz. Bulunan en iyi uygun tasarım
ayrı tutulur ve aramanın geçici kötüleşmesinden etkilenmez.

**Eğitim modeli:** Lineer elastik, küçük yer değiştirmeli, birinci mertebe
Euler–Bernoulli çerçeve hesabı. Burkulma, yerel levha burkulması, yanal
burulmalı burkulma, ikinci mertebe, kesme kapasitesi, kesme deformasyonu,
bağlantılar, deprem, yorulma ve tam çelik tasarım hükümleri kapsam dışındadır.
K1–K8 profilleri gerçek IPE/HEA/HEB ürünleri değildir. Bunlar boyutları
belirtilmiş ideal kaynaklı I kesitleridir; imalat uygunluğu iddia edilmez.
Sonuç bir uygulama veya imalat projesi olarak kullanılamaz.

## 1. Çalıştırma

Python 3.9 veya üstü; NumPy hesap, Matplotlib çizim için kullanılır.
ZIP'i çıkarın, `05-simulated-annealing-frame` klasöründe terminal açın:

```bash
python -m pip install -r requirements.txt
python sa_cerceve.py
python grafikleri_ciz.py
```

NumPy 2.3.5 ve Matplotlib 3.10.8 ile kontrol edildi. Hazır sonuçlar pakettedir.
Testler:

```bash
python -m unittest test_hesap.py -v
```

Program `sonuclar` altındaki aynı adlı dosyaları yeniler. Farklı deneyleri
ayrı klasörlerde tutun. Hesabı değiştirince grafikleri de yeniden çalıştırın;
bu nottaki varsayılan sayılar ve eski PNG'ler otomatik güncellenmez.

## 2. Sistem ve yükler

Açıklık 6 m, kat yüksekliği 3 m. Her iki taban ankastre. Kolon–kiriş
birleşimleri rijittir; eleman ucu mafsalı yoktur.

| Düğüm | x (mm) | y (mm) | Mesnet / yük |
|---|---:|---:|---|
| D1 | 0 | 0 | ux,uy,theta sabit |
| D2 | 6000 | 0 | ux,uy,theta sabit |
| D3 | 0 | 3000 | +10 kN yatay |
| D4 | 3000 | 3000 | −100 kN düşey |
| D5 | 6000 | 3000 | +10 kN yatay |

| Eleman | Bağlantı | Profil değişkeni |
|---|---|---|
| E1 | D1–D3 | Sol kolon |
| E2 | D2–D5 | Sağ kolon |
| E3 | D3–D4 | Kiriş |
| E4 | D4–D5 | Kiriş |

Kiriş orta yükü bir düğümde uygulanabilsin diye iki sonlu elemana ayrılır;
iki yarı aynı profili kullanır. Toplam tasarım değişkeni sayısı üçtür.
E=200.000 MPa, yoğunluk=7.850 kg/m³. Öz ağırlık yük olarak eklenmez;
amaç fonksiyonunda eleman kütleleri hesaplanır. Verilen yükler tek bir
varsayımsal yük durumudur; yük birleşimleri oluşturulmaz.

## 3. Öğretim kataloğu

h toplam yükseklik, b başlık genişliği, tw gövde kalınlığı, tf başlık
kalınlığıdır. Bütün boyutlar mm'dir. Kaynak dikişleri ve köşe yuvarlatmaları
hesaba katılmaz. Kesitler simetriktir, kuvvetli eksen etrafında eğilir.

| Profil | h | b | tw | tf |
|---|---:|---:|---:|---:|
| K1 | 180 | 100 | 6 | 8 |
| K2 | 220 | 110 | 6 | 9 |
| K3 | 260 | 130 | 7 | 10 |
| K4 | 300 | 150 | 8 | 12 |
| K5 | 340 | 170 | 8 | 14 |
| K6 | 380 | 190 | 9 | 16 |
| K7 | 420 | 210 | 10 | 18 |
| K8 | 460 | 230 | 10 | 20 |

A=2 b tf+(h−2tf)tw.

I=[b h³−(b−tw)(h−2tf)³]/12.

W=I/(h/2).

Her adayda A, I ve W birlikte değişir. Yalnız alanı değiştirip atalet momentini
sabit bırakmak gibi bir yaklaşım kullanılmaz. Hesaplanan özellikler
`profil_katalogu.csv` içinde bulunur. 8³=512 kombinasyon vardır.

## 4. Analiz ve model kısıtları

Her düğümde ux, uy ve theta serbestlikleri vardır. 2B elastik çerçeve elemanı
hem EA/L eksenel hem EI eğilme rijitliği içerir. Yerel matrisler dönüşüm
matrisiyle global sisteme taşınır; mesnet koşullarından sonra K_ff u_f=F_f
çözülür. Yerel eleman uç kuvvetleri k_local T u_e, reaksiyonlar K u−F'dir.

Kısıtlar:

1. Her elemanda |N|/A + max(|M_i|,|M_j|)/W ≤ 160 MPa.
2. D3,D4,D5 düğümlerindeki en büyük |ux| ≤ 10 mm.
3. |uy_D4 − (uy_D3+uy_D5)/2| ≤ 20 mm.

160 MPa, 10 mm ve 20 mm bu dersin problem sınırlarıdır; bir standardın bütün
koşullarını temsil etmez. Üçüncü kontrol yalnız kiriş orta düğümünün uçları
birleştiren doğruya göre hareketidir; kiriş üzerindeki sürekli maksimum
sehmin arandığı iddia edilmez.

Elemanlar arasında yayılı yük yoktur. Yükler düğümlerde uygulandığından
her elemanın momenti doğrusal, eksenel kuvveti sabittir; bu modelde uç
momentleriyle yapılan maksimum normal gerilme kontrolü yeterlidir.
|N|/A+|M|/W yalnız elastik normal gerilme hesabıdır, bir çelik beam-column
stabilite etkileşim denklemi değildir. Asimetrik yatay yük altında sol ve sağ
kolonların farklı seçilmesine izin verilir.

Amaç: m=sum(rho A_i L_i) → minimum. Çubuk uzunlukları sabit; toplam 12 m.

## 5. Benzetimli tavlama

Tasarım x=(sol kolon indeksi, sağ kolon indeksi, kiriş indeksi). Başlangıçta
bütün elemanlar K8'dir. Bu aday her yeni yük durumunda ayrıca kontrol edilir;
uygun olduğu varsayılmaz. Her adımda üç değişkenden biri eşit olasılıkla
seçilir ve profil kalan yedi seçenekten biriyle eşit olasılıkla değiştirilir.
Bu komşuluk simetriktir; ileri/geri öneri olasılıkları aynıdır.

Uygun aday için enerji E=m/m_max. m_max bütün elemanların K8 olduğu kütledir.
Uygunsuz aday için E=m/m_max+2+V; V boyutsuz pozitif ihlal toplamıdır:

V=sum(max(0,sigma_i/160−1)) + max(0,drift/10−1)
  + max(0,göreli_orta_sehim/20−1).

Kod sınır değerlerini `Problem` nesnesinden alır. Uygunluk toleransı V için
10^-10'dur. Uygun adayın enerjisi en fazla 1, uygunsuzunki 2'den büyüktür;
böylece uygunsuz hafif bir aday uygun bir tasarımdan daha düşük enerjili
olamaz. Yine de yüksek sıcaklıkta uygunsuz duruma geçiş mümkün olabilir.
Çıktı olarak yalnız en iyi UYGUN aday raporlanır.

Delta=E_yeni−E_mevcut:

- Delta ≤ 0 ise yeni aday kabul edilir.
- Delta > 0 ise kabul olasılığı exp(−Delta/T)'dir.

Bu T gerçek çelik sıcaklığı değildir, boyutsuz arama parametresidir.
Başlangıç T0=0,5; son Tson=0,002. 3.000 öneri boyunca geometrik soğuma:

T_k=T0 (Tson/T0)^[(k−1)/(adım_sayısı−1)].

Bir örnek: Delta=0,1 iken T=0,5 için kabul olasılığı yaklaşık %81,9;
T=0,01 için yaklaşık %0,00454'tür. Aramanın başında pahalı seçeneklere geçiş
kolay, sonunda zordur. Her değerlendirilen uygun aday en iyi kayıtla
karşılaştırılır; mevcut adayın geçici kötüleşmesi en iyi kaydı bozmaz.

`kotu_kabul` sayısı, enerji artmasına rağmen kabul edilen adımları gösterir.
Uygunlar arasında bu daha ağır tasarıma geçiştir; uygunsuz adaylar arasında
enerji ile kütle aynı sıralamayı vermek zorunda değildir.

## 6. Bağımsız koşular ve hesap bütçesi

0–9 tohumlarıyla 10 koşu yapılır. Aynı K8 başlangıcı kullanılır ama rastgele
komşular ve kabul kararları farklıdır. Her koşu başlangıç dahil 3.001 aday
isteği içerir. Tekrarlanan kombinasyonun sonucu önbellekten alınır; her
benzersiz kombinasyon için bir matris çözümü yapılır. Koşular arasında
önbellek paylaşılmaz. Varsayılan koşularda benzersiz analiz sayıları
388–414 arasındadır. Bütçe tabloları istek ve matris çözümü sayılarını ayırır.

Tam tarama bütün SA koşuları bittikten sonra yeni bir modelle yapılır;
512 kombinasyon ayrı ayrı çözülür. SA, bu taramanın sonuçlarına erişmez.
Tam tarama ile doğrulama, tanımlı katalogdaki global minimumu belirler;
sürekli kesit uzayında veya gerçek yapı tasarımında optimum iddia edilmez.
Bu küçük örnekte tam tarama zaten kolaydır; 10 SA koşusunun toplamının tam
taramadan daha hızlı olduğu iddia edilmez.

## 7. Varsayılan sonuçlar

| Çıktı | Değer |
|---|---:|
| Kombinasyon sayısı | 512 |
| Modelde uygun kombinasyon | 260 |
| Sol kolon | K1: 180×100×6×8 mm |
| Sağ kolon | K3: 260×130×7×10 mm |
| Kiriş | K5: 340×170×8×14 mm |
| Başlangıç kütlesi, K8/K8/K8 | 1.262,28 kg |
| En iyi kütle | 503,4048 kg |
| Başlangıca göre azalma | %60,1194 |
| En büyük normal gerilme | 154,05598 MPa |
| En büyük çatı düğümü yatay hareketi | 1,127061 mm |
| Kiriş göreli orta sehim | 10,070203 mm |
| Tam tarama minimumuna ulaşan koşu | 10/10 |

Bu başarı başka yük ve ayarlarda garanti değildir. Farklı kolon profilleri,
verilen tek yönlü yatay yük ve bu basitleştirilmiş modelin sonucudur. Ters
yönlü yatay yük, burkulma ve diğer yük birleşimleri eklenince değişebilir.

## 8. Dosyalar ve kontroller

| Dosya | İşlev |
|---|---|
| sa_cerceve.py | Katalog, çerçeve analizi, SA, tam tarama |
| grafikleri_ciz.py | Sistem/yakınsama ve tavlama mantığı grafikleri |
| test_hesap.py | Sekiz doğrulama testi |
| sonuclar/kosular.csv | Her koşunun sonucu, farkı ve hesap bütçesi |
| sonuclar/tavlama_izi.csv | Sıcaklık, kabul, mevcut ve en iyi durum |
| sonuclar/tum_kombinasyonlar.csv | 512 kombinasyonun sonuçları |
| sonuclar/profil_katalogu.csv | Boyutlar ve hesaplanan A,I,W |
| sonuclar/eleman_kontrolleri.csv | En iyi SA tasarımının eleman kontrolleri |
| sonuclar/ozet.json | Parametreler, referans, en iyi sonuç ve düğüm verileri |
| sonuclar/ders_ozeti.png | Çerçeve ve sonuç karşılaştırması |
| sonuclar/tavlama_mantigi.png | İlk koşuda sıcaklık ve kötü aday kabulü |
| SONUC_KONTROLLERI.md | Sayısal kontrol özeti |

Sekiz test geçti: konsolun eksenel ve eğilme kapalı çözümleri; döndürülmüş
konsol; global denge ve enerji; simetrik yük altında simetri; kesit özellikleri;
kabul olasılığı ve komşuluk; tam tarama/önbellek/tekrarlanabilirlik; uygun
çözüm bulunmaması. Testler kullanılan modeli doğrular, kapsam dışı tasarım
kontrollerini tamamlamaz.

## 9. Alıştırmalar

Yatay yükü artırın:

```bash
python sa_cerceve.py --yatay-kn 40
python grafikleri_ciz.py
```

Daha kısa arama:

```bash
python sa_cerceve.py --adim 300 --kosu 20
```

`tavlama()` fonksiyonunun T0 ve Tson parametrelerini değiştirerek daha hızlı
ve daha yavaş soğumayı karşılaştırın. Ana çağrıda parametreleri açıkça
verin. Aynı tohumları ve öneri bütçesini koruyun. Sorular:

1. Kötü aday kabulü sıfıra yaklaştırılırsa başarı oranı nasıl değişir?
2. En iyi uygun kayıt sabitken mevcut enerji neden yükseliyor?
3. Daha çok kabul, mutlaka daha iyi sonuç anlamına geliyor mu?
4. Katalog seçenek sayısı arttığında tam tarama ve SA nasıl ölçeklenir?

## 10. Kaynaklar ve koleksiyon

- Kirkpatrick, Gelatt ve Vecchi (1983), *Optimization by Simulated Annealing*:
  https://doi.org/10.1126/science.220.4598.671
- OpenSees, *Elastic Beam Column Element*: 2B elastik elemanda A,E,Iz ve
  koordinat dönüşümü parametrelerinin teknik arka planı:
  https://openseesdocumentation.readthedocs.io/en/latest/user/manual/model/elements/elasticBeamColumn.html

Kaynak kontrol tarihi: 26 Ekim 2026. Bu kod OpenSees'i çağırmaz; matris
analizi NumPy ile yazılmış ve analitik kontrollerle test edilmiştir. Ders
kataloğu bu paket için oluşturulmuştur, dış üretici verisi değildir.

Koleksiyon: GA–kolon → ACO–kiriş → PSO–kafes → DE–kiriş → SA–çerçeve.
Sonraki önerilen örnek NSGA-II ile kütle ve yer değiştirmeyi birlikte ele
alan çok amaçlı optimizasyondur; bu pakete dahil değildir.
