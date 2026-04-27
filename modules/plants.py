"""
植物模块 - 植物种子目录与生长系统
rarity: 0普通(5G) 1少见(10G) 2稀有(15G) 3珍藏(20G) 4传说(25G)
"""
import time

MUTATION_CHANCE = 0.05  # 5%变异概率

PLANTS_CATALOG = [
    # ── 普通 5G ──
    {"id": "clover",       "name": "🍀 幸运草",      "desc": "四叶草，快速成长",          "rarity": 0, "seed_price": 5,  "grow_time_s": 60,  "adult_lifespan_s": 300,  "harvest_gold": 2,  "harvest_interval_s": 30, "icon": "🍀"},
    {"id": "moonlight",    "name": "🌿 月光草",      "desc": "夜间叶片微光",              "rarity": 0, "seed_price": 5,  "grow_time_s": 80,  "adult_lifespan_s": 360,  "harvest_gold": 3,  "harvest_interval_s": 30, "icon": "🌿"},
    {"id": "glowmoss",     "name": "🌿 微光苔",       "desc": "星尘雾气中自发光",          "rarity": 0, "seed_price": 5,  "grow_time_s": 70,  "adult_lifespan_s": 330,  "harvest_gold": 2,  "harvest_interval_s": 25, "icon": "🌿"},
    {"id": "bubblemush",   "name": "🍄 泡泡菇",       "desc": "释放无害彩色泡泡",          "rarity": 0, "seed_price": 5,  "grow_time_s": 90,  "adult_lifespan_s": 420,  "harvest_gold": 3,  "harvest_interval_s": 35, "icon": "🍄"},
    {"id": "sweetvine",    "name": "🌿 甜梦藤",       "desc": "助眠安神的廉价饮品",        "rarity": 0, "seed_price": 5,  "grow_time_s": 75,  "adult_lifespan_s": 350,  "harvest_gold": 2,  "harvest_interval_s": 28, "icon": "🌿"},

    # ── 少见 10G ──
    {"id": "mushroom",     "name": "🍄 跳舞蘑菇",    "desc": "随节拍摇摆的奇妙菌类",      "rarity": 1, "seed_price": 10, "grow_time_s": 120, "adult_lifespan_s": 600,  "harvest_gold": 6,  "harvest_interval_s": 45, "icon": "🍄"},
    {"id": "coppervine",  "name": "🌿 铜鳞藤",       "desc": "藤蔓覆盖铜色鳞片",          "rarity": 1, "seed_price": 10, "grow_time_s": 150, "adult_lifespan_s": 720,  "harvest_gold": 8,  "harvest_interval_s": 60, "icon": "🌿"},
    {"id": "lotus_light", "name": "🌸 幻光莲",       "desc": "花瓣随情绪变色",            "rarity": 1, "seed_price": 10, "grow_time_s": 180, "adult_lifespan_s": 900,  "harvest_gold": 10, "harvest_interval_s": 70, "icon": "🌸"},
    {"id": "stardustcotton","name": "🌸 星尘棉",      "desc": "棉絮能吸附星尘",            "rarity": 1, "seed_price": 10, "grow_time_s": 160, "adult_lifespan_s": 800,  "harvest_gold": 9,  "harvest_interval_s": 65, "icon": "🌸"},
    {"id": "echogourd",   "name": "🎃 回声瓜",       "desc": "敲击时会重复声音",          "rarity": 1, "seed_price": 10, "grow_time_s": 140, "adult_lifespan_s": 700,  "harvest_gold": 7,  "harvest_interval_s": 55, "icon": "🎃"},

    # ── 稀有 15G ──
    {"id": "crystal_flower","name": "✨ 发光萤石花",  "desc": "黑暗中绽放的晶体之花",      "rarity": 2, "seed_price": 15, "grow_time_s": 300, "adult_lifespan_s": 1200, "harvest_gold": 15, "harvest_interval_s": 90, "icon": "✨"},
    {"id": "frostflower",  "name": "❄️ 冻脉花",       "desc": "花瓣常年覆盖薄冰",          "rarity": 2, "seed_price": 15, "grow_time_s": 360, "adult_lifespan_s": 1440, "harvest_gold": 18, "harvest_interval_s": 100,"icon": "❄️"},
    {"id": "bloodroot",    "name": "🌿 血根草",       "desc": "根部鲜红如血",              "rarity": 2, "seed_price": 15, "grow_time_s": 330, "adult_lifespan_s": 1320, "harvest_gold": 16, "harvest_interval_s": 95, "icon": "🌿"},
    {"id": "gemcactus",    "name": "🌵 宝石仙人掌",   "desc": "刺尖凝结细小水晶",          "rarity": 2, "seed_price": 15, "grow_time_s": 380, "adult_lifespan_s": 1500, "harvest_gold": 20, "harvest_interval_s": 110,"icon": "🌵"},
    {"id": "gravityoak",   "name": "🌳 重力橡树",     "desc": "树干内产生局部重力异常",    "rarity": 2, "seed_price": 15, "grow_time_s": 420, "adult_lifespan_s": 1680, "harvest_gold": 22, "harvest_interval_s": 120,"icon": "🌳"},
    {"id": "mistlotus",    "name": "🌸 幻雾莲",       "desc": "释放致幻孢子云",            "rarity": 2, "seed_price": 15, "grow_time_s": 350, "adult_lifespan_s": 1400, "harvest_gold": 17, "harvest_interval_s": 105,"icon": "🌸"},

    # ── 珍藏 20G ──
    {"id": "rainbow_shell","name": "🪩 彩虹贝壳花",  "desc": "折射七彩光芒",              "rarity": 3, "seed_price": 20, "grow_time_s": 600, "adult_lifespan_s": 2400, "harvest_gold": 35, "harvest_interval_s": 120,"icon": "🪩"},
    {"id": "dragonpepper", "name": "🌶️ 龙息椒",       "desc": "果实内封存龙息火焰",        "rarity": 3, "seed_price": 20, "grow_time_s": 720, "adult_lifespan_s": 2880, "harvest_gold": 42, "harvest_interval_s": 140,"icon": "🌶️"},
    {"id": "startear",     "name": "🌸 星泪树",       "desc": "落叶如流星坠落",            "rarity": 3, "seed_price": 20, "grow_time_s": 900, "adult_lifespan_s": 3600, "harvest_gold": 50, "harvest_interval_s": 160,"icon": "🌸"},
    {"id": "goldpumpkin",  "name": "🎃 黄金南瓜",     "desc": "果肉坚硬如黄金永不腐烂",    "rarity": 3, "seed_price": 20, "grow_time_s": 840, "adult_lifespan_s": 3360, "harvest_gold": 48, "harvest_interval_s": 150,"icon": "🎃"},
    {"id": "lawvine",      "name": "🌿 法则藤蔓",     "desc": "每7天产出一枚完整法则碎片", "rarity": 3, "seed_price": 20, "grow_time_s": 1000,"adult_lifespan_s": 4000, "harvest_gold": 55, "harvest_interval_s": 180,"icon": "🌿"},

    # ── 传说 25G ──
    {"id": "moon_crystal", "name": "💎 月亮水晶藤",  "desc": "汲取月光生长的传说植物",    "rarity": 4, "seed_price": 25, "grow_time_s": 1200,"adult_lifespan_s": 3600, "harvest_gold": 80, "harvest_interval_s": 180,"icon": "💎"},
    {"id": "eternalrose", "name": "🌹 永恒玫瑰",     "desc": "永不凋谢，正午释放时停领域","rarity": 4, "seed_price": 25, "grow_time_s": 1500,"adult_lifespan_s": 5400, "harvest_gold": 100,"harvest_interval_s": 200,"icon": "🌹"},
    {"id": "clockflower",  "name": "⏰ 时计花",       "desc": "花朵呈钟表状，正午时间静止","rarity": 4, "seed_price": 25, "grow_time_s": 1800,"adult_lifespan_s": 7200, "harvest_gold": 120,"harvest_interval_s": 240,"icon": "⏰"},
    {"id": "worldtree",   "name": "🌲 世界树之苗",   "desc": "九界之树，树冠下作物加速",  "rarity": 4, "seed_price": 25, "grow_time_s": 2400,"adult_lifespan_s": 10800,"harvest_gold": 150,"harvest_interval_s": 300,"icon": "🌲"},

    # ── P0-B1 新增 ──
    # ── 普通 5G ──
    {"id": "gold_grass",   "name": "🌾 金穗草",      "desc": "麦穗在阳光下闪着金光",      "rarity": 0, "seed_price": 5,  "grow_time_s": 65,  "adult_lifespan_s": 310,  "harvest_gold": 3,  "harvest_interval_s": 28, "icon": "🌾"},
    {"id": "sunflower",    "name": "🌻 向日葵",      "desc": "永远朝着太阳的方向",        "rarity": 0, "seed_price": 5,  "grow_time_s": 85,  "adult_lifespan_s": 380,  "harvest_gold": 4, "harvest_interval_s": 32, "icon": "🌻"},
    {"id": "mint",         "name": "🌿 薄荷",        "desc": "清凉的香气沁人心脾",        "rarity": 0, "seed_price": 5,  "grow_time_s": 70,  "adult_lifespan_s": 330,  "harvest_gold": 2,  "harvest_interval_s": 26, "icon": "🌿"},

    # ── 少见 10G ──
    {"id": "fire_flower",  "name": "🌺 火焰花",      "desc": "花瓣尖端燃烧着不灭的火焰",  "rarity": 1, "seed_price": 10, "grow_time_s": 170,  "adult_lifespan_s": 780,  "harvest_gold": 9, "harvest_interval_s": 60, "icon": "🌺"},
    {"id": "thorn_vine",   "name": "🥀 荆棘藤",      "desc": "藤蔓上长满尖锐的刺",        "rarity": 1, "seed_price": 10, "grow_time_s": 150,  "adult_lifespan_s": 650,  "harvest_gold": 7, "harvest_interval_s": 50, "icon": "🥀"},
    {"id": "silver_leaf",  "name": "🍃 银叶草",      "desc": "叶片泛着金属光泽",          "rarity": 1, "seed_price": 10, "grow_time_s": 130,  "adult_lifespan_s": 580,  "harvest_gold": 6, "harvest_interval_s": 48, "icon": "🍃"},

    # ── 稀有 15G ──
    {"id": "shadow_orchid","name": "🌸 暗影兰",      "desc": "只在月光下绽放的神秘兰花",  "rarity": 2, "seed_price": 15, "grow_time_s": 340, "adult_lifespan_s": 1360,  "harvest_gold": 18, "harvest_interval_s": 100, "icon": "🌸"},
    {"id": "desert_cactus","name": "🌵 沙漠仙人掌",  "desc": "能在极端环境中存储生命之水",  "rarity": 2, "seed_price": 15, "grow_time_s": 390, "adult_lifespan_s": 1550,  "harvest_gold": 21, "harvest_interval_s": 115, "icon": "🌵"},
    {"id": "crystal_kelp", "name": "🌊 水晶海藻",    "desc": "半透明的海藻折射七彩光芒",  "rarity": 2, "seed_price": 15, "grow_time_s": 310, "adult_lifespan_s": 1250,  "harvest_gold": 16, "harvest_interval_s": 92, "icon": "🌊"},

    # ── 珍藏 20G ──
    {"id": "life_fruit_tree","name": "🍎 生命果实树", "desc": "传说食其果可延年益寿",      "rarity": 3, "seed_price": 20, "grow_time_s": 780, "adult_lifespan_s": 3100, "harvest_gold": 45,  "harvest_interval_s": 145, "icon": "🍎"},
    {"id": "star_grass",   "name": "🌟 星辰草",      "desc": "每片叶子都像一颗星星",      "rarity": 3, "seed_price": 20, "grow_time_s": 660, "adult_lifespan_s": 2600,  "harvest_gold": 38,  "harvest_interval_s": 130, "icon": "🌟"},
    {"id": "eternal_pumpkin","name":"🎃 永恒南瓜",   "desc": "永远不会腐烂的神奇南瓜",    "rarity": 3, "seed_price": 20, "grow_time_s": 920, "adult_lifespan_s": 3600, "harvest_gold": 52, "harvest_interval_s": 170, "icon": "🎃"},

    # ── 传说 25G ──
    {"id": "world_flower", "name": "🌐 世界花",      "desc": "花蕊中能看到整个世界的缩影",  "rarity": 4, "seed_price": 25, "grow_time_s": 1800, "adult_lifespan_s": 7200, "harvest_gold": 130, "harvest_interval_s": 250,"icon": "🌐"},
    {"id": "genesis_crystal","name":"💎 创世晶花",   "desc": "据说世界诞生时开的第一朵花",  "rarity": 4, "seed_price": 25, "grow_time_s": 2100, "adult_lifespan_s": 9000, "harvest_gold": 145, "harvest_interval_s": 280,"icon": "💎"},
    {"id": "void_bloom",   "name": "🌀 虚空之花",    "desc": "来自虚空的奇异花朵",        "rarity": 4, "seed_price": 25, "grow_time_s": 1600, "adult_lifespan_s": 6000, "harvest_gold": 110, "harvest_interval_s": 220,"icon": "🌀"},
]

PLANT_RARITY_COLORS = {
    0: "#888888",
    1: "#2E7D32",
    2: "#1565C0",
    3: "#6A1B9A",
    4: "#E65100",
}

PLANT_RARITY_NAMES = {
    0: "普通",
    1: "少见",
    2: "稀有",
    3: "珍藏",
    4: "传说",
}

MAX_PLANTS = 10

def get_plant_catalog():
    return PLANTS_CATALOG

def get_plant_by_id(plant_id):
    for p in PLANTS_CATALOG:
        if p["id"] == plant_id:
            return p
    return None

def calc_grow_stage(elapsed_s, grow_time_s):
    if elapsed_s < grow_time_s * 0.33:
        return 0
    elif elapsed_s < grow_time_s * 0.66:
        return 1
    elif elapsed_s < grow_time_s:
        return 2
    else:
        return 3

STAGE_NAMES = ["🌰 种子", "🌱 发芽", "🌿 幼苗", "🌳 成年"]
STAGE_ICONS = {0: "🌰", 1: "🌱", 2: "🌿", 3: "🌳"}
