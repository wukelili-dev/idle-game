"""
英雄模块 - 定义玩家属性和成长系统
"""
import random
from .inventory import Inventory


class Hero:
    """英雄类"""
    def __init__(self):
        self.hp = 100
        self.max_hp = 100
        self.attack = 10
        self.defense = 5
        self.exp = 0
        self.level = 1
        self.gold = 100
        self.weapon = None
        self.armor = None
        self.kill_count = 0
        self.potions = 0
        self.inventory = Inventory()  # 背包对象
        self.is_player = True   # True=主角，False=队友
        self.role_name = "勇者"  # 显示名称

    def add_to_inventory(self, equip):
        """添加装备到背包"""
        self.inventory.add(equip)

    def equip_item(self, index):
        """穿戴背包中的装备"""
        equip = self.inventory.get(index)
        if not equip:
            return None, "无效的背包位置!"
        if self.level < equip.get("level_req", 0):
            return None, "等级不够!"
        
        if equip["type"] == "weapon":
            self.weapon = equip
        elif equip["type"] == "armor":
            self.armor = equip
        self.inventory.remove(index)
        return equip, "穿戴成功"

    def sell_item(self, index):
        """出售背包中的物品，返回物品和售价"""
        equip = self.inventory.remove(index)
        if not equip:
            return None, 0
        return equip, equip.get("sell_price", 10)

    def get_inventory(self):
        """获取背包对象"""
        return self.inventory

    def get_total_attack(self):
        """获取总攻击力（基础+武器）"""
        if self.weapon and isinstance(self.weapon, dict):
            return self.attack + self.weapon.get("attack", 0)
        return self.attack

    def get_crit_rate(self):
        """获取暴击率"""
        if self.weapon and isinstance(self.weapon, dict):
            return self.weapon.get("crit_rate", 0)
        return 0

    def get_total_defense(self):
        """获取总防御力（基础+护甲）"""
        if self.armor and isinstance(self.armor, dict):
            return self.defense + self.armor.get("defense", 0)
        return self.defense

    def get_max_hp_with_bonus(self):
        """获取最大生命值（基础+护甲加成）"""
        bonus = 0
        if self.armor and isinstance(self.armor, dict):
            bonus = self.armor.get("hp_bonus", 0)
        return self.max_hp + bonus

    def take_damage(self, damage):
        """受到伤害，血量不会降到负数"""
        self.hp = max(0, self.hp - damage)
        return self.hp

    def heal(self, amount):
        """恢复生命值"""
        max_hp = self.get_max_hp_with_bonus()
        self.hp = min(max_hp, self.hp + amount)
        return self.hp

    def gain_exp(self, amount):
        """获得经验，可能触发升级，最高100级"""
        MAX_LEVEL = 100
        if self.level >= MAX_LEVEL:
            return ["已达到最高等级!"]
        
        self.exp += amount
        level_up_msgs = []
        
        while self.exp >= self.level * 100 and self.level < MAX_LEVEL:
            exp_needed = self.level * 100
            self.exp -= exp_needed
            self.level += 1
            self.max_hp += 20
            self.hp = min(self.hp + 20, self.get_max_hp_with_bonus())
            self.attack += 3
            self.defense += 2
            level_up_msgs.append(f"升级了! 现在是 {self.level} 级!")
            
            if self.level >= MAX_LEVEL:
                level_up_msgs.append("恭喜! 已达到最高等级100级!")
                break
                
        return level_up_msgs

    def equip_weapon(self, weapon):
        """装备武器"""
        self.weapon = weapon

    def equip_armor(self, armor):
        """装备护甲"""
        self.armor = armor

    def copy_for_recruit(self, level, role_name):
        """创建队友（等级固定，无装备，共享背包）"""
        recruit = Hero()
        recruit.is_player = False
        recruit.role_name = role_name
        # 基础属性与等级挂钩
        recruit.level = max(1, level)
        recruit.max_hp = 80 + (recruit.level - 1) * 18
        recruit.hp = recruit.max_hp
        recruit.attack = 8 + (recruit.level - 1) * 2
        recruit.defense = 4 + (recruit.level - 1) * 2
        recruit.exp = 0
        recruit.gold = 0
        # 共享背包由 GameCore 管理，此处 inventory 不使用
        recruit.inventory = None
        return recruit

    def to_dict(self):
        """转换为字典（用于存档）"""
        return {
            "hp": self.hp,
            "max_hp": self.max_hp,
            "attack": self.attack,
            "defense": self.defense,
            "exp": self.exp,
            "level": self.level,
            "gold": self.gold,
            "weapon": self.weapon,
            "armor": self.armor,
            "kill_count": self.kill_count,
            "potions": self.potions,
            "inventory": self.inventory.to_dict() if self.inventory else {},
            "is_player": self.is_player,
            "role_name": self.role_name,
        }

    def from_dict(self, data):
        """从字典加载（用于读档）"""
        self.hp = data.get("hp", 100)
        self.max_hp = data.get("max_hp", 100)
        self.attack = data.get("attack", 10)
        self.defense = data.get("defense", 5)
        self.exp = data.get("exp", 0)
        self.level = data.get("level", 1)
        self.gold = data.get("gold", 100)
        self.weapon = data.get("weapon", None)
        self.armor = data.get("armor", None)
        self.kill_count = data.get("kill_count", 0)
        self.potions = data.get("potions", 0)
        self.inventory = Inventory()
        self.inventory.from_dict(data.get("inventory", {}))
        self.is_player = data.get("is_player", True)
        self.role_name = data.get("role_name", "勇者")
