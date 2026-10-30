# Ders 04 — Diferansiyel evrim ile betonarme kiriş optimizasyonu

Bu örnek üç aşamalıdır: (1) sürekli boyut ve donatı alanı aramak,
(2) sonucu ölçü adımları ve donatı adet/çap seçeneklerine dönüştürmek,
(3) seçenekleri yeniden birlikte tarayarak yuvarlamanın maliyetini incelemek.

**Kapsam:** Tek açıklıklı basit mesnetli kirişin pozitif eğilme kesiti;
normal ağırlıklı beton ve tek sırada çekme donatısı. ACI tipi basınç bloğu,
minimum donatı ve çekme kontrollü kesit koşulları kullanılır. TS 500/TBDY'nin
tamamını uygulayan bir proje hesabı değildir. Kesme, sehim, çatlak, burulma,
deprem, ankraj, bindirme ve tam donatı detaylandırması kapsam dışındadır.
“Katalog adayı” yalnızca tanımlı seçenekler ve bu model koşulları bakımından
uygundur; doğrudan şantiyede uygulanabilecek tasarım anlamına gelmez.

## 1. Çalıştırma

Python 3.9 veya üstü gerekir. ZIP'i çıkarıp `04-differential-evolution-beam` klasöründe terminal açın:

```bash
python -m pip install -r requirements.txt
python de_kiris.py
python grafikleri_ciz.py
```

Ana hesap NumPy, çizimler Matplotlib kullanır. NumPy 2.3.5 ve Matplotlib
3.10.8 ortamında çalıştırıldı. Sonuçlar ve hazır PNG'ler pakette bulunur.
Testler:

```bash
python -m unittest test_hesap.py -v
```

Program `sonuclar` altındaki aynı adlı dosyaları yeniler. Her deneyi ayrı
klasörde tutun. Girdileri değiştirdiğinizde çizim komutunu tekrar çalıştırın;
PNG'ler ve bu nottaki varsayılan sonuçlar kendiliğinden güncellenmez.

## 2. Problem tanımı

| Girdi | Değer |
|---|---|
| Açıklık | 6 m |
| Katsayılı dış yayılı yük | 30 kN/m, öz ağırlık hariç |
| Öz ağırlık | 25 kN/m³ × brüt kesit; yük çarpanı 1,2 |
| Beton fc' | 30 MPa |
| Donatı fy / Es | 420 / 200.000 MPa |
| Beton maliyeti | 3.000 PB/m³ |
| Donatı maliyeti | 35 PB/kg |
| Çelik yoğunluğu | 7.850 kg/m³ |

PB varsayımsal para birimidir; güncel fiyat araştırması değildir. 1,2 yük
çarpanı bu dersin kabulüdür; tam bir yük birleşimi kontrolü yapılmaz.

DE tasarım vektörü x=[b,h,As]:

- Genişlik b: 250–450 mm, sürekli.
- Toplam yükseklik h: 350–700 mm, sürekli.
- Alt donatı alanı As: 200–4.000 mm², sürekli.

Sürekli modelde donatı adedi/çapı henüz bilinmez. Alt yüzden donatı ağırlık
merkezine uzaklık 60 mm kabul edilir: d=h−60. **Bu 60 mm pas payı değildir.**
Yerleşim kontrolü sürekli aşamada yapılmaz; donatı düzeni seçildiğinde yapılır.

Katalog aşaması:

- b: 250–450 mm, 25 mm adımlı (9 seçenek).
- h: 350–700 mm, 25 mm adımlı (15 seçenek).
- n: 2,3,4,5,6; çap: 12,16,20,24,28 mm.
- Dış etriye yüzüne örtü 35 mm; etriye çapı 8 mm; agrega 20 mm.
- Gerçek merkez örtüsü 35+8+çap/2; d=h−bu değer.
- Toplam 9×15×5×5=3.375 aday; 25 mm ölçü adımı öğretim tercihidir.

## 3. Hesap modeli

Birimler: mm, mm², MPa=N/mm², kNm, m³, kg.

As=nπçap²/4 ifadesi yalnız katalog aşamasında kullanılır. Sürekli aşamada As,
DE'nin üçüncü değişkenidir.

Eşdeğer beton bloğu:

a=As fy/(0,85 fc' b), c=a/beta1.

beta1=max(0,65; min(0,85; 0,85−0,05(fc'−28)/7)).

Çekme şekil değiştirmesi: epsilon_t=0,003(d−c)/c.

Çekme kontrollü kabul: epsilon_t ≥ fy/Es+0,003 = 0,0051.

Bu koşul sağlanırsa M_model=0,90 As fy(d−a/2)/10^6.

Minimum alan: As_min=max(0,25 sqrt(fc')/fy; 1,4/fy) b d.

Öz ağırlık kesit değiştikçe yeniden hesaplanır:

w=30+1,2×25×bh×10^-6; Mu=wL²/8.

Katalog için net çubuk aralığı:

net=[b−2(35+8)−n çap]/(n−1).

gerekli=max(25 mm; çap; 4×agrega/3).

Amaç fonksiyonu:

Vb=(bh−As)×10^-6×L; ms=As×10^-6×L×7850.

C=3000 Vb+35 ms → minimum.

Yalnız net beton ve düz alt donatı maliyeti vardır. Üst/montaj donatısı,
etriye miktarı, kanca, bindirme, ankraj, kalıp, işçilik ve fire dahil değildir.
Etriye çapı sadece yerleşim geometrisinde kullanılır; etriye tasarımı yapılmaz.

Kod önce akma varsayımıyla deneme momentini hesaplar. Çekme kontrollü olmayan
aday uygun kabul edilmez ve kapasite sütunu boş bırakılır. O adayın deneme
momenti yalnız kısıt ihlalinin arama sinyalinde kullanılır; geçerli kapasite
olarak sunulmaz.

## 4. DE/rand/1/bin algoritması

Her aday bir kiriş tasarımıdır. Kullanılan varyant:

- `rand`: donor tabanı rastgele bir adaydır.
- `1`: bir fark vektörü kullanılır.
- `bin`: bileşen bazında binom çaprazlama yapılır.

Hedef i için i'den farklı, birbirinden de farklı a,b,c adayları seçilir:

v=x_a+F(x_b−x_c).

F=0,7 farkın etkisini belirler. CR=0,9 ile her bileşen donor v'den alınır;
aksi halde hedef adayın bileşeni korunur. Rastgele bir bileşenin donordan
gelmesi zorunlu tutulur. Yeni aday hedefinden daha iyiyse yerini alır.

Değişkenlerin farklı birimleri olduğundan önce [0,1] aralığına normalize
edilir. Donor bu aralığı aşarsa sınıra kırpılır. Hesap için gerçek mm/mm²
birimlerine dönülür. Gerilme/kapasiteyi sağlamak için tasarımlar ayrıca
onarılmaz. Nesiller senkrondur: bütün donorlar önceki popülasyondan seçilir.

40 aday, 300 nesil ve 0–9 tohumlarıyla 10 bağımsız koşu kullanılır. Nesil 0
başlangıç popülasyonudur. Başlangıç tamamen rastgeledir; referans sonuçlar
başlangıca eklenmez. Her koşu 40×301=12.040 değerlendirme yapar.

### Kısıtlar ve seçim

Uygun aday uygunsuzdan önce gelir. Uygunlar maliyete; uygunsuzlar boyutsuz
pozitif kısıt ihlallerinin toplamına göre karşılaştırılır. Toplam şu terimleri
kapsar: moment açığı/Mu, minimum donatı açığı/As_min, şekil değiştirme
sınırı açığı/epsilon_min ve değişken sınırı ihlalleri/ilgili değişken aralığı.
Her terimin negatif değeri sıfır alınır.

Uygunluk toleransı 10^-10'dur. Varsayılan DE sonucu aktif moment sınırına
bu toleransla oturur: deneme kapasitesi talebin yaklaşık 1,5×10^-8 kNm altında
kalabilir. Bu son basamak farkı açıkça `ihlal` sütununda tutulur; gösterimdeki
yuvarlama ile uygunluk kontrolü yapılmaz.

## 5. Bağımsız sayısal referans

b ve h, 0,5 mm adımla taranır: 401×701=281.101 kesit noktası. Her b,h için
moment denkleminden gerekli As analitik olarak hesaplanır; minimum donatı ve
alan alt sınırı da dikkate alınır. Daha sonra bütün model koşulları kontrol
edilir. Maliyet, bu problemde sabit b,h için As ile arttığından en küçük uygun
As seçimi o kesit noktası için ekonomiktir.

Denklem: q As²−d As+k=0,
q=fy/(2×0,85 fc' b), k=Mu×10^6/(0,9 fy).

Sayısal olarak kararlı küçük kök:

As=2k/[d+sqrt(d²−4qk)].

Diskriminant negatifse tek donatılı aday mümkün değildir. Sürekli modelin
60 mm merkez örtüsü bu referansta da aynen kullanılır.

**Bu tarama sürekli global optimum ispatı değildir.** Alan analitik, boyutlar
ise ızgaralıdır. DE ızgara noktalarının arasında biraz daha iyi çözüm
bulabilir; bu nedenle referansa göre fark negatif çıkabilir. PSO örneğindeki
kapalı analitik optimumla aynı tür referans değildir. Referans, DE'nin bütün
koşuları bittikten sonra hesaplanır ve DE aramasına bilgi vermez.

## 6. Dönüşüm ve yeniden seçim

İlk dönüşüm kuralı bilerek basittir:

1. b ve h yukarı doğru 25 mm ölçü adımına yuvarlanır.
2. Yuvarlanan ölçü ve +25,+50 mm komşuları incelenir.
3. Donatı alanı DE'nin As değerinden küçük olmayacak şekilde n/çap seçilir.
4. Her adayın gerçek d değeri, öz ağırlığı, kapasitesi, minimum donatısı,
   sünekliği ve net aralığı yeniden hesaplanır.
5. Bu yerel adaylar arasından en ucuz uygun olan seçilir.

Varsayılan çözüm için 117 yerel aday incelenir. Bu kural düşük maliyet
GARANTİSİ vermez; önceki As hedefini korumak yüksek bir h seçildiğinde fazla
donatıya yol açabilir.

Ardından bütün 3.375 katalog adayı bağımsız olarak taranır. Burada As'nin
sürekli sonuçtan küçük olmasına izin verilir: değişen h ve gerçek d nedeniyle
daha az donatı yeterli olabilir. Yeterlilik yeniden hesapla belirlenir.
Bu son tarama tanımlı sonlu katalog içinde en ucuz uygun adayı verir.

Sürekli modelin d=h−60 kabulü ile katalog modelinin gerçek donatı merkezleri
farklıdır. Bu nedenle iki modelin amaç değerlerini aynı problemin kesin alt
ve üst sınırları gibi yorumlamayın. Aradaki maliyet değişiminde boyut/adet/çap
ayrıklaştırması kadar d varsayımının değişimi de etkilidir.

## 7. Varsayılan sonuçlar

| Aşama | Kesit (cm) | Donatı | Maliyet (PB) |
|---|---|---|---:|
| En iyi sürekli DE | 25,00×47,61095 | As=1.047,27765 mm² | 3.850,07907 |
| 0,5 mm sayısal referans | 25,00×47,60 | As=1.047,58003 mm² | 3.850,07924 |
| Yukarı yuvarlama/yerel seçim | 25×50 | 2Ø28 | 4.257,96779 |
| Bütün katalogda yeniden seçim | 25×52,5 | 3Ø20 | 3.899,21005 |

10 DE koşusunun tamamı uygun sonuç vermiş ve ızgara referansına %0,1 içinde
kalmıştır. Bu başka ayarlar için garanti değildir. Katalogda 1.329 uygun
aday bulunmuştur. Katalog taramasının sonucu, basit dönüşümden %8,43 daha
ucuzdur. Donatı/ölçü seçimini birlikte değerlendirmek bu örnekte faydalıdır.

Son katalog adayında moment talebi 152,71875 kNm, kapasite 157,09266 kNm,
net donatı aralığı 52 mm'dir. Tam kısıt tablosu `SONUC_KONTROLLERI.md` içindedir.

Önceki ACO örneğinde boyut adımı 50 mm idi; burada katalog 25 mm adımlıdır.
Sonuçların farklı olması, tek başına DE'nin ACO'dan daha iyi olduğunu göstermez.
Algoritma karşılaştırması için aynı tasarım alanı, aynı hesap modeli ve aynı
değerlendirme bütçesi kullanılmalıdır. Izgara/katalog taramalarının maliyeti
DE bütçesinden ayrı raporlanır; bu örnekte bir hız üstünlüğü iddia edilmez.

## 8. Dosyalar

| Dosya | İşlev |
|---|---|
| de_kiris.py | Kesit hesabı, DE, ızgara referansı ve donatı seçimi |
| grafikleri_ciz.py | Yakınsama, kesit ve kısıt görselleri |
| test_hesap.py | Yedi doğrulama testi |
| requirements.txt | NumPy ve Matplotlib |
| sonuclar/de_kosular.csv | Her koşunun tasarımı ve referanstan farkı |
| sonuclar/yakinsama.csv | Nesil bazında en iyi uygun maliyet |
| sonuclar/katalog_taramasi.csv | 3.375 adayın kontrolleri |
| sonuclar/donusum_adaylari.csv | Basit dönüşümde incelenen adaylar |
| sonuclar/ozet.json | Girdiler, ayarlar ve bütün aşamaların özeti |
| sonuclar/ders_ozeti.png | Üç aşamanın görsel karşılaştırması |
| sonuclar/kisit_kontrolleri.png | Son katalog adayının kısıt oranları |
| SONUC_KONTROLLERI.md | Sayısal kısıt tablosu |

## 9. Doğrulamalar ve alıştırmalar

Yedi test başarıyla geçti: bağımsız sayısal kesit hesabı; gerekli As ters
çözümü; süneklik/yerleşim ihlalleri; DE donor ayrıklığı ve zorunlu çaprazlama;
sabit tohumla tekrarlanabilirlik ve yakınsama; ızgara/katalog sonuçları;
yük değişimi ve uygun çözüm bulunmaması. Bunlar eksik tasarım kontrollerini
tamamlamaz; uygulanan modelin yazılım kontrolleridir.

Yük deneyi:

```bash
python de_kiris.py --yuk 40
python grafikleri_ciz.py
```

Daha düşük arama bütçesi:

```bash
python de_kiris.py --populasyon 15 --nesil 50 --kosu 20
```

Kodda `diferansiyel_evrim()` F ve CR parametrelerini alır. F=0,4/0,7/1,0 ve
CR=0,3/0,9 değerlerini aynı bütçe ve tohumlarla deneyin. Parametreyi ana
çağrıya ekleyerek bütün koşularda aynı seçimi uygulayın. Sadece en iyi koşuya
bakmayın; uygun koşu oranını, ortalama/en kötü maliyeti ve hesap sayısını
karşılaştırın. Katalog boyut adımını değiştirirken dönüşüm kuralını da aynı
adımla uyumlu güncelleyin; yalnız tarama aralıklarını değiştirmek yeterli değildir.

## 10. Kaynaklar

- Storn ve Price (1997), *Differential Evolution – A Simple and Efficient
  Heuristic for Global Optimization over Continuous Spaces*:
  https://doi.org/10.1023/A:1008202821328
- Mento, *Beam — ACI 318-19*: basınç bloğu, moment, minimum donatı ve gerekli
  donatı alanı ifadeleri:
  https://mento-docs.readthedocs.io/en/latest/theory/beam_aci_318_19.html
- StructurePoint, ACI 318-19 revizyonları: çekme kontrollü kiriş koşulu:
  https://structurepoint.org/pdfs/StructurePoint_Software_Impact_of_changes_from_ACI_318-14_to_ACI-318-19.pdf

Kaynak kontrol tarihi: 26 Ekim 2026. Kullanılan hesap, standardın sınırlı bir
kesit modelidir; tam standarda uygunluk sertifikası değildir.

Koleksiyon: GA–kolon → ACO–kiriş → PSO–kafes → DE–sürekli kiriş ve donatı seçimi.
Sonraki önerilen çalışma: benzetimli tavlama ile çelik çerçevede profil seçimi.
Bu sonraki örnek mevcut pakete dahil değildir.
