"""
工厂模块 - 工厂系统数据配置
"""

# ── 工厂建造费用 ──
FACTORY_BUILD_COST = {
    "木材": 50,
    "铁矿": 30,
    "石头": 40,
    "皮革": 20,
}

# ── 工厂基础产出 ──
FACTORY_BASE_INTERVAL_S = 300   # 基准结算周期（5分钟）
FACTORY_BASE_PROFIT = 50        # 基准每次利润（金币）

# ── 部门配置 ──
# key: 部门id, name: 显示名, cost_gold: 金币费用, cost_resources: 材料费用,
# bonus_factor: 利润倍率加成, desc: 说明
DEPARTMENTS = [
    {
        "id": "basic",
        "name": "基础车间",
        "cost_gold": 0,
        "cost_resources": {},
        "bonus_factor": 1.0,
        "desc": "工厂原始部门",
        "built": True,      # 建造工厂时自带
    },
    {
        "id": "craft",
        "name": "加工车间",
        "cost_gold": 200,
        "cost_resources": {"木材": 30, "石头": 20},
        "bonus_factor": 0.3,
        "desc": "利润 +30%",
    },
    {
        "id": "logistics",
        "name": "物流部门",
        "cost_gold": 350,
        "cost_resources": {"铁矿": 25, "皮革": 20},
        "bonus_factor": 0.4,
        "desc": "利润 +40%",
    },
    {
        "id": "research",
        "name": "研发部门",
        "cost_gold": 500,
        "cost_resources": {"铁矿": 40, "石头": 30},
        "bonus_factor": 0.6,
        "desc": "利润 +60%",
    },
    {
        "id": "magic",
        "name": "魔法工坊",
        "cost_gold": 1000,
        "cost_resources": {"石头": 50, "铁矿": 50, "皮革": 30},
        "bonus_factor": 1.0,
        "desc": "利润 +100%（传说级）",
    },
]

# ── 工厂劳工 ──
MAX_FACTORY_WORKERS = 5
FACTORY_WORKER_COST_GOLD = 80   # 每位劳工费用
FACTORY_WORKER_BONUS = 0.15     # 每位劳工利润 +15%


def get_dept_by_id(dept_id):
    for d in DEPARTMENTS:
        if d["id"] == dept_id:
            return d
    return None


def calc_factory_bonus(dept_ids, worker_count):
    """计算工厂总利润倍率"""
    base = 1.0
    for did in dept_ids:
        dept = get_dept_by_id(did)
        if dept:
            base += dept["bonus_factor"]
    # 劳工加成
    base += worker_count * FACTORY_WORKER_BONUS
    return base


def get_factory_profit(interval_s=None):
    """返回本次结算金币 = 基准 * 倍率 * (interval / BASE)"""
    # interval 越大，积累越多
    if interval_s is None:
        interval_s = FACTORY_BASE_INTERVAL_S
    ratio = interval_s / FACTORY_BASE_INTERVAL_S
    # 使用 0，因为工厂 profit 信息需要从外部 GameCore 获取
    return ratio
