# Temsilci Pareto tasarımlarının model kontrolleri

Seçimler seed=0 kümesinden, tam tarama ile doğrulanarak alınmıştır.

| Tercih | Kütle (kg) | Hareket (mm) | E1 gerilme (MPa) | E2 gerilme (MPa) | E3 gerilme (MPa) |
|---|---:|---:|---:|---:|---:|
| En hafif | 37.723578 | 4.013700 | 133.333333 | -144.222051 | -144.222051 |
| 2 mm hedefinde en hafif | 77.017155 | 1.972662 | 61.538462 | -72.111026 | -72.111026 |
| En az yer değiştiren | 264.021465 | 0.609691 | 13.333333 | -24.037009 | -24.037009 |

Pozitif gerilme çekme, negatif gerilme basınçtır. Her üç tasarımda da
elemanların mutlak gerilmeleri 160 MPa sınırını sağlar. En hafif tasarım
2 mm hedefini sağlamaz; bu hedef zaten arama sırasında kısıt değildir.

Model izostatiktir: bütün alan düzenlerinde E1 çekme kuvveti 40 kN,
E2 ve E3 basınç kuvvetleri yaklaşık 72,111 kN olur. Alan büyüdükçe
gerilmeler ve tepe hareketi azalır; toplam kütle artar.

Tam tarama 1.728 kombinasyonu değerlendirir; 891 uygun kombinasyon ve
58 farklı Pareto amaç noktası vardır. Bağımsız 2B süpürme testi bu
Pareto kümesini doğrulamıştır. On NSGA-II koşusu da 58 noktayı bulmuştur.

Bu tablo burkulma, stabilite, bağlantı ve tam standart kontrollerini kapsamaz.