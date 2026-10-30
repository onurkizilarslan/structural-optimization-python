# En iyi SA adayının model kontrolleri

Sol kolon K1, sağ kolon K3, kiriş K5. Birimler: kN, kNm, MPa.

| Eleman | Profil | Mutlak N | Mutlak uç M maksimumu | Maks. normal gerilme |
|---|---|---:|---:|---:|
| E1 | K1 | 43.831103 | 15.793630 | 118.148905 |
| E2 | K3 | 56.168897 | 52.807011 | 154.055981 |
| E3 | K5 | 17.544981 | 115.699680 | 136.408354 |
| E4 | K5 | 17.544981 | 115.699680 | 136.408354 |

En büyük normal gerilme 154.055981 MPa ≤ 160 MPa.
Çatı yatay hareketi 1.127061 mm ≤ 10 mm.
Kiriş göreli orta sehim 10.070203 mm ≤ 20 mm.
Kütle 503.404800 kg. Tam taramayla aynı minimum.

## Düğüm hareketleri ve reaksiyonlar

| Düğüm | ux (mm) | uy (mm) | theta (rad) | Rx (kN) | Ry (kN) | Mz (kNm) |
|---|---:|---:|---:|---:|---:|---:|
| D1 | 0.000000 | 0.000000 | 0.00000000 | 7.544981 | 43.831103 | -6.841315 |
| D2 | 0.000000 | 0.000000 | 0.00000000 | -27.544981 | 56.168897 | 29.827933 |
| D3 | 1.127061 | -0.254438 | -0.00477963 | -0.000000 | -0.000000 | -0.000000 |
| D4 | 1.090791 | -10.295849 | 0.00032478 | -0.000000 | 0.000000 | -0.000000 |
| D5 | 1.054521 | -0.196854 | 0.00353810 | 0.000000 | -0.000000 | 0.000000 |

Reaksiyonların serbest düğümlerde görülen son basamak değerleri sayısal çözüm artıklarıdır.
Bu kontroller stabilite, kesme, bağlantı veya standardın tam tasarım koşullarını kapsamaz.