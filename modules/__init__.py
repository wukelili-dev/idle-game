"""
Hero Workshop v3.0 - 模块包初始化
"""

from .equipment import WEAPONS, ARMORS, get_weapons, get_armors
from .equipment_drops import generate_drop, get_drop_summary, get_rarity_by_monster_level
from .buildings import (BUILDING_CONFIGS, get_all_building_names, 
                        get_all_wonders, get_wonder_names, WORKER_CONFIG)
from .maps import get_all_maps, get_map_enemies, print_map_info, print_enemy_info, MAP_ENEMIES
from .hero import Hero
from .game_core import GameCore

__all__ = [
    'WEAPONS', 'ARMORS', 'get_weapons', 'get_armors',
    'generate_drop', 'get_drop_summary', 'get_rarity_by_monster_level',
    'BUILDING_CONFIGS', 'get_all_building_names',
    'get_all_wonders', 'get_wonder_names', 'WORKER_CONFIG',
    'get_all_maps', 'get_map_enemies', 'print_map_info', 'print_enemy_info', 'MAP_ENEMIES',
    'Hero', 'GameCore',
]
