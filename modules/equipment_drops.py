"""
装备掉落系统 - 随机生成装备
"""

import random


# 装备名称前缀
WEAPON_PREFIXES = ["铁", "钢", "银", "金", "魔法", "神圣", "暗黑", "冰霜", "火焰", "雷电", "远古", "神圣", "恶魔", "龙"]
ARMOR_PREFIXES = ["皮", "铁", "钢", "银", "金", "魔法", "神圣", "暗黑", "冰霜", "火焰", "雷电", "远古", "圣", "魔"]
WEAPON_SUFFIXES = ["剑", "刀", "斧", "锤", "戟", "弓", "匕首", "杖"]
ARMOR_SUFFIXES = ["甲", "盔", "盾", "袍", "衣", "铠", "胄", "披风"]

# 特殊装备名称
SPECIAL_WEAPON_NAMES = ["轩辕剑", "青龙偃月刀", "方天画戟", "丈八蛇矛", "倚天剑", "屠龙刀"]
SPECIAL_ARMOR_NAMES = ["玄武甲", "凤凰袍", "白虎盔", "青龙铠", "麒麟胄", "天使之翼"]

# 装备稀有度
RARITY = {
    "普通": {"color": "#AAAAAA", "stat_range": 0.3, "drop_rate": 0.15, "special_chance": 0},
    "稀有": {"color": "#55AAFF", "stat_range": 0.5, "drop_rate": 0.10, "special_chance": 0.05},
    "史诗": {"color": "#AA55FF", "stat_range": 0.8, "stat_bonus": 0.5, "drop_rate": 0.05, "special_chance": 0.15},
    "传说": {"color": "#FFAA00", "stat_range": 1.0, "stat_bonus": 1.0, "drop_rate": 0.02, "special_chance": 0.30},
}

# 极品装备（无等级限制，商店不可购买）
PERFECT_WEAPON_NAMES = ["如意金箍棒", "九齿钉耙", "降妖宝杖", "混铁棍", "风火轮", "风火蒲扇"]
PERFECT_ARMOR_NAMES = ["锁子黄金甲", "藕丝步云履", "凤翅紫金冠", "凯甲", "天蚕丝披风"]


def generate_weapon_name(perfect=False):
    """生成武器名称"""
    if perfect:
        return random.choice(PERFECT_WEAPON_NAMES)
    prefix = random.choice(WEAPON_PREFIXES)
    suffix = random.choice(WEAPON_SUFFIXES)
    return f"{prefix}{suffix}"


def generate_armor_name(perfect=False):
    """生成护甲名称"""
    if perfect:
        return random.choice(PERFECT_ARMOR_NAMES)
    prefix = random.choice(ARMOR_PREFIXES)
    suffix = random.choice(ARMOR_SUFFIXES)
    return f"{prefix}{suffix}"


def get_rarity_by_monster_level(level):
    """根据怪物等级确定掉落稀有度"""
    roll = random.random()
    
    if level >= 20:  # 高级地图
        if roll < 0.02:  # 2%传说
            return "传说"
        elif roll < 0.10:  # 8%史诗
            return "史诗"
        elif roll < 0.25:  # 15%稀有
            return "稀有"
        else:
            return "普通"
    elif level >= 15:  # 中级地图
        if roll < 0.05:
            return "史诗"
        elif roll < 0.15:
            return "稀有"
        elif roll < 0.30:
            return "普通"
        else:
            return None  # 不掉装备
    elif level >= 10:  # 初级进阶
        if roll < 0.05:
            return "稀有"
        elif roll < 0.15:
            return "普通"
        else:
            return None
    else:  # 新手地图
        if roll < 0.05:
            return "普通"
        else:
            return None


def get_perfect_drop_chance(level):
    """获取极品装备掉落概率"""
    if level >= 20:
        return 0.02  # 2%
    elif level >= 15:
        return 0.01  # 1%
    elif level >= 10:
        return 0.005  # 0.5%
    return 0


def generate_weapon(level, rarity="普通", is_perfect=False, is_boss=False):
    """生成武器"""
    base_stats = {
        "普通": {"attack": (3, 8), "crit_rate": (0, 3)},
        "稀有": {"attack": (6, 12), "crit_rate": (3, 8)},
        "史诗": {"attack": (12, 22), "crit_rate": (8, 15)},
        "传说": {"attack": (22, 38), "crit_rate": (15, 25)},
    }
    
    stats = base_stats.get(rarity, base_stats["普通"])
    
    # 根据怪物等级缩放（更温和）
    scale = 1 + (level - 1) * 0.05
    if is_boss:
        scale *= 1.3
    
    attack = int(random.randint(stats["attack"][0], stats["attack"][1]) * scale)
    crit_rate = int(random.randint(stats["crit_rate"][0], stats["crit_rate"][1]) * min(scale, 1.5))
    crit_rate = min(crit_rate, 50)  # 暴击概率最高50%
    
    name = generate_weapon_name(is_perfect)
    
    equip = {
        "name": name,
        "type": "weapon",
        "rarity": "极品" if is_perfect else rarity,
        "rarity_color": "#FF5555" if is_perfect else RARITY.get(rarity, {}).get("color", "#AAAAAA"),
        "attack": attack,
        "crit_rate": crit_rate,
        "crit_dmg": 150,
        "special": None,
        "level_req": 0 if is_perfect else max(1, level - 2),
        "is_perfect": is_perfect,
    }
    
    # 极品装备自带吸血，属性在传说基础上提升50%
    if is_perfect:
        equip["special"] = {"name": "吸血", "value": random.randint(8, 15)}
        equip["level_req"] = 0
        # 极品装备属性在传说基础上提升50%
        equip["attack"] = int(equip["attack"] * 1.5)
        equip["crit_rate"] = min(50, int(equip["crit_rate"] * 1.3))
    
    # 史诗/传说有概率带特殊属性
    elif rarity in ["史诗", "传说"] and random.random() < RARITY[rarity]["special_chance"]:
        special_options = [
            {"name": "吸血", "value": random.randint(3, 8)},
            {"name": "破甲", "value": random.randint(5, 15)},
            {"name": "连击", "value": random.randint(5, 10)},
        ]
        equip["special"] = random.choice(special_options)
    
    return equip


def generate_armor(level, rarity="普通", is_perfect=False, is_boss=False):
    """生成护甲"""
    base_stats = {
        "普通": {"defense": (2, 5), "hp_bonus": (10, 30)},
        "稀有": {"defense": (4, 10), "hp_bonus": (25, 60)},
        "史诗": {"defense": (10, 20), "hp_bonus": (60, 120)},
        "传说": {"defense": (20, 35), "hp_bonus": (120, 220)},
    }
    
    stats = base_stats.get(rarity, base_stats["普通"])
    scale = 1 + (level - 1) * 0.05
    if is_boss:
        scale *= 1.3
    
    defense = int(random.randint(stats["defense"][0], stats["defense"][1]) * scale)
    hp_bonus = int(random.randint(stats["hp_bonus"][0], stats["hp_bonus"][1]) * scale)
    
    name = generate_armor_name(is_perfect)
    
    equip = {
        "name": name,
        "type": "armor",
        "rarity": "极品" if is_perfect else rarity,
        "rarity_color": "#FF5555" if is_perfect else RARITY.get(rarity, {}).get("color", "#AAAAAA"),
        "defense": defense,
        "hp_bonus": hp_bonus,
        "special": None,
        "level_req": 0 if is_perfect else max(1, level - 2),
        "is_perfect": is_perfect,
    }
    
    # 极品装备自带吸血，属性在传说基础上提升50%
    if is_perfect:
        equip["special"] = {"name": "吸血", "value": random.randint(8, 15)}
        equip["level_req"] = 0
        # 极品装备属性在传说基础上提升50%
        equip["defense"] = int(equip["defense"] * 1.5)
        equip["hp_bonus"] = int(equip["hp_bonus"] * 1.5)
    
    # 史诗/传说有概率带特殊属性
    elif rarity in ["史诗", "传说"] and random.random() < RARITY[rarity]["special_chance"]:
        special_options = [
            {"name": "吸血", "value": random.randint(2, 5)},
            {"name": "反伤", "value": random.randint(5, 10)},
            {"name": "护盾", "value": random.randint(10, 20)},
        ]
        equip["special"] = random.choice(special_options)
    
    return equip


def generate_drop(monster_level, is_boss=False):
    """生成怪物掉落装备（可能掉落武器或护甲）"""
    rarity = get_rarity_by_monster_level(monster_level)
    
    # Boss掉落概率更高
    if is_boss and not rarity:
        rarity = "普通"
    elif is_boss:
        # Boss更容易掉好东西
        roll = random.random()
        if roll < 0.10:
            rarity = "传说"
        elif roll < 0.30:
            rarity = "史诗"
        elif roll < 0.50:
            rarity = "稀有"
        else:
            rarity = "普通"
    
    if not rarity:
        return None
    
    # 检查极品装备掉落
    is_perfect = False
    if not is_boss and random.random() < get_perfect_drop_chance(monster_level):
        is_perfect = True
    elif is_boss and random.random() < 0.05:  # Boss 5% 极品
        is_perfect = True
    
    # 生成武器或护甲
    if random.random() < 0.5:
        return generate_weapon(monster_level, rarity, is_perfect, is_boss)
    else:
        return generate_armor(monster_level, rarity, is_perfect, is_boss)


def get_drop_summary(equip):
    """获取装备掉落摘要"""
    if not equip:
        return None
    
    rarity_color = equip.get("rarity_color", "#AAAAAA")
    name = equip["name"]
    level_req = equip["level_req"]
    is_perfect = equip.get("is_perfect", False)
    
    if is_perfect:
        info = f"[极品] {name} (无等级限制)"
    else:
        info = f"[{equip['rarity']}] {name} (Lv.{level_req}+)"
    
    if equip["type"] == "weapon":
        info += f" ATK:{equip['attack']} CRIT:{equip['crit_rate']}%"
    else:
        info += f" DEF:{equip['defense']} HP+:{equip['hp_bonus']}"
    
    if equip.get("special"):
        info += f" [{equip['special']['name']}+{equip['special']['value']}]"
    
    return info
