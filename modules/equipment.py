"""
装备模块 - 定义武器和护甲数据
"""

# ══════════════════════════════════════════════
# 20把武器 - 含等级限制、暴击伤害差异化
# 分档：Tier1(Lv1-4) Tier2(Lv5-9) Tier3(Lv10-14) Tier4(Lv15-19) Tier5(Lv20-30)
# ══════════════════════════════════════════════
WEAPONS = [
    # Tier 1 新手 (Lv1-4)
    {"name": "木棍", "attack": 8, "crit_rate": 0, "crit_dmg": 150, "level_req": 1, "cost": {"金币": 10}},
    {"name": "石斧", "attack": 12, "crit_rate": 3, "crit_dmg": 150, "level_req": 1, "cost": {"木材": 15}},
    {"name": "骨刀", "attack": 10, "crit_rate": 8, "crit_dmg": 160, "level_req": 2, "cost": {"皮革": 8, "木材": 8}},  # 暴击流
    {"name": "铁匕首", "attack": 18, "crit_rate": 5, "crit_dmg": 150, "level_req": 3, "cost": {"铁矿": 20}},  # Tier1天花板

    # Tier 2 进阶 (Lv5-9)
    {"name": "短剑", "attack": 22, "crit_rate": 5, "crit_dmg": 150, "level_req": 5, "cost": {"木材": 15, "铁矿": 20}},
    {"name": "战斧", "attack": 30, "crit_rate": 6, "crit_dmg": 150, "level_req": 5, "cost": {"木材": 20, "铁矿": 30, "皮革": 12}},  # 暴力流
    {"name": "弯刀", "attack": 24, "crit_rate": 15, "crit_dmg": 170, "level_req": 6, "cost": {"铁矿": 35, "皮革": 18}},  # 暴击流
    {"name": "铁剑", "attack": 38, "crit_rate": 8, "crit_dmg": 150, "level_req": 8, "cost": {"铁矿": 50}},  # Tier2天花板

    # Tier 3 精良 (Lv10-14)
    {"name": "长剑", "attack": 45, "crit_rate": 8, "crit_dmg": 150, "level_req": 10, "cost": {"木材": 25, "铁矿": 60}},
    {"name": "钢剑", "attack": 55, "crit_rate": 10, "crit_dmg": 150, "level_req": 11, "cost": {"铁矿": 85, "皮革": 30}},
    {"name": "巨剑", "attack": 48, "crit_rate": 20, "crit_dmg": 180, "level_req": 12, "cost": {"木材": 35, "铁矿": 75, "皮革": 25}},  # 暴击流
    {"name": "魔法铁剑", "attack": 65, "crit_rate": 12, "crit_dmg": 150, "level_req": 14, "cost": {"铁矿": 100, "皮革": 40}},  # Tier3天花板

    # Tier 4 稀有 (Lv15-19)
    {"name": "雷鸣剑", "attack": 75, "crit_rate": 12, "crit_dmg": 150, "level_req": 16, "cost": {"铁矿": 120, "皮革": 60, "木材": 40}},
    {"name": "火焰剑", "attack": 85, "crit_rate": 14, "crit_dmg": 160, "level_req": 17, "cost": {"铁矿": 150, "皮革": 80}},
    {"name": "寒冰剑", "attack": 78, "crit_rate": 22, "crit_dmg": 180, "level_req": 18, "cost": {"铁矿": 140, "皮革": 90, "木材": 50}},  # 暴击流
    {"name": "圣剑", "attack": 100, "crit_rate": 15, "crit_dmg": 150, "level_req": 20, "cost": {"铁矿": 180, "皮革": 120, "木材": 70}},  # Tier4天花板

    # Tier 5 传说 (Lv20-30)
    {"name": "暗影刃", "attack": 115, "crit_rate": 18, "crit_dmg": 170, "level_req": 23, "cost": {"皮革": 200, "铁矿": 220}},
    {"name": "龙鳞剑", "attack": 130, "crit_rate": 20, "crit_dmg": 160, "level_req": 25, "cost": {"皮革": 280, "铁矿": 300, "木材": 120}},
    {"name": "魔法龙剑", "attack": 145, "crit_rate": 22, "crit_dmg": 180, "level_req": 28, "cost": {"皮革": 350, "铁矿": 400, "木材": 180}},  # 暴击流
    {"name": "龙魂剑", "attack": 160, "crit_rate": 25, "crit_dmg": 200, "level_req": 30, "cost": {"皮革": 450, "铁矿": 500, "木材": 250}},  # 终极武器
]

# ══════════════════════════════════════════════
# 20件护甲 - 含等级限制、防御/血量重设计
# 分档：Tier1(Lv1-4) Tier2(Lv5-9) Tier3(Lv10-14) Tier4(Lv15-19) Tier5(Lv20-30)
# ══════════════════════════════════════════════
ARMORS = [
    # Tier 1 新手 (Lv1-4)
    {"name": "布衣", "defense": 4, "hp_bonus": 15, "level_req": 1, "cost": {"金币": 8}},
    {"name": "皮甲", "defense": 8, "hp_bonus": 30, "level_req": 1, "cost": {"皮革": 15}},
    {"name": "骨甲", "defense": 6, "hp_bonus": 45, "level_req": 2, "cost": {"皮革": 12, "木材": 10}},
    {"name": "铁甲", "defense": 12, "hp_bonus": 50, "level_req": 3, "cost": {"铁矿": 25}},  # Tier1天花板

    # Tier 2 进阶 (Lv5-9)
    {"name": "铁胸甲", "defense": 15, "hp_bonus": 70, "level_req": 5, "cost": {"铁矿": 40, "皮革": 20}},
    {"name": "钢甲", "defense": 20, "hp_bonus": 90, "level_req": 7, "cost": {"铁矿": 60}},
    {"name": "锁子甲", "defense": 18, "hp_bonus": 110, "level_req": 7, "cost": {"铁矿": 55, "皮革": 25}},  # 血牛流
    {"name": "骑士甲", "defense": 25, "hp_bonus": 100, "level_req": 9, "cost": {"铁矿": 80, "皮革": 40, "木材": 30}},  # Tier2天花板

    # Tier 3 精良 (Lv10-14)
    {"name": "银甲", "defense": 30, "hp_bonus": 140, "level_req": 10, "cost": {"铁矿": 100, "皮革": 50}},
    {"name": "魔法铁甲", "defense": 38, "hp_bonus": 170, "level_req": 12, "cost": {"铁矿": 140, "皮革": 70}},
    {"name": "符文甲", "defense": 32, "hp_bonus": 200, "level_req": 12, "cost": {"铁矿": 120, "皮革": 80, "木材": 40}},  # 血牛流
    {"name": "闪电甲", "defense": 45, "hp_bonus": 180, "level_req": 14, "cost": {"铁矿": 180, "皮革": 90}},  # Tier3天花板

    # Tier 4 稀有 (Lv15-19)
    {"name": "火焰甲", "defense": 50, "hp_bonus": 250, "level_req": 16, "cost": {"铁矿": 200, "皮革": 120}},
    {"name": "寒冰甲", "defense": 58, "hp_bonus": 280, "level_req": 17, "cost": {"铁矿": 240, "皮革": 140, "木材": 60}},
    {"name": "暗影甲", "defense": 52, "hp_bonus": 320, "level_req": 18, "cost": {"皮革": 200, "铁矿": 200}},  # 血牛流
    {"name": "圣甲", "defense": 70, "hp_bonus": 300, "level_req": 20, "cost": {"铁矿": 300, "皮革": 180, "木材": 80}},  # Tier4天花板

    # Tier 5 传说 (Lv20-30)
    {"name": "龙鳞甲", "defense": 80, "hp_bonus": 420, "level_req": 23, "cost": {"皮革": 320, "铁矿": 350, "木材": 100}},
    {"name": "魔法龙甲", "defense": 90, "hp_bonus": 480, "level_req": 26, "cost": {"皮革": 400, "铁矿": 450, "木材": 150}},
    {"name": "圣光护铠", "defense": 85, "hp_bonus": 550, "level_req": 28, "cost": {"铁矿": 500, "皮革": 380, "木材": 120}},  # 血牛流
    {"name": "龙魂甲", "defense": 110, "hp_bonus": 600, "level_req": 30, "cost": {"皮革": 550, "铁矿": 600, "木材": 200}},  # 终极护甲
]


def get_weapons():
    """获取所有武器列表"""
    return WEAPONS


def get_armors():
    """获取所有护甲列表"""
    return ARMORS


def get_weapon_by_name(name):
    """根据名称获取武器"""
    for wpn in WEAPONS:
        if wpn["name"] == name:
            return wpn
    return None


def get_armor_by_name(name):
    """根据名称获取护甲"""
    for arm in ARMORS:
        if arm["name"] == name:
            return arm
    return None
