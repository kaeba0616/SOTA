"""
석판 데이터 서비스
"""
import json
import os
from typing import List, Dict, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TabletService:
    """석판 데이터 관리 서비스"""

    _instance = None
    _tablets: List[Dict] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_tablets()
        return cls._instance

    def _load_tablets(self):
        """tablet.json에서 석판 데이터 로드"""
        tablet_path = os.path.join(PROJECT_ROOT, 'tablet.json')
        try:
            with open(tablet_path, 'r', encoding='utf-8') as f:
                self._tablets = json.load(f)
            print(f"석판 데이터 로드 완료: {len(self._tablets)}개")
        except Exception as e:
            print(f"석판 데이터 로드 실패: {e}")
            self._tablets = []

    def get_all_tablets(self) -> List[Dict]:
        """모든 석판 반환"""
        return self._tablets

    def get_tablet_by_id(self, tablet_id: str) -> Optional[Dict]:
        """ID로 석판 조회"""
        for tablet in self._tablets:
            if tablet['id'] == tablet_id:
                return tablet
        return None

    def get_tablet_by_name(self, name: str) -> Optional[Dict]:
        """이름으로 석판 조회"""
        for tablet in self._tablets:
            if tablet['name'] == name:
                return tablet
        return None

    def get_tablets_by_ids(self, tablet_ids: List[str]) -> List[Dict]:
        """여러 ID로 석판 조회"""
        tablets = []
        for tablet_id in tablet_ids:
            tablet = self.get_tablet_by_id(tablet_id)
            if tablet:
                tablets.append(tablet)
        return tablets

    def format_tablet_response(self, tablet: Dict) -> Dict:
        """석판 데이터를 API 응답 형식으로 변환"""
        props = tablet.get('properties', {})
        effects = []

        for effect in tablet.get('effects', []):
            effect_data = {
                'type': effect.get('type', 'level_add'),
                'value': effect.get('value', effect.get('level_add', 0))
            }
            if 'pos' in effect:
                effect_data['pos'] = effect['pos']
            if 'shape' in effect:
                effect_data['shape'] = effect['shape']
            effects.append(effect_data)

        return {
            'id': tablet['id'],
            'name': tablet['name'],
            'image_url': tablet.get('image_url', ''),
            'rotatable': props.get('rotatable', False) or props.get('can_rotate', False),
            'rarity': props.get('rarity', '일반'),
            'restriction': props.get('restriction'),
            'effects': effects
        }

    def get_all_formatted(self) -> List[Dict]:
        """모든 석판을 API 응답 형식으로 반환"""
        return [self.format_tablet_response(t) for t in self._tablets]
