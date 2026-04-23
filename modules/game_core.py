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
                     STAGE_NAMES, STAGE_ICONS, MAX_PLANTS)
from .tavern import (generate_tavern_roster, tavern_roster_to_dict, tavern_roster_from_dict)
from .factory import (FACTORY_BUILD_COST, FACTORY_BASE_INTERVAL_S,
                      FACTORY_BASE_PROFIT, DEPARTMENTS, MAX_FACTORY_WORKERS,
                      FACTORY_WORKER_COST_GOLD, get_dept_by_id,
                      calc_factory_bonus)


# ═══════════════ 伤害公式常量 ═══════════════
DEF_COEFF = 50  # 防御衰减系数，DEF越高中和收益递减越慢


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
        self.logs = []
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
        self._start_plant_system()

        # ── 工厂系统 ──
        self.factory = None    # None 表示未建造，dict 表示已建造
        self.factory_departments = []   # list of dept_id 已解锁部门
        self.factory_workers = 0         # 工厂劳工数量
        self.factory_last_profit_time = 0  # 上次结算时间戳
        self.factory_thread = None
        self._start_factory_system()

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
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {msg}")
        if len(self.logs) > 100:
            self.logs.pop(0)

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
        }
        self.plants.append(plant)
        self.add_log(f"🌱 种下了 {pd['icon']} {pd['name']}")
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

    def harvest_plant(self, plant_id):
        """手动收割植物（仅成年可收割）"""
        plant = None
        for p in self.plants:
            if p["id"] == plant_id:
                plant = p
                break
        if not plant:
            return False, "植物不存在"

        pd = get_plant_by_id(plant["plant_id"])
        elapsed = time.time() - plant["planted_at"]
        stage = calc_grow_stage(elapsed, pd["grow_time_s"])

        if stage < 3:
            return False, "植物尚未成年，无法收割"

        # 计算本次收割收益
        adult_elapsed = elapsed - pd["grow_time_s"]
        interval = pd["harvest_interval_s"]
        prev_harvests = plant.get("harvest_count", 0)
        current_harvests = int(adult_elapsed // interval)

        gain = (current_harvests + 1 - prev_harvests) * pd["harvest_gold"]
        self.player.gold += gain
        plant["harvest_count"] = current_harvests + 1
        self.add_log(f"🌾 收割了 {pd['icon']} {pd['name']} 获得 {gain}G")
        return True, f"收割成功! +{gain}G"

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
        self.add_log(f"战斗: 英雄 vs {enemy_data['name']}{boss_tag}")

        while e_hp > 0 and self.player.hp > 0:
            # 玩家攻击怪物
            p_dmg = calc_damage(self.player.get_total_attack(), enemy_data["defense"])
            is_crit = random.randint(1, 100) <= self.player.get_crit_rate()
            crit_mult = self.player.weapon.get("crit_dmg", 150) if isinstance(self.player.weapon, dict) else 150
            if is_crit:
                p_dmg = int(p_dmg * crit_mult / 100)
                self.add_log(f"  暴击! {p_dmg} 伤害!")
            else:
                self.add_log(f"  你对敌人造成 {p_dmg} 伤害")
            e_hp -= p_dmg
            
            # 吸血效果
            special = self.player.weapon.get("special") if isinstance(self.player.weapon, dict) else None
            if special and special.get("name") == "吸血":
                lifesteal = special["value"]
                heal = int(p_dmg * lifesteal / 100)
                if heal > 0:
                    self.player.heal(heal)
                    self.add_log(f"  💉 吸血恢复 {heal} HP")
            special = self.player.armor.get("special") if isinstance(self.player.armor, dict) else None
            if special and special.get("name") == "吸血":
                lifesteal = special["value"]
                heal = int(p_dmg * lifesteal / 100)
                if heal > 0:
                    self.player.heal(heal)
                    self.add_log(f"  💉 吸血恢复 {heal} HP")
            
            if e_hp <= 0:
                break

            # 敌人攻击怪物
            e_dmg = calc_damage(enemy_data["attack"], self.player.get_total_defense())
            self.player.take_damage(e_dmg)
            self.add_log(f"  {enemy_data['name']} 对英雄造成 {e_dmg} 伤害")

            # 自动药水检查（被攻击后立即判断）
            self._try_auto_potion()

            time.sleep(0.5)

        if self.player.hp > 0:
            self.add_log(f"胜利! 击败 {enemy_data['name']}!")
            self.player.gold += enemy_data["gold"]
            self.player.kill_count += 1
            self.add_log(f"  +{enemy_data['exp']} 经验 +{enemy_data['gold']} 金币")
            for item, amount in enemy_data["drops"].items():
                self.resources[item] = self.resources.get(item, 0) + amount
                self.add_log(f"  +{amount} {item}")
            
            # 装备掉落
            drop = generate_drop(enemy_data.get("level", 1), is_boss)
            if drop:
                # 计算售价
                drop["sell_price"] = self._calc_drop_sell_price(drop)
                self.player.add_to_inventory(drop)
                summary = get_drop_summary(drop)
                self.add_log(f"  🎁 获得装备: {summary}")
            
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
                self.add_log(f"  🎁 捡到小物件: {item['name']}")
            
            msgs = self.player.gain_exp(enemy_data["exp"])
            for m in msgs:
                self.add_log(m)
            # 战斗胜利后获取下一个敌人
            next_enemy, next_is_boss = get_random_enemy(self.current_map)
            self.current_enemy = next_enemy
            self.current_enemy_is_boss = next_is_boss
            return True, "Victory"
        else:
            self.add_log(f"被 {enemy_data['name']}!")
            self.player.hp = self.player.get_max_hp_with_bonus() // 2
            self.add_log(f"恢复: {self.player.hp}/{self.player.get_max_hp_with_bonus()}")
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
                    self.add_log("没有可用敌人!")
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
            self.add_log(f"🔄 刷新敌人: {enemy['name']}{boss_tag}")
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
        """队伍战斗（全员随机顺序攻击，怪物随机目标）"""
        if self.is_battling:
            return False, '战斗中...'

        self.heal_full_team()
        self.is_battling = True
        e_hp = enemy_data['hp']
        boss_tag = ' [BOSS]' if is_boss else ''
        self.add_log('队伍战斗: 群雄 vs {0}{1}'.format(enemy_data['name'], boss_tag))

        while e_hp > 0:
            # ---- 队友全员攻击阶段（随机顺序）----
            alive = [m for m in self.team if m.hp > 0]
            if not alive:
                break

            random.shuffle(alive)  # 随机攻击顺序
            for member in alive:
                if e_hp <= 0:
                    break
                if member.hp <= 0:
                    continue

                p_dmg = calc_damage(member.get_total_attack(), enemy_data['defense'])
                is_crit = random.randint(1, 100) <= member.get_crit_rate()
                crit_mult = member.weapon.get("crit_dmg", 150) if isinstance(member.weapon, dict) else 150
                if is_crit:
                    p_dmg = int(p_dmg * crit_mult / 100)
                    self.add_log('  {0} 暴击! {1} 伤害!'.format(member.role_name, p_dmg))
                else:
                    self.add_log('  {0} 攻击造成 {1} 伤害'.format(member.role_name, p_dmg))
                e_hp -= p_dmg

                # 吸血效果
                for slot in [member.weapon, member.armor]:
                    if isinstance(slot, dict) and slot.get('special', {}).get('name') == '吸血':
                        heal = int(p_dmg * slot['special']['value'] / 100)
                        if heal > 0:
                            member.heal(heal)
                            self.add_log('  {0} 吸血 +{1} HP'.format(member.role_name, heal))

            if e_hp <= 0:
                break

            # ---- 怪物攻击阶段（随机目标）----
            alive = [m for m in self.team if m.hp > 0]
            if not alive:
                break
            target = random.choice(alive)
            e_dmg = calc_damage(enemy_data['attack'], target.get_total_defense())
            target.take_damage(e_dmg)
            self.add_log('  {0} 攻击 {1} -{2} HP'.format(enemy_data['name'], target.role_name, e_dmg))

            if target.is_player:
                self._try_auto_potion()

            # 通报倒下成员
            for m in self.team:
                if m.hp <= 0 and not getattr(m, '_died_reported', False):
                    self.add_log('  {0} 倒下了!'.format(m.role_name))
                    m._died_reported = True

            time.sleep(0.3)

        self.is_battling = False
        alive = [m for m in self.team if m.hp > 0]

        if alive and e_hp <= 0:
            self.add_log('胜利! 击败 {0}!'.format(enemy_data['name']))
            total_exp = enemy_data['exp']
            exp_per = total_exp // len(self.team)
            for m in self.team:
                m._died_reported = False
                msgs = m.gain_exp(exp_per)
                for msg in msgs:
                    self.add_log('  {0}'.format(msg))
            self.player.gold += enemy_data['gold']
            self.add_log('  +{0} 经验(平分) +{1}G'.format(total_exp, enemy_data['gold']))
            for item, amount in enemy_data['drops'].items():
                self.resources[item] = self.resources.get(item, 0) + amount
                self.add_log('  +{0} {1}'.format(amount, item))

            drop = generate_drop(enemy_data.get('level', 1), is_boss)
            if drop:
                drop['sell_price'] = self._calc_drop_sell_price(drop)
                self.player.inventory.add(drop)
                summary = get_drop_summary(drop)
                self.add_log('  获得装备: {0}'.format(summary))

            if random.random() < 0.3:
                item = random.choice(NOVELTY_ITEMS)
                novelty = {
                    'name': item['name'], 'type': 'novelty', 'desc': item['desc'],
                    'price': item['price'], 'rarity_idx': item.get('rarity_idx', 0),
                    'sell_price': int(item['price'] * 0.8),
                }
                self.player.inventory.add(novelty)
                self.add_log('  捡到小物件: {0}'.format(item['name']))

            next_enemy, next_is_boss = get_random_enemy(self.current_map)
            self.current_enemy = next_enemy
            self.current_enemy_is_boss = next_is_boss
            return True, 'Victory'
        else:
            for m in self.team:
                m._died_reported = False
            self.add_log('队伍全灭! 被 {0} 击败...'.format(enemy_data['name']))
            for m in self.team:
                m.hp = m.get_max_hp_with_bonus() // 2
            self.add_log('  全体恢复: {0}/{1}'.format(
                self.player.hp, self.player.get_max_hp_with_bonus()))
            next_enemy, next_is_boss = get_random_enemy(self.current_map)
            self.current_enemy = next_enemy
            self.current_enemy_is_boss = next_is_boss
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

    def tavern_from_dict(self, data):
        """酒馆状态反序列化"""
        self.tavern_roster = tavern_roster_from_dict(data.get('roster', []))
        self.tavern_last_refresh = data.get('last_refresh', time.time())
