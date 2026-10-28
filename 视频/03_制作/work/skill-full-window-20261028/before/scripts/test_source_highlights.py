import unittest
from source_highlights import validate_source_highlights

class SourceHighlightTests(unittest.TestCase):
    def test_source_box_survives_crop_as_separate_layer(self):
        a={'width':2254,'height':1710,'crop':[320,0,1660,1660],'highlights':[{'rect':[805,1284,218,65],'strokeWidth':5}]}
        self.assertEqual(validate_source_highlights(a),a['highlights'])
    def test_out_of_crop_target_is_rejected(self):
        with self.assertRaises(ValueError):validate_source_highlights({'width':1000,'height':800,'crop':[300,200,400,300],'highlights':[{'rect':[10,10,50,30]}]})
    def test_unannotated_media_keeps_legacy_behavior(self):
        self.assertEqual(validate_source_highlights({'width':1000,'height':800}),[])

if __name__=='__main__':unittest.main()
