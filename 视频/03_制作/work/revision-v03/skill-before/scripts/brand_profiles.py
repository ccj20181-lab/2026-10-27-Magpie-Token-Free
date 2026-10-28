"""Shared brand defaults; project settings take precedence over workspace inference."""
from __future__ import annotations

import copy
from pathlib import Path

CAISHU_ROOT = Path('/Users/henry/Desktop/财叔 AI Lab')
MIAODONG_ROOT = Path('/Users/henry/Desktop/秒懂金融学院')
CAISHU_LOGO = CAISHU_ROOT / '00_品牌与经营/品牌资产/logo/caishu_ai_lab_primary_logo.png'
MIAODONG_LOGO = MIAODONG_ROOT / '00_品牌与业务中枢/品牌资产/logo/miaodong_finance_logo.png'
CAISHU_LEGACY_SERIES_TITLES = {'每天分享一个AI炸裂操作', '每天分享一个AI商业操作'}
PROFILES = {
    'miaodong_finance': {
        'workspace': MIAODONG_ROOT,
        'series_title': '每天一个AI理财小技巧',
        'output_root': MIAODONG_ROOT / '02_内容生产/视频/每天一个AI理财小技巧',
        'corner_logo': {
            'variant': 'miaodong_finance',
            'path': str(MIAODONG_LOGO),
            'width': 136, 'height': 136,
        },
    },
    'caishu_ai_lab': {
        'workspace': CAISHU_ROOT,
        'series_title': '每天一条AI干货',
        'output_root': CAISHU_ROOT / '03_内容生产/项目',
        'corner_logo': {
            'variant': 'caishu_ai_lab',
            'path': str(CAISHU_LOGO),
            'width': 236, 'height': 88,
            'background': 'rgba(255,255,255,0.96)',
            'padding_x': 12, 'padding_y': 8, 'border_radius': 18,
        },
    },
}


def workspace_profile(path):
    resolved = Path(path).expanduser().resolve()
    for name, profile in PROFILES.items():
        if resolved.is_relative_to(profile['workspace']):
            return name
    return None


def resolve_brand_profile(plan=None, *, workspace=None, project_dir=None):
    plan = plan or {}
    explicit = plan.get('brand_profile')
    if explicit:
        if explicit not in PROFILES:
            raise ValueError(f'unknown brand_profile: {explicit}')
        return explicit
    corner = plan.get('corner_logo') or {}
    if corner.get('variant') in PROFILES:
        return corner['variant']
    logo = corner.get('path') or plan.get('corner_logo_image') or plan.get('corner_logo_path')
    if logo:
        resolved = Path(logo).expanduser().resolve()
        for name, profile in PROFILES.items():
            known = [Path(profile['corner_logo']['path']).resolve()]
            if name == 'caishu_ai_lab':
                legacy = CAISHU_ROOT / '03_内容生产/工作流与模板/AI视频工作流历史资产/logo/caishu_ai_lab_logo.png'
                if legacy.exists():
                    known.append(legacy.resolve())
            if resolved in known:
                return name
    for path in (workspace or Path.cwd(), project_dir):
        if path is not None:
            name = workspace_profile(path)
            if name:
                return name
    return 'miaodong_finance'  # Existing behavior outside either workspace.


def apply_brand_defaults(plan, *, workspace=None, project_dir=None):
    result = copy.deepcopy(plan)
    name = resolve_brand_profile(result, workspace=workspace, project_dir=project_dir)
    result['brand_profile'] = name
    if not result.get('series_title') or (
        name == 'caishu_ai_lab' and result['series_title'] in CAISHU_LEGACY_SERIES_TITLES
    ):
        result['series_title'] = PROFILES[name]['series_title']
    if not (result.get('corner_logo') or result.get('corner_logo_image') or result.get('corner_logo_path')):
        result['corner_logo'] = copy.deepcopy(PROFILES[name]['corner_logo'])
    return result
