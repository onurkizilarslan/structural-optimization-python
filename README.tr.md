# Python ile Yapı Tasarımında Optimizasyon

Onur Kızılarslan'ın yapı tasarımında optimizasyon dersi için yapay zekâ desteğiyle hazırlanmış altı uygulama.

[English](README.md) · [Doğrulama](VALIDATION.md) · [Hazırlanma süreci](PROVENANCE.md) · [Lisans durumu](LICENSE_STATUS.md)

| Ders | Algoritma ve yapı |
|---|---|
| 1 | [Genetik algoritma · Betonarme kolon](01-genetic-algorithm-column/README.tr.md) |
| 2 | [Karınca kolonisi · Betonarme kiriş](02-ant-colony-beam/README.tr.md) |
| 3 | [Parçacık sürüsü · Çelik kafes](03-particle-swarm-truss/README.tr.md) |
| 4 | [Diferansiyel evrim · Betonarme kiriş](04-differential-evolution-beam/README.tr.md) |
| 5 | [Benzetimli tavlama · Çelik çerçeve](05-simulated-annealing-frame/README.tr.md) |
| 6 | [NSGA-II · Çok amaçlı çelik kafes](06-nsga2-truss/README.tr.md) |

## Başlangıç

Python 3.11 veya üstü kullanın. Ana klasörde sanal ortam oluşturup bağımlılıkları kurun:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python validate.py
```

Ardından istediğiniz ders klasörüne girin; README.tr.md ve OKU.md dosyalarındaki komutları izleyin. Kodlar, ayrıntılı Türkçe ders notları ve hazır sonuçlar klasörlerdedir. Ders 2–6 ayrıca grafikler ve birim testleri içerir. Ders 1, çalıştırma ve tam tarama karşılaştırmasıyla kontrol edilir.

## Sonuçları yorumlama

Örneklerin problemleri, tasarım uzayları ve hesap bütçeleri farklıdır; sonuçları doğrudan karşılaştırarak bir algoritmanın üstün olduğu sonucuna varmayın. Küçük ayrık problemlerde tam tarama zaten pratiktir. Amaç algoritmaları öğrenmek ve hesapları doğrulamaktır.

Modeller eğitim amaçlıdır. Betonarme örnekleri tam yönetmelik kontrolü yapmaz; çelik örnekleri burkulma gibi zorunlu kontrolleri içermez. Fiyatlar varsayımsaldır. Model kısıtlarının sağlanması, gerçek yapının güvenli olduğunu göstermez.

Programlar mevcut sonuç dosyalarını yeniler. Parametre değişince grafikleri yeniden üretin; açıklamalardaki sayılar kendiliğinden değişmez. Üçüncü taraf kaynaklar her dersin OKU.md dosyasında belirtilmiştir.

## Yapay zekâ desteği ve lisans

Kodlar, açıklamalar ve görseller OpenAI ChatGPT/Codex desteğiyle hazırlanmıştır. Sayısal kontroller bağımsız uzman incelemesi anlamına gelmez. Yeniden kullanım lisansı henüz seçilmemiştir; bu hazırlık sürümüne MIT veya Creative Commons lisansı otomatik eklenmemiştir.
