"""
勇者工坊 v3.0 - Idle Game
Run: python main.py
"""

from modules.inventory import NOVELTY_ITEMS, NOVELTY_RARITY_COLORS, NOVELTY_RARITY_NAMES
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.equipment import WEAPONS, ARMORS
from modules.buildings import (BUILDING_CONFIGS, get_all_building_names,
                               get_all_wonders, get_wonder_names, WORKER_CONFIG)
from modules.maps import get_all_maps, get_map_enemies, print_map_info, print_enemy_info
from modules.hero import Hero
from modules.game_core import GameCore


class App:
    def __init__(self):
        self.game = GameCore()
        self.root = tk.Tk()
        self.root.title("勇者工坊 v3.0")
        self.root.geometry("1280x900")
        self.root.resizable(True, True)

        self._last_building_snap = {}
        self._last_farm_snap = None
        self._last_factory_snap = None
        self.setup_ui()
        self.refresh_ui()
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()

    # ──────────────── UI Setup ────────────────

    def setup_ui(self):
        # ── Top bar ──
        top = tk.Frame(self.root, relief="groove", bd=1)
        top.pack(fill="x", pady=0)
        tk.Label(top, text="\u2694 勇者工坊 v3.0",
                 font=("Arial", 15, "bold")).pack(side="left", padx=15, pady=6)
        self.gold_label = tk.Label(top, text="\U0001FA99 100",
                                   font=("Arial", 14, "bold"), fg="#B8860B")
        self.gold_label.pack(side="right", padx=15, pady=6)
        self.kills_label = tk.Label(top, text="击杀: 0",
                                    font=("Arial", 10), fg="#888")
        self.kills_label.pack(side="right", padx=10, pady=6)

        # ── Main body (PanedWindow for resizable) ──
        self.pw = tk.PanedWindow(self.root, orient="horizontal", sashwidth=4)
        self.pw.pack(fill="both", expand=True, padx=4, pady=4)

        # Left panel
        left_container = tk.Frame(self.pw)
        self.pw.add(left_container, minsize=220, width=260)
        self._build_left(left_container)

        # Center panel
        center_container = tk.Frame(self.pw)
        self.pw.add(center_container, minsize=280, width=310)
        self._build_center(center_container)

        # Right panel
        right_container = tk.Frame(self.pw)
        self.pw.add(right_container, minsize=300, width=400)
        self._build_right(right_container)

        # ── Bottom: Inventory grid ──
        self._build_inventory()

        # ── Log ──
        self._build_log()

        # ── Bottom bar ──
        bar = tk.Frame(self.root, relief="groove", bd=1)
        bar.pack(fill="x")
        tk.Button(bar, text="存档", command=self.save_game,
                  bg="#5B9BD5", fg="white", font=("Arial", 9),
                  relief="groove", padx=12).pack(side="left", padx=8, pady=4)
        tk.Button(bar, text="读档", command=self.load_game,
                  bg="#5B9BD5", fg="white", font=("Arial", 9),
                  relief="groove", padx=12).pack(side="left", padx=4, pady=4)
        tk.Button(bar, text="帮助", command=self.show_help,
                  bg="#999", fg="white", font=("Arial", 9),
                  relief="groove", padx=12).pack(side="right", padx=8, pady=4)

    # ── Left: 资源 + 建筑 + 奇观 (scrollable) ──
    def _build_left(self, parent):
        # Canvas + scrollbar for entire left panel
        canvas = tk.Canvas(parent, highlightthickness=0)
        vsb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas)
        canvas.create_window((0, 0), window=inner, anchor="nw")

        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Also resize inner frame width to match canvas
            canvas.itemconfigure(canvas.find_withtag("all")[0], width=event.width)
        canvas.bind("<Configure>", on_configure)

        # Enable mousewheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        self._left_canvas = canvas
        self._left_inner = inner

        # 资源
        rf = ttk.LabelFrame(inner, text="\U0001F4E6 资源", padding=6)
        rf.pack(fill="x", padx=4, pady=(6, 3))
        self.res_labels = {}
        self.res_buy_entries = {}
        MATERIALS = [("Wood", "\U0001F332", 4), ("Iron", "\u2692", 6), 
                     ("Leather", "\U0001F9B4", 4), ("Stone", "\u26F0", 2)]
        for res, emoji, buy_price in MATERIALS:
            row = tk.Frame(rf)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{emoji} {res}:", font=("Arial", 10),
                     width=10, anchor="w").pack(side="left")
            self.res_labels[res] = tk.Label(row, text="0", font=("Arial", 10, "bold"),
                                            fg="#333", anchor="w", width=6)
            self.res_labels[res].pack(side="left")
            
            # 购买/出售 buttons
            tk.Button(row, text="B", font=("Arial", 7), bg="#4CAF50", fg="white",
                      width=2, relief="raised",
                      command=lambda r=res: self.buy_material(r)).pack(side="left", padx=1)
            tk.Button(row, text="S", font=("Arial", 7), bg="#FF9800", fg="white",
                      width=2, relief="raised",
                      command=lambda r=res: self.sell_material(r)).pack(side="left", padx=1)
            self.res_buy_entries[res] = tk.Entry(row, width=3, font=("Arial", 8))
            self.res_buy_entries[res].insert(0, "10")
            self.res_buy_entries[res].pack(side="left", padx=2)

        # 建筑
        bf = ttk.LabelFrame(inner, text="\U0001F3D7 建筑", padding=6)
        bf.pack(fill="x", padx=4, pady=3)
        self.building_widgets = {}
        for bname in get_all_building_names():
            bframe = tk.Frame(bf, relief="groove", bd=1)
            bframe.pack(fill="x", pady=4, ipady=4)

            hdr = tk.Frame(bframe)
            hdr.pack(fill="x", padx=6)
            tk.Label(hdr, text=bname, font=("Arial", 10, "bold")).pack(side="left")
            count_lbl = tk.Label(hdr, text="x0", font=("Arial", 9), fg="#888")
            count_lbl.pack(side="right")

            info_lbl = tk.Label(bframe, text="未建造", font=("Arial", 8), fg="#aaa")
            info_lbl.pack(anchor="w", padx=6)

            build_btn = tk.Button(bframe, text="建造",
                                  command=lambda n=bname: self.build_building(n),
                                  bg="#4CAF50", fg="white", font=("Arial", 9),
                                  relief="groove", padx=8)
            build_btn.pack(fill="x", padx=6, pady=(2, 0))

            upgrade_frame = tk.Frame(bframe)
            upgrade_frame.pack(fill="x", padx=6, pady=(2, 4))

            self.building_widgets[bname] = {
                "count": count_lbl,
                "info": info_lbl,
                "upgrade_frame": upgrade_frame,
            }

        # 奇观
        wf = ttk.LabelFrame(inner, text="\u2728 奇观", padding=6)
        wf.pack(fill="x", padx=4, pady=3)
        self.wonder_buttons = {}
        for wn in get_wonder_names():
            btn = tk.Button(wf, text=wn, command=lambda w=wn: self.build_wonder(w),
                           font=("Arial", 9), bg="#FFF8DC", fg="#333",
                           relief="groove", anchor="w", padx=10)
            btn.pack(fill="x", pady=2)
            self.wonder_buttons[wn] = btn

    # ── Center: Hero + 地图 + Battle ──
    def _build_center(self, parent):
        # Hero stats
        hf = ttk.LabelFrame(parent, text="\U0001F9D1 英雄属性", padding=8)
        hf.pack(fill="x", padx=4, pady=(4, 3))

        self.hp_var = tk.StringVar(value="生命: 100/100")
        self.attack_var = tk.StringVar(value="攻击: 10")
        self.defense_var = tk.StringVar(value="防御: 5")
        self.crit_var = tk.StringVar(value="CRIT: 0%")
        self.level_var = tk.StringVar(value="Lv.1")
        self.exp_var = tk.StringVar(value="经验: 0/100")
        self.weapon_var = tk.StringVar(value="武器: None")
        self.armor_var = tk.StringVar(value="护甲: None")

        for var in [self.level_var, self.exp_var, self.hp_var,
                    self.attack_var, self.defense_var, self.crit_var,
                    self.weapon_var, self.armor_var]:
            tk.Label(hf, textvariable=var, font=("Arial", 10),
                     anchor="w").pack(fill="x", padx=4, pady=1)

        # 地图
        mf = ttk.LabelFrame(parent, text="\U0001F5FA 地图", padding=8)
        mf.pack(fill="x", padx=4, pady=3)

        self.map_var = tk.StringVar(value="\u50B2\u6765\u56FD")
        tk.Label(mf, textvariable=self.map_var, font=("Arial", 12, "bold"),
                 fg="#1565C0").pack(pady=2)

        map_btn_frame = tk.Frame(mf)
        map_btn_frame.pack(fill="x", pady=4)
        self.map_buttons = {}
        for mn in get_all_maps().keys():
            btn = tk.Button(map_btn_frame, text=mn, command=lambda m=mn: self.change_map(m),
                           font=("Arial", 8), relief="groove", padx=6)
            btn.pack(side="left", padx=2, pady=2)
            self.map_buttons[mn] = btn

        # 敌人
        ef = ttk.LabelFrame(parent, text="💀 敌人", padding=8)
        ef.pack(fill="x", padx=4, pady=3)

        self.enemy_var = tk.StringVar(value="???")
        tk.Label(ef, textvariable=self.enemy_var, font=("Arial", 11, "bold"),
                 fg="#C62828").pack(pady=2)
        
        # 刷新敌人按钮
        self.refresh_btn = tk.Button(ef, text="🔄 刷新敌人",
                                     command=self.do_refresh_enemy,
                                     font=("Arial", 9), bg="#9E9E9E",
                                     fg="white", relief="groove", width=12)
        self.refresh_btn.pack(pady=2)

        # Battle buttons
        btn_area = tk.Frame(parent)
        btn_area.pack(pady=6)

        self.battle_btn = tk.Button(btn_area, text="\u2694 战斗",
                                    command=self.do_battle,
                                    font=("Arial", 12, "bold"), bg="#2196F3",
                                    fg="white", relief="groove", width=16, pady=4)
        self.battle_btn.pack(pady=3)

        self.auto_btn = tk.Button(btn_area, text="\u26A1 自动战斗",
                                  command=self.toggle_auto,
                                  font=("Arial", 10), bg="#FF9800",
                                  fg="white", relief="groove", width=16, pady=2)
        self.auto_btn.pack(pady=3)
        self.auto_label = tk.Label(btn_area, text="自动: 关", fg="#999",
                                   font=("Arial", 9))
        self.auto_label.pack()

        # 药水
        pot_area = ttk.LabelFrame(parent, text="\U0001F9EA 药水", padding=6)
        pot_area.pack(fill="x", padx=4, pady=3)
        self.potions_var = tk.StringVar(value="x0")
        tk.Button(pot_area, text="购买 (25G)", command=self.do_buy_potion,
                  bg="#4CAF50", fg="white", font=("Arial", 9),
                  relief="groove", padx=8).pack(side="left", padx=4)
        tk.Label(pot_area, textvariable=self.potions_var,
                 font=("Arial", 11, "bold")).pack(side="left", padx=8)
        tk.Button(pot_area, text="使用 (+20HP)", command=self.do_use_potion,
                  bg="#E91E63", fg="white", font=("Arial", 9),
                  relief="groove", padx=8).pack(side="left", padx=4)

        # Auto-potion setting
        ap_area = ttk.LabelFrame(parent, text="\U0001F9EA 自动药水", padding=6)
        ap_area.pack(fill="x", padx=4, pady=3)
        tk.Label(ap_area, text="当 HP < ", font=("Arial", 9)).pack(side="left", padx=2)
        self.auto_potion_var = tk.StringVar(value="OFF")
        ap_combo = ttk.Combobox(ap_area, textvariable=self.auto_potion_var,
                                values=["OFF", "30%", "50%", "80%"],
                                state="readonly", width=5, font=("Arial", 9))
        ap_combo.pack(side="left", padx=4)
        ap_combo.bind("<<ComboboxSelected>>", self._on_auto_potion_change)
        self.auto_potion_label = tk.Label(ap_area, text="",
                                          font=("Arial", 8), fg="#888")
        self.auto_potion_label.pack(side="left", padx=4)

    # ── Right: Shop tabs ──
    def _build_right(self, parent):
        nb = ttk.Notebook(parent)
        nb.pack(fill="both", expand=True)

        wtab = tk.Frame(nb)
        nb.add(wtab, text=" \u2694 武器 ")
        self._build_shop(wtab, WEAPONS, "weapon")

        atab = tk.Frame(nb)
        nb.add(atab, text=" \U0001F6E1 Armor ")
        self._build_shop(atab, ARMORS, "armor")

        # Novelty shop tab
        ntab = tk.Frame(nb)
        nb.add(ntab, text=" \U0001F3FA Novelty ")
        self._build_杂货_shop(ntab)

        # ── Farm Tab ──
        self.farm_tab = tk.Frame(nb)
        nb.add(self.farm_tab, text=" \U0001F31F Farm ")
        self._build_farm_tab(self.farm_tab)

        # ── 工厂 Tab ──
        self.factory_tab = tk.Frame(nb)
        nb.add(self.factory_tab, text=" \U0001F3ED 工厂 ")
        self._build_factory_tab(self.factory_tab)

    def _build_shop(self, parent, items, kind):
        canvas = tk.Canvas(parent, highlightthickness=0)
        vsb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        for item in items:
            if kind == "weapon":
                crit = f" CRIT{item['crit_rate']}%" if item["crit_rate"] > 0 else ""
                text = f"{item['name']}  ATK:{item['attack']}{crit}  ({self._cost_str(item['cost'])})"
                color = "#7B1FA2"
            else:
                hp = f" HP+{item['hp_bonus']}" if item["hp_bonus"] > 0 else ""
                text = f"{item['name']}  DEF:{item['defense']}{hp}  ({self._cost_str(item['cost'])})"
                color = "#512DA8"

            btn = tk.Button(inner, text=text,
                           command=lambda i=item, k=kind: self.buy_equipment(i, k),
                           font=("Consolas", 9), bg=color, fg="white",
                           anchor="w", relief="groove", padx=10, pady=3)
            btn.pack(fill="x", pady=1, padx=4)

    @staticmethod
    def _cost_str(cost):
        if not cost:
            return "Free"
        m = {"Gold": "G", "Wood": "W", "Iron": "I", "Leather": "L", "Stone": "S"}
        return " ".join(f"{m.get(k, k)}{v}" for k, v in cost.items())

    # ── Novelty Shop ──
    def _build_杂货_shop(self, parent):
        canvas = tk.Canvas(parent, highlightthickness=0)
        sb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, padx=6, pady=6)
        canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.bind("<Configure>", _on_configure)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # Sort items by price
        sorted_items = sorted(NOVELTY_ITEMS, key=lambda x: x["price"])

        for item in sorted_items:
            price = item["price"]
            rarity_idx = 0 if price <= 8 else (1 if price <= 20 else (2 if price <= 38 else (3 if price <= 55 else 4)))
            color = NOVELTY_RARITY_COLORS[rarity_idx]
            rarity_name = NOVELTY_RARITY_NAMES[rarity_idx]

            frame = tk.Frame(inner, relief="groove", bd=1)
            frame.pack(fill="x", pady=2, padx=4)

            # Icon + name + price
            top_row = tk.Frame(frame)
            top_row.pack(fill="x", padx=6, pady=4)
            tk.Label(top_row, text=item["name"], font=("Arial", 10, "bold"),
                     fg=color, anchor="w").pack(side="left")
            tk.Label(top_row, text=f"{rarity_name} · {price}G", font=("Arial", 8),
                     fg="#999", anchor="e").pack(side="right")

            # Desc
            tk.Label(frame, text=item["desc"], font=("Arial", 8),
                     fg="#666", anchor="w").pack(fill="x", padx=6, pady=(0, 4))

            # 购买 button
            tk.Button(frame, text="购买", command=lambda it=item: self.buy_杂货(it),
                      bg=color, fg="white", font=("Arial", 8, "bold"),
                      relief="groove", padx=8).pack(side="right", padx=6, pady=4)

    def buy_杂货(self, item):
        ok, msg = self.game.buy_杂货_item(item)
        self.game.add_log(msg)
        self.refresh_ui()

    # ═══════════════════ Farm ═══════════════════
    def _build_farm_tab(self, parent):
        from modules.plants import get_plant_catalog, PLANT_RARITY_COLORS, PLANT_RARITY_NAMES

        top = tk.Frame(parent)
        top.pack(fill="x", padx=6, pady=4)

        tk.Label(top, text="🌱 我的农场", font=("Arial", 11, "bold")).pack(side="left")
        self.farm_info_lbl = tk.Label(top, text="0/10 plants",
                                       font=("Arial", 10), fg="#555")
        self.farm_info_lbl.pack(side="right")

        # Plant list frame (scrollable)
        list_frame = tk.Frame(parent)
        list_frame.pack(fill="both", expand=True, padx=6, pady=2)
        self.farm_plant_frames = []
        self.farm_plant_canvas = tk.Canvas(list_frame, highlightthickness=0)
        farm_sb = ttk.Scrollbar(list_frame, orient="vertical", command=self.farm_plant_canvas.yview)
        farm_inner = tk.Frame(self.farm_plant_canvas)
        farm_inner.bind("<Configure>",
                        lambda e: self.farm_plant_canvas.configure(scrollregion=self.farm_plant_canvas.bbox("all")))
        self.farm_plant_canvas.create_window((0, 0), window=farm_inner, anchor="nw")
        self.farm_plant_canvas.configure(yscrollcommand=farm_sb.set)
        self.farm_plant_canvas.pack(side="left", fill="both", expand=True)
        farm_sb.pack(side="right", fill="y")
        self.farm_plant_inner = farm_inner

        # Seed shop (scrollable)
        shop_lbl_frame = ttk.LabelFrame(parent, text="种子商店", padding=6)
        shop_lbl_frame.pack(fill="x", padx=6, pady=4)
        shop_container = tk.Frame(shop_lbl_frame)
        shop_container.pack(fill="x")
        self.farm_seed_canvas = tk.Canvas(shop_container, highlightthickness=0, height=160)
        shop_sb = ttk.Scrollbar(shop_container, orient="vertical", command=self.farm_seed_canvas.yview)
        self.farm_seed_inner = tk.Frame(self.farm_seed_canvas)
        self.farm_seed_inner.bind("<Configure>",
            lambda e: self.farm_seed_canvas.configure(
                scrollregion=self.farm_seed_canvas.bbox("all")))
        self.farm_seed_canvas.create_window((0, 0), window=self.farm_seed_inner, anchor="nw")
        self.farm_seed_canvas.configure(yscrollcommand=shop_sb.set)
        self.farm_seed_canvas.pack(side="left", fill="x", expand=True)
        shop_sb.pack(side="right", fill="y")

        catalog = get_plant_catalog()
        for pd in catalog:
            rc = PLANT_RARITY_COLORS.get(pd["rarity"], "#888")
            price = pd["seed_price"]
            text = (f"{pd['icon']} {pd['name']}  {pd['desc']}  "
                    f"产{int(pd['harvest_gold'])}G/{int(pd['harvest_interval_s'])}s  "
                    f"{PLANT_RARITY_NAMES.get(pd['rarity'],'')} [{price}G]")
            btn = tk.Button(self.farm_seed_inner, text=text, font=("Consolas", 9), fg=rc,
                            anchor="w", relief="groove", padx=8,
                            command=lambda p=pd: self._plant_seed(p))
            btn.pack(fill="x", pady=1)

    def _plant_seed(self, pd):
        ok, msg = self.game.plant_seed(pd["id"], cost_gold=pd["seed_price"])
        self.game.add_log(msg)
        self.refresh_farm_ui()

    def refresh_farm_ui(self):
        """刷新农场 UI（植物状态面板）"""
        if not hasattr(self, "farm_plant_inner"):
            return
        plants = self.game.plants
        self.farm_info_lbl.config(text=f"{len(plants)}/{getattr(__import__('modules.plants', fromlist=['MAX_PLANTS']), 'MAX_PLANTS')} plants")

        # 快照：只记录植物数量和各植物关键状态
        from modules.plants import get_plant_by_id, calc_grow_stage
        now = time.time()
        snap_parts = []
        for plant in plants:
            pd = get_plant_by_id(plant["plant_id"])
            if not pd:
                continue
            elapsed = now - plant["planted_at"]
            stage = calc_grow_stage(elapsed, pd["grow_time_s"])
            snap_parts.append((plant["id"], stage, plant.get("harvest_count", 0)))
        new_snap = (len(plants), tuple(snap_parts))

        # 阶段变化才重建（生长阶段从0→1→2→3 会触发，但同阶段内不触发）
        if new_snap == self._last_farm_snap:
            return
        self._last_farm_snap = new_snap

        # Clear old frames
        for w in self.farm_plant_inner.pack_slaves():
            w.destroy()

        from modules.plants import get_plant_by_id as _get, PLANT_RARITY_COLORS
        if not plants:
            tk.Label(self.farm_plant_inner, text="(no plants yet — buy seeds above)",
                     font=("Arial", 9), fg="#aaa").pack(pady=8)
            return

        for plant in plants:
            pd = get_plant_by_id(plant["plant_id"])
            if not pd:
                continue
            status = self.game._plant_status(plant)
            rc = PLANT_RARITY_COLORS.get(pd["rarity"], "#888")

            frame = tk.Frame(self.farm_plant_inner, relief="groove", bd=1)
            frame.pack(fill="x", pady=2, padx=2)

            tk.Label(frame, text=f"{pd['icon']} {pd['name']}", font=("Arial", 10, "bold"), fg=rc)\
                .pack(anchor="w", padx=6)
            tk.Label(frame, text=f"  {status['stage_name']}  {status['progress']}  {status['time_left']}",
                     font=("Consolas", 8), fg="#555").pack(anchor="w", padx=6)

            if status["stage"] < 3:
                remaining = status["remaining_s"]
                cost = int(remaining * 0.5)
                tk.Button(frame, text=f"⚡ 加速 ({cost}G)",
                          font=("Arial", 8), bg="#FFF9C4", relief="groove",
                          command=lambda p=plant["id"]: self._speedup(p))\
                    .pack(anchor="e", padx=4, pady=2)

    def _speedup(self, plant_id):
        ok, msg = self.game.speedup_plant(plant_id)
        self.game.add_log(msg)
        self.refresh_farm_ui()

    # ═══════════════════ 工厂 ═══════════════════
    def _build_factory_tab(self, parent):
        from modules.factory import FACTORY_BUILD_COST, DEPARTMENTS, MAX_FACTORY_WORKERS

        top = tk.Frame(parent)
        top.pack(fill="x", padx=6, pady=4)
        tk.Label(top, text="🏭 工厂", font=("Arial", 11, "bold")).pack(side="left")
        self.factory_status_lbl = tk.Label(top, text="未建造",
                                            font=("Arial", 10), fg="#c00")
        self.factory_status_lbl.pack(side="right")

        self.factory_body = tk.Frame(parent)
        self.factory_body.pack(fill="both", expand=True, padx=6, pady=2)

        self._refresh_factory_ui()

    def _refresh_factory_ui(self):
        """重建工厂 tab 内容"""
        try:
            if not hasattr(self, "factory_body"):
                return

            g = self.game
            new_snap = (
                g.factory is not None,
                tuple(sorted(g.factory_departments)) if g.factory_departments else (),
                g.factory_workers
            )
            if new_snap == self._last_factory_snap:
                return
            self._last_factory_snap = new_snap

            for w in self.factory_body.pack_slaves():
                w.destroy()

            from modules.factory import FACTORY_BUILD_COST, FACTORY_WORKER_COST_GOLD, DEPARTMENTS, MAX_FACTORY_WORKERS, get_dept_by_id, calc_factory_bonus

            g = self.game

            if g.factory is None:
                # 建造按钮
                tk.Label(self.factory_body, text="工厂尚未建造!",
                         font=("Arial", 10), fg="#888").pack(pady=8)
                cost_str = " ".join(f"{k}{v}" for k, v in FACTORY_BUILD_COST.items())
                tk.Label(self.factory_body, text=f"费用: {cost_str}",
                         font=("Consolas", 9), fg="#555").pack()
                tk.Button(self.factory_body, text="🏗️ 建造 工厂",
                          font=("Arial", 11, "bold"), bg="#1976D2", fg="white",
                          relief="groove", command=self._build_factory).pack(pady=8)
                return

            # 工厂已建造
            finfo = g.get_factory_info()
            self.factory_status_lbl.config(
                text=f"Profit: {finfo['profit_per_cycle']}G / {finfo['cycle_seconds']}s  ×{finfo['bonus_factor']:.2f}",
                fg="#2E7D32")

            # 部门列表
            depts_frame = ttk.LabelFrame(self.factory_body, text="部门", padding=6)
            depts_frame.pack(fill="x", pady=4)
            for dept in DEPARTMENTS:
                did = dept["id"]
                built = did in g.factory_departments
                cost_parts = [f"G{dept['cost_gold']}"] if dept["cost_gold"] > 0 else []
                for k, v in dept["cost_resources"].items():
                    cost_parts.append(f"{k}{v}")
                cost_str = " | ".join(cost_parts) if cost_parts else "Free"
                bg = "#E8F5E9" if built else "#ECEFF1"
                text = f"{'✅' if built else '🔒'} {dept['name']} — {dept['desc']} [{cost_str}]"
                cmd = (lambda d=dept: self._buy_dept(d["id"])) if 未建造 else None
                btn = tk.Button(depts_frame, text=text, font=("Consolas", 9), bg=bg,
                                 fg="#333", anchor="w", relief="groove", padx=8,
                                 command=cmd)
                btn.pack(fill="x", pady=1)

            # 劳工管理
            workers_frame = ttk.LabelFrame(self.factory_body, text="劳工", padding=6)
            workers_frame.pack(fill="x", pady=4)
            tk.Label(workers_frame, text=f"数量: {finfo['worker_count']}/{MAX_FACTORY_WORKERS}  "
                                         f"(每人+15%, {FACTORY_WORKER_COST_GOLD}G/人)",
                     font=("Arial", 9), fg="#555").pack(anchor="w")
            btns = tk.Frame(workers_frame)
            btns.pack()
            tk.Button(btns, text="+ Hire", font=("Arial", 9, "bold"), bg="#4CAF50", fg="white",
                      command=self._hire_factory_worker).pack(side="left", padx=4)
            tk.Button(btns, text="- Fire", font=("Arial", 9), bg="#F44336", fg="white",
                      command=self._fire_factory_worker).pack(side="left", padx=4)
        except Exception as e:
            import traceback
            traceback.print_exc()
            if hasattr(self, 'game'):
                self.game.add_log(f"工厂 UI ERROR: {e}")

    def _build_factory(self):
        try:
            ok, msg = self.game.build_factory()
            self.game.add_log(msg)
            self._refresh_factory_ui()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.game.add_log(f"ERROR: {e}")

    def _buy_dept(self, dept_id):
        from modules.factory import get_dept_by_id
        dept = get_dept_by_id(dept_id)
        ok, msg = self.game.buy_department(dept_id)
        self.game.add_log(msg)
        self._refresh_factory_ui()

    def _hire_factory_worker(self):
        ok, msg = self.game.hire_factory_worker()
        self.game.add_log(msg)
        self._refresh_factory_ui()

    def _fire_factory_worker(self):
        ok, msg = self.game.fire_factory_worker()
        self.game.add_log(msg)
        self._refresh_factory_ui()

    # ── Bottom: Inventory grid ──
    def _build_inventory(self):
        inv_outer = ttk.LabelFrame(self.root, text="\U0001F392 Inventory", padding=6)
        inv_outer.pack(fill="x", padx=4, pady=2)

        self.inv_count_label = tk.Label(inv_outer, text="0/20",
                                        font=("Arial", 10, "bold"), fg="#666")
        self.inv_count_label.pack(anchor="e")

        grid_frame = tk.Frame(inv_outer)
        grid_frame.pack(fill="x")

        self.inv_slots = []
        COLS = 5
        for i in range(20):
            row, col = divmod(i, COLS)
            cell = tk.Frame(grid_frame, relief="groove", bd=1)
            cell.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")

            lbl = tk.Label(cell, text="Empty", font=("Consolas", 8),
                           fg="#aaa", width=20, height=1, anchor="w", padx=4)
            lbl.pack(side="left", fill="x", expand=True)

            type_lbl = tk.Label(cell, text="", font=("Arial", 8, "bold"),
                                width=2, padx=1)
            type_lbl.pack(side="left")

            btn_e = tk.Button(cell, text="E", font=("Arial", 8, "bold"),
                           bg="#4CAF50", fg="white", relief="raised", width=2, height=1,
                           command=lambda idx=i: self.equip_item(idx))
            btn_e.pack(side="left", padx=1)
            
            btn_s = tk.Button(cell, text="S", font=("Arial", 8, "bold"),
                           bg="#FF9800", fg="white", relief="raised", width=2, height=1,
                           command=lambda idx=i: self.sell_item(idx))
            btn_s.pack(side="left", padx=1)

            self.inv_slots.append({"lbl": lbl, "btn_e": btn_e, "btn_s": btn_s,
                                   "type_lbl": type_lbl})

        for c in range(COLS):
            grid_frame.columnconfigure(c, weight=1)

    # ── Log ──
    def _build_log(self):
        lf = ttk.LabelFrame(self.root, text="📜 战斗日志", padding=4)
        lf.pack(fill="both", expand=True, padx=4, pady=(2, 2))

        sb = ttk.Scrollbar(lf)
        sb.pack(side="right", fill="y")
        self.log_listbox = tk.Listbox(lf, font=("Consolas", 9),
                                      selectbackground="#BBDEFB",
                                      highlightthickness=0,
                                      yscrollcommand=sb.set)
        self.log_listbox.pack(side="left", fill="both", expand=True)
        sb.config(command=self.log_listbox.yview)

    # ──────────────── Actions ────────────────

    def build_building(self, name):
        ok, msg = self.game.build_building(name)
        self.game.add_log(msg)
        self.refresh_buildings()

    def upgrade_building(self, name, idx):
        ok, msg = self.game.upgrade_building(name, idx)
        if not ok:
            self.game.add_log(f"Warning: {msg}")
        self.refresh_buildings()

    def buy_equipment(self, item, kind):
        if kind == "weapon":
            ok, msg = self.game.buy_weapon(item)
        else:
            ok, msg = self.game.buy_armor(item)
        if not ok:
            self.game.add_log(f"Warning: {msg}")
        self.refresh_ui()

    def equip_item(self, idx):
        result = self.game.player.equip_item(idx)
        if result[0]:
            equip, msg = result
            self.game.add_log(f"Equipped: {equip['name']}")
            if equip.get("special"):
                self.game.add_log(f"  \u2728 {equip['special']['name']}+{equip['special']['value']}")
        else:
            self.game.add_log(f"Equip failed: {result[1]}")
        self.refresh_ui()

    def change_map(self, map_name):
        if map_name in self.game.unlocked_maps:
            ok, msg = self.game.change_map(map_name)
            self.game.add_log(msg)
            self.refresh_ui()
        else:
            ok, msg = self.game.unlock_map(map_name)
            if ok:
                self.game.add_log(msg)
                self.game.change_map(map_name)
                self.refresh_ui()
            else:
                self.game.add_log(f"无法解锁: {msg}")

    def do_refresh_enemy(self):
        """刷新当前敌人"""
        if self.game.is_battling:
            self.game.add_log("战斗中无法刷新!")
            return
        from modules.maps import get_random_enemy
        enemy, is_boss = get_random_enemy(self.game.current_map)
        if enemy:
            self.game.current_enemy = enemy
            self.game.current_enemy_is_boss = is_boss
            boss_tag = " [BOSS]" if is_boss else ""
            self.enemy_var.set(f"{enemy['name']}{boss_tag}  HP:{enemy['hp']}  ATK:{enemy['attack']}")
            self.game.add_log(f"🔄 刷新敌人: {enemy['name']}{boss_tag}")

    def do_battle(self):
        if self.game.is_battling:
            return
        # 随机获取敌人，有5%概率遇到BOSS
        from modules.maps import get_random_enemy
        enemy, is_boss = get_random_enemy(self.game.current_map)
        if not enemy:
            self.game.add_log("没有敌人!")
            return
        # 保存当前敌人信息
        self.game.current_enemy = enemy
        self.game.current_enemy_is_boss = is_boss
        t = threading.Thread(target=self._battle_wrapper, args=(enemy, is_boss), daemon=True)
        t.start()

    def _battle_wrapper(self, enemy, is_boss=False):
        self.root.after(0, lambda: self.battle_btn.config(state="disabled"))
        try:
            result, msg = self.game.battle(enemy, is_boss=is_boss)
        except Exception as e:
            self.game.add_log(f"Battle error: {e}")
        finally:
            self.game.is_battling = False
            self.root.after(0, lambda: self.battle_btn.config(state="normal"))

    def toggle_auto(self):
        self.game.auto_battle = not self.game.auto_battle
        if self.game.auto_battle:
            self.auto_label.config(text="自动: 开", fg="#4CAF50")
            self.game.add_log("Auto battle ON!")
            self.game.start_auto_battle()
        else:
            self.auto_label.config(text="自动: 关", fg="#999")
            self.game.add_log("Auto battle OFF.")

    def do_buy_potion(self):
        ok, msg = self.game.buy_potion()
        self.game.add_log(msg)
        self.refresh_ui()

    def do_use_potion(self):
        ok, msg = self.game.use_potion()
        self.game.add_log(msg)
        self.refresh_ui()

    def _on_auto_potion_change(self, event=None):
        val_str = self.auto_potion_var.get()
        mapping = {"OFF": 0, "30%": 30, "50%": 50, "80%": 80}
        val = mapping.get(val_str, 0)
        self.game.set_auto_potion_threshold(val)
        if val > 0:
            self.auto_potion_label.config(text=f"Active ({val}%)", fg="#4CAF50")
            self.game.add_log(f"Auto-potion ON: HP < {val}%")
        else:
            self.auto_potion_label.config(text="Disabled", fg="#999")
            self.game.add_log("Auto-potion OFF")

    def _restore_auto_potion_ui(self):
        """读档后恢复自动药水下拉框状态"""
        t = self.game.auto_potion_threshold
        rev = {0: "OFF", 30: "30%", 50: "50%", 80: "80%"}
        self.auto_potion_var.set(rev.get(t, "OFF"))
        if t > 0:
            self.auto_potion_label.config(text=f"Active ({t}%)", fg="#4CAF50")
        else:
            self.auto_potion_label.config(text="Disabled", fg="#999")

    def hire_worker(self, name, idx):
        ok, msg = self.game.hire_worker(name, idx)
        self.game.add_log(msg)
        self.refresh_ui()

    def fire_worker(self, name, idx):
        ok, msg = self.game.fire_worker(name, idx)
        self.game.add_log(msg)
        self.refresh_ui()

    def build_wonder(self, wonder_name):
        ok, msg = self.game.build_wonder(wonder_name)
        self.game.add_log(msg)
        if ok and wonder_name in self.wonder_buttons:
            self.wonder_buttons[wonder_name].config(text=f"\u2705 {wonder_name}", state="disabled")
        self.refresh_ui()

    def use_杂货_item(self, idx):
        ok, msg = self.game.use_杂货_item(idx)
        self.game.add_log(msg)
        self.refresh_ui()

    def sell_item(self, idx):
        ok, msg = self.game.sell_inventory_item(idx)
        self.game.add_log(msg)
        self.refresh_ui()

    def buy_material(self, material):
        try:
            amount = int(self.res_buy_entries[material].get())
        except ValueError:
            amount = 10
            self.res_buy_entries[material].delete(0, tk.END)
            self.res_buy_entries[material].insert(0, "10")
        ok, msg = self.game.buy_material(material, amount)
        self.game.add_log(msg)
        self.refresh_ui()

    def sell_material(self, material):
        try:
            amount = int(self.res_buy_entries[material].get())
        except ValueError:
            amount = 10
            self.res_buy_entries[material].delete(0, tk.END)
            self.res_buy_entries[material].insert(0, "10")
        ok, msg = self.game.sell_material(material, amount)
        self.game.add_log(msg)
        self.refresh_ui()

    # ──────────────── Refresh ────────────────

    def refresh_buildings(self):
        for bname in get_all_building_names():
            config = BUILDING_CONFIGS[bname]
            count = self.game.buildings.get(bname, 0)
            levels = self.game.building_levels.get(bname, [])
            self.building_widgets[bname]["count"].config(text=f"x{count}")

            if levels:
                avg_lvl = sum(levels) / len(levels)
                avg_output = config.get_output(int(avg_lvl))
                avg_interval = config.get_interval(int(avg_lvl))
                total_workers = sum(
                    self.game.building_workers.get(bname, [0])[i]
                    for i in range(min(len(levels), len(self.game.building_workers.get(bname, []))))
                )
                total_max = sum(config.get_max_workers(l) for l in levels)
                self.building_widgets[bname]["info"].config(
                    text=f"Avg: {avg_output}/{avg_interval}s | \u26CF{total_workers}/{total_max}")
            else:
                self.building_widgets[bname]["info"].config(text="未建造")

            # 快照对比：只有结构变化时才重建按钮
            workers_snap = tuple(
                self.game.building_workers.get(bname, [0])[i]
                for i in range(len(levels))
            )
            new_snap = (count, tuple(levels), workers_snap)
            if new_snap == self._last_building_snap.get(bname):
                continue
            self._last_building_snap[bname] = new_snap

            uf = self.building_widgets[bname]["upgrade_frame"]
            for w in uf.winfo_children():
                w.destroy()

            if not levels:
                continue

            for idx, lvl in enumerate(levels):
                row = tk.Frame(uf)
                row.pack(fill="x", pady=1)
                interval = config.get_interval(lvl)
                workers = (self.game.building_workers.get(bname, [0])[idx]
                           if idx < len(self.game.building_workers.get(bname, [])) else 0)
                output = config.get_output(lvl, workers)
                max_w = config.get_max_workers(lvl)
                next_cost = config.get_upgrade_cost(lvl + 1)
                cost_s = f"G{next_cost.get('Gold',0)} W{next_cost.get('Wood',0)}"

                tk.Label(row, text=f"Lv{lvl} {output}/{interval}s \u26CF{workers}/{max_w}",
                         font=("Arial", 8), anchor="w").pack(side="left")
                tk.Button(row, text="Up", font=("Arial", 7), bg="#E64A19", fg="white",
                         relief="groove",
                         command=lambda n=bname, i=idx: self.upgrade_building(n, i)).pack(side="right", padx=1)
                tk.Button(row, text="+", font=("Arial", 7), bg="#1976D2", fg="white",
                         relief="groove", width=2,
                         command=lambda n=bname, i=idx: self.hire_worker(n, i)).pack(side="right", padx=1)
                tk.Button(row, text="-", font=("Arial", 7), bg="#757575", fg="white",
                         relief="groove", width=2,
                         command=lambda n=bname, i=idx: self.fire_worker(n, i)).pack(side="right", padx=1)

    def refresh_ui(self):
        try:
            # 资源
            for res, val in self.game.resources.items():
                if res in self.res_labels:
                    self.res_labels[res].config(text=str(val))
            self.gold_label.config(text=f"🪙 {self.game.player.gold}")
            self.kills_label.config(text=f"击杀: {self.game.player.kill_count}")

            # Hero
            p = self.game.player
            max_hp = p.get_max_hp_with_bonus()
            self.hp_var.set(f"生命: {p.hp}/{max_hp}")
            self.attack_var.set(f"攻击: {p.get_total_attack()}")
            self.defense_var.set(f"防御: {p.get_total_defense()}")
            self.crit_var.set(f"CRIT: {p.get_crit_rate()}%")
            self.level_var.set(f"Lv.{p.level}")
            self.exp_var.set(f"经验: {p.exp}/{p.level * 100}")
            w_name = p.weapon["name"] if p.weapon and isinstance(p.weapon, dict) else "None"
            a_name = p.armor["name"] if p.armor and isinstance(p.armor, dict) else "None"
            self.weapon_var.set(f"武器: {w_name}")
            self.armor_var.set(f"护甲: {a_name}")
            self.potions_var.set(f"x{p.potions}")

            # 地图
            self.map_var.set(self.game.current_map)
            for mn, btn in self.map_buttons.items():
                if mn in self.game.unlocked_maps:
                    btn.config(bg="#4CAF50", fg="white")
                else:
                    cost = get_all_maps()[mn].get("unlock_cost", 0)
                    btn.config(bg="#BDBDBD", fg="#333", text=f"{mn}({cost}G)")

            # 敌人
            enemy = self.game.current_enemy
            is_boss = self.game.current_enemy_is_boss
            if enemy:
                boss_tag = " [BOSS]" if is_boss else ""
                self.enemy_var.set(f"{enemy['name']}{boss_tag}  HP:{enemy['hp']}  ATK:{enemy['attack']}")
            else:
                self.enemy_var.set("No enemy")

            # Inventory
            inv = p.get_inventory()
            self.inv_count_label.config(text=f"{inv.count()}/20")
            for i in range(20):
                slot = self.inv_slots[i]
                item = inv.get(i)
                if item:
                    item_type = item.get("type", "equipment")
                    if item_type == "杂货":
                        # 杂货物品
                        rc = NOVELTY_RARITY_COLORS.get(item.get("rarity_idx", 0), "#888")
                        txt = item["name"]
                        slot["lbl"].config(text=txt, fg=rc)
                        slot["type_lbl"].config(text="🎁", fg=rc)
                        # S按钮：所有杂货均可出售
                        slot["btn_s"].config(state="normal", bg="#FF9800", activebackground="#FF9800")
                        if item.get("kind") == "plant_seed":
                            # 植物种子：E按钮改为种植
                            slot["btn_e"].config(state="normal", bg="#4CAF50", fg="white",
                                              activebackground="#388E3C",
                                              command=lambda idx=i: self.use_杂货_item(idx))
                        else:
                            # 其他杂货：E禁用
                            slot["btn_e"].config(state="disabled", bg="#BDBDBD", activebackground="#BDBDBD",
                                              text="E")
                    else:
                        # 装备
                        rc = item.get("rarity_color", "#333")
                        lvl_req = item.get("level_req", 0)
                        sell_price = item.get("sell_price", 10)
                        icon = "✅" if p.level >= lvl_req else "🔒"
                        if item["type"] == "weapon":
                            txt = f"{icon} {item['name']} ATK:{item['attack']}"
                            slot["type_lbl"].config(text="⚔", fg="#7B1FA2")
                        else:
                            txt = f"{icon} {item['name']} DEF:{item['defense']}"
                            slot["type_lbl"].config(text="🛡", fg="#512DA8")
                        txt += f" 💰{sell_price}"
                        slot["lbl"].config(text=txt, fg=rc)
                        slot["btn_e"].config(state="normal" if p.level >= lvl_req else "disabled",
                                          bg="#4CAF50" if p.level >= lvl_req else "#BDBDBD",
                                          activebackground="#4CAF50" if p.level >= lvl_req else "#BDBDBD",
                                          text="E",
                                          command=lambda idx=i: self.equip_item(idx))
                        slot["btn_s"].config(state="normal", bg="#FF9800", activebackground="#FF9800")
                else:
                    slot["lbl"].config(text="Empty", fg="#ccc")
                    slot["type_lbl"].config(text="")
                    slot["btn_e"].config(state="disabled", bg="#BDBDBD", activebackground="#BDBDBD")
                    slot["btn_s"].config(state="disabled", bg="#BDBDBD", activebackground="#BDBDBD")

            # Log - 保存当前位置，刷新后恢复
            was_at_bottom = False
            try:
                pos = self.log_listbox.yview()
                # 判断是否在底部附近
                was_at_bottom = (pos[1] - pos[0]) < 1.1 or pos[0] > 0.9
                saved_pos = pos[0]
            except:
                was_at_bottom = True
                saved_pos = 0
            
            self.log_listbox.delete(0, tk.END)
            for log in self.game.logs[-50:]:
                self.log_listbox.insert(tk.END, log)
            
            if was_at_bottom:
                self.log_listbox.see(tk.END)
            else:
                self.log_listbox.yview_moveto(saved_pos)
            self.refresh_buildings()
            self.refresh_farm_ui()
            self._refresh_factory_ui()
        except Exception as e:
            import traceback
            print("ERROR in refresh_ui:")
            traceback.print_exc()
        finally:
            self.root.after(300, self.refresh_ui)  # 确保循环继续

    def update_loop(self):
        pass

    def save_game(self):
        data = {
            "resources": self.game.resources,
            "buildings": self.game.buildings,
            "building_levels": self.game.building_levels,
            "building_workers": self.game.building_workers,
            "player": self.game.player.to_dict(),
            "current_map": self.game.current_map,
            "unlocked_maps": list(self.game.unlocked_maps),
            "current_enemy_idx": self.game.current_enemy_idx,
            "wonders": list(self.game.wonders.keys()),
            "plants": self.game.plants,
            "factory": self.game.factory,
            "factory_departments": self.game.factory_departments,
            "factory_workers": self.game.factory_workers,
            "factory_last_profit_time": getattr(self.game, "factory_last_profit_time", 0),
            "auto_potion_threshold": self.game.auto_potion_threshold,
        }
        with open("D:\\pyproject\\hero_workshop\\save.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.game.add_log("Game saved!")

    def load_game(self):
        save_path = "D:\\pyproject\\hero_workshop\\save.json"
        if not os.path.exists(save_path):
            self.game.add_log("No save file!")
            return
        with open(save_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.game.resources = data.get("resources", {"Wood": 0, "Iron": 0, "Leather": 0, "Stone": 0})
        self.game.buildings = data.get("buildings", {})
        self.game.building_levels = data.get("building_levels", {})
        self.game.building_workers = data.get("building_workers", {})
        self.game.player.from_dict(data.get("player", {}))
        self.game.current_map = data.get("current_map", "\u50B2\u6765\u56FD")
        self.game.unlocked_maps = set(data.get("unlocked_maps", ["\u50B2\u6765\u56FD"]))
        self.game.current_enemy_idx = data.get("current_enemy_idx", 0)
        self.game.wonders = {name: True for name in data.get("wonders", [])}
        self.game.plants = data.get("plants", [])
        self.game.factory = data.get("factory")
        self.game.factory_departments = data.get("factory_departments", ["basic"] if data.get("factory") else [])
        self.game.factory_workers = data.get("factory_workers", 0)
        self.game.factory_last_profit_time = data.get("factory_last_profit_time", 0)
        self.game.auto_potion_threshold = data.get("auto_potion_threshold", 0)
        for wn in self.game.wonders:
            if wn in self.wonder_buttons:
                self.wonder_buttons[wn].config(text=f"\u2705 {wn}", state="disabled")
        for name, levels in self.game.building_levels.items():
            for idx in range(len(levels)):
                self.game.start_building_production(name, idx)
        self.game.add_log("Game loaded!")
        self._restore_auto_potion_ui()

    def show_help(self):
        msg = """勇者工坊 v3.0

地图:
- AoLai(Lv1): Butterfly,Parrot,Lobster,Crab | BOSS:9HeadDemon
- DaTang(Lv11/500G): SilverArm,Techin,GoldArm,Captain | BOSS:SnakeSpirit
- YangGuan(Lv15/1000G): TurkArcher,PersianBlade | BOSS:TurkBowKing,PersianAssassin
- DongHai(Lv20/2000G): SeaGuard,TurtleGen,SnailDemon | BOSS:ShrimpFiend,Brahma,SeaSage,BloodSnail

建筑: 
药水: 25G each, heal 20HP.

Click map button to switch/unlock maps!
Click Battle or 自动战斗 to fight!"""
        messagebox.showinfo("帮助", msg)

    def run(self):
        self.root.mainloop()


# ── Novelty Shop Items ──
if __name__ == "__main__":
    app = App()
    app.run()
