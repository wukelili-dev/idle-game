"""
图鉴基础数据模块 - 支持植物/怪物/牧场/装备/小物件五类图鉴分册
"""
import time


# ═══════════════════ 分册配置 ═══════════════════
CODEX_BOOKS = {
    "plants":     {"name": "🌿 植物图鉴", "icon": "🌿", "total": 40},
    "monsters":   {"name": "🐉 怪物图鉴", "icon": "🐉", "total": 34},
    "ranch":      {"name": "🐾 牧场图鉴", "icon": "🐾", "total": 32},
    "equipment":  {"name": "⚔️ 装备图鉴", "icon": "⚔️", "total": 0},   # 0=动态
    "novelty":    {"name": "🎁 小物件图鉴", "icon": "🎁", "total": 25},
}

# ═══════════════════ 图鉴进度奖励表（暂不触发） ═══════════════════
CODEX_REWARDS = {
    "plants": {
        25:  {"desc": "变异概率 +3%",               "effect": "plant_mutation_bonus"},
        50:  {"desc": "种子商店价格 -15%",           "effect": "plant_shop_discount"},
        75:  {"desc": "农田上限 +3",                 "effect": "plant_capacity_bonus"},
        100: {"desc": "🏆 植物大师 · 全植物产出 +20%", "effect": "plant_output_bonus"},
    },
    "monsters": {
        25:  {"desc": "解锁牧场槽位 +1",              "effect": "ranch_slot_bonus"},
        50:  {"desc": "精灵笼价格 -20%",              "effect": "trap_discount"},
        75:  {"desc": "牧场产出 +10%",                "effect": "ranch_output_bonus"},
        100: {"desc": "🏆 怪物学者 · BOSS捕获率 +10%", "effect": "boss_capture_bonus"},
    },
}


class CodexManager:
    """图鉴管理器"""

    def __init__(self):
        self.entries = {}  # {entry_id: dict}

    def discover(self, kind, entry_id, name, icon, desc, rarity, source):
        """发现新条目，返回 (is_new, entry)

        - 首次发现: is_new=True，记录 discovered + discovered_at
        - 重复发现: is_new=False，更新 source（追加）但不改 discovered_at
        """
        existing = self.entries.get(entry_id)
        if existing and existing.get("discovered"):
            return False, existing

        now = time.time()
        entry = {
            "id": entry_id,
            "kind": kind,
            "name": name,
            "icon": icon,
            "desc": desc,
            "rarity": rarity,
            "discovered": True,
            "discovered_at": now,
            "source": source,
        }
        self.entries[entry_id] = entry
        return True, entry

    def get_progress(self, kind):
        """返回 (discovered_count, total_count)"""
        book = CODEX_BOOKS.get(kind)
        if not book:
            return (0, 0)
        total = book["total"]
        discovered = sum(
            1 for e in self.entries.values()
            if e["kind"] == kind and e.get("discovered")
        )
        return (discovered, total)

    def get_all_by_kind(self, kind):
        """返回该分册全部条目列表，未发现也要包含（占位符）"""
        book = CODEX_BOOKS.get(kind)
        if not book:
            return []
        discovered = {
            e["id"]: e for e in self.entries.values()
            if e["kind"] == kind and e.get("discovered")
        }
        # 以已发现条目为主，编号未发现的占位
        result = list(discovered.values())
        return result

    def get_recent_discoveries(self, count=5):
        """最近发现的新条目"""
        items = [e for e in self.entries.values() if e.get("discovered")]
        items.sort(key=lambda e: e.get("discovered_at", 0), reverse=True)
        return items[:count]

    def to_dict(self):
        """序列化"""
        return {eid: dict(entry) for eid, entry in self.entries.items()}

    def from_dict(self, data):
        """反序列化"""
        self.entries = {}
        for eid, entry in data.items():
            self.entries[eid] = dict(entry)
