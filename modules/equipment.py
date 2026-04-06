"""
装备模块 - 定义武器和护甲数据
"""

# 20种武器 - 攻击/暴击率/暴击伤害(150%)
WEAPONS = [
    {"name": "木棍", "attack": 3, "crit_rate": 0, "crit_dmg": 150, "cost": {"Gold": 5}},
    {"name": "石斧", "attack": 5, "crit_rate": 5, "crit_dmg": 150, "cost": {"Wood": 10}},
    {"name": "骨刀", "attack": 8, "crit_rate": 8, "crit_dmg": 150, "cost": {"Leather": 5, "Wood": 5}},
    {"name": "铁匕首", "attack": 12, "crit_rate": 10, "crit_dmg": 150, "cost": {"Iron": 15}},
    {"name": "短剑", "attack": 16, "crit_rate": 12, "crit_dmg": 150, "cost": {"Wood": 10, "Iron": 20}},
    {"name": "战斧", "attack": 20, "crit_rate": 15, "crit_dmg": 150, "cost": {"Wood": 15, "Iron": 25, "Leather": 10}},
    {"name": "铁剑", "attack": 25, "crit_rate": 18, "crit_dmg": 150, "cost": {"Iron": 40}},
    {"name": "弯刀", "attack": 30, "crit_rate": 20, "crit_dmg": 150, "cost": {"Iron": 50, "Leather": 15}},
    {"name": "长剑", "attack": 35, "crit_rate": 22, "crit_dmg": 150, "cost": {"Wood": 20, "Iron": 60}},
    {"name": "钢剑", "attack": 42, "crit_rate": 25, "crit_dmg": 150, "cost": {"Iron": 80, "Leather": 20}},
    {"name": "巨剑", "attack": 50, "crit_rate": 28, "crit_dmg": 150, "cost": {"Wood": 30, "Iron": 100, "Leather": 30}},
    {"name": "魔法铁剑", "attack": 58, "crit_rate": 30, "crit_dmg": 150, "cost": {"Iron": 120, "Leather": 40}},
    {"name": "雷鸣剑", "attack": 65, "crit_rate": 32, "crit_dmg": 150, "cost": {"Iron": 80, "Leather": 60, "Wood": 40}},
    {"name": "火焰剑", "attack": 72, "crit_rate": 35, "crit_dmg": 150, "cost": {"Iron": 100, "Leather": 80}},
    {"name": "寒冰剑", "attack": 80, "crit_rate": 38, "crit_dmg": 150, "cost": {"Iron": 120, "Leather": 100, "Wood": 50}},
    {"name": "圣剑", "attack": 90, "crit_rate": 40, "crit_dmg": 150, "cost": {"Iron": 150, "Leather": 120, "Wood": 80}},
    {"name": "暗影刃", "attack": 100, "crit_rate": 42, "crit_dmg": 150, "cost": {"Leather": 150, "Iron": 180}},
    {"name": "龙鳞剑", "attack": 115, "crit_rate": 45, "crit_dmg": 150, "cost": {"Leather": 200, "Iron": 220, "Wood": 100}},
    {"name": "魔法龙剑", "attack": 130, "crit_rate": 48, "crit_dmg": 150, "cost": {"Leather": 250, "Iron": 280, "Wood": 150}},
    {"name": "龙魂剑", "attack": 150, "crit_rate": 50, "crit_dmg": 150, "cost": {"Leather": 300, "Iron": 350, "Wood": 200}},
]

# 20种护甲 - 防御/生命加成
ARMORS = [
    {"name": "布衣", "defense": 3, "hp_bonus": 0, "cost": {"Gold": 5}},
    {"name": "皮甲", "defense": 6, "hp_bonus": 10, "cost": {"Leather": 10}},
    {"name": "LeatherCoat", "defense": 10, "hp_bonus": 20, "cost": {"Leather": 20}},
    {"name": "BoneArmor", "defense": 15, "hp_bonus": 30, "cost": {"Leather": 15, "Wood": 10}},
    {"name": "铁甲", "defense": 22, "hp_bonus": 50, "cost": {"Iron": 30}},
    {"name": "IronChestplate", "defense": 30, "hp_bonus": 70, "cost": {"Iron": 50, "Leather": 20}},
    {"name": "SteelArmor", "defense": 40, "hp_bonus": 100, "cost": {"Iron": 80}},
    {"name": "Chainmail", "defense": 50, "hp_bonus": 130, "cost": {"Iron": 100, "Leather": 40}},
    {"name": "骑士甲", "defense": 60, "hp_bonus": 160, "cost": {"Iron": 130, "Leather": 60, "Wood": 30}},
    {"name": "SilverArmor", "defense": 72, "hp_bonus": 200, "cost": {"Iron": 160, "Leather": 80}},
    {"name": "MagicIronArmor", "defense": 85, "hp_bonus": 240, "cost": {"Iron": 200, "Leather": 100}},
    {"name": "RuneArmor", "defense": 100, "hp_bonus": 280, "cost": {"Iron": 150, "Leather": 130, "Wood": 50}},
    {"name": "LightningArmor", "defense": 115, "hp_bonus": 320, "cost": {"Iron": 180, "Leather": 160}},
    {"name": "FlameArmor", "defense": 130, "hp_bonus": 360, "cost": {"Iron": 220, "Leather": 200, "Wood": 60}},
    {"name": "FrostArmor", "defense": 145, "hp_bonus": 400, "cost": {"Iron": 260, "Leather": 240, "Wood": 80}},
    {"name": "圣甲", "defense": 160, "hp_bonus": 450, "cost": {"Iron": 300, "Leather": 280, "Wood": 100}},
    {"name": "暗影甲", "defense": 180, "hp_bonus": 500, "cost": {"Leather": 320, "Iron": 350}},
    {"name": "龙鳞甲", "defense": 200, "hp_bonus": 550, "cost": {"Leather": 380, "Iron": 400, "Wood": 120}},
    {"name": "魔法龙甲", "defense": 220, "hp_bonus": 620, "cost": {"Leather": 450, "Iron": 480, "Wood": 150}},
    {"name": "DragonSoulArmor", "defense": 250, "hp_bonus": 700, "cost": {"Leather": 500, "Iron": 550, "Wood": 200}},
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
