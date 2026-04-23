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
    """根据怪物等级确定掉落稀有度（重设计版 - 掉率大幅提升）"""
    roll = random.random()
    
    if level >= 20:  # 高级地图
        if roll < 0.05:    # 5%传说
            return "传说"
        elif roll < 0.20:   # 15%史诗
            return "史诗"
        elif roll < 0.45:   # 25%稀有
            return "稀有"
        else:              # 55%普通
            return "普通"
            
    elif level >= 15:  # 中级地图
        if roll < 0.02:
            return "传说"
        elif roll < 0.10:
            return "史诗"
        elif roll < 0.25:
            return "稀有"
        elif roll < 0.50:
            return "普通"
        else:
            return None
            
    elif level >= 10:  # 初级进阶
        if roll < 0.05:
            return "史诗"
        elif roll < 0.20:
            return "稀有"
        elif roll < 0.50:
            return "普通"
        else:
            return None
            
    else:  # 新手地图 (Lv1-9)
        if roll < 0.10:
            return "稀有"
        elif roll < 0.40:
            return "普通"
        else:
            return None


def get_perfect_drop_chance(level, is_boss=False):
    """获取极品装备掉落概率（重设计版）"""
    if is_boss:
        return 0.08  # Boss 8%
    if level >= 20:
        return 0.03  # 3%
    elif level >= 15:
        return 0.015  # 1.5%
    elif level >= 10:
        return 0.008  # 0.8%
    return 0.003  # Lv1-9: 0.3%


def generate_weapon(level, rarity="普通", is_perfect=False, is_boss=False):
    """生成武器（重设计版 - 属性范围扩大，暴击伤害差异化）"""
    base_stats = {
        "普通": {"attack": (8, 20), "crit_rate": (0, 5), "crit_dmg": (150, 150)},
        "稀有": {"attack": (22, 45), "crit_rate": (5, 12), "crit_dmg": (150, 160)},
        "史诗": {"attack": (50, 90), "crit_rate": (12, 22), "crit_dmg": (160, 180)},
        "传说": {"attack": (100, 150), "crit_rate": (20, 35), "crit_dmg": (170, 200)},
    }
    
    stats = base_stats.get(rarity, base_stats["普通"])
    
    # 缩放公式：每级+3%基础属性（比旧版+5%更温和）
    scale = 1 + (level - 1) * 0.03
    if is_boss:
        scale *= 1.25  # Boss加成25%
    
    attack = int(random.randint(stats["attack"][0], stats["attack"][1]) * scale)
    crit_rate = min(50, random.randint(stats["crit_rate"][0], stats["crit_rate"][1]))
    crit_dmg = random.randint(stats["crit_dmg"][0], stats["crit_dmg"][1])
    
    name = generate_weapon_name(is_perfect)
    
    equip = {
        "name": name,
        "type": "weapon",
        "rarity": "极品" if is_perfect else rarity,
        "rarity_color": "#FF5555" if is_perfect else RARITY.get(rarity, {}).get("color", "#AAAAAA"),
        "attack": attack,
        "crit_rate": crit_rate,
        "crit_dmg": crit_dmg,
        "special": None,
        "level_req": 0 if is_perfect else max(1, level - 2),
        "is_perfect": is_perfect,
    }
    
    # 极品装备：在传说基础上×1.4，无等级限制，必带特殊属性，暴击伤害固定200%
    if is_perfect:
        equip["attack"] = int(equip["attack"] * 1.4)
        equip["crit_rate"] = min(50, int(equip["crit_rate"] * 1.2))
        equip["level_req"] = 0
        equip["crit_dmg"] = 200
        equip["special"] = random.choice([
            {"name": "吸血", "value": random.randint(10, 20)},
            {"name": "破甲", "value": random.randint(15, 25)},
            {"name": "连击", "value": random.randint(10, 18)},
        ])
    
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
    """生成护甲（重设计版 - 属性范围扩大）"""
    base_stats = {
        "普通": {"defense": (4, 12), "hp_bonus": (20, 60)},
        "稀有": {"defense": (15, 35), "hp_bonus": (70, 150)},
        "史诗": {"defense": (40, 75), "hp_bonus": (180, 320)},
        "传说": {"defense": (85, 140), "hp_bonus": (380, 600)},
    }
    
    stats = base_stats.get(rarity, base_stats["普通"])
    scale = 1 + (level - 1) * 0.03
    if is_boss:
        scale *= 1.25
    
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
    
    # 极品装备：在传说基础上×1.4，无等级限制，必带特殊属性
    if is_perfect:
        equip["defense"] = int(equip["defense"] * 1.4)
        equip["hp_bonus"] = int(equip["hp_bonus"] * 1.4)
        equip["level_req"] = 0
        equip["special"] = random.choice([
            {"name": "吸血", "value": random.randint(10, 20)},
            {"name": "反伤", "value": random.randint(15, 25)},
            {"name": "护盾", "value": random.randint(15, 30)},
        ])
    
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
    if random.random() < get_perfect_drop_chance(monster_level, is_boss):
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
