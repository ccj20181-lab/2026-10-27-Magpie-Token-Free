import os
import unittest
from pathlib import Path
from contextlib import contextmanager

from brand_profiles import CAISHU_ROOT, MIAODONG_ROOT, PROFILES, apply_brand_defaults, resolve_brand_profile
from director import brand_metadata
from render_ai_coach_demo import apply_corner_logo_variant


@contextmanager
def in_workspace(path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


class BrandProfileTests(unittest.TestCase):
    def test_actual_workspace_defaults_and_render_metadata(self):
        for workspace, expected in [(CAISHU_ROOT, 'caishu_ai_lab'), (MIAODONG_ROOT, 'miaodong_finance')]:
            with self.subTest(workspace=workspace), in_workspace(workspace):
                plan = apply_brand_defaults({})
                meta = brand_metadata(plan, 'test', lambda path, slug, name: str(path))
                self.assertEqual(meta['brandProfile'], expected)
                self.assertEqual(meta['motionStyle'], 'caishu-editorial-v1' if expected=='caishu_ai_lab' else 'white-line-v1')
                self.assertEqual(meta['seriesTitle'], PROFILES[expected]['series_title'])
                self.assertEqual(meta['cornerLogoPath'], PROFILES[expected]['corner_logo']['path'])
                self.assertEqual(meta['cornerLogoWidth'], PROFILES[expected]['corner_logo']['width'])

    def test_frozen_brand_survives_shared_renderer_directory(self):
        plan = apply_brand_defaults({}, workspace=MIAODONG_ROOT)
        with in_workspace(CAISHU_ROOT / '.agents/skills/ai-coach-daily-demo/remotion'):
            meta = brand_metadata(plan, 'test', lambda path, slug, name: str(path))
        self.assertEqual(meta['brandProfile'], 'miaodong_finance')

    def test_historical_explicit_logo_and_banner_are_preserved(self):
        original = {'corner_logo_image': str(PROFILES['miaodong_finance']['corner_logo']['path']), 'series_title': '已确认的栏目'}
        updated = apply_brand_defaults(original, workspace=CAISHU_ROOT)
        self.assertEqual(updated['brand_profile'], 'miaodong_finance')
        self.assertEqual(updated['corner_logo_image'], original['corner_logo_image'])
        self.assertEqual(updated['series_title'], original['series_title'])
        self.assertNotIn('corner_logo', updated)
        self.assertNotIn('brand_profile', original)
        variant = apply_corner_logo_variant(original, 'miaodong_finance')
        self.assertEqual(variant['series_title'], original['series_title'])

    def test_explicit_variant_and_custom_configuration(self):
        plan = apply_corner_logo_variant({}, 'caishu_ai_lab')
        with in_workspace(MIAODONG_ROOT):
            updated = apply_brand_defaults(plan)
        self.assertEqual(updated['brand_profile'], 'caishu_ai_lab')
        self.assertEqual(updated['series_title'], '每天一条AI干货')
        custom = {'brand_profile': 'caishu_ai_lab', 'series_title': '已确认横幅', 'corner_logo': {'path': '/custom/logo.png', 'width': 220}}
        self.assertEqual(apply_brand_defaults(custom, workspace=MIAODONG_ROOT), custom)

    def test_explicit_motion_direction_is_preserved(self):
        plan=apply_brand_defaults({'brand_profile':'caishu_ai_lab','motion_style':'user-chosen-style'})
        meta=brand_metadata(plan,'test',lambda path,slug,name:str(path))
        self.assertEqual(meta['motionStyle'],'user-chosen-style')

    def test_unknown_explicit_profile_is_not_silently_replaced(self):
        with self.assertRaises(ValueError):
            resolve_brand_profile({'brand_profile': 'unknown'}, workspace=CAISHU_ROOT)

    def test_retired_caishu_banners_are_migrated_only_for_caishu(self):
        for title in ['每天分享一个AI炸裂操作', '每天分享一个AI商业操作']:
            original = {'brand_profile': 'caishu_ai_lab', 'series_title': title}
            updated = apply_brand_defaults(original, workspace=MIAODONG_ROOT)
            self.assertEqual(updated['series_title'], '每天一条AI干货')
            self.assertEqual(original['series_title'], title)
            other_brand = {'brand_profile': 'miaodong_finance', 'series_title': title}
            self.assertEqual(apply_brand_defaults(other_brand)['series_title'], title)


if __name__ == '__main__':
    unittest.main()
