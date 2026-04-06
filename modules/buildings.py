"""
建筑模块 - 定义建筑配置、劳工系统和奇观系统
"""

# 建筑最大数量限制
MAX_BUILDING_COUNT = 3

# 劳工配置
WORKER_CONFIG = {
    "hire_cost": {"金币": 50},  # 雇佣成本
    "output_bonus": 0.5,  # 每个劳工增加50%产量
    "wage": 5,  # 每个劳工每周期工资（金币）
    "wage_interval": 60,  # 工资支付间隔（秒）
    "max_workers_per_level": {  # 每级最大劳工数
        1: 2,  # 1级建筑最多2个劳工
        2: 4,  # 2级建筑最多4个劳工
        3: 6,  # 3级建筑最多6个劳工
        4: 8,
        5: 10,
    }
}


class BuildingConfig:
    """建筑配置类"""
    def __init__(self, name, base_interval, base_output, build_cost, worker_cost=None):
        self.name = name
        self.base_interval = base_interval
        self.base_output = base_output
        self.build_cost = build_cost
        self.worker_cost = worker_cost or {"金币": 50}  # 雇佣劳工成本

    def get_interval(self, level):
        """根据等级获取生产间隔"""
        return max(1, int(self.base_interval * (1 - (level - 1) * 0.1)))

    def get_output(self, level, worker_count=0):
        """根据等级和劳工数获取产量"""
        base = int(self.base_output * (1 + (level - 1) * 0.5))
        # 劳工加成
        bonus = 1 + (worker_count * WORKER_CONFIG["output_bonus"])
        return int(base * bonus)

    def get_upgrade_cost(self, level):
        """获取升级成本"""
        gold = int(20 * (level ** 1.5))
        wood = int(15 * (level ** 1.3))
        return {"金币": gold, "木材": wood}

    def get_max_workers(self, level):
        """获取该等级下最大劳工数"""
        max_workers_map = WORKER_CONFIG["max_workers_per_level"]
        # 如果等级超过配置，使用最高等级配置
        for lvl in sorted(max_workers_map.keys(), reverse=True):
            if level >= lvl:
                return max_workers_map[lvl]
        return max_workers_map[1]


# 建筑配置
BUILDING_CONFIGS = {
    "伐木场": BuildingConfig( "伐木场", 3, 1, {"金币": 10}),
    "铁矿": BuildingConfig("铁矿", 5, 1, {"木材": 10}),
    "狩猎场": BuildingConfig("狩猎场", 4, 1, {"木材": 10, "铁矿": 5}),
    "采石场": BuildingConfig("采石场", 6, 1, {"金币": 15, "木材": 20}),  # 采石场
}

# 建筑产出资源映射
BUILDING_OUTPUTS = {
    "伐木场": "木材",
    "铁矿": "铁矿",
    "狩猎场": "皮革",
    "采石场": "石头",  # 采石场产出石头
}


# ============ 奇观系统 ============

class WonderConfig:
    """奇观配置类（纯装饰，无实际效果）"""
    def __init__(self, name, description, build_cost):
        self.name = name
        self.description = description
        self.build_cost = build_cost  # 建造成本


WONDERS = {
    "天空之城": WonderConfig(
        "天空之城",
        "传说中的浮空城市，象征着无上的荣耀",
        {"金币": 10000, "木材": 5000, "铁矿": 3000, "石头": 2000, "皮革": 1000}
    ),
    "永恒熔炉": WonderConfig(
        "永恒熔炉",
        "永不熄灭的熔炉，工匠们的终极梦想",
        {"金币": 8000, "木材": 3000, "铁矿": 5000, "石头": 3000}
    ),
    "生命之树": WonderConfig(
        "生命之树",
        "古老的神树，据说能带来好运",
        {"金币": 6000, "木材": 6000, "铁矿": 2000, "石头": 2000, "皮革": 2000}
    ),
}


def get_building_config(name):
    """获取建筑配置"""
    return BUILDING_CONFIGS.get(name)


def get_all_building_names():
    """获取所有建筑名称"""
    return list(BUILDING_CONFIGS.keys())


def get_building_output_resource(name):
    """获取建筑产出的资源类型"""
    return BUILDING_OUTPUTS.get(name, "木材")


def get_building_cost(name):
    """获取建筑建造成本"""
    config = BUILDING_CONFIGS.get(name)
    if config:
        return config.build_cost
    return {}


def get_wonder_config(name):
    """获取奇观配置"""
    return WONDERS.get(name)


def get_all_wonders():
    """获取所有奇观"""
    return WONDERS


def get_wonder_names():
    """获取所有奇观名称"""
    return list(WONDERS.keys())
