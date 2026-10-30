"""python -m unittest test_hesap.py -v"""
import unittest
from dataclasses import replace
import numpy as np
from sa_cerceve import *

class Kontroller(unittest.TestCase):
    def test_konsol_egilme_eksenel(self):
        L=3000.;E=200000.;A=2000.;I=8e6
        nodes=np.array([[0,0],[L,0]],float)
        loads=np.array([0,0,0,1000,-1000,0.])
        r=analiz(nodes,[(0,1)],[dict(A_mm2=A,I_mm4=I)],E,loads,[0,1,2])
        self.assertAlmostEqual(r['u'][3],1000*L/(E*A),places=10)
        self.assertAlmostEqual(r['u'][4],-1000*L**3/(3*E*I),places=10)
        self.assertAlmostEqual(r['u'][5],-1000*L**2/(2*E*I),places=10)
        self.assertAlmostEqual(r['R'][2],1000*L,places=6)

    def test_donmus_konsol(self):
        nodes=np.array([[0,0],[0,3000]],float);E=200000;I=8e6
        r=analiz(nodes,[(0,1)],[dict(A_mm2=2000,I_mm4=I)],E,np.array([0,0,0,1000,0,0.]),[0,1,2])
        self.assertAlmostEqual(r['u'][3],1000*3000**3/(3*E*I),places=10)

    def test_global_denge_enerji(self):
        m=Cerceve(Problem());secs=[m.cat[i] for i in [0,2,4,4]]
        a=analiz(m.nodes,m.elements,secs,m.p.E,m.loads,m.fixed)
        np.testing.assert_allclose(a['R'][a['free']],0,atol=1e-7)
        total=(a['R']+m.loads).reshape(-1,3)
        self.assertAlmostEqual(sum(total[:,0]),0,places=6)
        self.assertAlmostEqual(sum(total[:,1]),0,places=6)
        self.assertAlmostEqual(sum(total[:,2]+m.nodes[:,0]*total[:,1]-m.nodes[:,1]*total[:,0]),0,places=4)
        self.assertAlmostEqual(float(a['u']@a['K']@a['u']),float(a['u']@m.loads),places=5)

    def test_simetrik_yuk(self):
        m=Cerceve(replace(Problem(),yatay_N=0));r=m.hesapla((3,3,4));u=np.array(r['u']).reshape(-1,3)
        self.assertAlmostEqual(u[2,1],u[4,1],places=10)
        self.assertAlmostEqual(u[2,0],-u[4,0],places=10)
        self.assertAlmostEqual(u[3,0],0,places=10)

    def test_katalog(self):
        p=katalog()[0]
        self.assertEqual(p['A_mm2'],2584)
        self.assertAlmostEqual(p['I_mm4'],2*(100*8**3/12+100*8*86**2)+6*164**3/12)
        self.assertAlmostEqual(p['W_mm3'],p['I_mm4']/90)

    def test_kabul_ve_komsu(self):
        self.assertEqual(kabul_olasiligi(-1,.1),1)
        self.assertAlmostEqual(kabul_olasiligi(.2,.1),math.exp(-2))
        self.assertLess(kabul_olasiligi(.2,.01),kabul_olasiligi(.2,1))
        rng=np.random.default_rng(4)
        for _ in range(100):
            y=komsu((0,3,7),rng)
            self.assertEqual(sum(a!=b for a,b in zip(y,(0,3,7))),1)
            self.assertTrue(all(0<=i<8 for i in y))

    def test_referans_cache_ve_tavlama(self):
        m=Cerceve(Problem())
        rows=[m.hesapla(x) for x in itertools.product(range(8),repeat=3)]
        valid=[r for r in rows if r['uygun']]
        self.assertEqual(len(valid),260)
        ref=min(valid,key=lambda r:r['kutle_kg'])
        self.assertAlmostEqual(ref['kutle_kg'],503.4048)
        self.assertEqual(ref['indeks'],[0,2,4])
        self.assertEqual(m.solves,512);m.hesapla((0,2,4));self.assertEqual(m.solves,512)
        a,h,st=tavlama(Cerceve(Problem()),seed=3,adim=300)
        b,h2,_=tavlama(Cerceve(Problem()),seed=3,adim=300)
        self.assertEqual(a,b);self.assertEqual(h,h2)
        vals=[r['en_iyi_uygun_kutle_kg'] for r in h if r['en_iyi_uygun_kutle_kg'] is not None]
        self.assertTrue(all(y<=x for x,y in zip(vals,vals[1:])))
        self.assertEqual(st['analiz_cozumu'],st['benzersiz_aday'])
        self.assertEqual(st['degerlendirme'],301)
        self.assertGreater(st['kotu_kabul'],0)

    def test_uygun_cozum_yok(self):
        m=Cerceve(replace(Problem(),dusey_N=1e9))
        best,_,_=tavlama(m,adim=30)
        self.assertIsNone(best)
        self.assertFalse(m.hesapla((7,7,7))['uygun'])

if __name__=='__main__':unittest.main()
