"""
背包模块 - 背包数据与物品管理
"""
import random


# ── Novelty Shop Items ──
NOVELTY_ITEMS = [
    # 普通 (5-8G)
    {"name": "🍀 幸运草",        "desc": "据说能带来好运的四叶草",  "price": 5, "rarity_idx": 0,
     "kind": "plant_seed", "plant_id": "clover"},
    {"name": "🗺️ 破旧地图碎片",  "desc": "像是某个宝藏的一部分",    "price": 8,  "rarity_idx": 0},
    {"name": "🐚 普通贝壳",      "desc": "大海的味道，若有若无",    "price": 6,  "rarity_idx": 0},
    {"name": "🪶 褪色羽毛",      "desc": "曾经鲜艳，如今黯淡",     "price": 5,  "rarity_idx": 0},
    {"name": "🪨 普通石头",       "desc": "形状还算圆润",            "price": 3,  "rarity_idx": 0},
    # 少见 (10-20G)
    {"name": "🍄 跳舞的蘑菇",    "desc": "随着节拍轻轻摇摆",        "price": 10, "rarity_idx": 1,
     "kind": "plant_seed", "plant_id": "mushroom"},
    {"name": "🔮 迷你水晶球",    "desc": "偶尔会闪烁一下",          "price": 20, "rarity_idx": 1},
    {"name": "🕯️ 永不熄灭的蜡烛", "desc": "火焰永不熄灭",           "price": 18, "rarity_idx": 1},
    {"name": "✨ 发光萤石",       "desc": "在黑暗中散发柔光",       "price": 16, "rarity_idx": 1},
    {"name": "🌱 沉睡的种子",    "desc": "似乎永远不会发芽",        "price": 12, "rarity_idx": 1},
    {"name": "🎃 迷你南瓜灯",    "desc": "万圣节纪念品",            "price": 14, "rarity_idx": 1},
    {"name": "🧊 冰冻的眼泪",    "desc": "永远不会融化的冰晶",     "price": 19, "rarity_idx": 1},
    # 稀有 (22-38G)
    {"name": "🐚 会说话的贝壳",  "desc": "会重复最后听到的话",     "price": 25, "rarity_idx": 2},
    {"name": "🎈 装在瓶中的微风", "desc": "打开时会有风轻轻吹过",   "price": 22, "rarity_idx": 2},
    {"name": "🔮 占卜水晶球",    "desc": "偶尔能看到模糊的影像",   "price": 30, "rarity_idx": 2},
    {"name": "🎵 会唱歌的水晶",  "desc": "轻敲会发出清脆声响",     "price": 28, "rarity_idx": 2},
    {"name": "🧱 谜之方块",      "desc": "没人知道它是怎么出现的", "price": 33, "rarity_idx": 2},
    {"name": "🔭 迷你望远镜",    "desc": "据说能看见月亮背面",      "price": 35, "rarity_idx": 2},
    # 珍藏 (40-55G)
    {"name": "🪩 彩虹贝壳",       "desc": "折射出七彩光芒",         "price": 45, "rarity_idx": 3},
    {"name": "❄️ 跳舞的雪花",     "desc": "在温暖的地方也能存在",   "price": 48, "rarity_idx": 3},
    {"name": "💎 月亮碎片",       "desc": "散发着淡淡的银光",       "price": 52, "rarity_idx": 3},
    {"name": "🌈 凝固的彩虹",    "desc": "触碰它就会消失",          "price": 55, "rarity_idx": 3},
    # 传说 (60G+)
    {"name": "🧬 时间的沙漏",     "desc": "沙子流向不明",            "price": 65, "rarity_idx": 4},
    {"name": "🌙 梦境碎片",       "desc": "收藏着一个完整的梦",     "price": 70, "rarity_idx": 4},
    {"name": "⭐ 坠落的流星",    "desc": "许愿成功率提升100%",      "price": 80, "rarity_idx": 4},
]

NOVELTY_RARITY_COLORS = {
    0: "#888888",  # 普通
    1: "#2E7D32",  # 少见
    2: "#1565C0",  # 稀有
    3: "#6A1B9A",  # 珍藏
    4: "#E65100",  # 传说
}

NOVELTY_RARITY_NAMES = {
    0: "普通",
    1: "少见",
    2: "稀有",
    3: "珍藏",
    4: "传说",
}

MAX_INVENTORY = 20


class Inventory:
    """背包容器"""

    def __init__(self, capacity=MAX_INVENTORY):
        self.capacity = capacity
        self.items = []  # [{"name":..., "type": "equipment"|"novelty", ...}]

    def count(self):
        return len(self.items)

    def is_full(self):
        return len(self.items) >= self.capacity

    def add(self, item: dict):
        """添加物品到背包，返回是否成功"""
        if self.is_full():
            return False
        self.items.append(item)
        return True

    def remove(self, idx: int):
        """移除指定位置物品，返回物品或None"""
        if idx < 0 or idx >= len(self.items):
            return None
        return self.items.pop(idx)

    def get(self, idx: int):
        if 0 <= idx < len(self.items):
            return self.items[idx]
        return None

    def to_dict(self):
        return {
            "items": self.items,
            "capacity": self.capacity,
        }

    def from_dict(self, data):
        self.items = data.get("items", [])
        self.capacity = data.get("capacity", MAX_INVENTORY)
