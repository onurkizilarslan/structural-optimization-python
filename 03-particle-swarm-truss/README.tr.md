# Parçacık sürüsü · Çelik kafes

[Ana sayfa](../README.tr.md) · [English](README.md)

Problem, formüller, birimler, algoritma adımları, sonuçlar ve alıştırmalar için [Türkçe ders notunu açın](OKU.md).

## Çalıştırma

Ana depo klasöründen:

```bash
cd 03-particle-swarm-truss
python -m pip install -r requirements.txt
python pso_kafes.py
python grafikleri_ciz.py
```

Çıktılar aynı adlı sonuç dosyalarının üzerine yazılır. Girdi değişince grafikleri yeniden üretin.

## Kontrol

```bash
python -m unittest test_hesap.py -v
```

Bu çalışma eğitim amaçlıdır. Kapsam dışındaki tasarım kontrolleri ders notunda açıklanmıştır.
