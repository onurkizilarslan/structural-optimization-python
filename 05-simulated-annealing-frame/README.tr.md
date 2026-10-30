# Benzetimli tavlama · Çelik çerçeve

[Ana sayfa](../README.tr.md) · [English](README.md)

Problem, formüller, birimler, algoritma adımları, sonuçlar ve alıştırmalar için [Türkçe ders notunu açın](OKU.md).

## Çalıştırma

Ana depo klasöründen:

```bash
cd 05-simulated-annealing-frame
python -m pip install -r requirements.txt
python sa_cerceve.py
python grafikleri_ciz.py
```

Çıktılar aynı adlı sonuç dosyalarının üzerine yazılır. Girdi değişince grafikleri yeniden üretin.

## Kontrol

```bash
python -m unittest test_hesap.py -v
```

Bu çalışma eğitim amaçlıdır. Kapsam dışındaki tasarım kontrolleri ders notunda açıklanmıştır.
