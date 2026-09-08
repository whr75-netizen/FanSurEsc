import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from perfect_pixel import get_perfect_pixel, PaletteOptions, get_palette_pixel, scaled_grid
from perfect_pixel.palette import rgb_to_oklab,oklab_to_rgb,_grid_edges


class PaletteTests(unittest.TestCase):
    def setUp(self):
        y,x=np.indices((40,48))
        self.a=np.stack([120+x*2,80+y*3,60+(x+y)],axis=2).astype(np.uint8)
        self.a[12:18,12:18]=(0,0,0)
        self.a[13:15,13:15]=(255,255,255)

    def test_decimal_scales_and_fixed_base(self):
        expected={'.8':(56,58),'.9':(63,65),'1':(70,73),'1.1':(77,80),'1.2':(84,87)}
        base=(70,73)
        for scale,value in expected.items():self.assertEqual(scaled_grid(base,scale),value)
        self.assertEqual(base,(70,73))
        self.assertEqual(scaled_grid((1,1),'.1'),(1,1))

    def test_invalid_parameters(self):
        for scale in ['nan','inf','0','-1','5','bad']:
            with self.assertRaises(ValueError):scaled_grid((70,73),scale)
        for base in [(0,2),(2.2,2),(True,2),(4097,2)]:
            with self.assertRaises(ValueError):scaled_grid(base)
        for options in [PaletteOptions(tones_per_family=5),PaletteOptions(color_families=1),PaletteOptions(flatten_strength=float('nan')),PaletteOptions(color_priorities=(('#ff0000',5),)),PaletteOptions(flatten_strength='0.5'),PaletteOptions(feature_strength='0.5'),PaletteOptions(refine_intensity='0.2')]:
            with self.assertRaises(ValueError):get_palette_pixel(self.a,(12,10),options=options)
        with self.assertRaises(ValueError):get_palette_pixel(self.a.astype(float),(12,10))

    def test_color_roundtrip(self):
        a=np.random.default_rng(123).random((1000,3)).astype(np.float32)
        self.assertLess(float(np.max(np.abs(oklab_to_rgb(rgb_to_oklab(a))-a))),2e-5)

    def test_unchanged_input_deterministic_and_discrete_palette(self):
        before=self.a.copy()
        r=get_palette_pixel(self.a,(12,10))
        r2=get_palette_pixel(self.a,(12,10))
        np.testing.assert_array_equal(self.a,before)
        np.testing.assert_array_equal(r.image,r2.image)
        self.assertEqual(r.image.shape,(10,12,3))
        entries={tuple(x) for x in r.palette}
        self.assertTrue(all(tuple(x) in entries for x in r.image.reshape(-1,3)))
        self.assertLessEqual(len(entries),r.metadata['max_colors'])
        self.assertTrue(all(len(f)<=3 for f in r.metadata['family_palette_indices']))
        original_colors={tuple(x) for x in self.a.reshape(-1,3)}
        self.assertTrue(entries.issubset(original_colors))

    def test_palette_frozen_when_only_resolution_changes(self):
        a=get_palette_pixel(self.a,(12,10),'.8')
        b=get_palette_pixel(self.a,(12,10),'1.2')
        np.testing.assert_array_equal(a.palette,b.palette)
        self.assertEqual(a.image.shape[:2],(8,9))
        self.assertEqual(b.image.shape[:2],(12,14))

    def test_transparency_no_junk_bleed(self):
        a=np.zeros((24,24,4),dtype=np.uint8)
        a[:,:,:3]=(255,0,255)
        a[5:19,5:19]=(80,180,60,255)
        r=get_palette_pixel(a,(12,12))
        self.assertEqual(set(np.unique(r.image[...,3])),{0,255})
        self.assertTrue(np.all(r.image[r.image[...,3]==0]==0))
        self.assertTrue(np.all(np.abs(r.palette.astype(int)-[80,180,60])<=1))

    def test_fully_transparent_and_tiny(self):
        a=np.zeros((1,1,4),dtype=np.uint8)
        r=get_palette_pixel(a,(2,3))
        self.assertEqual(r.image.shape,(3,2,4));self.assertFalse(r.image.any())
        a=np.full((1,1,3),127,dtype=np.uint8)
        r=get_palette_pixel(a,(2,3))
        self.assertTrue(np.all(np.abs(r.image.astype(int)-127)<=1))

    def test_color_priority_cannot_change_alpha(self):
        a=np.zeros((12,12,4),dtype=np.uint8)
        a[:,:4]=(255,0,0,255)
        plain=get_palette_pixel(a,(1,1),options=PaletteOptions(flatten_strength=0,feature_strength=0,refine_intensity=0))
        weighted=get_palette_pixel(a,(1,1),options=PaletteOptions(flatten_strength=0,feature_strength=0,refine_intensity=0,color_priorities=(('#ff0000',4),)))
        np.testing.assert_array_equal(plain.image[...,3],weighted.image[...,3])

    def test_edges_exact_count_monotonic_and_full_coverage(self):
        for dims in [(12,10),(3,2),(60,70)]:
            x,y=_grid_edges(self.a,dims,.45)
            self.assertEqual((len(x),len(y)),(dims[0]+1,dims[1]+1))
            self.assertEqual((x[0],x[-1],y[0],y[-1]),(0,48,0,40))
            self.assertTrue((np.diff(x)>0).all() and (np.diff(y)>0).all())

    def test_original_mode_center_and_upstream_still_available(self):
        r=get_palette_pixel(self.a,(12,10),options=PaletteOptions(refine_intensity=0),mode='original')
        np.testing.assert_array_equal(r.image,self.a[np.arange(2,40,4)[:,None],np.arange(2,48,4)[None,:]])
        self.assertTrue(callable(get_perfect_pixel))

    def test_explicit_priority_and_tone_one(self):
        r=get_palette_pixel(self.a,(12,10),options=PaletteOptions(tones_per_family=1,color_priorities=(('#000000',2),('#e0b080',.5))))
        self.assertLessEqual(len(r.palette),r.metadata['max_colors'])
        self.assertTrue(all(len(f)<=1 for f in r.metadata['family_palette_indices']))

    def test_dominant_flat_source_color_exact(self):
        a=self.a.copy()
        a[:15]=(238,239,255)
        r=get_palette_pixel(a,(12,10))
        self.assertIn((238,239,255),{tuple(x) for x in r.palette})


if __name__=='__main__':unittest.main()
