"""Çalıştırma: python -m unittest test_hesap.py -v"""
import math
import unittest
from dataclasses import replace
from aco_kiris import Problem, hesapla, aco, tam_tarama, olasiliklar


class Kontroller(unittest.TestCase):
    def test_bagimsiz_el_hesabi(self):
        # 300x500, 4Ø20: bağımsız sayısal referans.
        r=hesapla((300,500,4,20),Problem())
        self.assertAlmostEqual(r['d_mm'],447)
        self.assertAlmostEqual(r['As_mm2'],1256.637061436)
        self.assertAlmostEqual(r['Mu_kNm'],155.25)
        self.assertAlmostEqual(r['M_model_kNm'],195.943072157)
        self.assertAlmostEqual(r['net_aralik_mm'],44.666666667)
        self.assertTrue(r['uygun'])

    def test_asiri_donati_reddedilir(self):
        r=hesapla((250,350,6,28),Problem())
        self.assertFalse(r['cekme_kontrollu'])
        self.assertIsNone(r['M_model_kNm'])
        self.assertFalse(r['uygun'])

    def test_yuk_artisi_ve_ozagirlik(self):
        p=Problem()
        a=hesapla((300,500,4,20),p)
        b=hesapla((300,550,4,20),p)
        self.assertGreater(b['Mu_kNm'],a['Mu_kNm'])
        c=hesapla((300,500,4,20),replace(p,dis_yuk=40))
        self.assertAlmostEqual(c['Mu_kNm']-a['Mu_kNm'],45)

    def test_olasilik_ve_kesif(self):
        q=olasiliklar([.05,20,1,1])
        self.assertAlmostEqual(sum(q),1)
        self.assertTrue(all(v>=.10/4 for v in q))

    def test_tam_tarama_ve_aco(self):
        p=Problem()
        ref,rows=tam_tarama(p)
        self.assertEqual(len(rows),1000)
        self.assertEqual(sum(r['uygun'] for r in rows),385)
        self.assertAlmostEqual(ref['maliyet_PB'],3950.241644643,places=6)
        for seed in range(10):
            best,trace,_=aco(p,seed)
            self.assertTrue(best['uygun'])
            self.assertGreaterEqual(best['maliyet_PB']+1e-8,ref['maliyet_PB'])
            good=[r['en_iyi_maliyet_PB'] for r in trace if r['en_iyi_maliyet_PB'] is not None]
            self.assertTrue(all(b<=a+1e-9 for a,b in zip(good,good[1:])))
            # Sabit tohumla aynı koşu tekrarlanabilmeli.
            if seed==0:
                self.assertEqual((best,trace),aco(p,seed)[:2])

    def test_uygun_cozum_yok(self):
        p=replace(Problem(),dis_yuk=10000)
        ref,_=tam_tarama(p)
        self.assertIsNone(ref)
        best,_,_=aco(p,0,5,3)
        self.assertFalse(best['uygun'])


if __name__=='__main__':
    unittest.main()
