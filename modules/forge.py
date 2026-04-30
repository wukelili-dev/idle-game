"""
锻造与强化系统 — 强化（+1~+10）+ 锻造配方 + 套装效果
"""
import random

# ═══════════════════ 强化配置（+1~+10）═══════════════════
# 每级: bonus_pct (基础属性加成%), cost (铁矿+金币), success_rate
FORTIFY_CONFIG = [
    # level, bonus_pct, 铁矿, 金币, success_rate
    (1,  5,   5,   50,   1.00),
    (2,  10,  10,  100,  0.95),
    (3,  15,  20,  200,  0.90),
    (4,  20,  35,  350,  0.80),
    (5,  25,  50,  500,  0.70),
    (6,  30,  70,  700,  0.55),
    (7,  40,  100, 1000, 0.40),
    (8,  50,  150, 1500, 0.25),
    (9,  65,  200, 2000, 0.15),
    (10, 80,  300, 3000, 0.05),
]

# 保护符: 消耗1张护锻符保护失败不掉级
PROTECT_CHARM_COST = {"铁矿": 50, "金币": 500}  # 护锻符合成成本


def get_fortify_info(level):
    """获取指定强化等级的信息（0-based index = level-1）"""
    if level < 1 or level > 10:
        return None
    lvl, bonus, iron, gold, rate = FORTIFY_CONFIG[level - 1]
    return {"level": lvl, "bonus_pct": bonus, "cost": {"铁矿": iron, "金币": gold}, "success_rate": rate}


def get_fortify_bonus(forge_level):
    """获取指定强化等级的属性加成倍率"""
    if forge_level <= 0:
        return 1.0
    info = get_fortify_info(forge_level)
    if not info:
        return 1.0
    return 1.0 + info["bonus_pct"] / 100.0


# ═══════════════════ 锻造配方 ═══════════════════
# 每件装备: name, type, stats, passive, core_material, iron_cost, gold_cost

FORGE_RECIPES = [
    # ── 白品质材料锻造 → 基础型装备 ──
    {"name": "霜绒软甲", "type": "armor", "defense": 25, "hp_bonus": 80,
     "passive": {"name": "闪避", "desc": "闪避+8%", "dodge": 8},
     "material": "霜绒", "material_count": 10, "iron": 30, "gold": 200, "rarity": 0,
     "forge_set": None},
    {"name": "蟾露短刃", "type": "weapon", "attack": 35, "crit_rate": 10, "crit_dmg": 150,
     "passive": {"name": "毒伤", "desc": "攻击附带3%最大生命毒伤", "poison_pct": 3},
     "material": "蟾露", "material_count": 10, "iron": 30, "gold": 200, "rarity": 0,
     "forge_set": None},
    {"name": "翠甲圆盾", "type": "armor", "defense": 30, "hp_bonus": 60,
     "passive": {"name": "铁壁", "desc": "防御+10%", "def_pct": 10},
     "material": "翠甲", "material_count": 10, "iron": 30, "gold": 200, "rarity": 0,
     "forge_set": None},
    {"name": "凤卵法杖", "type": "weapon", "attack": 30, "crit_rate": 8, "crit_dmg": 150,
     "passive": {"name": "生机", "desc": "战斗开始回复10%HP", "start_heal_pct": 10},
     "material": "凤卵", "material_count": 10, "iron": 30, "gold": 200, "rarity": 0,
     "forge_set": None},

    # ── 绿品质材料锻造 → 进阶型装备 ──
    {"name": "招财护符", "type": "armor", "defense": 35, "hp_bonus": 120,
     "passive": {"name": "招财", "desc": "金币掉落+15%", "gold_bonus_pct": 15},
     "material": "金蟾油", "material_count": 10, "iron": 50, "gold": 500, "rarity": 1,
     "forge_set": None},
    {"name": "噬牙短剑", "type": "weapon", "attack": 50, "crit_rate": 12, "crit_dmg": 150,
     "passive": {"name": "狂战", "desc": "攻击+8%", "atk_pct": 8},
     "material": "犬牙", "material_count": 10, "iron": 50, "gold": 500, "rarity": 1,
     "forge_set": None},
    {"name": "暗噬之刃", "type": "weapon", "attack": 55, "crit_rate": 15, "crit_dmg": 150,
     "passive": {"name": "噬魂", "desc": "击杀回复3%HP", "kill_heal_pct": 3},
     "material": "暗凝胶", "material_count": 10, "iron": 50, "gold": 500, "rarity": 1,
     "forge_set": None},
    {"name": "镀金护手", "type": "weapon", "attack": 48, "crit_rate": 10, "crit_dmg": 150,
     "passive": {"name": "贪婪", "desc": "击杀怪物金币+20%", "kill_gold_pct": 20},
     "material": "黄金凝胶", "material_count": 10, "iron": 50, "gold": 500, "rarity": 1,
     "forge_set": None},

    # ── 蓝品质材料锻造 → 强力型装备 ──
    {"name": "凤羽长弓", "type": "weapon", "attack": 85, "crit_rate": 18, "crit_dmg": 150,
     "passive": {"name": "涅槃", "desc": "濒死回复30%HP（每场1次）", "death_save_heal": 30},
     "material": "凤羽", "material_count": 15, "iron": 80, "gold": 1000, "rarity": 2,
     "forge_set": None},
    {"name": "鹤翎剑", "type": "weapon", "attack": 78, "crit_rate": 25, "crit_dmg": 150,
     "passive": {"name": "长生", "desc": "每3回合回复5%HP", "regen_interval": 3, "regen_pct": 5},
     "material": "鹤羽", "material_count": 15, "iron": 60, "gold": 1000, "rarity": 2,
     "forge_set": None},
    {"name": "虎骨碎锤", "type": "weapon", "attack": 120, "crit_rate": 8, "crit_dmg": 170,
     "passive": {"name": "碎骨", "desc": "暴击时额外+20%暴击伤害", "crit_bonus_pct": 20},
     "material": "虎骨", "material_count": 15, "iron": 120, "gold": 1200, "rarity": 2,
     "forge_set": None},
    {"name": "玄甲重铠", "type": "armor", "defense": 55, "hp_bonus": 300,
     "passive": {"name": "荆棘", "desc": "防御+15%，受击5%概率眩晕攻击者", "def_pct": 15, "stun_chance": 5},
     "material": "金龟壳", "material_count": 10, "iron": 80, "gold": 1000, "rarity": 2,
     "forge_set": None},
    {"name": "王鬃战盔", "type": "weapon", "attack": 100, "crit_rate": 15, "crit_dmg": 150,
     "passive": {"name": "威压", "desc": "攻击+10%，首回合伤害+15%", "atk_pct": 10, "first_strike_pct": 15},
     "material": "王鬃", "material_count": 15, "iron": 100, "gold": 1100, "rarity": 2,
     "forge_set": None},
    {"name": "嗜血狼牙", "type": "weapon", "attack": 92, "crit_rate": 12, "crit_dmg": 150,
     "passive": {"name": "嗜血", "desc": "击杀后攻击+8%持续2回合", "kill_atk_buff": 8, "kill_buff_turns": 2},
     "material": "狼牙", "material_count": 15, "iron": 100, "gold": 1100, "rarity": 2,
     "forge_set": None},
    {"name": "暗影豹刺", "type": "weapon", "attack": 95, "crit_rate": 20, "crit_dmg": 150,
     "passive": {"name": "破甲", "desc": "攻击15%概率无视防御", "ignore_def_chance": 15},
     "material": "玄影豹皮", "material_count": 15, "iron": 90, "gold": 1100, "rarity": 2,
     "forge_set": None},
    {"name": "熊罴铁壁", "type": "armor", "defense": 65, "hp_bonus": 350,
     "passive": {"name": "铁壁", "desc": "HP+15%", "hp_pct": 15},
     "material": "熊胆", "material_count": 15, "iron": 100, "gold": 1100, "rarity": 2,
     "forge_set": None},
    {"name": "幻狐之刃", "type": "weapon", "attack": 90, "crit_rate": 22, "crit_dmg": 150,
     "passive": {"name": "幻惑", "desc": "10%概率使敌人混乱1回合", "confuse_chance": 10},
     "material": "狐尾", "material_count": 15, "iron": 90, "gold": 1100, "rarity": 2,
     "forge_set": None},
    {"name": "焚天刃", "type": "weapon", "attack": 98, "crit_rate": 18, "crit_dmg": 150,
     "passive": {"name": "焚天", "desc": "攻击附带5%攻击力的火焰伤害", "fire_dmg_pct": 5},
     "material": "火狐毛", "material_count": 15, "iron": 100, "gold": 1100, "rarity": 2,
     "forge_set": None},
    {"name": "灵森法衣", "type": "armor", "defense": 42, "hp_bonus": 280,
     "passive": {"name": "灵森", "desc": "每5回合回复8%HP", "regen_interval": 5, "regen_pct": 8},
     "material": "精灵粉", "material_count": 15, "iron": 80, "gold": 1000, "rarity": 2,
     "forge_set": None},

    # ── 紫品质材料锻造 → 稀有型装备 ──
    {"name": "冲锋角铠", "type": "armor", "defense": 60, "hp_bonus": 320,
     "passive": {"name": "冲锋", "desc": "首回合攻击+25%", "first_strike_pct": 25},
     "material": "甲犀角", "material_count": 10, "iron": 150, "gold": 2000, "rarity": 3,
     "forge_set": None},
    {"name": "玄心玉佩", "type": "armor", "defense": 48, "hp_bonus": 400,
     "passive": {"name": "玄心", "desc": "全属性+5%", "all_stats_pct": 5},
     "material": "竹心", "material_count": 10, "iron": 150, "gold": 2000, "rarity": 3,
     "forge_set": None},
    {"name": "圣羽法杖", "type": "weapon", "attack": 70, "crit_rate": 15, "crit_dmg": 150,
     "passive": {"name": "圣佑", "desc": "受致命伤害免死1次（保留1HP），每场限1次", "death_save": True},
     "material": "圣羽", "material_count": 10, "iron": 150, "gold": 2000, "rarity": 3,
     "forge_set": None},
    {"name": "五行灵环", "type": "armor", "defense": 50, "hp_bonus": 350,
     "passive": {"name": "五行", "desc": "每场随机：攻+10%/防+10%/暴击+10%/吸血+8%/HP+10%",
                "random_buff": True},
     "material": "灵叶", "material_count": 10, "iron": 150, "gold": 2000, "rarity": 3,
     "forge_set": None},

    # ── 橙品质材料锻造 → 传说型装备 ──
    {"name": "垂云杖", "type": "weapon", "attack": 150, "crit_rate": 15, "crit_dmg": 150,
     "passive": {"name": "云盾", "desc": "每2回合获云盾（吸收15%最大HP伤害）",
                "cloud_shield_interval": 2, "cloud_shield_pct": 15},
     "material": "云须", "material_count": 20, "iron": 200, "gold": 5000, "rarity": 4,
     "forge_set": "垂云套"},
    {"name": "浪淘沙刃", "type": "weapon", "attack": 160, "crit_rate": 20, "crit_dmg": 150,
     "passive": {"name": "破浪", "desc": "无视20%防御", "ignore_def_pct": 20},
     "material": "浪核", "material_count": 20, "iron": 250, "gold": 5000, "rarity": 4,
     "forge_set": "垂云套"},
    {"name": "范式圣剑", "type": "weapon", "attack": 140, "crit_rate": 25, "crit_dmg": 150,
     "passive": {"name": "牺牲", "desc": "死亡时队友+20%攻击3回合",
                "death_buff_atk_pct": 20, "death_buff_turns": 3},
     "material": "薪火", "material_count": 20, "iron": 200, "gold": 5000, "rarity": 4,
     "forge_set": "垂云套"},
    {"name": "颜如玉卷", "type": "weapon", "attack": 130, "crit_rate": 18, "crit_dmg": 150,
     "passive": {"name": "书香", "desc": "经验+25% 金币+25%", "exp_bonus_pct": 25, "gold_bonus_pct": 25},
     "material": "书香", "material_count": 20, "iron": 180, "gold": 5000, "rarity": 4,
     "forge_set": "垂云套"},
]

# ═══════════════════ 套装效果 ═══════════════════
SET_EFFECTS = {
    "垂云套": {
        "pieces": ["垂云杖", "浪淘沙刃", "范式圣剑", "颜如玉卷"],
        "effects": {
            2: {"desc": "全属性+5%", "all_stats_pct": 5},
            3: {"desc": "全属性+10% + 每回合云盾", "all_stats_pct": 10, "cloud_shield_per_turn": True},
        },
    },
}

# ═══════════════════ 锻造装备颜色（按材料品质）═══════════════════
FORGE_RARITY_COLORS = {
    0: "#cccccc",  # 白
    1: "#4caf50",  # 绿
    2: "#2196f3",  # 蓝
    3: "#9c27b0",  # 紫
    4: "#ff9800",  # 橙
}


def get_forge_recipe_by_name(name):
    """根据名称查找锻造配方"""
    for r in FORGE_RECIPES:
        if r["name"] == name:
            return r
    return None


def get_forge_recipes_by_rarity(rarity):
    """获取指定品质的锻造配方"""
    return [r for r in FORGE_RECIPES if r["rarity"] == rarity]


def get_all_forge_recipes():
    """获取所有锻造配方"""
    return FORGE_RECIPES


def get_set_effect(forge_set, piece_count):
    """获取套装效果"""
    if not forge_set or forge_set not in SET_EFFECTS:
        return None
    effects = SET_EFFECTS[forge_set]["effects"]
    result = None
    for threshold in sorted(effects.keys()):
        if piece_count >= threshold:
            result = effects[threshold]
    return result


def build_forged_equip(recipe):
    """根据配方构建锻造装备dict"""
    equip = {
        "name": recipe["name"],
        "type": recipe["type"],
        "rarity": "锻造",
        "rarity_color": FORGE_RARITY_COLORS.get(recipe["rarity"], "#cccccc"),
        "level_req": 1,
        "is_perfect": False,
        "sell_price": recipe["gold"] // 2,
        # 锻造专属字段
        "forge_level": 0,
        "is_forged": True,
        "forge_set": recipe.get("forge_set"),
        "passive": recipe["passive"],
    }
    if recipe["type"] == "weapon":
        equip["attack"] = recipe["attack"]
        equip["crit_rate"] = recipe["crit_rate"]
        equip["crit_dmg"] = recipe.get("crit_dmg", 150)
        equip["special"] = None
    else:
        equip["defense"] = recipe["defense"]
        equip["hp_bonus"] = recipe["hp_bonus"]
        equip["special"] = None
    return equip


def count_set_pieces(equipment_list, forge_set):
    """统计hero身上同套装的锻造装备数量（weapon + armor）"""
    if not forge_set:
        return 0
    count = 0
    for equip in equipment_list:
        if equip and isinstance(equip, dict) and equip.get("forge_set") == forge_set:
            count += 1
    return count
