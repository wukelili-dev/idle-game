"""
游戏核心模块 - 游戏逻辑主类
"""
import time
import threading
import random
from .hero import Hero
from .buildings import (get_building_config, get_building_output_resource, 
                        MAX_BUILDING_COUNT, WORKER_CONFIG, get_wonder_config)
from .maps import get_map_enemies, get_all_maps, can_enter_map, get_unlock_cost, get_random_enemy
from .equipment_drops import generate_drop, get_drop_summary
from .inventory import NOVELTY_ITEMS
from .plants import (get_plant_catalog, get_plant_by_id, calc_grow_stage,
                     STAGE_NAMES, STAGE_ICONS, MAX_PLANTS, MUTATION_CHANCE)
from .tavern import (generate_tavern_roster, tavern_roster_to_dict, tavern_roster_from_dict)
from .factory import (FACTORY_BUILD_COST, FACTORY_BASE_INTERVAL_S,
                      FACTORY_BASE_PROFIT, DEPARTMENTS, MAX_FACTORY_WORKERS,
                      FACTORY_WORKER_COST_GOLD, get_dept_by_id,
                      calc_factory_bonus)
from .codex import CodexManager
from .ranch_manager import RanchManager, get_creature_by_id, RARITY_PRICE
from .forge import (FORTIFY_CONFIG, FORGE_RECIPES, PROTECT_CHARM_COST,
                    get_fortify_info, get_forge_recipe_by_name,
                    get_all_forge_recipes, build_forged_equip,
                    get_set_effect, count_set_pieces)


# ═══════════════ 伤害公式常量 ═══════════════
DEF_COEFF = 50  # 防御衰减系数，DEF越高中和收益递减越慢

# ═══════════════ 农场饲料产出 ═══════════════
FEED_INTERVAL_BY_RARITY = {0: 600, 1: 600, 2: 480, 3: 480, 4: 360}
FEED_TYPE_BY_RARITY = {0: "普通饲料", 1: "普通饲料", 2: "高级饲料", 3: "高级饲料", 4: "精华饲料"}

# ═══════════════ 肥料递减系数 ═══════════════
FERTILIZER_DIMINISHING = [1.0, 0.7, 0.4, 0.25, 0.15, 0.1]


def calc_damage(attack, defense):
    """计算伤害（使用防御衰减公式）
    
    公式: 伤害 = ATK × (1 - DEF/(DEF+50)) × random(0.9~1.1)
    - 防御永远有意义，永远不会锁死为0
    - 每点防御的边际收益递减（防止高防无解）
    """
    reduction = defense / (defense + DEF_COEFF)
    base = attack * (1 - reduction)
    variance = random.uniform(0.9, 1.1)
    return max(1, int(base * variance))


class GameCore:
    """游戏核心类"""
    def __init__(self):
        self.resources = {"木材": 0, "铁矿": 0, "皮革": 0, "石头": 0}  # 新增石头资源
        self.buildings = {}  # 建筑数量
        self.building_levels = {}  # 建筑等级列表
        self.building_workers = {}  # 建筑劳工数量 {name: [count, count, ...]}
        self.player = Hero()
        self.current_map = "傲来国"  # 初始地图
        self.unlocked_maps = {"傲来国"}  # 已解锁地图
        self.current_enemy_idx = 0
        self.current_enemy = None  # 当前敌人信息
        self.current_enemy_is_boss = False  # 当前敌人是否为BOSS
        self.is_battling = False
        self.auto_battle = False
        self.auto_battle_thread = None
        self.auto_potion_threshold = 0  # 0=关, 30/50/80=血量百分比阈值
        self.running = True
        self.logs = []       # 杂项日志（农场/牧场/建筑/系统）
        self.battle_logs = [] # 战斗日志
        self.production_active = set()
        self.wonders = {}  # 已建造的奇观 {name: True}
        # ── 队伍系统 ──
        self.team = [self.player]   # 队伍列表，index 0 是主角
        self.current_member_idx = 0  # 当前选中的队友索引（UI切换用）
        # ── 酒馆系统 ──
        self.tavern_roster = generate_tavern_roster(self.player.level)  # 当前可招募角色
        self.tavern_last_refresh = time.time()  # 上次刷新时间戳
        self.wage_thread = None  # 工资支付线程
        self._start_wage_system()  # 启动工资系统

        # ── 农场系统 ──
        self.plants = []      # [{id, plant_id, planted_at, speedups}]
        self.plant_thread = None
        self.mutated_plants = {}  # 变异记录
        self._start_plant_system()

        # ── 工厂系统 ──
        self.factory = None    # None 表示未建造，dict 表示已建造
        self.factory_departments = []   # list of dept_id 已解锁部门
        self.factory_workers = 0         # 工厂劳工数量
        self.factory_last_profit_time = 0  # 上次结算时间戳
        self.factory_thread = None
        self._start_factory_system()

        # ── 图鉴系统 ──
        self.codex = CodexManager()

        # ── 牧场系统 ──
        self.ranch = RanchManager()

        # ── 饲料/肥料背包 ──
        self.feed_bag = {}       # {"普通饲料": N, "高级饲料": N, "精华饲料": N}
        self.fertilizer_bag = {}  # {"普通肥料": N, "精制肥料": N}

    def _start_wage_system(self):
        """启动工资支付系统"""
        def pay_wages():
            while self.running:
                time.sleep(WORKER_CONFIG["wage_interval"])
                if not self.running:
                    break
                total_workers = 0
                total_wage = 0
                for name, worker_list in self.building_workers.items():
                    for count in worker_list:
                        total_workers += count
                total_wage = total_workers * WORKER_CONFIG["wage"]
                
                if total_wage > 0:
                    if self.player.gold >= total_wage:
                        self.player.gold -= total_wage
                        self.add_log(f"💰 支付工资: {total_wage}G ({total_workers}个劳工)")
                    else:
                        # 金币不足，解雇所有劳工
                        self.add_log(f"⚠️ 金币不足支付工资! 解雇所有劳工!")
                        for name in self.building_workers:
                            self.building_workers[name] = [0] * len(self.building_workers[name])
        
        self.wage_thread = threading.Thread(target=pay_wages, daemon=True)
        self.wage_thread.start()

    def add_log(self, msg):
        """添加杂项日志"""
        timestamp = time.strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {msg}")
        if len(self.logs) > 100:
            self.logs.pop(0)

    def add_battle_log(self, msg):
        """添加战斗日志"""
        timestamp = time.strftime("%H:%M:%S")
        self.battle_logs.append(f"[{timestamp}] {msg}")
        if len(self.battle_logs) > 100:
            self.battle_logs.pop(0)

    # ═══════════════════ 农场系统 ═══════════════════

    def _start_plant_system(self):
        """启动植物生产线程"""
        def plant_loop():
            while self.running:
                time.sleep(1)
                self._tick_plants()

        self.plant_thread = threading.Thread(target=plant_loop, daemon=True)
        self.plant_thread.start()

    def _tick_plants(self):
        """每帧更新植物状态（结算产金、移除枯萎成年植物）"""
        now = time.time()
        changed = False
        to_remove = []

        for plant in self.plants:
            pd = get_plant_by_id(plant["plant_id"])
            if not pd:
                continue

            elapsed = now - plant["planted_at"]
            stage = calc_grow_stage(elapsed, pd["grow_time_s"])

            if stage >= 3:
                # 成年：检查是否产出金币
                adult_elapsed = elapsed - pd["grow_time_s"]
                interval = pd["harvest_interval_s"]
                # 以 planted_at 为基准，累计已产出的次数
                prev_harvests = plant.get("harvest_count", 0)
                current_harvests = int(adult_elapsed // interval)
                if current_harvests > prev_harvests:
                    gain = (current_harvests - prev_harvests) * pd["harvest_gold"]
                    self.player.gold += gain
                    self.add_log(f"🌳 {pd['icon']} {pd['name']} 产出 {gain}G")
                    plant["harvest_count"] = current_harvests
                    changed = True

                # 饲料产出
                feed_interval = FEED_INTERVAL_BY_RARITY.get(pd.get("rarity", 0), 600)
                feed_type = FEED_TYPE_BY_RARITY.get(pd.get("rarity", 0), "普通饲料")
                prev_feeds = plant.get("feed_count", 0)
                current_feeds = int(adult_elapsed // feed_interval)
                if current_feeds > prev_feeds:
                    gain = current_feeds - prev_feeds
                    self.feed_bag[feed_type] = self.feed_bag.get(feed_type, 0) + gain
                    self.add_log(f"🌾 {pd['icon']} {pd['name']} 产出 {feed_type}×{gain}")
                    plant["feed_count"] = current_feeds
                    changed = True

                # 枯萎检测
                if adult_elapsed >= pd["adult_lifespan_s"]:
                    self.add_log(f"🥀 {pd['name']} 枯萎了")
                    to_remove.append(plant["id"])
                    changed = True

        for pid in to_remove:
            self.plants = [p for p in self.plants if p["id"] != pid]

        return changed

    def plant_seed(self, plant_id, cost_gold=5):
        """种植一颗种子，cost_gold 控制花费（Farm按钮默认5G，商店按物品价）"""
        if self.player.gold < cost_gold:
            return False, f"金币不足! 需要{cost_gold}G"
        if len(self.plants) >= MAX_PLANTS:
            return False, f"田地已满! 最多种{MAX_PLANTS}棵"

        pd = get_plant_by_id(plant_id)
        if not pd:
            return False, "未知种子"

        self.player.gold -= cost_gold
        plant = {
            "id": f"plant_{int(time.time() * 1000)}",
            "plant_id": plant_id,
            "planted_at": time.time(),
            "harvest_count": 0,
            "feed_count": 0,
            "fertilizers": [],
            "mutation_bonus": 0.0,
        }
        self.plants.append(plant)
        self.add_log(f"🌱 种下了 {pd['icon']} {pd['name']}")
        # 图鉴：发现植物
        if pd:
            self.codex.discover("plants", plant_id, pd["name"], pd["icon"], pd["desc"], pd["rarity"], "种植")
        return True, f"已种植 {pd['name']}"

    def speedup_plant(self, plant_id):
        """加速植物生长（花费金币）"""
        plant = None
        for p in self.plants:
            if p["id"] == plant_id:
                plant = p
                break
        if not plant:
            return False, "植物不存在"

        pd = get_plant_by_id(plant["plant_id"])
        elapsed = time.time() - plant["planted_at"]
        remaining = max(0, pd["grow_time_s"] - elapsed)
        if remaining <= 0:
            return False, "已经成年，无需加速"

        # 加速到成年的金币 = 剩余秒数 * 0.5
        cost = int(remaining * 0.5)
        if self.player.gold < cost:
            return False, f"金币不足! 需要 {cost}G"

        self.player.gold -= cost
        plant["planted_at"] = time.time() - pd["grow_time_s"]
        self.add_log(f"⚡ 加速了 {pd['name']} 的生长 (花费 {cost}G)")
        return True, f"已加速! {pd['name']} 立即成熟"

    def use_fertilizer(self, plant_id, fertilizer_type):
        """对作物使用肥料，缩短生长时间并提升变异概率（效果递减）"""
        if fertilizer_type not in self.fertilizer_bag or self.fertilizer_bag[fertilizer_type] <= 0:
            return False, f"{fertilizer_type}不足!"

        plant = None
        for p in self.plants:
            if p["id"] == plant_id:
                plant = p
                break
        if not plant:
            return False, "植物不存在"

        pd = get_plant_by_id(plant["plant_id"])
        elapsed = time.time() - plant["planted_at"]
        if elapsed >= pd["grow_time_s"]:
            return False, "已成年，无需施肥"

        # 消耗肥料
        self.fertilizer_bag[fertilizer_type] -= 1
        if self.fertilizer_bag[fertilizer_type] <= 0:
            del self.fertilizer_bag[fertilizer_type]

        # 递减系数
        fert_count = len(plant.get("fertilizers", []))
        factor = FERTILIZER_DIMINISHING[min(fert_count, len(FERTILIZER_DIMINISHING) - 1)]

        # 肥料效果
        if fertilizer_type == "精制肥料":
            grow_pct = 0.08 * factor
            mutation_pct = 0.02 * factor
        else:
            grow_pct = 0.03 * factor
            mutation_pct = 0.005 * factor

        # 缩短生长时间
        remaining = pd["grow_time_s"] - elapsed
        shorten = remaining * grow_pct
        plant["planted_at"] += shorten

        # 累加变异概率
        plant["fertilizers"] = plant.get("fertilizers", [])
        plant["fertilizers"].append(fertilizer_type)
        plant["mutation_bonus"] = plant.get("mutation_bonus", 0.0) + mutation_pct

        pct_str = f"{grow_pct*100:.1f}%"
        self.add_log(f"🧪 对 {pd['name']} 使用{fertilizer_type}: 生长-{pct_str} 变异+{mutation_pct*100:.1f}%")
        return True, f"已施肥! {pd['name']} 生长-{pct_str}"

    def get_plant_status(self, plant_id):
        """返回植物当前状态详情"""
        for p in self.plants:
            if p["id"] == plant_id:
                return self._plant_status(p)
        return None

    def _plant_status(self, plant):
        pd = get_plant_by_id(plant["plant_id"])
        if not pd:
            return None
        now = time.time()
        elapsed = now - plant["planted_at"]
        stage = calc_grow_stage(elapsed, pd["grow_time_s"])
        remaining = max(0, pd["grow_time_s"] - elapsed)
        stage_name = STAGE_NAMES[stage]
        icon = STAGE_ICONS[stage]

        # 进度条
        if stage < 3:
            total = pd["grow_time_s"]
            pct = min(100, int(elapsed / total * 100))
            bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
            progress = f"[{bar}] {pct}%"
            time_left = f"剩余{int(remaining)}s"
        else:
            adult_elapsed = elapsed - pd["grow_time_s"]
            interval = pd["harvest_interval_s"]
            next_harvest = interval - (adult_elapsed % interval)
            progress = f"每{int(interval)}s 产出 {pd['harvest_gold']}G"
            time_left = f"下次产出{int(next_harvest)}s"

        return {
            "id": plant["id"],
            "name": f"{icon} {pd['name']}",
            "stage": stage,
            "stage_name": stage_name,
            "progress": progress,
            "time_left": time_left,
            "remaining_s": remaining,
            "adult": stage >= 3,
            "desc": pd["desc"],
        }

    # ═══════════════════ 工厂系统 ═══════════════════

    def _start_factory_system(self):
        """启动工厂结算线程"""
        def factory_loop():
            while self.running:
                time.sleep(5)   # 每5秒检查一次
                self._tick_factory()

        self.factory_thread = threading.Thread(target=factory_loop, daemon=True)
        self.factory_thread.start()

    def _tick_factory(self):
        """工厂盈利结算"""
        if not self.factory:
            return

        now = time.time()
        if self.factory_last_profit_time == 0:
            self.factory_last_profit_time = now
            return

        interval = now - self.factory_last_profit_time
        if interval < FACTORY_BASE_INTERVAL_S:
            return

        bonus = calc_factory_bonus(self.factory_departments, self.factory_workers)
        profit = int(FACTORY_BASE_PROFIT * bonus * (interval / FACTORY_BASE_INTERVAL_S))
        self.player.gold += profit
        self.factory_last_profit_time = now
        self.add_log(f"🏭 工厂盈利: +{profit}G (×{bonus:.2f})")

    def build_factory(self):
        """建造工厂"""
        if self.factory is not None:
            return False, "工厂已存在! 不能重复建造"

        if not self.can_afford(FACTORY_BUILD_COST):
            cost_str = ", ".join([f"{k}{v}" for k, v in FACTORY_BUILD_COST.items()])
            return False, f"资源不足! 需要: {cost_str}"

        self.spend_resources(FACTORY_BUILD_COST)
        self.factory = {"built": True}
        self.factory_departments = ["basic"]   # 自带基础车间
        self.factory_workers = 0
        self.factory_last_profit_time = time.time()
        self.add_log("🏭 工厂建造完成! (基础车间已解锁)")
        return True, "工厂建造成功!"

    def buy_department(self, dept_id):
        """购买工厂部门"""
        if self.factory is None:
            return False, "尚未建造工厂!"
        if dept_id in self.factory_departments:
            return False, "该部门已存在"

        dept = get_dept_by_id(dept_id)
        if not dept:
            return False, "部门不存在"

        cost = {"金币": dept["cost_gold"], **dept["cost_resources"]}
        if not self.can_afford(cost):
            return False, "资源不足"

        self.spend_resources(cost)
        self.factory_departments.append(dept_id)
        self.add_log(f"🏗️ 部门 '{dept['name']}' 解锁! (+{int(dept['bonus_factor']*100)}%)")
        return True, f"{dept['name']} 已解锁! 利润 +{int(dept['bonus_factor']*100)}%"

    def hire_factory_worker(self):
        """工厂雇佣劳工"""
        if self.factory is None:
            return False, "尚未建造工厂!"
        if self.factory_workers >= MAX_FACTORY_WORKERS:
            return False, f"已达上限! 最多{MAX_FACTORY_WORKERS}人"

        if self.player.gold < FACTORY_WORKER_COST_GOLD:
            return False, f"金币不足! 需要{FACTORY_WORKER_COST_GOLD}G"

        self.player.gold -= FACTORY_WORKER_COST_GOLD
        self.factory_workers += 1
        self.add_log(f"👷 工厂雇佣第{self.factory_workers}号员工 (+15%利润)")
        return True, f"员工 #{self.factory_workers} 上岗!"

    def fire_factory_worker(self):
        """工厂解雇劳工"""
        if self.factory is None:
            return False, "尚未建造工厂!"
        if self.factory_workers <= 0:
            return False, "工厂没有员工"

        self.factory_workers -= 1
        self.add_log(f"👋 工厂解雇1人 (剩余: {self.factory_workers})")
        return True, f"已解雇! 剩余 {self.factory_workers} 人"

    def get_factory_info(self):
        """返回工厂状态摘要"""
        if self.factory is None:
            return None
        bonus = calc_factory_bonus(self.factory_departments, self.factory_workers)
        interval = FACTORY_BASE_INTERVAL_S
        profit_per = int(FACTORY_BASE_PROFIT * bonus)
        return {
            "built": True,
            "departments": self.factory_departments,
            "worker_count": self.factory_workers,
            "bonus_factor": bonus,
            "profit_per_cycle": profit_per,
            "cycle_seconds": interval,
        }

    def can_afford(self, cost):
        """检查是否能支付成本"""
        for res, amount in cost.items():
            if res == "金币":
                if self.player.gold < amount:
                    return False
            elif self.resources.get(res, 0) < amount:
                return False
        return True

    def spend_resources(self, cost):
        """消耗资源"""
        for res, amount in cost.items():
            if res == "金币":
                self.player.gold -= amount
            else:
                self.resources[res] -= amount

    def build_building(self, name):
        """建造建筑，最多3个"""
        config = get_building_config(name)
        if not config:
            return False, "Building not found"
        # 检查最大数量限制
        current_count = self.buildings.get(name, 0)
        if current_count >= MAX_BUILDING_COUNT:
            return False, f"最多只能建造{MAX_BUILDING_COUNT}个{name}!"
        if not self.can_afford(config.build_cost):
            return False, "Not enough resources!"

        self.spend_resources(config.build_cost)
        self.buildings[name] = current_count + 1
        if name not in self.building_levels:
            self.building_levels[name] = []
            self.building_workers[name] = []
        self.building_levels[name].append(1)
        self.building_workers[name].append(0)  # 初始0个劳工
        self.add_log(f"已建造 {name}! 总数: {self.buildings[name]}")
        self.start_building_production(name, self.buildings[name] - 1)
        return True, f"Built {name} x{self.buildings[name]}"

    def upgrade_building(self, name, idx):
        """升级建筑"""
        if name not in self.building_levels or idx >= len(self.building_levels[name]):
            return False, "Building not found"

        current_level = self.building_levels[name][idx]
        new_level = current_level + 1
        config = get_building_config(name)
        cost = config.get_upgrade_cost(new_level)

        if not self.can_afford(cost):
            return False, f"Not enough! Need G{cost.get('金币',0)} W{cost.get('木材',0)}"

        self.spend_resources(cost)
        self.building_levels[name][idx] = new_level
        self.add_log(f"{name} Lv.{current_level} -> Lv.{new_level}")
        self.start_building_production(name, idx)
        return True, f"Upgraded! {name} Lv.{new_level}"

    def start_building_production(self, name, idx):
        """启动建筑生产线程"""
        key = f"{name}_{idx}"
        if key in self.production_active:
            return

        def produce():
            self.production_active.add(key)
            config = get_building_config(name)
            while self.running and self.buildings.get(name, 0) > idx:
                levels = self.building_levels.get(name, [])
                if idx >= len(levels):
                    break
                level = levels[idx]
                workers = self.building_workers[name][idx]
                interval = config.get_interval(level)
                output = config.get_output(level, workers)
                time.sleep(interval)

                levels2 = self.building_levels.get(name, [])
                if idx >= len(levels2):
                    break

                res_name = get_building_output_resource(name)
                self.resources[res_name] += output
            self.production_active.discard(key)

        t = threading.Thread(target=produce, daemon=True)
        t.start()

    def hire_worker(self, name, idx):
        """雇佣劳工"""
        if name not in self.building_levels or idx >= len(self.building_levels[name]):
            return False, "建筑不存在"
        
        config = get_building_config(name)
        level = self.building_levels[name][idx]
        current_workers = self.building_workers[name][idx]
        max_workers = config.get_max_workers(level)
        
        if current_workers >= max_workers:
            return False, f"该建筑等级最多雇佣{max_workers}个劳工"
        
        cost = config.worker_cost
        if not self.can_afford(cost):
            return False, f"金币不足! 需要{cost['金币']}G"
        
        self.spend_resources(cost)
        self.building_workers[name][idx] += 1
        self.add_log(f"{name} #{idx+1} 雇佣了1个劳工! 当前: {self.building_workers[name][idx]}/{max_workers}")
        return True, "雇佣成功"

    def fire_worker(self, name, idx):
        """解雇劳工"""
        if name not in self.building_workers or idx >= len(self.building_workers[name]):
            return False, "建筑不存在"
        
        if self.building_workers[name][idx] <= 0:
            return False, "该建筑没有劳工"
        
        self.building_workers[name][idx] -= 1
        self.add_log(f"{name} #{idx+1} 解雇了1个劳工")
        return True, "解雇成功"

    def build_wonder(self, wonder_name):
        """建造奇观（纯装饰，无实际效果）"""
        if wonder_name in self.wonders:
            return False, "奇观已建造"
        
        config = get_wonder_config(wonder_name)
        if not config:
            return False, "奇观不存在"
        
        if not self.can_afford(config.build_cost):
            cost_str = ", ".join([f"{k}{v}" for k, v in config.build_cost.items()])
            return False, f"资源不足! 需要: {cost_str}"
        
        self.spend_resources(config.build_cost)
        self.wonders[wonder_name] = True
        self.add_log(f"🎉 奇观 '{wonder_name}' 建造完成!")
        self.add_log(f"   效果: {config.description}")
        return True, f"成功建造 {wonder_name}"

    def buy_weapon(self, wpn):
        """购买武器（进入背包）"""
        # 等级检查
        if self.player.level < wpn.get("level_req", 0):
            return False, f"等级不足! 需要 Lv.{wpn['level_req']}"
        if not self.can_afford(wpn["cost"]):
            return False, "资源不足!"
        if self.player.inventory.is_full():
            return False, "背包已满! (最多20件)"
        self.spend_resources(wpn["cost"])
        sell_price = self._calc_shop_sell_price(wpn["cost"])
        equip = {
            "name": wpn["name"],
            "type": "weapon",
            "rarity": "商店",
            "rarity_color": "#FFFFFF",
            "attack": wpn["attack"],
            "crit_rate": wpn["crit_rate"],
            "crit_dmg": wpn.get("crit_dmg", 150),
            "special": wpn.get("special"),
            "level_req": wpn.get("level_req", 1),
            "is_perfect": False,
            "sell_price": sell_price,
            "forge_level": 0,
            "is_forged": False,
            "forge_set": None,
            "passive": None,
        }
        self.player.add_to_inventory(equip)
        self.add_log(f"购买装备进入背包: {wpn['name']}")
        return True, f"{wpn['name']} 已放入背包"

    def buy_armor(self, arm):
        """购买护甲（进入背包）"""
        # 等级检查
        if self.player.level < arm.get("level_req", 0):
            return False, f"等级不足! 需要 Lv.{arm['level_req']}"
        if not self.can_afford(arm["cost"]):
            return False, "资源不足!"
        if self.player.inventory.is_full():
            return False, "背包已满! (最多20件)"
        self.spend_resources(arm["cost"])
        sell_price = self._calc_shop_sell_price(arm["cost"])
        equip = {
            "name": arm["name"],
            "type": "armor",
            "rarity": "商店",
            "rarity_color": "#FFFFFF",
            "defense": arm["defense"],
            "hp_bonus": arm["hp_bonus"],
            "special": arm.get("special"),
            "level_req": arm.get("level_req", 1),
            "is_perfect": False,
            "sell_price": sell_price,
            "forge_level": 0,
            "is_forged": False,
            "forge_set": None,
            "passive": None,
        }
        self.player.add_to_inventory(equip)
        self.add_log(f"购买装备进入背包: {arm['name']}")
        return True, f"{arm['name']} 已放入背包"

    def buy_novelty_item(self, item):
        """购买杂货铺物品"""
        # 种子类 → 直接种植，不进背包（金币已在plant_seed中扣除）
        if item.get("kind") == "plant_seed":
            ok, msg = self.plant_seed(item["plant_id"])
            return ok, msg

        if self.player.gold < item["price"]:
            return False, f"金币不足! 需要 {item['price']}G"
        if self.player.inventory.is_full():
            return False, "背包已满! (最多20件)"
        self.player.gold -= item["price"]
        novelty = {
            "name": item["name"],
            "type": "novelty",
            "desc": item["desc"],
            "price": item["price"],
            "rarity_idx": item["rarity_idx"],
            "sell_price": int(item["price"] * 0.8),   # 可出售，退款80%
        }
        self.player.add_to_inventory(novelty)
        self.add_log(f"🎁 购买了: {item['name']}")
        return True, f"{item['name']} 已放入背包"

    def use_novelty_item(self, idx):
        """使用背包中的杂货物品（目前仅支持植物种子）"""
        item = self.player.inventory.get(idx)
        if not item:
            return False, "无效的背包位置!"

        if item.get("kind") == "plant_seed":
            plant_id = item.get("plant_id")
            if not plant_id:
                return False, "种子数据异常!"
            if len(self.plants) >= MAX_PLANTS:
                return False, f"田地已满! 最多种{MAX_PLANTS}棵"

            from modules.plants import get_plant_by_id
            pd = get_plant_by_id(plant_id)
            self.player.inventory.remove(idx)
            plant = {
                "id": f"plant_{int(time.time() * 1000)}",
                "plant_id": plant_id,
                "planted_at": time.time(),
                "harvest_count": 0,
                "feed_count": 0,
                "fertilizers": [],
                "mutation_bonus": 0.0,
            }
            self.plants.append(plant)
            self.add_log(f"🌱 种下了 {pd['icon']} {pd['name']} (掉落物)")
            return True, f"已种植 {pd['name']}"

        return False, "该物品无法使用"

    def buy_potion(self):
        """购买药水"""
        if self.player.gold < 25:
            return False, "金币不足! Need 25G"
        self.player.gold -= 25
        self.player.potions += 1
        return True, "Bought potion!"

    def use_potion(self):
        """使用药水"""
        if self.player.potions <= 0:
            return False, "No potions!"
        if self.player.hp >= self.player.get_max_hp_with_bonus():
            return False, "HP is full!"
        self.player.potions -= 1
        heal = min(20, self.player.get_max_hp_with_bonus() - self.player.hp)
        self.player.heal(heal)
        return True, f"Used potion! Healed {heal} HP"

    def _try_auto_potion(self):
        """自动药水：血量低于阈值时自动使用/购买药水"""
        if self.auto_potion_threshold <= 0:
            return
        max_hp = self.player.get_max_hp_with_bonus()
        if max_hp <= 0:
            return
        hp_pct = self.player.hp * 100 / max_hp
        if hp_pct >= self.auto_potion_threshold:
            return

        # 尝试使用药水
        if self.player.potions > 0:
            heal = min(20, max_hp - self.player.hp)
            if heal > 0:
                self.player.potions -= 1
                self.player.heal(heal)
                self.add_log(f"  💊 自动药水! +{heal} HP (剩余: {self.player.potions})")
            return

        # 没有药水，尝试购买（金币不够就等下一次，绝不关闭自动药水）
        if self.player.gold >= 25:
            self.player.gold -= 25
            self.player.potions += 1
            self.add_log(f"  💊 自动购买药水 (25G), 使用中!")
            heal = min(20, max_hp - self.player.hp)
            if heal > 0:
                self.player.potions -= 1
                self.player.heal(heal)
                self.add_log(f"  💊 自动药水! +{heal} HP (剩余: {self.player.potions})")

    def set_auto_potion_threshold(self, value):
        """设置自动药水阈值"""
        self.auto_potion_threshold = value

    def battle(self, enemy_data, is_boss=False):
        """战斗逻辑"""
        if self.is_battling:
            return False, "战斗中..."

        self.is_battling = True
        e_hp = enemy_data["hp"]
        boss_tag = " [BOSS]" if is_boss else ""
        self.add_battle_log(f"战斗: 英雄 vs {enemy_data['name']}{boss_tag}")

        while e_hp > 0 and self.player.hp > 0:
            # 玩家攻击怪物
            p_dmg = calc_damage(self.player.get_total_attack(), enemy_data["defense"])
            is_crit = random.randint(1, 100) <= self.player.get_crit_rate()
            crit_mult = self.player.weapon.get("crit_dmg", 150) if isinstance(self.player.weapon, dict) else 150
            if is_crit:
                p_dmg = int(p_dmg * crit_mult / 100)
                self.add_battle_log(f"  暴击! {p_dmg} 伤害!")
            else:
                self.add_battle_log(f"  你对敌人造成 {p_dmg} 伤害")
            e_hp -= p_dmg
            
            # 吸血效果
            special = self.player.weapon.get("special") if isinstance(self.player.weapon, dict) else None
            if special and special.get("name") == "吸血":
                lifesteal = special["value"]
                heal = int(p_dmg * lifesteal / 100)
                if heal > 0:
                    self.player.heal(heal)
                    self.add_battle_log(f"  💉 吸血恢复 {heal} HP")
            special = self.player.armor.get("special") if isinstance(self.player.armor, dict) else None
            if special and special.get("name") == "吸血":
                lifesteal = special["value"]
                heal = int(p_dmg * lifesteal / 100)
                if heal > 0:
                    self.player.heal(heal)
                    self.add_battle_log(f"  💉 吸血恢复 {heal} HP")
            
            if e_hp <= 0:
                break

            # 敌人攻击怪物
            e_dmg = calc_damage(enemy_data["attack"], self.player.get_total_defense())
            self.player.take_damage(e_dmg)
            self.add_battle_log(f"  {enemy_data['name']} 对英雄造成 {e_dmg} 伤害")

            # 自动药水检查（被攻击后立即判断）
            self._try_auto_potion()

            time.sleep(0.5)

        if self.player.hp > 0:
            self.add_battle_log(f"胜利! 击败 {enemy_data['name']}!")
            self.player.gold += enemy_data["gold"]
            self.player.kill_count += 1
            self.add_battle_log(f"  +{enemy_data['exp']} 经验 +{enemy_data['gold']} 金币")
            for item, amount in enemy_data["drops"].items():
                self.resources[item] = self.resources.get(item, 0) + amount
                self.add_battle_log(f"  +{amount} {item}")
            
            # 装备掉落
            drop = generate_drop(enemy_data.get("level", 1), is_boss)
            if drop:
                # 计算售价
                drop["sell_price"] = self._calc_drop_sell_price(drop)
                self.player.add_to_inventory(drop)
                summary = get_drop_summary(drop)
                self.add_battle_log(f"  🎁 获得装备: {summary}")
            
            # 小物件掉落（30%概率，掉落商店杂货）
            if random.random() < 0.3:
                item = random.choice(NOVELTY_ITEMS)
                # 小物件售出价 = 商店购入价 × 80%
                sell_price = int(item["price"] * 0.8)
                novelty = {
                    "name": item["name"],
                    "type": "novelty",
                    "desc": item["desc"],
                    "price": item["price"],
                    "rarity_idx": item.get("rarity_idx", 0),
                    "sell_price": sell_price,   # 可出售!
                }
                self.player.add_to_inventory(novelty)
                self.add_battle_log(f"  🎁 捡到小物件: {item['name']}")
            
            msgs = self.player.gain_exp(enemy_data["exp"])
            for m in msgs:
                self.add_battle_log(m)
            # 战斗胜利后获取下一个敌人
            next_enemy, next_is_boss = get_random_enemy(self.current_map)
            self.current_enemy = next_enemy
            self.current_enemy_is_boss = next_is_boss
            return True, "Victory"
        else:
            self.add_battle_log(f"被 {enemy_data['name']}!")
            self.player.hp = self.player.get_max_hp_with_bonus() // 2
            self.add_battle_log(f"恢复: {self.player.hp}/{self.player.get_max_hp_with_bonus()}")
            # 战斗失败后也获取新敌人
            next_enemy, next_is_boss = get_random_enemy(self.current_map)
            self.current_enemy = next_enemy
            self.current_enemy_is_boss = next_is_boss
            return False, "Defeat"

    def start_auto_battle(self):
        """启动自动战斗"""
        if self.auto_battle_thread and self.auto_battle_thread.is_alive():
            return
        self.auto_battle_thread = threading.Thread(
            target=self._auto_battle_loop, 
            daemon=True
        )
        self.auto_battle_thread.start()

    def _auto_battle_loop(self):
        """自动战斗循环"""
        while self.auto_battle and self.running:
            if not self.is_battling:
                # 随机获取敌人，有5%概率遇到BOSS
                from .maps import get_random_enemy
                self.try_refresh_tavern()
                enemy, is_boss = get_random_enemy(self.current_map)
                if enemy:
                    result, msg = self.battle_team(enemy, is_boss=is_boss)
                    self.is_battling = False
                else:
                    self.add_battle_log("没有可用敌人!")
                    break
            time.sleep(0.5)

    def change_map(self, map_name):
        """切换地图"""
        can_enter, msg = can_enter_map(map_name, self.player.level, self.unlocked_maps)
        if can_enter:
            self.current_map = map_name
            self.current_enemy_idx = 0
            self.add_log(f"进入地图: {map_name}")
            return True, f"已进入 {map_name}"
        return False, msg

    def unlock_map(self, map_name):
        """解锁新地图"""
        all_maps = get_all_maps()
        if map_name not in all_maps:
            return False, "地图不存在"
        if map_name in self.unlocked_maps:
            return False, "地图已解锁"
        cost = get_unlock_cost(map_name)
        if self.player.gold < cost:
            return False, f"金币不足! 需要{cost}G"
        self.player.gold -= cost
        self.unlocked_maps.add(map_name)
        self.add_log(f"解锁地图: {map_name}")
        return True, f"已解锁 {map_name}"

    def get_current_map_enemies(self):
        """获取当前地图的敌人列表"""
        return get_map_enemies(self.current_map)

    def refresh_enemy(self):
        """刷新当前敌人（随机获取新敌人，有概率遇到BOSS）"""
        if self.is_battling:
            return None, False, "战斗中无法刷新"
        enemy, is_boss = get_random_enemy(self.current_map)
        if enemy:
            boss_tag = " [BOSS]" if is_boss else ""
            self.add_battle_log(f"🔄 刷新敌人: {enemy['name']}{boss_tag}")
        return enemy, is_boss, "已刷新敌人"

    def _calc_shop_sell_price(self, cost):
        """计算商店装备售价（80%）"""
        # 只计算金币成本，其他资源按比例转换
        gold_value = cost.get("金币", 0)
        # 木材=2G, 铁矿=3G, 皮革=2G, 石头=1G
        gold_value += cost.get("木材", 0) * 2
        gold_value += cost.get("铁矿", 0) * 3
        gold_value += cost.get("皮革", 0) * 2
        gold_value += cost.get("石头", 0) * 1
        return int(gold_value * 0.8)

    def _calc_drop_sell_price(self, equip):
        """计算掉落装备售价"""
        rarity = equip.get("rarity", "普通")
        is_perfect = equip.get("is_perfect", False)
        
        # 基础价格根据属性计算
        if equip["type"] == "weapon":
            base = 10 + equip["attack"] * 2 + equip["crit_rate"]
        else:
            base = 10 + equip["defense"] * 2 + equip["hp_bonus"] // 10
        
        # 稀有度系数
        rarity_mult = {
            "普通": 0.8,
            "稀有": 1.0,
            "史诗": 1.3,
            "传说": 1.8,
            "极品": 2.5,
        }.get(rarity, 0.8)
        
        price = int(base * rarity_mult)
        
        # 特殊属性加成
        special = equip.get("special")
        if special:
            price += special["value"] * 5
        
        # 极品装备额外加成
        if is_perfect:
            price = int(price * 1.5)
        
        return max(5, price)

    def sell_inventory_item(self, idx):
        """出售背包中的物品"""
        item = self.player.inventory.get(idx)
        if not item:
            return False, "无效的背包位置!"
        sell_price = item.get("sell_price", 10)
        if sell_price <= 0:
            return False, f"{item['name']} 不可出售!"
        self.player.inventory.remove(idx)
        self.player.gold += sell_price
        self.add_log(f"💰 出售 {item['name']} 获得 {sell_price}G")
        return True, f"出售成功! +{sell_price}G"

    # ═══════════════════ 强化与锻造系统 ═══════════════════

    def fortify_equipment(self, equip_ref, use_charm=False):
        """强化装备（+1~+10）
        equip_ref: 装备dict的引用（player.weapon, player.armor, 或 backpack item）
        use_charm: 是否使用护锻符保护不掉级
        返回 (ok, message)
        """
        current_level = equip_ref.get("forge_level", 0)
        if current_level >= 10:
            return False, "已达到最高强化等级 +10!"

        next_level = current_level + 1
        info = get_fortify_info(next_level)
        if not info:
            return False, "强化配置错误!"

        cost = dict(info["cost"])

        # 检查护锻符
        if use_charm:
            charm_cost = dict(PROTECT_CHARM_COST)
            for k, v in charm_cost.items():
                cost[k] = cost.get(k, 0) + v

        if not self.can_afford(cost):
            cost_str = ", ".join(f"{k}{v}" for k, v in cost.items())
            return False, f"资源不足! 需要: {cost_str}"

        self.spend_resources(cost)

        # 判定成功
        success = random.random() < info["success_rate"]
        if success:
            equip_ref["forge_level"] = next_level
            self.add_log(f"🔨 强化成功! {equip_ref['name']} → +{next_level}")
            return True, f"强化成功! {equip_ref['name']} +{next_level}"
        else:
            charm_text = ""
            if use_charm:
                charm_text = "（护锻符保护不掉级）"
                self.add_log(f"🔨 强化失败! {equip_ref['name']} 护锻符保护不掉级")
            elif next_level > 5:
                # +6~+10 失败掉1级
                if current_level > 0:
                    equip_ref["forge_level"] = current_level - 1
                    self.add_log(f"🔨 强化失败! {equip_ref['name']} 掉回 +{current_level - 1}")
                    return False, f"强化失败! 掉回 +{current_level - 1}{charm_text}"
                else:
                    self.add_log(f"🔨 强化失败! {equip_ref['name']} 保持 +{current_level}")
                    return False, f"强化失败! 保持 +{current_level}{charm_text}"
            else:
                # +1~+5 不掉级
                self.add_log(f"🔨 强化失败! {equip_ref['name']} 保持 +{current_level}")
                return False, f"强化失败! 保持 +{current_level}{charm_text}"

    def forge_equipment(self, recipe_name):
        """锻造装备（使用牧场材料+铁矿+金币）
        返回 (ok, message, equip_dict_or_None)
        """
        recipe = get_forge_recipe_by_name(recipe_name)
        if not recipe:
            return False, "锻造配方不存在!", None

        # 检查核心材料
        warehouse = self.ranch.get_warehouse_summary()
        mat_name = recipe["material"]
        mat_count = recipe["material_count"]
        if warehouse.get(mat_name, 0) < mat_count:
            return False, f"{mat_name}不足! 需要{mat_count}个, 当前{warehouse.get(mat_name, 0)}个", None

        # 检查费用
        cost = {"铁矿": recipe["iron"], "金币": recipe["gold"]}
        if not self.can_afford(cost):
            cost_str = ", ".join(f"{k}{v}" for k, v in cost.items())
            return False, f"资源不足! 需要: {cost_str}", None

        if self.player.inventory.is_full():
            return False, "背包已满! (最多20件)", None

        # 消耗
        self.spend_resources(cost)
        self.ranch.output_warehouse[mat_name] -= mat_count
        if self.ranch.output_warehouse[mat_name] <= 0:
            del self.ranch.output_warehouse[mat_name]

        equip = build_forged_equip(recipe)
        self.player.add_to_inventory(equip)
        self.add_log(f"🔨 锻造成功! 获得 {equip['name']}")
        return True, f"锻造成功! 获得 {equip['name']}", equip

    def get_forge_recipes_for_ui(self):
        """获取所有锻造配方（用于UI展示）"""
        warehouse = self.ranch.get_warehouse_summary()
        recipes = []
        for r in get_all_forge_recipes():
            can_forge = (
                warehouse.get(r["material"], 0) >= r["material_count"]
                and self.resources.get("铁矿", 0) >= r["iron"]
                and self.player.gold >= r["gold"]
            )
            recipes.append({
                **r,
                "can_forge": can_forge,
                "owned_mat": warehouse.get(r["material"], 0),
            })
        return recipes

    def get_fortify_info_for_ui(self, equip):
        """获取装备的强化信息（用于UI展示）"""
        current = equip.get("forge_level", 0)
        if current >= 10:
            return {"current": 10, "maxed": True}
        next_info = get_fortify_info(current + 1)
        return {
            "current": current,
            "maxed": False,
            "next_level": next_info["level"],
            "next_bonus": next_info["bonus_pct"],
            "cost": next_info["cost"],
            "success_rate": next_info["success_rate"],
        }

    # ═══════════════════ 战斗被动效果处理 ═══════════════════

    def _get_member_passives(self, member):
        """获取成员所有被动效果列表"""
        passives = []
        for slot in [member.weapon, member.armor]:
            if slot and isinstance(slot, dict):
                p = slot.get("passive")
                if p and isinstance(p, dict):
                    passives.append(p)
        # 套装效果
        pieces = []
        for slot in [member.weapon, member.armor]:
            if slot and isinstance(slot, dict) and slot.get("is_forged"):
                pieces.append(slot)
        for eq in pieces:
            fs = eq.get("forge_set")
            if fs:
                count = count_set_pieces(pieces, fs)
                effect = get_set_effect(fs, count)
                if effect:
                    passives.append(effect)
        return passives

    def _apply_battle_start_passives(self, member):
        """应用战斗开始时的被动效果"""
        for p in self._get_member_passives(member):
            if p.get("start_heal_pct"):
                heal = int(member.get_max_hp_with_bonus() * p["start_heal_pct"] / 100)
                member.heal(heal)
                self.add_battle_log(f"  {member.role_name} 生机回复 +{heal} HP")
            if p.get("random_buff"):
                import random as _rnd
                buff = _rnd.choice(["atk", "def", "crit", "lifesteal", "hp"])
                if buff == "atk":
                    p["_active_buff"] = {"atk_pct": 10}
                    self.add_battle_log(f"  {member.role_name} 五行·攻 +10%")
                elif buff == "def":
                    p["_active_buff"] = {"def_pct": 10}
                    self.add_battle_log(f"  {member.role_name} 五行·防 +10%")
                elif buff == "crit":
                    p["_active_buff"] = {"crit_bonus": 10}
                    self.add_battle_log(f"  {member.role_name} 五行·暴击 +10%")
                elif buff == "lifesteal":
                    p["_active_buff"] = {"lifesteal": 8}
                    self.add_battle_log(f"  {member.role_name} 五行·吸血 +8%")
                else:
                    p["_active_buff"] = {"hp_pct": 10}
                    self.add_battle_log(f"  {member.role_name} 五行·HP +10%")
        member._battle_turn = 0
        member._shield_hp = 0
        member._death_save_used = False
        member._kill_atk_buff_turns = 0
        member._kill_atk_buff = 0

    def _apply_attack_passives(self, member, enemy_data):
        """应用攻击时的被动效果，返回额外伤害"""
        extra_dmg = 0
        for p in self._get_member_passives(member):
            # 毒伤: 攻击附带X%最大生命毒伤
            if p.get("poison_pct"):
                extra_dmg += int(enemy_data["hp"] * p["poison_pct"] / 100)
            # 火焰伤害: 攻击附带X%攻击力的火焰伤害
            if p.get("fire_dmg_pct"):
                extra_dmg += int(member.get_total_attack() * p["fire_dmg_pct"] / 100)
            # 首回合额外伤害
            if p.get("first_strike_pct") and member._battle_turn <= 1:
                extra_dmg += int(member.get_total_attack() * p["first_strike_pct"] / 100)
        return extra_dmg

    def _on_attack_hit_passives(self, member, enemy_data):
        """攻击命中后的额外效果，返回 (extra_msgs, confuse_enemy)"""
        msgs = []
        confuse = False
        for p in self._get_member_passives(member):
            # 幻惑: X%概率使敌人混乱
            if p.get("confuse_chance") and random.random() * 100 < p["confuse_chance"]:
                confuse = True
                msgs.append(f"  {member.role_name} 幻惑触发! 敌人混乱1回合!")
        return msgs, confuse

    def _apply_defend_passives(self, member, attacker_name, incoming_dmg):
        """应用受击时的被动效果，返回 (actual_dmg, stun_attacker, msgs)"""
        msgs = []
        stun = False
        actual = incoming_dmg
        for p in self._get_member_passives(member):
            # 闪避
            if p.get("dodge") and random.randint(1, 100) <= p["dodge"]:
                actual = 0
                msgs.append(f"  {member.role_name} 闪避了攻击!")
                return actual, stun, msgs
            # 云盾吸收
            if getattr(member, '_shield_hp', 0) > 0:
                absorbed = min(member._shield_hp, actual)
                member._shield_hp -= absorbed
                actual -= absorbed
                msgs.append(f"  {member.role_name} 云盾吸收 {absorbed} 伤害!")
            # 受击眩晕
            if p.get("stun_chance") and random.randint(1, 100) <= p["stun_chance"]:
                stun = True
                msgs.append(f"  {member.role_name} 荆棘反击! {attacker_name} 眩晕!")
        return actual, stun, msgs

    def _apply_per_turn_passives(self, member):
        """每回合开始的被动效果"""
        msgs = []
        member._battle_turn += 1
        # 云盾
        for p in self._get_member_passives(member):
            shield_interval = p.get("cloud_shield_interval")
            if shield_interval and member._battle_turn % shield_interval == 0:
                shield_pct = p.get("cloud_shield_pct", 15)
                member._shield_hp = int(member.get_max_hp_with_bonus() * shield_pct / 100)
                msgs.append(f"  {member.role_name} 获得云盾 (吸收{member._shield_hp}伤害)")
            # 每N回合回血
            regen_interval = p.get("regen_interval")
            if regen_interval and member._battle_turn % regen_interval == 0:
                heal = int(member.get_max_hp_with_bonus() * p["regen_pct"] / 100)
                member.heal(heal)
                msgs.append(f"  {member.role_name} 回复 +{heal} HP")
            # 击杀后攻击buff衰减
            if member._kill_atk_buff_turns > 0:
                member._kill_atk_buff_turns -= 1
                if member._kill_atk_buff_turns <= 0:
                    member._kill_atk_buff = 0
                    msgs.append(f"  {member.role_name} 嗜血buff消失")
        return msgs

    def _apply_on_kill_passives(self, member):
        """击杀敌人后的被动效果"""
        msgs = []
        for p in self._get_member_passives(member):
            # 击杀回复HP
            if p.get("kill_heal_pct"):
                heal = int(member.get_max_hp_with_bonus() * p["kill_heal_pct"] / 100)
                member.heal(heal)
                msgs.append(f"  {member.role_name} 噬魂回复 +{heal} HP")
            # 击杀后攻击buff
            if p.get("kill_atk_buff"):
                member._kill_atk_buff = p["kill_atk_buff"]
                member._kill_atk_buff_turns = p.get("kill_buff_turns", 2)
                msgs.append(f"  {member.role_name} 嗜血! 攻击+{member._kill_atk_buff}% ({member._kill_atk_buff_turns}回合)")
        return msgs

    def _get_gold_bonus_pct(self):
        """获取全队金币掉落加成"""
        total = 0
        for m in self.team:
            for p in self._get_member_passives(m):
                total += p.get("gold_bonus_pct", 0)
        return total

    def _get_exp_bonus_pct(self):
        """获取全队经验加成"""
        total = 0
        for m in self.team:
            for p in self._get_member_passives(m):
                total += p.get("exp_bonus_pct", 0)
        return total

    def _get_kill_gold_bonus_pct(self):
        """获取击杀怪物金币加成"""
        total = 0
        for m in self.team:
            for p in self._get_member_passives(m):
                total += p.get("kill_gold_pct", 0)
        return total

    # ── Material Trading ──
    MATERIAL_PRICES = {
        "木材": {"sell": 2, "buy": 4},
        "铁矿": {"sell": 3, "buy": 6},
        "皮革": {"sell": 2, "buy": 4},
        "石头": {"sell": 1, "buy": 2},
    }

    def buy_material(self, material, amount):
        """购买材料"""
        if material not in self.MATERIAL_PRICES:
            return False, f"未知材料: {material}"
        
        price = self.MATERIAL_PRICES[material]["buy"] * amount
        if self.player.gold < price:
            return False, f"金币不足! 需要 {price}G"
        
        self.player.gold -= price
        self.resources[material] = self.resources.get(material, 0) + amount
        self.add_log(f"📦 购买 {amount} {material} 花费 {price}G")
        return True, f"购买成功! -{price}G"

    def sell_material(self, material, amount):
        """出售材料"""
        if material not in self.MATERIAL_PRICES:
            return False, f"未知材料: {material}"
        
        if self.resources.get(material, 0) < amount:
            return False, f"{material}不足! 当前: {self.resources.get(material, 0)}"
        
        price = self.MATERIAL_PRICES[material]["sell"] * amount
        self.resources[material] -= amount
        self.player.gold += price
        self.add_log(f"💰 出售 {amount} {material} 获得 {price}G")
        return True, f"出售成功! +{price}G"

    # ═══════════════════ 队伍系统 ═══════════════════

    def get_team(self):
        """返回队伍列表（包含主角）"""
        return self.team

    def get_current_member(self):
        """返回当前选中的成员"""
        if 0 <= self.current_member_idx < len(self.team):
            return self.team[self.current_member_idx]
        return self.player

    def switch_member(self, idx):
        """切换当前选中的队伍成员"""
        if idx < 0 or idx >= len(self.team):
            return False, '无效成员'
        self.current_member_idx = idx
        member = self.team[idx]
        self.add_log('切换到: {0} Lv.{1}'.format(member.role_name, member.level))
        return True, '已切换到 {0}'.format(member.role_name)

    def recruit_member(self, role_name, level, cost, gear):
        """招募队友（从酒馆）"""
        if len(self.team) >= 3:
            return False, '队伍已满! 最多3人'
        if self.player.gold < cost:
            return False, '金币不足! 需要 {0}G'.format(cost)
        self.player.gold -= cost

        from .hero import Hero
        new_member = Hero().copy_for_recruit(level, role_name)
        for eq in gear:
            self.player.inventory.add(eq)
            self.add_log('  获得装备: {0} ({1})'.format(eq['name'], eq.get('rarity', '普通')))

        self.team.append(new_member)
        self.add_log('招募了队友: {0} Lv.{1}'.format(role_name, level))
        return True, '招募成功! {0} 加入队伍!'.format(role_name)

    def kick_member(self, idx):
        """踢出队友（idx 0 为主角，不能踢）"""
        if idx == 0:
            return False, '不能踢出主角!'
        if idx < 0 or idx >= len(self.team):
            return False, '无效成员'
        name = self.team[idx].role_name
        del self.team[idx]
        if self.current_member_idx >= len(self.team):
            self.current_member_idx = len(self.team) - 1
        self.add_log('{0} 已离队'.format(name))
        return True, '{0} 已离队'.format(name)

    def heal_full_team(self):
        """全体满血"""
        for m in self.team:
            m.hp = m.get_max_hp_with_bonus()

    # ═══════════════════ 酒馆系统 ═══════════════════

    def get_tavern_roster(self):
        """返回当前酒馆可招募角色"""
        return self.tavern_roster

    def try_refresh_tavern(self):
        """尝试刷新酒馆（每隔1小时自动刷新）"""
        now = time.time()
        auto = False
        if now - self.tavern_last_refresh >= 3600:
            auto = True
            self._do_tavern_refresh()
        return auto

    def _do_tavern_refresh(self):
        """执行酒馆刷新"""
        existing = {m.role_name for m in self.team}
        self.tavern_roster = generate_tavern_roster(self.player.level, existing)
        self.tavern_last_refresh = time.time()
        self.add_log('酒馆刷新了! (新角色登场)')

    def manual_refresh_tavern(self):
        """手动刷新酒馆（消耗50G）"""
        if self.player.gold < 50:
            return False, '金币不足! 需要50G刷新酒馆'
        self.player.gold -= 50
        self._do_tavern_refresh()
        return True, '酒馆已刷新!'

    def get_tavern_time_left(self):
        """距离下次自动刷新的秒数"""
        elapsed = time.time() - self.tavern_last_refresh
        return max(0, int(3600 - elapsed))

    # ═══════════════════ 队伍战斗逻辑 ═══════════════════

    def battle_team(self, enemy_data, is_boss=False):
        """队伍战斗（全员随机顺序攻击，怪物随机目标），含被动效果处理"""
        if self.is_battling:
            return False, '战斗中...'

        self.is_battling = True
        e_hp = enemy_data['hp']
        e_max_hp = e_hp
        boss_tag = ' [BOSS]' if is_boss else ''
        self.add_battle_log('队伍战斗: 群雄 vs {0}{1}'.format(enemy_data['name'], boss_tag))

        # ── 战斗开始被动 ──
        for m in self.team:
            self._apply_battle_start_passives(m)

        while e_hp > 0:
            # ── 每回合被动 ──
            for m in self.team:
                if m.hp > 0:
                    for msg in self._apply_per_turn_passives(m):
                        self.add_battle_log(msg)

            # ---- 队友全员攻击阶段（随机顺序）----
            alive = [m for m in self.team if m.hp > 0]
            if not alive:
                break

            random.shuffle(alive)
            for member in alive:
                if e_hp <= 0:
                    break
                if member.hp <= 0:
                    continue

                # 检查无视防御
                eff_def = enemy_data['defense']
                for p in self._get_member_passives(member):
                    if p.get("ignore_def_pct"):
                        eff_def = int(eff_def * (1 - p["ignore_def_pct"] / 100))
                    if p.get("ignore_def_chance") and random.randint(1, 100) <= p["ignore_def_chance"]:
                        eff_def = 0
                        self.add_battle_log('  {0} 破甲触发! 无视防御!'.format(member.role_name))

                p_dmg = calc_damage(member.get_total_attack(), eff_def)

                # 击杀buff
                if getattr(member, '_kill_atk_buff', 0) > 0:
                    p_dmg = int(p_dmg * (1 + member._kill_atk_buff / 100))

                # 暴击判定
                crit_rate = member.get_crit_rate()
                for p in self._get_member_passives(member):
                    if p.get("_active_buff", {}).get("crit_bonus"):
                        crit_rate += p["_active_buff"]["crit_bonus"]
                is_crit = random.randint(1, 100) <= crit_rate
                crit_mult = member.weapon.get("crit_dmg", 150) if isinstance(member.weapon, dict) else 150
                # 暴击伤害加成
                for p in self._get_member_passives(member):
                    if p.get("crit_bonus_pct"):
                        crit_mult += p["crit_bonus_pct"]
                if is_crit:
                    p_dmg = int(p_dmg * crit_mult / 100)
                    self.add_battle_log('  {0} 暴击! {1} 伤害!'.format(member.role_name, p_dmg))
                else:
                    self.add_battle_log('  {0} 攻击造成 {1} 伤害'.format(member.role_name, p_dmg))

                # 额外伤害（毒伤/火焰/首回合）
                extra = self._apply_attack_passives(member, enemy_data)
                if extra:
                    p_dmg += extra
                    self.add_battle_log('  {0} 附加伤害 +{1}'.format(member.role_name, extra))

                e_hp -= p_dmg

                # 攻击命中被动（幻惑等）
                hit_msgs, confuse = self._on_attack_hit_passives(member, enemy_data)
                for msg in hit_msgs:
                    self.add_battle_log(msg)

                # 吸血效果（原有special）
                for slot in [member.weapon, member.armor]:
                    if isinstance(slot, dict) and slot.get('special', {}).get('name') == '吸血':
                        heal = int(p_dmg * slot['special']['value'] / 100)
                        if heal > 0:
                            member.heal(heal)
                            self.add_battle_log('  {0} 吸血 +{1} HP'.format(member.role_name, heal))
                    # 五行buff吸血
                    if isinstance(slot, dict):
                        active = slot.get('passive', {}).get('_active_buff', {})
                        if active.get('lifesteal'):
                            heal = int(p_dmg * active['lifesteal'] / 100)
                            if heal > 0:
                                member.heal(heal)
                                self.add_battle_log('  {0} 五行吸血 +{1} HP'.format(member.role_name, heal))

            if e_hp <= 0:
                break

            # ---- 怪物攻击阶段（随机目标）----
            alive = [m for m in self.team if m.hp > 0]
            if not alive:
                break
            target = random.choice(alive)
            e_dmg = calc_damage(enemy_data['attack'], target.get_total_defense())

            # 受击被动（闪避/云盾/眩晕）
            actual_dmg, stun, def_msgs = self._apply_defend_passives(target, enemy_data['name'], e_dmg)
            for msg in def_msgs:
                self.add_battle_log(msg)

            if actual_dmg > 0:
                target.take_damage(actual_dmg)
                self.add_battle_log('  {0} 攻击 {1} -{2} HP'.format(enemy_data['name'], target.role_name, actual_dmg))

            if target.is_player:
                self._try_auto_potion()

            # 通报倒下成员 + 死亡被动
            for m in self.team:
                if m.hp <= 0 and not getattr(m, '_died_reported', False):
                    # 死亡免死检查
                    saved = False
                    for p in self._get_member_passives(m):
                        if p.get("death_save") and not getattr(m, '_death_save_used', False):
                            m.hp = 1
                            m._death_save_used = True
                            self.add_battle_log('  {0} 圣佑触发! 免死!'.format(m.role_name))
                            saved = True
                        if p.get("death_save_heal") and not getattr(m, '_death_save_used', False):
                            heal = int(m.get_max_hp_with_bonus() * p["death_save_heal"] / 100)
                            m.hp = heal
                            m._death_save_used = True
                            self.add_battle_log('  {0} 涅槃触发! 回复 +{1} HP'.format(m.role_name, heal))
                            saved = True
                    if not saved:
                        m._died_reported = True
                        self.add_battle_log('  {0} 倒下了!'.format(m.role_name))
                        # 死亡时队友buff
                        for p in self._get_member_passives(m):
                            if p.get("death_buff_atk_pct"):
                                for ally in self.team:
                                    if ally is not m and ally.hp > 0:
                                        ally._death_ally_buff = p["death_buff_atk_pct"]
                                        ally._death_ally_buff_turns = p.get("death_buff_turns", 3)
                                        self.add_battle_log('  {0} 牺牲! {1} 攻击+{2}%'.format(
                                            m.role_name, ally.role_name, p["death_buff_atk_pct"]))

            time.sleep(0.3)

        self.is_battling = False
        alive = [m for m in self.team if m.hp > 0]

        if alive and e_hp <= 0:
            self.add_battle_log('胜利! 击败 {0}!'.format(enemy_data['name']))

            # 击杀被动
            for m in self.team:
                if m.hp > 0:
                    for msg in self._apply_on_kill_passives(m):
                        self.add_battle_log(msg)

            # 经验（含被动加成）
            total_exp = enemy_data['exp']
            exp_bonus = self._get_exp_bonus_pct()
            if exp_bonus:
                total_exp = int(total_exp * (1 + exp_bonus / 100))
            exp_per = total_exp // len(self.team)
            for m in self.team:
                m._died_reported = False
                msgs = m.gain_exp(exp_per)
                for msg in msgs:
                    self.add_battle_log('  {0}'.format(msg))

            # 金币（含被动加成）
            gold_earned = enemy_data['gold']
            gold_bonus = self._get_gold_bonus_pct()
            kill_gold_bonus = self._get_kill_gold_bonus_pct()
            if gold_bonus:
                gold_earned = int(gold_earned * (1 + gold_bonus / 100))
            if kill_gold_bonus:
                gold_earned = int(gold_earned * (1 + kill_gold_bonus / 100))
            self.player.gold += gold_earned
            self.add_battle_log('  +{0} 经验(平分) +{1}G'.format(total_exp, gold_earned))

            for item, amount in enemy_data['drops'].items():
                self.resources[item] = self.resources.get(item, 0) + amount
                self.add_battle_log('  +{0} {1}'.format(amount, item))

            drop = generate_drop(enemy_data.get('level', 1), is_boss)
            if drop:
                drop['sell_price'] = self._calc_drop_sell_price(drop)
                self.player.inventory.add(drop)
                summary = get_drop_summary(drop)
                self.add_battle_log('  获得装备: {0}'.format(summary))

            if random.random() < 0.3:
                item = random.choice(NOVELTY_ITEMS)
                novelty = {
                    'name': item['name'], 'type': 'novelty', 'desc': item['desc'],
                    'price': item['price'], 'rarity_idx': item.get('rarity_idx', 0),
                    'sell_price': int(item['price'] * 0.8),
                }
                self.player.inventory.add(novelty)
                self.add_battle_log('  捡到小物件: {0}'.format(item['name']))

            next_enemy, next_is_boss = get_random_enemy(self.current_map)
            self.current_enemy = next_enemy
            self.current_enemy_is_boss = next_is_boss
            if self.current_enemy:
                ename = self.current_enemy.get("name", "")
                eicon = self.current_enemy.get("icon", "👾")
                edesc = self.current_enemy.get("desc", "")
                erarity = self.current_enemy.get("rarity", 0)
                eid = self.current_enemy.get("id", ename)
                if eid:
                    self.codex.discover("monsters", eid, ename, eicon, edesc, erarity, "战斗")
            return True, 'Victory'
        else:
            for m in self.team:
                m._died_reported = False
            self.add_battle_log('队伍全灭! 被 {0} 击败...'.format(enemy_data['name']))
            for m in self.team:
                m.hp = m.get_max_hp_with_bonus() // 2
            self.add_battle_log('  全体恢复: {0}/{1}'.format(
                self.player.hp, self.player.get_max_hp_with_bonus()))
            next_enemy, next_is_boss = get_random_enemy(self.current_map)
            self.current_enemy = next_enemy
            self.current_enemy_is_boss = next_is_boss
            if self.current_enemy:
                ename = self.current_enemy.get("name", "")
                eicon = self.current_enemy.get("icon", "👾")
                edesc = self.current_enemy.get("desc", "")
                erarity = self.current_enemy.get("rarity", 0)
                eid = self.current_enemy.get("id", ename)
                if eid:
                    self.codex.discover("monsters", eid, ename, eicon, edesc, erarity, "战斗")
            return False, 'Defeat'

    # ═══════════════════ 存档扩展 ═══════════════════

    def team_to_dict(self):
        """队伍序列化"""
        return {
            'members': [m.to_dict() for m in self.team],
            'current_idx': self.current_member_idx,
        }

    def team_from_dict(self, data):
        """队伍反序列化"""
        from .hero import Hero
        members = data.get('members', [])
        self.team = []
        for md in members:
            h = Hero()
            h.from_dict(md)
            self.team.append(h)
        self.current_member_idx = data.get('current_idx', 0)
        if not self.team:
            self.team = [self.player]
        if self.current_member_idx >= len(self.team):
            self.current_member_idx = 0

    def tavern_to_dict(self):
        """酒馆状态序列化"""
        return {
            'roster': tavern_roster_to_dict(self.tavern_roster),
            'last_refresh': self.tavern_last_refresh,
        }

    def buy_ranch_creature(self, creature_id: str):
        """购买牧场生物"""
        creature = get_creature_by_id(creature_id)
        if not creature:
            return False, f"未知生物: {creature_id}"
        ok, msg, new_gold = self.ranch.buy_creature(creature_id, self.player.gold)
        if not ok:
            return False, msg
        self.player.gold = new_gold
        self.add_log(f"🏠 购入 {creature['icon']} {creature['name']}!")
        # 图鉴发现
        self.codex.discover("ranch", creature_id, creature["name"], creature["icon"],
                           creature["desc"], creature["rarity"], "购买")
        return True, f"购入 {creature['icon']} {creature['name']}!"

    def feed_ranch_creature(self, index: int):
        """饲养牧场生物"""
        instances = self.ranch.ranch_inventory
        if index < 0 or index >= len(instances):
            return False, "生物不存在"
        instance = instances[index]
        creature = get_creature_by_id(instance["creature_id"])
        if not creature:
            return False, "数据异常"
        ok, msg, new_gold = self.ranch.feed_creature(index, self.player.gold)
        if not ok:
            return False, msg
        self.player.gold = new_gold
        self.add_log(f"🦴 饲养了 {creature['icon']} {creature['name']} (消耗 {creature['feed_cost']}G)")
        return True, f"{creature['icon']} {creature['name']} 开始产出!"

    def harvest_ranch_creature(self, index: int):
        """收获牧场生物产出"""
        result = self.ranch.harvest_creature(index)
        if not result:
            return False, "还未到产出时间!"
        self.add_log(f"📦 {result['creature_icon']} {result['creature_name']} 产出 "
                     f"{result['count']}×{result['output_type']} "
                     f"({result['personality']}+{int((result['bonus']-1)*100)}%)")
        return True, f"获得 {result['count']}×{result['output_type']}!"

    def sell_ranch_output(self, output_type: str, count: int):
        """卖出牧场产出物"""
        old_gold = self.player.gold
        ok, msg, new_gold = self.ranch.sell_output(output_type, count, old_gold)
        if not ok:
            return False, msg
        self.player.gold = new_gold
        gain = new_gold - old_gold
        self.add_log(f"💰 卖出 {count}×{output_type}! +{gain}G")
        return True, f"卖出成功! +{gain}G"

    def ranch_tick(self):
        """牧场产出Tick（可由主循环调用或独立线程）"""
        changed, fertilizer_gains = self.ranch.check_outputs()
        for fert_type, count in fertilizer_gains.items():
            self.fertilizer_bag[fert_type] = self.fertilizer_bag.get(fert_type, 0) + count
            self.add_log(f"🧪 牧场产出 {fert_type}×{count}")
        return changed

    def tavern_from_dict(self, data):
        """酒馆状态反序列化"""
        self.tavern_roster = tavern_roster_from_dict(data.get('roster', []))
        self.tavern_last_refresh = data.get('last_refresh', time.time())

    def to_dict(self):
        """序列化全部游戏状态为字典"""
        return {
            "resources": self.resources,
            "buildings": self.buildings,
            "building_levels": self.building_levels,
            "building_workers": self.building_workers,
            "player": self.player.to_dict(),
            "current_map": self.current_map,
            "unlocked_maps": list(self.unlocked_maps),
            "current_enemy_idx": self.current_enemy_idx,
            "wonders": list(self.wonders.keys()),
            "plants": self.plants,
            "factory": self.factory,
            "factory_departments": self.factory_departments,
            "factory_workers": self.factory_workers,
            "factory_last_profit_time": getattr(self, "factory_last_profit_time", 0),
            "auto_potion_threshold": self.auto_potion_threshold,
            "team": self.team_to_dict(),
            "tavern": self.tavern_to_dict(),
            "codex": self.codex.to_dict(),
            "ranch": self.ranch.to_dict(),
            "current_member_idx": self.current_member_idx,
            "mutated_plants": self.mutated_plants,
            "feed_bag": self.feed_bag,
            "fertilizer_bag": self.fertilizer_bag,
            "battle_logs": self.battle_logs,
        }

    def from_dict(self, data):
        """从字典恢复全部游戏状态"""
        self.resources = data.get("resources", {})
        self.buildings = data.get("buildings", {})
        self.building_levels = data.get("building_levels", {})
        self.building_workers = data.get("building_workers", {})
        self.player.from_dict(data.get("player", {}))
        self.current_map = data.get("current_map", "傲来国")
        self.unlocked_maps = set(data.get("unlocked_maps", ["傲来国"]))
        self.current_enemy_idx = data.get("current_enemy_idx", 0)
        self.wonders = {n: True for n in data.get("wonders", [])}
        self.plants = data.get("plants", [])
        self.factory = data.get("factory")
        self.factory_departments = data.get("factory_departments",
                                            ["basic"] if data.get("factory") else [])
        self.factory_workers = data.get("factory_workers", 0)
        self.factory_last_profit_time = data.get("factory_last_profit_time", 0)
        self.auto_potion_threshold = data.get("auto_potion_threshold", 0)
        self.team_from_dict(data.get("team", []))
        self.tavern_from_dict(data.get("tavern", []))
        self.codex.from_dict(data.get("codex", {}))
        self.ranch.from_dict(data.get("ranch", {}))
        self.current_member_idx = data.get("current_member_idx", 0)
        self.mutated_plants = data.get("mutated_plants", {})
        self.feed_bag = data.get("feed_bag", {})
        self.fertilizer_bag = data.get("fertilizer_bag", {})
        self.battle_logs = data.get("battle_logs", [])
        # 重启建筑生产线程
        for name, levels in self.building_levels.items():
            for idx in range(len(levels)):
                self.start_building_production(name, idx)

    def save_to_file(self, filepath):
        """存档到 JSON 文件"""
        import json
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    def load_from_file(self, filepath):
        """从 JSON 文件读档"""
        import os, json
        if not os.path.exists(filepath):
            return False
        with open(filepath, "r", encoding="utf-8") as f:
            self.from_dict(json.load(f))
        return True
