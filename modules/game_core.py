"""
游戏核心模块 - 游戏逻辑主类
"""
import time
import threading
import random
from .hero import Hero
from .buildings import (get_building_config, get_building_output_resource, 
                        MAX_BUILDING_COUNT, WORKER_CONFIG, get_wonder_config)
from .maps import get_map_enemies, get_all_maps, can_enter_map, get_unlock_cost
from .equipment_drops import generate_drop, get_drop_summary
from .inventory import NOVELTY_ITEMS
from .plants import (get_plant_catalog, get_plant_by_id, calc_grow_stage,
                     STAGE_NAMES, STAGE_ICONS, MAX_PLANTS)
from .factory import (FACTORY_BUILD_COST, FACTORY_BASE_INTERVAL_S,
                      FACTORY_BASE_PROFIT, DEPARTMENTS, MAX_FACTORY_WORKERS,
                      FACTORY_WORKER_COST_GOLD, get_dept_by_id,
                      calc_factory_bonus)


class GameCore:
    """游戏核心类"""
    def __init__(self):
        self.resources = {"Wood": 0, "Iron": 0, "Leather": 0, "Stone": 0}  # 新增石头资源
        self.buildings = {}  # 建筑数量
        self.building_levels = {}  # 建筑等级列表
        self.building_workers = {}  # 建筑劳工数量 {name: [count, count, ...]}
        self.player = Hero()
        self.current_map = "傲来国"  # 初始地图
        self.unlocked_maps = {"傲来国"}  # 已解锁地图
        self.current_enemy_idx = 0
        self.is_battling = False
        self.auto_battle = False
        self.auto_battle_thread = None
        self.auto_potion_threshold = 0  # 0=关, 30/50/80=血量百分比阈值
        self.running = True
        self.logs = []
        self.production_active = set()
        self.wonders = {}  # 已建造的奇观 {name: True}
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

        cost = {"Gold": dept["cost_gold"], **dept["cost_resources"]}
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
            if res == "Gold":
                if self.player.gold < amount:
                    return False
            elif self.resources.get(res, 0) < amount:
                return False
        return True

    def spend_resources(self, cost):
        """消耗资源"""
        for res, amount in cost.items():
            if res == "Gold":
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
        self.add_log(f"Built {name}! Total: {self.buildings[name]}")
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
            return False, f"Not enough! Need G{cost.get('Gold',0)} W{cost.get('Wood',0)}"

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
                interval = config.get_interval(level)
                output = config.get_output(level)
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
            return False, f"金币不足! 需要{cost['Gold']}G"
        
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
            return False, "Not enough gold! Need 25G"
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
                self.add_log(f"  💊 Auto-potion! +{heal} HP (remaining: {self.player.potions})")
            return

        # 没有药水，尝试购买（金币不够就等下一次，绝不关闭自动药水）
        if self.player.gold >= 25:
            self.player.gold -= 25
            self.player.potions += 1
            self.add_log(f"  💊 Auto-bought potion (25G), using now!")
            heal = min(20, max_hp - self.player.hp)
            if heal > 0:
                self.player.potions -= 1
                self.player.heal(heal)
                self.add_log(f"  💊 Auto-potion! +{heal} HP (remaining: {self.player.potions})")

    def set_auto_potion_threshold(self, value):
        """设置自动药水阈值"""
        self.auto_potion_threshold = value

    def battle(self, enemy_data, is_boss=False):
        """战斗逻辑"""
        if self.is_battling:
            return False, "In battle..."

        self.is_battling = True
        e_hp = enemy_data["hp"]
        self.add_log(f"Battle: Hero vs {enemy_data['name']}")

        while e_hp > 0 and self.player.hp > 0:
            # 玩家攻击
            p_dmg = max(1, self.player.get_total_attack() - enemy_data["defense"] // 2 + random.randint(-3, 3))
            is_crit = random.randint(1, 100) <= self.player.get_crit_rate()
            if is_crit:
                p_dmg = int(p_dmg * 1.5)
                self.add_log(f"  CRIT! {p_dmg} damage!")
            else:
                self.add_log(f"  You dealt {p_dmg} damage")
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

            # 敌人攻击
            e_dmg = max(1, enemy_data["attack"] - self.player.get_total_defense() // 2 + random.randint(-2, 2))
            self.player.take_damage(e_dmg)
            self.add_log(f"  {enemy_data['name']} dealt {e_dmg} damage")

            # 自动药水检查（被攻击后立即判断）
            self._try_auto_potion()

            time.sleep(0.5)

        if self.player.hp > 0:
            self.add_log(f"Victory! Defeated {enemy_data['name']}!")
            self.player.gold += enemy_data["gold"]
            self.player.kill_count += 1
            self.add_log(f"  +{enemy_data['exp']} EXP +{enemy_data['gold']} Gold")
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
            return True, "Victory"
        else:
            self.add_log(f"Defeated by {enemy_data['name']}!")
            self.player.hp = self.player.get_max_hp_with_bonus() // 2
            self.add_log(f"Recovered: {self.player.hp}/{self.player.get_max_hp_with_bonus()}")
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
                # 每次从当前地图获取敌人
                enemies = self.get_current_map_enemies()
                if enemies and self.current_enemy_idx < len(enemies):
                    enemy = enemies[self.current_enemy_idx]
                    result, msg = self.battle(enemy)
                    
                    # 战斗胜利后推进敌人索引
                    if result:
                        if self.current_enemy_idx < len(enemies) - 1:
                            self.current_enemy_idx += 1
                        else:
                            self.current_enemy_idx = 0
                            self.add_log("Enemy list reset!")
                    
                    self.is_battling = False
                else:
                    self.add_log("No enemies available!")
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

    def _calc_shop_sell_price(self, cost):
        """计算商店装备售价（80%）"""
        # 只计算金币成本，其他资源按比例转换
        gold_value = cost.get("Gold", 0)
        # Wood=2G, Iron=3G, Leather=2G, Stone=1G
        gold_value += cost.get("Wood", 0) * 2
        gold_value += cost.get("Iron", 0) * 3
        gold_value += cost.get("Leather", 0) * 2
        gold_value += cost.get("Stone", 0) * 1
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
        "Wood": {"sell": 2, "buy": 4},
        "Iron": {"sell": 3, "buy": 6},
        "Leather": {"sell": 2, "buy": 4},
        "Stone": {"sell": 1, "buy": 2},
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
