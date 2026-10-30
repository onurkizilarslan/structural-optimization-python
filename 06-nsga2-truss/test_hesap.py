"""python -m unittest test_hesap.py -v"""
import unittest
from dataclasses import replace
import numpy as np
from nsga2_kafes import *

class Kontroller(unittest.TestCase):
    def test_dugum_dengesi_ve_enerji(self):
        m=Kafes(Problem());A=np.array([650.,1000,1250]);r=m.analiz(A)
        expected=np.array([40000,-120000*np.sqrt(13)/6,-120000*np.sqrt(13)/6])
        np.testing.assert_allclose(np.array(r['stress'])*A,expected,atol=1e-7)
        self.assertAlmostEqual(sum(r['reactions'][1::2]),120000,places=6)
        self.assertAlmostEqual(sum(r['reactions'][::2]),0,places=6)
        delta=np.sum(expected**2*m.L/(m.p.E*A))/m.p.yuk_N
        self.assertAlmostEqual(r['disp'],delta,places=10)

    def test_baskinlik_ve_esdegerlik(self):
        F=np.array([[1,4],[2,2],[4,1],[3,3],[2,2]],float)
        rank,front=sirala(F,np.zeros(5))
        self.assertEqual(set(front[0]),{0,1,2,4});self.assertEqual(rank[3],1)
        crowd=kalabalik(F,front)
        self.assertTrue(np.isinf(crowd[0]) and np.isinf(crowd[2]))
        self.assertFalse(np.any(np.isnan(crowd)))

    def test_kisit_onceligi(self):
        F=np.array([[10,10],[1,1],[.5,.5]])
        rank,_=sirala(F,np.array([0,.2,.4]))
        np.testing.assert_array_equal(rank,[0,1,2])

    def test_sabit_amac_kalabalik(self):
        F=np.array([[2,2],[2,2],[2,2]],float)
        _,front=sirala(F,np.zeros(3));d=kalabalik(F,front)
        np.testing.assert_array_equal(d,np.zeros(3))

    def test_hypervolume(self):
        hv=hypervolume(np.array([[1,3],[2,2],[3,3]]),np.zeros(2),np.ones(2),ref=(4,4))
        self.assertAlmostEqual(hv,5.)
        self.assertEqual(hypervolume([],np.zeros(2),np.ones(2)),0.)

    def test_bagimsiz_pareto_taramasi(self):
        m=Kafes(Problem());pop,F,v,fp,ff=tam_tarama(m)
        self.assertEqual(len(pop),1728);self.assertEqual(np.sum(v<=TOL),891)
        # Bağımsız 2B süpürme: önce kütle, sonra deplasman sırası.
        feasible=sorted(keyset(F[v<=TOL]));oracle=[];smallest=float('inf')
        for mass,disp in feasible:
            if disp<smallest:oracle.append((mass,disp));smallest=disp
        self.assertEqual(keyset(ff),set(oracle));self.assertEqual(len(oracle),58)
        light=ff[np.argmin(ff[:,0])]
        self.assertAlmostEqual(light[0],37.7235775124,places=7)
        self.assertAlmostEqual(light[1],4.0136999943,places=8)

    def test_tekrarlanabilirlik_ve_butce(self):
        m=Kafes(Problem());a,F,h=nsga2(m,seed=3,size=30,generations=10)
        b,F2,h2=nsga2(Kafes(Problem()),seed=3,size=30,generations=10)
        np.testing.assert_array_equal(a,b);np.testing.assert_array_equal(F,F2);self.assertEqual(h,h2)
        self.assertEqual(m.queries,330);self.assertLessEqual(m.solves,m.queries)
        self.assertTrue(all(m.cache[tuple(row)]['feasible'] for row in a))
        _,front=sirala(F,np.zeros(len(F)));self.assertEqual(len(front[0]),len(F))

    def test_uygun_cozum_yok(self):
        m=Kafes(replace(Problem(),yuk_N=1e8))
        pop,F,_=nsga2(m,size=10,generations=3)
        self.assertEqual(len(F),0)
        with self.assertRaises(ValueError):m.analiz([0,300,400])

if __name__=='__main__':unittest.main()
