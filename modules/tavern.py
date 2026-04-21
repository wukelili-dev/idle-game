"""
酒馆模块 - 招募队友系统
"""
import random
import time


# 角色名池
ROLE_NAME_POOL = [
    "剑圣·霜", "影刃·夜", "铁壁·钢", "神射手·翎",
    "狂战士·焚", "圣光使·曦", "暗法师·冥", "龙骑士·渊",
    "风语者·岚", "烈焰·炽", "寒冰·凛", "疾风·逍",
    "守护者·磐", "猎手·矢", "魔导师·墨", "武僧·悟",
    "游侠·云", "召唤师·灵", "刺客·霜", "圣骑士·盾",
]

# 高级角色名（会自带装备）
ELITE_ROLE_POOL = [
    "黄金圣骑·裁决", "暗影领主·噬", "苍穹龙将·霄",
    "修罗·杀", "天照·神", "不灭战魂·焚",
]

# 武器名（高级角色自带）
ELITE_WEAPONS = [
    {"name": "暗影巨剑", "attack": 25, "crit_rate": 18, "crit_dmg": 180, "rarity": "史诗", "rarity_color": "#9370DB", "sell_price": 120},
    {"name": "龙纹长弓", "attack": 22, "crit_rate": 25, "crit_dmg": 160, "rarity": "史诗", "rarity_color": "#9370DB", "sell_price": 110},
    {"name": "雷霆法杖", "attack": 18, "crit_rate": 12, "crit_dmg": 200, "rarity": "传说", "rarity_color": "#FF8C00", "sell_price": 180},
    {"name": "裂空之刃", "attack": 30, "crit_rate": 20, "crit_dmg": 170, "rarity": "传说", "rarity_color": "#FF8C00", "sell_price": 200},
    {"name": "星陨战斧", "attack": 35, "crit_rate": 10, "crit_dmg": 220, "rarity": "传说", "rarity_color": "#FF8C00", "sell_price": 250},
]

# 护甲名（高级角色自带）
ELITE_ARMORS = [
    {"name": "玄武战甲", "defense": 28, "hp_bonus": 80, "rarity": "史诗", "rarity_color": "#9370DB", "sell_price": 130},
    {"name": "天使羽衣", "defense": 20, "hp_bonus": 120, "rarity": "传说", "rarity_color": "#FF8C00", "sell_price": 200},
    {"name": "龙魂胸甲", "defense": 35, "hp_bonus": 100, "rarity": "传说", "rarity_color": "#FF8C00", "sell_price": 220},
    {"name": "暗影披风", "defense": 15, "hp_bonus": 150, "rarity": "史诗", "rarity_color": "#9370DB", "sell_price": 150},
    {"name": "圣光护铠", "defense": 25, "hp_bonus": 90, "rarity": "传说", "rarity_color": "#FF8C00", "sell_price": 190},
]

# 精英角色自带装备配置
ELITE_GEAR = {
    "weapon": ELITE_WEAPONS,
    "armor": ELITE_ARMORS,
}


def calc_recruit_cost(player_level, is_elite=False):
    """计算招募费用"""
    base = player_level * 100
    return base * 2 if is_elite else base


def calc_recruit_level(player_level):
    """随机生成队友等级（主角等级或低一级，最低1级）"""
    if random.random() < 0.6:
        return player_level
    return max(1, player_level - 1)


def generate_recruit(player_level):
    """生成一个可招募角色"""
    is_elite = random.random() < 0.15  # 15%精英概率
    level = calc_recruit_level(player_level)

    if is_elite:
        role_name = random.choice(ELITE_ROLE_POOL)
        # 精英角色自带装备
        wpn = random.choice(ELITE_WEAPONS)
        arm = random.choice(ELITE_ARMORS)
        equip_weapon = {
            "type": "weapon",
            "name": wpn["name"],
            "attack": wpn["attack"],
            "crit_rate": wpn["crit_rate"],
            "crit_dmg": wpn.get("crit_dmg", 150),
            "rarity": wpn["rarity"],
            "rarity_color": wpn["rarity_color"],
            "sell_price": wpn["sell_price"],
            "level_req": max(1, level - 3),
            "is_perfect": False,
        }
        equip_armor = {
            "type": "armor",
            "name": arm["name"],
            "defense": arm["defense"],
            "hp_bonus": arm["hp_bonus"],
            "rarity": arm["rarity"],
            "rarity_color": arm["rarity_color"],
            "sell_price": arm["sell_price"],
            "level_req": max(1, level - 3),
            "is_perfect": False,
        }
        equip = [equip_weapon, equip_armor]
    else:
        role_name = random.choice(ROLE_NAME_POOL)
        equip = []

    cost = calc_recruit_cost(player_level, is_elite)

    return {
        "role_name": role_name,
        "level": level,
        "is_elite": is_elite,
        "cost": cost,
        "gear": equip,   # 精英角色自带装备列表
    }


def generate_tavern_roster(player_level, existing_names=None):
    """生成酒馆当前角色列表（1~3个）"""
    if existing_names is None:
        existing_names = set()
    count = random.randint(1, 3)
    roster = []
    attempts = 0
    while len(roster) < count and attempts < 20:
        attempts += 1
        recruit = generate_recruit(player_level)
        if recruit["role_name"] not in existing_names:
            roster.append(recruit)
            existing_names.add(recruit["role_name"])
    return roster


def tavern_roster_to_dict(roster):
    """酒馆列表序列化"""
    return [{"role_name": r["role_name"], "level": r["level"],
             "is_elite": r["is_elite"], "cost": r["cost"],
             "gear": r["gear"]} for r in roster]


def tavern_roster_from_dict(data):
    """酒馆列表反序列化"""
    return data
