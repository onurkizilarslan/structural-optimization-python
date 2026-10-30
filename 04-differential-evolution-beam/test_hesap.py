"""python -m unittest test_hesap.py -v"""
import unittest
from dataclasses import replace
import math
import numpy as np
from de_kiris import *


class Kontroller(unittest.TestCase):
    def test_bagimsiz_kesit(self):
        r=katalog_adayi(300,500,4,20,Problem())
        self.assertAlmostEqual(r['d_mm'],447)
        self.assertAlmostEqual(r['As_mm2'],1256.6370614359)
        self.assertAlmostEqual(r['Mu_kNm'],155.25)
        self.assertAlmostEqual(r['M_model_kNm'],195.9430721569)
        self.assertAlmostEqual(r['net_aralik_mm'],44.6666666667)
        self.assertTrue(r['uygun'])

    def test_alan_ters_cozum(self):
        p=Problem()
        for b,h in [(250,476),(300,500),(400,650)]:
            area=float(gerekli_alan(b,h,p));r=hesapla([b,h,area],p)
            self.assertTrue(r['feasible'])
            self.assertGreaterEqual(r['m_trial']+1e-8,r['mu'])
            lower=hesapla([b,h,area*.999],p)
            self.assertFalse(lower['feasible'])

    def test_suneksiz_ve_sigmayan(self):
        self.assertFalse(hesapla([250,350,4000],Problem())['feasible'])
        r=katalog_adayi(250,500,6,20,Problem())
        self.assertFalse(r['uygun'])
        self.assertLess(r['net_aralik_mm'],r['gerekli_aralik_mm'])

    def test_de_donor_ve_caprazlama(self):
        rng=np.random.default_rng(8);pop=rng.random((12,3))
        child,donors,mask=deneme_uret(pop,rng,CR=0)
        for i,ids in enumerate(donors):
            self.assertEqual(len(set(ids)),3);self.assertNotIn(i,ids)
        self.assertTrue(np.all(mask.sum(axis=1)==1))
        self.assertTrue(np.all((child>=0)&(child<=1)))
        np.testing.assert_array_equal(child[~mask],pop[~mask])

    def test_de_tekrar_ve_iz(self):
        p=Problem();x,h=diferansiyel_evrim(p,seed=2,populasyon=20,nesil=60)
        y,h2=diferansiyel_evrim(p,seed=2,populasyon=20,nesil=60)
        np.testing.assert_array_equal(x,y);self.assertEqual(h,h2)
        vals=[r['en_iyi_uygun_maliyet_PB'] for r in h if r['en_iyi_uygun_maliyet_PB'] is not None]
        self.assertTrue(all(b<=a+1e-8 for a,b in zip(vals,vals[1:])))
        self.assertEqual(h[-1]['degerlendirme'],1220)

    def test_izgara_ve_katalog(self):
        p=Problem();r,n=izgara_referansi(p)
        self.assertEqual(n,281101)
        self.assertAlmostEqual(r['maliyet_PB'],3850.07923727067,places=6)
        best,rows=katalog_tara(p)
        self.assertEqual(len(rows),3375)
        self.assertEqual((best['b_mm'],best['h_mm'],best['adet'],best['cap_mm']),(250,525,3,20))
        converted,near=donustur([250,476.11,1047.28],p,rows)
        self.assertTrue(converted['uygun'])
        self.assertGreaterEqual(converted['As_mm2'],1047.28)
        self.assertGreater(converted['maliyet_PB'],best['maliyet_PB'])

    def test_yuk_ve_imkansiz_durum(self):
        p=Problem();r=hesapla([300,500,1200],p)
        r2=hesapla([300,500,1200],replace(p,dis_yuk=40))
        self.assertAlmostEqual(float(r2['mu']-r['mu']),45)
        impossible=replace(p,dis_yuk=10000)
        self.assertIsNone(izgara_referansi(impossible,5)[0])
        self.assertIsNone(katalog_tara(impossible)[0])


if __name__=='__main__':unittest.main()
