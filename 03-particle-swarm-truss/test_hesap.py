"""python -m unittest test_hesap.py -v"""
import unittest
from dataclasses import replace
import numpy as np
from pso_kafes import Problem,Kafes,lineer_analiz,analitik_referans,pso


class Kontroller(unittest.TestCase):
    def test_opensees_yayinlanmis_ornek(self):
        # OpenSees Basic Truss: kip-in birimleri, dört düğüm/üç eleman.
        nodes=np.array([[0,0],[144,0],[168,0],[72,96]],float)
        elements=np.array([[0,3],[1,3],[2,3]])
        loads=np.array([0,0,0,0,0,0,100,-50],float)
        r=lineer_analiz(nodes,elements,3000,[10,5,5],loads,np.arange(6))
        np.testing.assert_allclose(r['u'][-2:],[.530093,-.177894],atol=5e-7,rtol=0)
        np.testing.assert_allclose(r['force'],[43.9352,-57.5463,-55.3114],atol=6e-5,rtol=0)

    def test_dugum_dengesi_enerji(self):
        m=Kafes(Problem());A=np.array([700,1100,1300])
        r=lineer_analiz(m.nodes,m.elements,m.p.E_MPa,A,m.loads,m.fixed)
        np.testing.assert_allclose(r['reaction'][m.free],0,atol=1e-8)
        self.assertAlmostEqual(sum(r['reaction'][1::2]),120000,places=6)
        self.assertAlmostEqual(sum(r['reaction'][::2]),0,places=6)
        # Clapeyron: u^T F = sum(N² L / EA).
        self.assertAlmostEqual(float(r['u']@m.loads),
                               float(np.sum(r['force']**2*m.L/(m.p.E_MPa*A))),places=6)
        np.testing.assert_allclose(r['K'],r['K'].T,atol=1e-12)

    def test_kesitten_bagimsiz_kuvvet(self):
        m=Kafes(Problem());ref=analitik_referans(m)
        for A in ([200,200,200],[600,900,1300],[3000,2200,1700]):
            r=m.degerlendir(A)
            np.testing.assert_allclose(r['stress']*A,ref['force'],atol=1e-7)
            q=ref['force']**2*m.L/(m.p.E_MPa*m.p.yuk_N)
            self.assertAlmostEqual(float(-r['uy']),float(np.sum(q/A)),places=10)

    def test_analitik_kuresel_alt_sinir(self):
        m=Kafes(Problem());ref=analitik_referans(m)
        self.assertAlmostEqual(ref['mass'],75.62166666666667,places=8)
        q=ref['force']**2*m.L/(m.p.E_MPa*m.p.yuk_N)
        w=m.L*m.p.yogunluk_kg_mm3
        # Cauchy-Schwarz alt sınırı bu problemde sağlanır ve optimumu belgeler.
        alt_sinir=np.sum(np.sqrt(w*q))**2/m.p.deplasman_sinir_mm
        self.assertAlmostEqual(ref['mass'],alt_sinir,places=8)
        self.assertTrue(m.degerlendir(ref['areas'])['feasible'])

    def test_uygunsuz_ve_imkansiz(self):
        m=Kafes(Problem())
        self.assertFalse(m.degerlendir([200,200,200])['feasible'])
        self.assertIsNone(analitik_referans(Kafes(replace(Problem(),yuk_N=1e8))))
        with self.assertRaises(ValueError):m.degerlendir([0,200,200])

    def test_pso_tekrarlanabilir_ve_iz(self):
        m=Kafes(Problem());a,h=pso(m,seed=1,parcacik=20,iterasyon=50)
        b,h2=pso(m,seed=1,parcacik=20,iterasyon=50)
        np.testing.assert_array_equal(a,b);self.assertEqual(h,h2)
        vals=[v['en_iyi_uygun_kutle_kg'] for v in h if v['en_iyi_uygun_kutle_kg'] is not None]
        self.assertTrue(all(b<=a+1e-9 for a,b in zip(vals,vals[1:])))
        self.assertEqual(h[-1]['degerlendirme'],1020)
        self.assertGreaterEqual(float(m.degerlendir(a)['mass'])+1e-7,analitik_referans(m)['mass'])

    def test_toplu_tekil_analiz(self):
        m=Kafes(Problem());A=np.array([[700,1100,1300],[1500,1500,1500]])
        batch=m.degerlendir(A)
        for i,a in enumerate(A):
            r=lineer_analiz(m.nodes,m.elements,m.p.E_MPa,a,m.loads,m.fixed)
            np.testing.assert_allclose(batch['uf'][i],r['u'][m.free],atol=1e-12)
            np.testing.assert_allclose(batch['stress'][i],r['stress'],atol=1e-10)


if __name__=='__main__':unittest.main()
