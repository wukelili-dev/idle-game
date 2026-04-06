"""
地图模块 - 定义游戏地图和怪物分布
"""

# 地图定义
MAPS = {
    "傲来国": {
        "name": "傲来国",
        "description": "新手村，适合1-10级玩家练级",
        "min_level": 1,
        "enemies": ["蝴蝶", "鹦鹉", "龙虾", "巨蟹"],
        "bosses": ["九头精怪"],
        "unlock_cost": 0,  # 初始解锁
    },
    "大唐东": {
        "name": "大唐东",
        "description": "大唐东部边境，危险度中等",
        "min_level": 11,
        "enemies": ["失控的银甲唐兵", "太监", "失控的金甲唐兵", "唐兵统领"],
        "bosses": ["千年蛇魅"],
        "unlock_cost": 500,
    },
    "阳关": {
        "name": "阳关",
        "description": "西域边关，突厥和波斯势力出没",
        "min_level": 15,
        "enemies": ["突厥弩手", "波斯女刀客"],
        "bosses": ["突厥弩王", "波斯刺客"],
        "unlock_cost": 1000,
    },
    "东海": {
        "name": "东海",
        "description": "深海区域，强大的海妖盘踞",
        "min_level": 20,
        "enemies": ["龙虾", "巡海夜叉", "龟丞相", "螺精"],
        "bosses": ["万年虾妖", "梵天罗刹", "玄龟仙人", "嗜血妖螺"],
        "unlock_cost": 2000,
    },
}

# 怪物数据（按地图分布）
MAP_ENEMIES = {
    # 傲来国 - 新手村 (Lv.1-10)
    "蝴蝶": {"name": "蝴蝶", "hp": 15, "attack": 3, "defense": 1, "exp": 5, "gold": 3, "drops": {"皮革": 1}},
    "鹦鹉": {"name": "鹦鹉", "hp": 25, "attack": 5, "defense": 2, "exp": 8, "gold": 5, "drops": {"皮革": 1}},
    "龙虾": {"name": "龙虾", "hp": 40, "attack": 8, "defense": 3, "exp": 15, "gold": 10, "drops": {"皮革": 2}},
    "巨蟹": {"name": "巨蟹", "hp": 60, "attack": 12, "defense": 5, "exp": 25, "gold": 18, "drops": {"皮革": 2, "铁矿": 1}},
    "九头精怪": {"name": "九头精怪", "hp": 150, "attack": 20, "defense": 10, "exp": 80, "gold": 60, "drops": {"皮革": 5, "铁矿": 3, "木材": 5}},
    
    # 大唐东 (Lv.11-15)
    "失控的银甲唐兵": {"name": "失控的银甲唐兵", "hp": 80, "attack": 15, "defense": 8, "exp": 35, "gold": 25, "drops": {"铁矿": 2}},
    "太监": {"name": "太监", "hp": 60, "attack": 12, "defense": 5, "exp": 28, "gold": 20, "drops": {"皮革": 2}},
    "失控的金甲唐兵": {"name": "失控的金甲唐兵", "hp": 100, "attack": 18, "defense": 12, "exp": 45, "gold": 35, "drops": {"铁矿": 3}},
    "唐兵统领": {"name": "唐兵统领", "hp": 130, "attack": 22, "defense": 15, "exp": 60, "gold": 50, "drops": {"铁矿": 4, "皮革": 2}},
    "千年蛇魅": {"name": "千年蛇魅", "hp": 250, "attack": 30, "defense": 18, "exp": 120, "gold": 100, "drops": {"皮革": 8, "铁矿": 5, "木材": 3}},
    
    # 阳关 (Lv.15-20)
    "突厥弩手": {"name": "突厥弩手", "hp": 120, "attack": 25, "defense": 10, "exp": 55, "gold": 40, "drops": {"木材": 3, "铁矿": 2}},
    "波斯女刀客": {"name": "波斯女刀客", "hp": 140, "attack": 28, "defense": 12, "exp": 65, "gold": 50, "drops": {"皮革": 3, "铁矿": 3}},
    "突厥弩王": {"name": "突厥弩王", "hp": 280, "attack": 35, "defense": 20, "exp": 150, "gold": 120, "drops": {"木材": 6, "铁矿": 5, "皮革": 4}},
    "波斯刺客": {"name": "波斯刺客", "hp": 220, "attack": 40, "defense": 15, "exp": 130, "gold": 110, "drops": {"皮革": 6, "铁矿": 4}},
    
    # 东海 (Lv.20-30)
    "巡海夜叉": {"name": "巡海夜叉", "hp": 180, "attack": 35, "defense": 18, "exp": 90, "gold": 70, "drops": {"皮革": 4, "铁矿": 3}},
    "龟丞相": {"name": "龟丞相", "hp": 250, "attack": 30, "defense": 30, "exp": 110, "gold": 90, "drops": {"皮革": 5, "木材": 4}},
    "螺精": {"name": "螺精", "hp": 200, "attack": 38, "defense": 15, "exp": 100, "gold": 80, "drops": {"皮革": 3, "木材": 3}},
    "万年虾妖": {"name": "万年虾妖", "hp": 400, "attack": 45, "defense": 25, "exp": 200, "gold": 180, "drops": {"皮革": 8, "铁矿": 6}},
    "梵天罗刹": {"name": "梵天罗刹", "hp": 450, "attack": 50, "defense": 22, "exp": 220, "gold": 200, "drops": {"皮革": 10, "铁矿": 5, "木材": 5}},
    "玄龟仙人": {"name": "玄龟仙人", "hp": 500, "attack": 42, "defense": 40, "exp": 250, "gold": 220, "drops": {"皮革": 8, "木材": 8}},
    "嗜血妖螺": {"name": "嗜血妖螺", "hp": 380, "attack": 55, "defense": 20, "exp": 210, "gold": 190, "drops": {"皮革": 6, "铁矿": 8}},
}


def get_all_maps():
    """获取所有地图"""
    return MAPS


def get_map_names():
    """获取所有地图名称"""
    return list(MAPS.keys())


def get_map_info(map_name):
    """获取地图信息"""
    return MAPS.get(map_name)


def get_map_enemies(map_name):
    """获取地图中的敌人列表"""
    map_info = MAPS.get(map_name)
    if not map_info:
        return []
    return [MAP_ENEMIES[name] for name in map_info["enemies"] if name in MAP_ENEMIES]


def get_map_bosses(map_name):
    """获取地图中的BOSS列表"""
    map_info = MAPS.get(map_name)
    if not map_info:
        return []
    return [MAP_ENEMIES[name] for name in map_info.get("bosses", []) if name in MAP_ENEMIES]


def get_random_enemy(map_name, boss_chance=0.05):
    """随机获取一个敌人，有概率遇到BOSS
    
    Args:
        map_name: 地图名称
        boss_chance: BOSS出现概率，默认5%
    
    Returns:
        (enemy_data, is_boss): 敌人数据和是否为BOSS
    """
    import random
    
    map_info = MAPS.get(map_name)
    if not map_info:
        return None, False
    
    # 判断是否遇到BOSS
    if random.random() < boss_chance:
        bosses = get_map_bosses(map_name)
        if bosses:
            return random.choice(bosses), True
    
    # 返回普通怪物
    enemies = get_map_enemies(map_name)
    if enemies:
        return random.choice(enemies), False
    
    return None, False


def get_enemy_info(enemy_name):
    """获取敌人详细信息"""
    return MAP_ENEMIES.get(enemy_name)


def get_all_enemies():
    """获取所有敌人"""
    return MAP_ENEMIES


def can_enter_map(map_name, player_level, unlocked_maps):
    """检查是否可以进入地图"""
    map_info = MAPS.get(map_name)
    if not map_info:
        return False, "地图不存在"
    if map_name not in unlocked_maps:
        return False, "地图未解锁"
    if player_level < map_info["min_level"]:
        return False, f"需要等级 {map_info['min_level']}"
    return True, "可以进入"


def get_unlock_cost(map_name):
    """获取地图解锁费用"""
    map_info = MAPS.get(map_name)
    if map_info:
        return map_info.get("unlock_cost", 0)
    return None


def print_map_info():
    """打印所有地图信息"""
    print("=" * 60)
    print("游戏地图列表")
    print("=" * 60)
    for map_name, info in MAPS.items():
        print(f"\n【{info['name']}】")
        print(f"  描述: {info['description']}")
        print(f"  推荐等级: Lv.{info['min_level']}+")
        print(f"  解锁费用: {info['unlock_cost']}G")
        print(f"  怪物: {', '.join(info['enemies'])}")
        print(f"  BOSS: {', '.join(info.get('bosses', []))}")
    print("\n" + "=" * 60)


def print_enemy_info():
    """打印所有怪物信息"""
    print("=" * 80)
    print(f"共有 {len(MAP_ENEMIES)} 种怪物:")
    print("-" * 80)
    for name, enemy in MAP_ENEMIES.items():
        drops = ", ".join([f"{k}x{v}" for k, v in enemy["drops"].items()])
        print(f"{name}: HP={enemy['hp']}, ATK={enemy['attack']}, DEF={enemy['defense']}, "
              f"EXP={enemy['exp']}, Gold={enemy['gold']}, Drops=[{drops}]")
    print("=" * 80)
