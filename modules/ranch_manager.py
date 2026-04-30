"""
牧场管理器 - 牧场生物购买、饲养、产出、卖出
"""
import time
import random
from .ranch import RANCH_CATALOG

# 性格加成系数
PERSONALITY_BONUS = {
    "乖巧": 1.20,
    "活泼": 1.15,
    "幸运": 1.25,
    "睿智": 1.20,
    "忠诚": 1.15,
    "暴躁": 1.30,
    "高傲": 1.20,
    "懒惰": 0.70,
}

# 基础产出周期（秒）
BASE_OUTPUT_INTERVAL = 300
LAZY_OUTPUT_INTERVAL = 500

# 产出物单价（按稀有度 rarity）
RARITY_PRICE = {0: 1, 1: 2, 2: 3, 3: 5, 4: 8}


def get_creature_by_id(creature_id: str):
    """从目录查找生物配置"""
    for c in RANCH_CATALOG:
        if c["id"] == creature_id:
            return c
    return None


class RanchManager:
    def __init__(self, save_data=None):
        # ranch_inventory: 拥有的生物实例列表
        # 每个实例: {creature_id, last_fed_at, output_count}
        self.ranch_inventory = []
        # output_warehouse: 产出物仓库 {output_type: count}
        self.output_warehouse = {}

        if save_data:
            self.from_dict(save_data)

    # ── 核心操作 ──────────────────────────────────

    def buy_creature(self, creature_id: str, player_gold: int):
        """购买生物，返回 (success, message, new_gold)"""
        creature = get_creature_by_id(creature_id)
        if not creature:
            return False, f"未知生物: {creature_id}", player_gold

        if player_gold < creature["price"]:
            return False, f"金币不足! 需要 {creature['price']}G", player_gold

        new_gold = player_gold - creature["price"]
        instance = {
            "creature_id": creature_id,
            "last_fed_at": None,   # None = 饥饿状态
            "output_count": 0,     # 累计产出次数（用于计算下次产出时间）
        }
        self.ranch_inventory.append(instance)
        return True, f"购入 {creature['icon']} {creature['name']}!", new_gold

    def feed_creature(self, index: int, player_gold: int) -> tuple:
        """饲养指定生物（激活产出），返回 (success, message, new_gold)"""
        if index < 0 or index >= len(self.ranch_inventory):
            return False, "生物不存在", player_gold

        instance = self.ranch_inventory[index]
        creature = get_creature_by_id(instance["creature_id"])
        if not creature:
            return False, "数据异常", player_gold

        if player_gold < creature["feed_cost"]:
            return False, f"金币不足! 饲养需要 {creature['feed_cost']}G", player_gold

        new_gold = player_gold - creature["feed_cost"]
        instance["last_fed_at"] = time.time()
        return True, f"�喂养 {creature['icon']} {creature['name']}!", new_gold

    def check_outputs(self):
        """检查所有已饲养生物是否产出，产出则添加到仓库。
        返回 (changed, fertilizer_gains) — fertilizer_gains 为 {肥料类型: 数量}"""
        now = time.time()
        changed = False
        fertilizer_gains = {}

        for instance in self.ranch_inventory:
            if instance["last_fed_at"] is None:
                continue  # 饥饿，跳过

            creature = get_creature_by_id(instance["creature_id"])
            if not creature:
                continue

            rarity = creature.get("rarity", 0)
            personality = creature.get("personality", "乖巧")
            bonus = PERSONALITY_BONUS.get(personality, 1.0)
            interval = LAZY_OUTPUT_INTERVAL if personality == "懒惰" else BASE_OUTPUT_INTERVAL

            # 计算下次产出时间（以 last_fed_at + output_count * interval 为基准）
            last_fed = instance["last_fed_at"]
            output_count = instance["output_count"]
            next_output_at = last_fed + (output_count + 1) * interval

            if now >= next_output_at:
                # 触发产出
                base_count = 1
                actual_count = max(1, int(base_count * bonus))
                output_type = creature["output_type"]
                self.output_warehouse[output_type] = self.output_warehouse.get(output_type, 0) + actual_count
                instance["output_count"] += 1
                changed = True

                # 肥料产出：白/绿/蓝(0-2) 30%→普通肥料，紫/橙(3-4) 50%→精制肥料
                if rarity >= 3:
                    if random.random() < 0.5:
                        fertilizer_gains["精制肥料"] = fertilizer_gains.get("精制肥料", 0) + 1
                else:
                    if random.random() < 0.3:
                        fertilizer_gains["普通肥料"] = fertilizer_gains.get("普通肥料", 0) + 1

        return changed, fertilizer_gains

    def harvest_creature(self, index: int):
        """手动收获指定生物的产出（立即结算），返回 (output_info or None)"""
        if index < 0 or index >= len(self.ranch_inventory):
            return None

        instance = self.ranch_inventory[index]
        if instance["last_fed_at"] is None:
            return None

        creature = get_creature_by_id(instance["creature_id"])
        if not creature:
            return None

        personality = creature.get("personality", "乖巧")
        bonus = PERSONALITY_BONUS.get(personality, 1.0)
        interval = LAZY_OUTPUT_INTERVAL if personality == "懒惰" else BASE_OUTPUT_INTERVAL

        now = time.time()
        last_fed = instance["last_fed_at"]
        output_count = instance["output_count"]

        # 计算当前应产出的次数（从未产出到现在的累计）
        elapsed = now - last_fed
        # 上次已结算到 output_count，需要结算 output_count+1 次
        # 但 get_output_by_index 只结算一次
        pending_count = int(elapsed // interval) - output_count

        if pending_count <= 0:
            return None  # 还不到产出时间

        # 结算一次
        actual_count = max(1, int(1 * bonus))
        output_type = creature["output_type"]
        self.output_warehouse[output_type] = self.output_warehouse.get(output_type, 0) + actual_count
        instance["output_count"] += 1

        return {
            "output_type": output_type,
            "count": actual_count,
            "creature_name": creature["name"],
            "creature_icon": creature["icon"],
            "personality": personality,
            "bonus": bonus,
        }

    def sell_output(self, output_type: str, count: int, player_gold: int) -> tuple:
        """卖出产出物，返回 (success, message, new_gold)"""
        available = self.output_warehouse.get(output_type, 0)
        if available < count:
            return False, f"{output_type}不足! 当前: {available}", player_gold

        # 计算价格：遍历目录找到该产出物对应的 rarity
        price_per = 1
        for c in RANCH_CATALOG:
            if c["output_type"] == output_type:
                price_per = RARITY_PRICE.get(c["rarity"], 1)
                break

        total_price = price_per * count
        self.output_warehouse[output_type] -= count
        if self.output_warehouse[output_type] <= 0:
            del self.output_warehouse[output_type]
        new_gold = player_gold + total_price
        return True, f"卖出 {count}×{output_type} +{total_price}G", new_gold

    # ── 状态查询 ──────────────────────────────────

    def get_inventory_summary(self):
        """返回牧场生物状态列表（用于UI展示）"""
        result = []
        for i, instance in enumerate(self.ranch_inventory):
            creature = get_creature_by_id(instance["creature_id"])
            if not creature:
                continue
            fed = instance["last_fed_at"] is not None
            if fed:
                personality = creature.get("personality", "乖巧")
                bonus = PERSONALITY_BONUS.get(personality, 1.0)
                interval = LAZY_OUTPUT_INTERVAL if personality == "懒惰" else BASE_OUTPUT_INTERVAL
                next_in = max(0, instance["last_fed_at"] + (instance["output_count"] + 1) * interval - time.time())
                status = f"🍖 已饲养 ({int(next_in)}s后产出)"
            else:
                status = "⚠️ 饥饿（需饲养）"
            result.append({
                "index": i,
                "id": creature["id"],
                "name": f"{creature['icon']} {creature['name']}",
                "personality": creature.get("personality", "?"),
                "feed_cost": creature["feed_cost"],
                "output_type": creature["output_type"],
                "status": status,
                "fed": fed,
            })
        return result

    def get_warehouse_summary(self):
        """返回产出物仓库摘要"""
        return dict(self.output_warehouse)

    def get_catalog_by_rarity(self, rarity: int = None):
        """返回目录，可按稀有度筛选"""
        if rarity is None:
            return list(RANCH_CATALOG)
        return [c for c in RANCH_CATALOG if c["rarity"] == rarity]

    def get_catalog_summary(self, player_gold: int):
        """返回可购买的生物列表（含是否买得起）"""
        return [
            {
                "id": c["id"],
                "name": f"{c['icon']} {c['name']}",
                "rarity": c["rarity"],
                "price": c["price"],
                "feed_cost": c["feed_cost"],
                "personality": c.get("personality", "?"),
                "output_type": c["output_type"],
                "can_afford": player_gold >= c["price"],
            }
            for c in RANCH_CATALOG
        ]

    # ── 序列化 ──────────────────────────────────

    def to_dict(self):
        return {
            "inventory": self.ranch_inventory,
            "warehouse": self.output_warehouse,
        }

    def from_dict(self, data):
        self.ranch_inventory = data.get("inventory", [])
        self.output_warehouse = data.get("warehouse", {})
