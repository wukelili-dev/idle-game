"""
装备模块 - 定义武器和护甲数据
"""

# 20种武器 - 攻击/暴击率/暴击伤害(150%)
WEAPONS = [
    {"name": "木棍", "attack": 3, "crit_rate": 0, "crit_dmg": 150, "cost": {"金币": 5}},
    {"name": "石斧", "attack": 5, "crit_rate": 5, "crit_dmg": 150, "cost": {"木材": 10}},
    {"name": "骨刀", "attack": 8, "crit_rate": 8, "crit_dmg": 150, "cost": {"皮革": 5, "木材": 5}},
    {"name": "铁匕首", "attack": 12, "crit_rate": 10, "crit_dmg": 150, "cost": {"铁矿": 15}},
    {"name": "短剑", "attack": 16, "crit_rate": 12, "crit_dmg": 150, "cost": {"木材": 10, "铁矿": 20}},
    {"name": "战斧", "attack": 20, "crit_rate": 15, "crit_dmg": 150, "cost": {"木材": 15, "铁矿": 25, "皮革": 10}},
    {"name": "铁剑", "attack": 25, "crit_rate": 18, "crit_dmg": 150, "cost": {"铁矿": 40}},
    {"name": "弯刀", "attack": 30, "crit_rate": 20, "crit_dmg": 150, "cost": {"铁矿": 50, "皮革": 15}},
    {"name": "长剑", "attack": 35, "crit_rate": 22, "crit_dmg": 150, "cost": {"木材": 20, "铁矿": 60}},
    {"name": "钢剑", "attack": 42, "crit_rate": 25, "crit_dmg": 150, "cost": {"铁矿": 80, "皮革": 20}},
    {"name": "巨剑", "attack": 50, "crit_rate": 28, "crit_dmg": 150, "cost": {"木材": 30, "铁矿": 100, "皮革": 30}},
    {"name": "魔法铁剑", "attack": 58, "crit_rate": 30, "crit_dmg": 150, "cost": {"铁矿": 120, "皮革": 40}},
    {"name": "雷鸣剑", "attack": 65, "crit_rate": 32, "crit_dmg": 150, "cost": {"铁矿": 80, "皮革": 60, "木材": 40}},
    {"name": "火焰剑", "attack": 72, "crit_rate": 35, "crit_dmg": 150, "cost": {"铁矿": 100, "皮革": 80}},
    {"name": "寒冰剑", "attack": 80, "crit_rate": 38, "crit_dmg": 150, "cost": {"铁矿": 120, "皮革": 100, "木材": 50}},
    {"name": "圣剑", "attack": 90, "crit_rate": 40, "crit_dmg": 150, "cost": {"铁矿": 150, "皮革": 120, "木材": 80}},
    {"name": "暗影刃", "attack": 100, "crit_rate": 42, "crit_dmg": 150, "cost": {"皮革": 150, "铁矿": 180}},
    {"name": "龙鳞剑", "attack": 115, "crit_rate": 45, "crit_dmg": 150, "cost": {"皮革": 200, "铁矿": 220, "木材": 100}},
    {"name": "魔法龙剑", "attack": 130, "crit_rate": 48, "crit_dmg": 150, "cost": {"皮革": 250, "铁矿": 280, "木材": 150}},
    {"name": "龙魂剑", "attack": 150, "crit_rate": 50, "crit_dmg": 150, "cost": {"皮革": 300, "铁矿": 350, "木材": 200}},
]

# 20种护甲 - 防御/生命加成
ARMORS = [
    {"name": "布衣", "defense": 3, "hp_bonus": 0, "cost": {"金币": 5}},
    {"name": "皮甲", "defense": 6, "hp_bonus": 10, "cost": {"皮革": 10}},
    {"name": "皮外套", "defense": 10, "hp_bonus": 20, "cost": {"皮革": 20}},
    {"name": "骨甲", "defense": 15, "hp_bonus": 30, "cost": {"皮革": 15, "木材": 10}},
    {"name": "铁甲", "defense": 22, "hp_bonus": 50, "cost": {"铁矿": 30}},
    {"name": "铁胸甲", "defense": 30, "hp_bonus": 70, "cost": {"铁矿": 50, "皮革": 20}},
    {"name": "钢甲", "defense": 40, "hp_bonus": 100, "cost": {"铁矿": 80}},
    {"name": "锁子甲", "defense": 50, "hp_bonus": 130, "cost": {"铁矿": 100, "皮革": 40}},
    {"name": "骑士甲", "defense": 60, "hp_bonus": 160, "cost": {"铁矿": 130, "皮革": 60, "木材": 30}},
    {"name": "银甲", "defense": 72, "hp_bonus": 200, "cost": {"铁矿": 160, "皮革": 80}},
    {"name": "魔法铁甲", "defense": 85, "hp_bonus": 240, "cost": {"铁矿": 200, "皮革": 100}},
    {"name": "符文甲", "defense": 100, "hp_bonus": 280, "cost": {"铁矿": 150, "皮革": 130, "木材": 50}},
    {"name": "闪电甲", "defense": 115, "hp_bonus": 320, "cost": {"铁矿": 180, "皮革": 160}},
    {"name": "火焰甲", "defense": 130, "hp_bonus": 360, "cost": {"铁矿": 220, "皮革": 200, "木材": 60}},
    {"name": "寒冰甲", "defense": 145, "hp_bonus": 400, "cost": {"铁矿": 260, "皮革": 240, "木材": 80}},
    {"name": "圣甲", "defense": 160, "hp_bonus": 450, "cost": {"铁矿": 300, "皮革": 280, "木材": 100}},
    {"name": "暗影甲", "defense": 180, "hp_bonus": 500, "cost": {"皮革": 320, "铁矿": 350}},
    {"name": "龙鳞甲", "defense": 200, "hp_bonus": 550, "cost": {"皮革": 380, "铁矿": 400, "木材": 120}},
    {"name": "魔法龙甲", "defense": 220, "hp_bonus": 620, "cost": {"皮革": 450, "铁矿": 480, "木材": 150}},
    {"name": "龙魂甲", "defense": 250, "hp_bonus": 700, "cost": {"皮革": 500, "铁矿": 550, "木材": 200}},
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
