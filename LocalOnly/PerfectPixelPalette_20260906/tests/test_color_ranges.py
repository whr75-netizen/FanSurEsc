import colorsys
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from perfect_pixel import PaletteOptions,get_palette_pixel
from perfect_pixel.palette import rgb_to_oklab
from perfect_pixel.color_ranges import build_color_ranges,clean_tone_labels


def color(h,s,v):
    return np.rint(np.array(colorsys.hsv_to_rgb(h/360,s,v))*255).astype(np.uint8)


class ColorRangeTests(unittest.TestCase):
    def build(self,a):
        return build_color_ranges(a,rgb_to_oklab(a/255),np.ones(a.shape[:2]),PaletteOptions())

    def test_pink_brown_cream_not_competing_by_area(self):
        a = np.empty((50,50,3),dtype=np.uint8)
        a[:] = color(35,.25,.85)
        a[:20] = color(22,.5,.65)
        a[30:33,30:33] = color(10,.35,.9)
        a[1:3,1:3] = (140,140,140)
        palette,families,labels,tones,details = self.build(a)
        self.assertEqual(len({labels[25,25],labels[10,10],labels[31,31],labels[1,1]}),4)
        self.assertIn(tuple(color(10,.35,.9)),{tuple(c) for c in palette})
        self.assertFalse(details['part_seeds_or_coordinates'])
        self.assertFalse(details['range_pruning'])

    def test_same_hue_gradient_has_max_three_actual_source_colors(self):
        a = np.array([[color(35,.4,v) for v in np.linspace(.35,.95,80)]]*16,dtype=np.uint8)
        palette,families,labels,tones,_ = self.build(a)
        self.assertEqual(len(families),1)
        self.assertLessEqual(len(palette),3)
        self.assertTrue(set(map(tuple,palette)).issubset(set(map(tuple,a.reshape(-1,3)))))
        result = get_palette_pixel(a,(40,8))
        self.assertLessEqual(len(np.unique(result.image.reshape(-1,3),axis=0)),3)

    def test_cleanup_cannot_delete_color_range_or_feature(self):
        labels = np.zeros((9,9),dtype=np.int32)
        labels[2,2] = 1 # low-contrast outlier in same range
        labels[4,4] = 2 # another color range
        labels[6,6] = 3 # high-contrast feature
        families = np.zeros_like(labels)
        families[4,4] = 1
        importance = np.zeros(labels.shape)
        importance[6,6] = 1
        out = clean_tone_labels(labels,families,importance,.75)
        self.assertEqual(out[2,2],0)
        self.assertEqual(out[4,4],2)
        self.assertEqual(out[6,6],3)

    def test_legacy_explicit_and_options(self):
        a = np.full((12,12,3),(200,120,100),dtype=np.uint8)
        legacy = get_palette_pixel(a,(6,6),options=PaletteOptions(palette_method='legacy'))
        self.assertIsNone(legacy.metadata['color_range_details'])
        for opt in [PaletteOptions(palette_method='bad'),PaletteOptions(range_hue_width=0),PaletteOptions(range_hue_width=float('nan')),PaletteOptions(range_hue_width=True)]:
            with self.assertRaises(ValueError): get_palette_pixel(a,(6,6),options=opt)

    def test_red_wrap_dark_neutral(self):
        a = np.array([[color(359,.6,.8),color(1,.6,.8),(0,0,0),(255,255,255)]]*8,dtype=np.uint8)
        p,fs,labels,tones,d = self.build(a)
        self.assertEqual(labels[0,0],labels[0,1])
        self.assertEqual(labels[0,2],labels[0,3])
        self.assertNotEqual(labels[0,0],labels[0,2])


if __name__ == '__main__':
    unittest.main()
