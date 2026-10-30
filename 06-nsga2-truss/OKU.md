# Ders 06 — NSGA-II ile kütle ve yer değiştirme optimizasyonu

Bu örnekte tek bir en iyi sayı aramak yerine iki amacı birlikte ele alıyoruz:
**daha az kütle** ve **daha az tepe yer değiştirmesi**. Sonuç, aralarında
tercih yapılabilecek Pareto tasarımlarıdır.

Eğitim modeli: lineer elastik, küçük yer değiştirmeli, mafsallı düzlem kafes.
Burkulma, düzlem dışı stabilite, öz ağırlık yükü, bağlantılar, yorulma, deprem
ve gerçek profil/standart tasarım kontrolleri dahil değildir. Kesit alanı
listesi bir üretici profili kataloğu değildir. Gerilme sınırını sağlamak,
gerçek bir basınç çubuğunun güvenli olduğunu tek başına göstermez.

## 1. Çalıştırma

Python 3.9 veya üstü gerekir. ZIP'i çıkarıp `06-nsga2-truss` klasöründe:

```bash
python -m pip install -r requirements.txt
python nsga2_kafes.py
python grafikleri_ciz.py
```

NumPy hesap, Matplotlib çizim için kullanılır. Hazır sonuçlar pakette vardır.
Test ortamı: NumPy 2.3.5 ve Matplotlib 3.10.8.

```bash
python -m unittest test_hesap.py -v
```

Program `sonuclar` altındaki aynı adlı dosyaları yeniler. Farklı deneyleri
ayrı klasörlerde saklayın. Girdi değişince grafik komutunu tekrar çalıştırın;
bu nottaki varsayılan sayılar ve eski PNG'ler kendiliğinden güncellenmez.

## 2. Sistem ve tasarım değişkenleri

| Düğüm | Koordinat (mm) | Mesnet / yük |
|---|---|---|
| D1 | (0,0) | x,y sabit |
| D2 | (4000,0) | y sabit, x serbest |
| D3 | (2000,3000) | 120 kN aşağı yönde |

E1=D1–D2, E2=D1–D3, E3=D2–D3. Elastisite modülü 200.000 MPa;
yoğunluk 7.850 kg/m³; örnek mutlak gerilme sınırı 160 MPa'dır.
Bu sınır belirli bir çelik standardının tüm hükümlerini temsil etmez.
Yük tek bir analiz yüküdür, yük birleşimleri oluşturulmaz.

Her çubuk için alan seçenekleri (mm²):

200, 300, 400, 500, 650, 800, 1000, 1250, 1500, 2000, 2500, 3000.

Tasarım vektörü x=[A1,A2,A3]. Kod her alanı 0–11 arası bir indeksle temsil
eder. Toplam 12³=1.728 kombinasyon vardır.

Önceki PSO örneğinden iki fark vardır: burada alanlar ayrık seçeneklerdir
ve tepe hareketi 2 mm ile sınırlandırılmaz. Yer değiştirme, azaltılacak ikinci
amaçtır. Şekildeki 2 mm çizgisi yalnız sonuçlardan seçim yapmak için sonradan
eklenmiş bir tercih örneğidir.

## 3. Analiz, amaçlar ve kısıt

Her adayda global rijitlik matrisi yeniden oluşturulur. Eksenel çubuk için
B=[−c,−s,c,s], k_e=(EA/L) B^T B. Mesnet koşullarından sonra K_ff u_f=F_f
çözülür. Eleman gerilmesi sigma=(E/L) B u_e; kuvvet N=A sigma'dır.
Reaksiyonlar K u−F ile hesaplanır.

İki minimizasyon amacı:

f1 = m = rho sum(A_i L_i)  [kg]

f2 = |uy_D3|  [mm]

Kısıt: her elemanda |sigma_i| ≤ 160 MPa. Alanlar zaten listeden seçilir.
Yatay yer değiştirme hesaplanır fakat amaç veya kısıt olarak kullanılmaz.
Kütle hesaplanırken bütün çubuklar dahil edilir; bu kütlenin yerçekimi yükü
analize eklenmez.

Boyutsuz kısıt ihlali V=sum(max(0,|sigma_i|/160−1)).
V ≤ 10^-10 olan aday, bu modelin gerilme koşulunu sağlar.

## 4. Pareto baskınlığı nedir?

A tasarımı, B'den hiçbir amaçta kötü değil ve en az bir amaçta daha iyiyse
A, B'ye baskındır. Örneğin 80 kg / 2,0 mm tasarımı, 90 kg / 2,2 mm tasarımına
baskındır. Ancak 80 kg / 2,0 mm ile 90 kg / 1,5 mm arasında baskınlık yoktur:
biri daha hafif, diğeri daha az şekil değiştirir.

Başka uygun bir tasarım tarafından baskılanmayan noktalar Pareto kümesidir.
Bu kümeden birini seçmek için ek mühendislik hedefi veya kullanıcı tercihi
gerekir. Algoritma tek başına bütün kullanıcılar için doğru tercihi belirlemez.

Eşit kütle/deplasman üreten farklı alan dizilimleri olabilir. Özellikle E2 ve
E3 alanlarının yer değiştirmesi bu simetrik yük altında aynı iki amacı verir.
Raporlarda **58 farklı amaç noktası** denir; bunun 58 benzersiz fiziksel
alan dizilimi anlamına geldiği iddia edilmez. Her amaç noktasının bir temsilci
alan dizilimi saklanır.

## 5. Uygulanan NSGA-II

100 aday ve 80 nesil; 0–9 tohumlarıyla 10 bağımsız koşu kullanılır. Başlangıç
100 farklı rastgele tasarımdan oluşur; tam tarama çözümleri başlangıca eklenmez.

Bir neslin adımları:

1. Uygunluk ve baskınlıkla adayları cephelere ayır: rank 0, rank 1, ...
2. Her cephede kalabalıklık uzaklığını hesapla.
3. İkili turnuvada önce küçük rank, sonra büyük kalabalıklık uzaklığını seç.
4. Seçilen iki ebeveynden üniform çaprazlamayla çocuk üret.
5. Her gen için 1/3 olasılıkla listedeki rastgele bir indekse mutasyon uygula.
6. Ebeveyn ve çocukları birleştir; cephe sırasıyla en iyi 100 adayı koru.
7. Son cephe tamamen sığmazsa kalabalıklık uzaklığı büyük adayları seç.

Bu, ayrık değişkenlere uyarlanmış NSGA-II'dir; SBX gibi sürekli değişken
çaprazlaması kullanılmaz. Aynı genotipin çoğalmasını önlemek için çocuklar
kendi içlerinde, birleşik popülasyon da çevresel seçimden önce tekilleştirilir.
Farklı genotiplerin eşdeğer amaçları popülasyonda bulunabilir; raporlanan
Pareto amaç noktaları ayrıca tekilleştirilir.

Kalabalıklık uzaklığı, her amaçtaki iki komşunun farkını o cephenin amaç
aralığına böler ve amaçlar üzerinden toplar. Uç noktalar sonsuz uzaklıkla
korunur. Bir amaç aralığı sıfırsa o amaç katkı vermez. Bu mekanizma çözüm
kümesinin tek bir bölgede toplanmasını azaltır.

Kısıtlı baskınlıkta uygun aday uygunsuzdan üstündür. İki uygunsuz aday
arasında daha az V tercih edilir. İki uygun aday iki amaçla karşılaştırılır.
Simetrik adaylarda son basamak farkları yanlış baskınlık üretmesin diye
amaçlar sıralama/eşleşmede sekiz ondalığa yuvarlanır. CSV'lerde ham hesap
sonuçları tutulur; bu sayısal eşitlik kuralı açıkça belirtilmiştir.

## 6. Referans ve başarı ölçümü

Bütün NSGA-II koşuları bittikten sonra farklı model ve önbellekle 1.728
kombinasyon taranır. 891 kombinasyon gerilme koşulunu sağlar. Bu uygunlar
arasından tam Pareto kümesi çıkarılır. NSGA-II bu referansı arama sırasında
bilmez; referans ve aşağıdaki ölçüler sonradan hesaplanır.

- Kapsama: bulunan gerçek Pareto amaç noktası sayısı / 58.
- Doğruluk: bulunan kümedeki gerçekten Pareto olan noktalar / bulunan nokta sayısı.
- Hypervolume oranı: bulunan kümenin baskın olduğu normalize amaç alanı /
  tam Pareto kümesinin aynı referansla baskın olduğu alan.

Hypervolume için her amaç tam Pareto kümesinin minimum ve aralığıyla
normalize edilir. Referans noktası (1,1;1,1), yani her eksende 1,1'dir.
İki boyutta burada hesaplanan nicelik alandır; adı geleneksel olarak
hypervolume'dur. Büyük değer daha iyidir. Oranın 1'e yakın olması tek başına
bütün noktaların bulunduğunu kanıtlamaz; bu yüzden kapsama ve doğruluk da
ayrıca raporlanır.

Ara nesillerin hypervolume ölçüleri de sonradan, aynı sabit referansla
hesaplanır. Algoritmanın seçiminde veya durdurulmasında bu ölçü kullanılmaz.

Her koşuda başlangıç dahil 100×81=8.100 aday değerlendirme isteği vardır.
Aynı tasarım tekrar gelirse çözüm önbellekten alınır. Varsayılan koşularda
1.500–1.528 benzersiz matris analizi yapılmıştır. Ön belleğe baştan katalog
sonuçları doldurulmaz ve koşular arasında paylaşılmaz.

Bu küçük problemde tam tarama zaten pratiktir. 10 koşunun toplamının tam
taramadan daha hızlı olduğu iddia edilmez. Buradaki amaç NSGA-II'yi öğrenmek
ve çıktısını doğrulayabilmektir. Sonuçlar yalnız tanımlı ayrık model için
geçerlidir; gerçek yapı tasarımı veya sürekli alan uzayı için optimum değildir.

## 7. Varsayılan sonuçlar ve seçim

On koşunun tamamı 58 Pareto amaç noktasını buldu. Kapsama ve doğruluk %100,
hypervolume oranı 1,0 oldu. Bu başka ayarlarda başarı garantisi değildir.

Temsilciler önceden belirlenen ilk koşunun (seed=0) tam taramayla doğrulanmış
Pareto noktalarından seçilmiştir; koşular arasında en iyi görünen koşu seçilmez.

| Tercih | A1 (mm²) | A2 (mm²) | A3 (mm²) | Kütle (kg) | Hareket (mm) |
|---|---:|---:|---:|---:|---:|
| En hafif | 300 | 500 | 500 | 37,723578 | 4,013700 |
| 2 mm hedefinde en hafif | 650 | 1000 | 1000 | 77,017155 | 1,972662 |
| En az yer değiştiren | 3000 | 3000 | 3000 | 264,021465 | 0,609691 |

2 mm, optimizasyonun koşulu değildir. Sonuçlar üretildikten sonra “tepe
hareketi en fazla 2 mm olsun” tercihiyle uygun Pareto adayları süzülür ve
bunların en hafifi seçilir. Bu seçim bütün durumlar için önerilen tek tasarım
olarak sunulmaz. Daha sıkı bir hedef daha fazla kütle gerektirebilir.

Önceki PSO örneğinde 2 mm sınırı altında yaklaşık 75,62 kg bulunmuştu.
Buradaki 77,02 kg ile fark, alanların bu kez ayrık bir listeden seçilmesinden
kaynaklanır. İki algoritmanın performansını yalnız bu sayılarla kıyaslamak
doğru değildir; tasarım uzayı ve amaç tanımı aynı değildir.

## 8. Dosyalar

| Dosya | İşlev |
|---|---|
| nsga2_kafes.py | Kafes analizi, NSGA-II, tam tarama, ölçüler |
| grafikleri_ciz.py | Pareto, temsilci sistem ve yakınsama çizimleri |
| test_hesap.py | Sekiz doğrulama testi |
| requirements.txt | NumPy ve Matplotlib bağımlılıkları |
| sonuclar/tum_kombinasyonlar.csv | 1.728 tasarımın kütle/hareket/gerilme sonuçları |
| sonuclar/tam_pareto.csv | Tam taramadan 58 farklı amaç noktasının temsilcileri |
| sonuclar/nsga2_pareto.csv | Her koşunun son popülasyonundaki Pareto noktaları |
| sonuclar/kosular.csv | Kapsama, doğruluk, hypervolume ve hesap bütçesi |
| sonuclar/yakinsama.csv | Nesil bazında küme büyüklüğü ve hypervolume |
| sonuclar/temsilci_tasarimlar.csv | Üç seçim senaryosunun tasarımları |
| sonuclar/ozet.json | Parametreler ve sonuç özeti |
| sonuclar/pareto_ozeti.png | İki amaç ve tercihlerin görsel karşılaştırması |
| sonuclar/temsilci_kafesler.png | Aynı sistemde üç farklı alan düzeni |
| sonuclar/yakinsama.png | On koşunun hypervolume gelişimi |
| SONUC_KONTROLLERI.md | Temsilcilerin sayısal kontrolleri |

## 9. Doğrulamalar ve deneyler

Sekiz test geçti: düğüm dengesi/enerji ve analitik kuvvetler; Pareto baskınlığı
ve eşdeğer amaçlar; kısıt önceliği; sıfır amaç aralığında kalabalıklık;
kapalı örnekte hypervolume; bağımsız iki boyutlu sıralı taramayla Pareto
referansı; sabit tohum ve hesap bütçesi; uygun çözüm bulunmaması.
Bunlar eksik yapısal tasarım kontrollerini tamamlamaz.

Daha az nesil/popülasyonla deney:

```bash
python nsga2_kafes.py --populasyon 40 --nesil 20 --kosu 10
python grafikleri_ciz.py
```

Yükü artırma:

```bash
python nsga2_kafes.py --yuk-kn 180
python grafikleri_ciz.py
```

Sorular: Uç noktalar korunuyor mu? Kapsama ile hypervolume aynı hızda mı
artıyor? 2 mm sınırı yerine 1,5 mm seçince hangi tasarım tercih edilir?
Bir amaç diğerine ağırlıklı toplamla bağlansaydı bütün ayrık Pareto noktalarını
bulmak mümkün olur muydu? Kütle ve hareketin birimleri farklıyken doğrudan
sayılarını toplamak neden keyfi bir tercih üretir?

Bir ayarı değiştirirken diğerlerini ve tohumları koruyun. Kalabalıklık,
çaprazlama ve mutasyonun etkilerini ayrı deneylerle inceleyin.

## 10. Kaynak ve koleksiyon

Deb, Pratap, Agarwal ve Meyarivan (2002), *A Fast and Elitist Multiobjective
Genetic Algorithm: NSGA-II*, IEEE Transactions on Evolutionary Computation,
6(2), 182–197. https://doi.org/10.1109/4235.996017

Kod, bu yöntemin ayrık kesit alanları için öğretim uygulamasıdır. Popülasyon
tekilleştirmesi, seçilen çaprazlama/mutasyon ve sayısal eşitlik kuralları yukarıda
belirtilmiştir. Kafes geometrisi ve alan listesi bu ders için oluşturulmuştur.

Tamamlanan altı örnek: GA–betonarme kolon, ACO–betonarme kiriş,
PSO–çelik kafes, DE–sürekli kiriş/donatı seçimi, SA–çelik çerçeve ve
NSGA-II–çok amaçlı kafes tasarımı.
