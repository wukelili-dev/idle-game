"""
勇者工坊 v5.1 - Flet UI (Flet 0.84 Correct API)
Run: python main_flet.py
"""

import flet as ft
import asyncio
import random
import threading
import time
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.game_core import GameCore
from modules.equipment import WEAPONS, ARMORS
from modules.buildings import get_all_building_names, get_wonder_names, BUILDING_CONFIGS
from modules.maps import get_all_maps, get_random_enemy
from modules.inventory import NOVELTY_ITEMS, NOVELTY_RARITY_COLORS, NOVELTY_RARITY_NAMES
from modules.plants import get_plant_catalog, PLANT_RARITY_COLORS, PLANT_RARITY_NAMES
from modules.tavern import generate_tavern_roster
from modules.factory import DEPARTMENTS as FACTORY_DEPTS, FACTORY_BUILD_COST, calc_factory_bonus as calc_fb, FACTORY_BASE_PROFIT, FACTORY_BASE_INTERVAL_S

SAVE_PATH = "D:\\pyproject\\hero_workshop\\save.json"
I = ft.icons.Icons  # Flet 0.84: icons are at ft.icons.Icons.XXX
RARITY_COLORS = ["#cccccc", "#4FC3F7", "#BA68C8", "#FFA726", "#EF5350"]


def Cs(name):
    return getattr(ft.Colors, name, ft.Colors.GREY_500)


def cost_str(cost):
    if not cost:
        return "Free"
    m = {"\u91d1\u5e01": "\u91d1", "\u6728\u6750": "\u6728", "\u94c1\u77ff": "\u94c1",
         "\u76ae\u9769": "\u76ae", "\u77f3\u5934": "\u77f3"}
    return " ".join(f"{m.get(k, k)}{v}" for k, v in cost.items())


class HeroWorkshopApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "\u52c7\u8005\u5de5\u574a v5.1"
        self.page.window_width = 1280
        self.page.window_height = 900
        self.page.window_min_width = 960
        self.page.window_min_height = 640
        self.page.window_maximized = False
        self.page.window_resizable = True
        self.page.padding = 0
        self.page.spacing = 0
        self.page.font_family = "Microsoft YaHei"
        self.page.theme = ft.Theme(font_family="Microsoft YaHei")
        self.page.dark_theme = ft.Theme(font_family="Microsoft YaHei")
        self.game = GameCore()
        self._refs = {}
        self.auto_battle = False
        self.auto_potion_threshold = 0
        self.current_member = 0
        self.building_cards = ft.Column(scroll="auto")
        self.wonder_cards = ft.Column(scroll="auto")
        self.member_buttons = {}
        self.building_btns = {}
        self.wonder_btns = {}
        self._build_top_bar()
        self._build_body()
        self._build_bottom_bar()
        self._refresh_all_ui()
        self.page.run_task(self._update_loop)

    def _ref(self, key, ctrl):
        self._refs[key] = ctrl
        return ctrl

    # ─── Top Bar ────────────────────────────────────────────────
    def _build_top_bar(self):
        ab = ft.AppBar(title=ft.Text("\u2694 \u52c7\u8005\u5de5\u574a v5.1", size=18, weight=ft.FontWeight.BOLD))
        self._ref("kills_label", ft.Text("\u51fb\u6740: 0", size=13, color=Cs("GREY_500")))
        self._ref("gold_label", ft.Text("\U0001fa99 100", size=15, weight=ft.FontWeight.BOLD, color="#B8860B"))
        ab.actions = [
            self._refs["kills_label"],
            ft.Container(width=20),
            self._refs["gold_label"],
            ft.Container(width=10),
        ]
        self.page.appbar = ab

    # ─── Body ──────────────────────────────────────────────────
    def _build_body(self):
        self.body = ft.Row(
            controls=[self._build_left(), self._build_center(), self._build_right()],
            spacing=4, expand=True,
        )
        self.page.add(self.body)

    # ─── Left Panel ─────────────────────────────────────────────
    def _build_left(self):
        col = ft.Column(spacing=0, scroll="auto", expand=True)

        # Resources
        col.controls.append(ft.Container(
            content=ft.Column([
                ft.Text("\U0001f4e6 \u8d44\u6e90", size=14, weight=ft.FontWeight.BOLD, color=Cs("GREY_700")),
                ft.Divider(height=1),
            ], spacing=4),
            padding=ft.Padding.all(8),
            border=ft.Border.all(1, Cs("OUTLINE")),
            border_radius=6,
            margin=ft.Margin.only(right=4, bottom=4),
        ))

        MATERIALS = [("\u6728\u6750", "\U0001f332"), ("\u94c1\u77ff", "\u26cf\ufe0f"),
                     ("\u76ae\u9769", "\U0001f9e4"), ("\u77f3\u5934", "\u26f0\ufe0f")]
        for name, icon in MATERIALS:
            col.controls.append(ft.Row([
                ft.Text(f"{icon} {name}:", size=13, expand=2),
                self._ref(f"res_{name}", ft.Text("0", size=13, weight=ft.FontWeight.BOLD, expand=1)),
                ft.IconButton(icon=I.REMOVE, icon_size=15, on_click=lambda e, n=name: self._sell_mat(n)),
                ft.Text("\xd7", size=12),
                ft.IconButton(icon=I.ADD, icon_size=15, on_click=lambda e, n=name: self._buy_mat(n)),
            ], spacing=2, tight=True))

        # Buildings
        col.controls.append(ft.Container(
            content=ft.Text("\U0001f3d7 \u5efa\u7b51", size=14, weight=ft.FontWeight.BOLD, color=Cs("GREY_700")),
            padding=ft.Padding.only(left=4, top=10, bottom=4),
        ))
        self.building_cards = ft.Column(spacing=4, scroll="auto")
        col.controls.append(self.building_cards)
        for bname in get_all_building_names():
            self.building_cards.controls.append(self._build_building_card(bname))

        # Wonders
        col.controls.append(ft.Container(
            content=ft.Text("\u2728 \u5947\u89c2", size=14, weight=ft.FontWeight.BOLD, color=Cs("GREY_700")),
            padding=ft.Padding.only(left=4, top=8, bottom=4),
        ))
        self.wonder_cards = ft.Column(spacing=3, scroll="auto")
        col.controls.append(self.wonder_cards)
        for wname in get_wonder_names():
            self.wonder_cards.controls.append(self._build_wonder_card(wname))

        return ft.Container(content=col, width=230, padding=4, bgcolor=Cs("SURFACE_CONTAINER_LOWEST"))

    def _build_building_card(self, name):
        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(name, size=13, weight=ft.FontWeight.BOLD, expand=True),
                        self._ref(f"bld_count_{name}", ft.Text("x0", size=12, color=Cs("GREY_500"))),
                    ]),
                    self._ref(f"bld_info_{name}", ft.Text("\u672a\u5efa\u9020", size=11, color=Cs("GREY_400"))),
                    ft.Row([
                        ft.Button("\u5efa\u9020", scale=0.8, on_click=lambda e, n=name: self._build_building(n)),
                        self._ref(f"bld_upg_btn_{name}",
                                  ft.OutlinedButton("\u5347\u7ea7", scale=0.8,
                                                    on_click=lambda e, n=name: self._upgrade_building(n))),
                    ], spacing=4),
                ], spacing=3),
                padding=6, border=ft.Border.all(1, Cs("OUTLINE_VARIANT")), border_radius=6,
            ),
            ft.Container(
                content=ft.Row([
                    ft.Text("\u5de5\u4eba:", size=11, expand=1),
                    self._ref(f"worker_count_{name}", ft.Text("0/0", size=11, color=Cs("GREY_500"))),
                    ft.IconButton(icon=I.ADD, icon_size=14, on_click=lambda e, n=name: self._hire_worker(n)),
                    ft.Text("\u2715", size=11),
                    ft.IconButton(icon=I.REMOVE, icon_size=14, on_click=lambda e, n=name: self._fire_worker(n)),
                ], spacing=2, tight=True),
                padding=ft.Padding.only(left=6, right=6, bottom=4),
                bgcolor="#f5f5f5",
                border_radius=4,
            ),
        ], spacing=2)

    # ─── Center Panel ───────────────────────────────────────────
    def _build_wonder_card(self, name):
        wonder_btn = ft.Button("\u5efa\u9020\u5947\u89c2", scale=0.9, on_click=lambda e, n=name: self._build_wonder(n))
        self.wonder_btns[name] = wonder_btn
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(name, size=13, weight=ft.FontWeight.BOLD, expand=True),
                    self._ref(f"wonder_count_{name}", ft.Text("x0", size=12, color=Cs("GREY_500"))),
                ]),
                self._ref(f"wonder_info_{name}", ft.Text("\u672a\u5efa\u9020", size=11, color=Cs("GREY_400"))),
                ft.Container(
                    content=wonder_btn,
                    alignment=ft.alignment.Alignment(0.5, 0.5),
                ),
            ], spacing=3),
            padding=6, border=ft.Border.all(1, Cs("OUTLINE_VARIANT")), border_radius=6,
        )

    def _build_center(self):
        col = ft.Column(spacing=4, scroll="auto", expand=True)

        # Team row
        team_row = ft.Row(spacing=4)
        self.team_btns = []
        for i in range(3):
            btn = ft.Button(
                "\u2026" * 3, width=110,
                on_click=lambda e, idx=i: self._switch_member(idx)
            )
            self.team_btns.append(btn)
            team_row.controls.append(btn)
        team_row.controls.append(
            ft.Button("\U0001f37a \u9152\u9986", on_click=self._open_tavern_tab, scale=0.9)
        )
        col.controls.append(ft.Container(
            content=ft.Column([
                ft.Text("\U0001f465 \u961f\u4f0d", size=14, weight=ft.FontWeight.BOLD),
                team_row,
            ], spacing=4),
            padding=6, border=ft.Border.all(1, Cs("OUTLINE_VARIANT")), border_radius=6,
        ))

        # Hero stats
        self.hero_stats = ft.Column(spacing=1)
        col.controls.append(ft.Container(
            content=ft.Column([
                self._ref("hero_name_lbl", ft.Text("\U0001f9d9 \u52c7\u8005 Lv.1", size=14, weight=ft.FontWeight.BOLD)),
                self.hero_stats,
            ], spacing=2),
            padding=6, border=ft.Border.all(1, Cs("OUTLINE_VARIANT")), border_radius=6,
        ))
        self._init_hero_stats()

        # Map + Enemy
        map_btns_row = ft.Row(wrap=True, spacing=4)
        for mname in get_all_maps().keys():
            btn = ft.Button(mname, scale=0.85, on_click=lambda e, m=mname: self._change_map(m),
                                     style=ft.ButtonStyle(bgcolor=Cs("BLUE_600"), color=ft.Colors.WHITE))
            map_btns_row.controls.append(btn)
            self._ref(f"map_btn_{mname}", btn)

        col.controls.append(ft.Container(
            content=ft.Column([
                ft.Text("\U0001f5fa \u5730\u56fe", size=14, weight=ft.FontWeight.BOLD),
                self._ref("map_lbl", ft.Text("\u50b2\u6765\u56fd", size=13, color=Cs("BLUE_700"))),
                map_btns_row,
                ft.Divider(),
                self._ref("enemy_display",
                          ft.Text("\U0001f480 ??? HP:?? ATK:??", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_800)),
                ft.Row([
                    ft.Button("\U0001f504 \u5237\u65b0\u654c\u4eba", on_click=self._refresh_enemy),
                    self._ref("refresh_cost_lbl", ft.Text("", size=12)),
                ], spacing=4),
            ], spacing=4),
            padding=6, border=ft.Border.all(1, Cs("OUTLINE_VARIANT")), border_radius=6,
        ))

        # Battle buttons
        col.controls.append(ft.Container(
            content=ft.Column([
                self._ref("battle_btn",
                          ft.Button("\u2694 \u6218\u6597", width=200, height=45,
                                            on_click=self._do_battle,
                                            style=ft.ButtonStyle(bgcolor=Cs("BLUE_600")))),
                self._ref("auto_btn",
                          ft.Button("\u26a1 \u81ea\u52a8\u6218\u6597", width=200,
                                            on_click=self._toggle_auto,
                                            style=ft.ButtonStyle(bgcolor=Cs("ORANGE_600")))),
                self._ref("auto_status_lbl",
                          ft.Text("\u81ea\u52a8: \u5173", size=12, color=Cs("GREY_500"))),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            padding=4,
        ))

        # Auto potion threshold
        thresh_opts = ["OFF", "30%", "50%", "80%"]
        self._ref("auto_potion_dd", ft.Dropdown(
            options=[ft.dropdown.Option(o) for o in thresh_opts],
            value="OFF", width=80, height=32,
        ))
        self._ref("auto_potion_lbl", ft.Text("已关闭", size=12, color=Cs("GREY_500")))
        # Potions
        col.controls.append(ft.Container(
            content=ft.Column([
                ft.Text("\U0001f9ea \u836f\u6c34", size=14, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.Button("\u8d2d\u4e70 (25G)", scale=0.85, on_click=self._buy_potion),
                    self._ref("potions_lbl", ft.Text("x0", size=13)),
                    ft.Button("\u4f7f\u7528 +20HP", scale=0.85, on_click=self._use_potion),
                ], spacing=4),
                ft.Row([
                    ft.Text("\u81ea\u52a8 HP<", size=12),
                    self._refs["auto_potion_dd"],
                    self._refs["auto_potion_lbl"],
                ], spacing=4, alignment=ft.MainAxisAlignment.START),
            ], spacing=4),
            padding=6, border=ft.Border.all(1, Cs("OUTLINE_VARIANT")), border_radius=6,
        ))

        # Combat log
        self.log_view = ft.ListView(expand=True, spacing=2, auto_scroll=True)
        col.controls.append(ft.Container(
            content=ft.Column([
                ft.Text("\U0001f4cb \u6218\u6597\u65e5\u5fd7", size=14, weight=ft.FontWeight.BOLD),
                ft.Container(content=self.log_view,
                             border=ft.Border.all(1, Cs("OUTLINE_VARIANT")),
                             border_radius=4, padding=4, expand=True, height=160),
            ], spacing=4),
            padding=4,
        ))
        self._restore_auto_potion_ui()
        
        # Add dropdown change handler after UI is built
        def on_auto_potion_change(e):
            self._on_auto_potion_change()
        self._refs["auto_potion_dd"].on_change = on_auto_potion_change

        return ft.Container(content=col, expand=True, padding=4, bgcolor=Cs("SURFACE_CONTAINER_LOWEST"))

    def _init_hero_stats(self):
        for key, default in [
            ("hp_lbl", "\u751f\u547d: 100/100"),
            ("atk_lbl", "\u653b\u51fb: 10"),
            ("def_lbl", "\u9632\u5fa1: 5"),
            ("crit_lbl", "CRIT: 0%"),
            ("exp_lbl", "\u7ecf\u9a8c: 0/100"),
            ("wpn_lbl", "\u6b66\u5668: None"),
            ("arm_lbl", "\u62a4\u7532: None"),
        ]:
            self._ref(key, ft.Text(default, size=12))

    # ─── Right Panel ─────────────────────────────────────────────
    def _build_right(self):
        self._tab_bar = ft.TabBar(
            tabs=[
                ft.Tab(label="\u2694 \u6b66\u5668"),
                ft.Tab(label="\U0001f6e1 \u62a4\u7532"),
                ft.Tab(label="\U0001f381 \u6742\u8d27"),
                ft.Tab(label="\U0001f392 \u80cc\u5305"),
                ft.Tab(label="\u2b50 \u6750\u6599"),
                ft.Tab(label="\U0001f37a \u9152\u9986"),
                ft.Tab(label="\U0001f331 \u519c\u573a"),
                ft.Tab(label="\U0001f3ed \u5de5\u5382"),
            ],
        )
        self._tab_contents = [
            self._build_weapon_tab(),
            self._build_armor_tab(),
            self._build_novelty_tab(),
            self._build_bag_tab(),
            self._build_materials_tab(),
            self._build_tavern_tab(),
            self._build_farm_tab(),
            self._build_factory_tab(),
        ]
        self._tab_view = ft.TabBarView(controls=self._tab_contents, expand=True)
        self.right_tabs = ft.Tabs(
            content=ft.Column([self._tab_bar, self._tab_view], spacing=0, expand=True),
            length=8,
            expand=True,
        )
        return ft.Container(content=self.right_tabs, expand=True, padding=4)

    def _build_weapon_tab(self):
        items = []
        for w in WEAPONS:
            crit = f" CRIT{w['crit_rate']}%" if w["crit_rate"] > 0 else ""
            ridx = min(w.get("rarity_idx", 0), 4)
            color = RARITY_COLORS[ridx]
            items.append(ft.ListTile(
                title=ft.Text(f"{w['name']}  ATK:{w['attack']}{crit}", size=12, color=color),
                subtitle=ft.Text(cost_str(w["cost"]), size=11, color=Cs("GREY_500")),
                trailing=ft.IconButton(icon=I.SHOPPING_CART,
                                       on_click=lambda e, wpn=w: self._buy_weapon(wpn)),
            ))
        return ft.ListView(items, spacing=2, expand=True)

    def _build_armor_tab(self):
        items = []
        for a in ARMORS:
            hp = f" HP+{a['hp_bonus']}" if a["hp_bonus"] > 0 else ""
            ridx = min(a.get("rarity_idx", 0), 4)
            color = RARITY_COLORS[ridx]
            items.append(ft.ListTile(
                title=ft.Text(f"{a['name']}  DEF:{a['defense']}{hp}", size=12, color=color),
                subtitle=ft.Text(cost_str(a["cost"]), size=11, color=Cs("GREY_500")),
                trailing=ft.IconButton(icon=I.SHOPPING_CART,
                                       on_click=lambda e, arm=a: self._buy_armor(arm)),
            ))
        return ft.ListView(items, spacing=2, expand=True)

    def _build_novelty_tab(self):
        items = []
        for item in sorted(NOVELTY_ITEMS, key=lambda x: x["price"]):
            ridx = min(item.get("rarity_idx", 0), 4)
            color = NOVELTY_RARITY_COLORS[ridx]
            items.append(ft.ListTile(
                title=ft.Text(item["name"], size=12, color=color, weight=ft.FontWeight.BOLD),
                subtitle=ft.Text(f"{NOVELTY_RARITY_NAMES[ridx]} \xb7 {item['desc']}", size=11),
                trailing=ft.Text(f"{item['price']}G", size=12, weight=ft.FontWeight.BOLD),
                on_click=lambda e, it=item: self._buy_novelty(it),
            ))
        return ft.ListView(items, spacing=2, expand=True)


    def _build_bag_tab(self):
        # 标题行
        self._ref("bag_count_lbl", ft.Text("\u80cc\u5305: 0/20", size=13, weight=ft.FontWeight.BOLD))
        title_row = ft.Row([
            self._refs["bag_count_lbl"],
            ft.Container(expand=True),
            ft.Text("\u70b9\u51fb\u88c5\u5907\u540d\u7b31\u6253\u62d4\u6216\u5356\u51fa", size=11, color=Cs("GREY_500")),
        ], spacing=8)

        # 当前装备区
        equip_ctr = ft.Column([
            ft.Text("\u2014\u2014 \u5f53\u524d\u88c5\u5907 \u2014\u2014", size=13, weight=ft.FontWeight.BOLD),
            ft.Row([
                self._ref("eq_weapon_lbl", ft.Text("\u6b66\u5668: \u672a\u88c5\u5907", size=12)),
                ft.Container(expand=True),
                self._ref("eq_armor_lbl", ft.Text("\u62a4\u7532: \u672a\u88c5\u5907", size=12)),
            ], spacing=12),
        ], spacing=4)

        # 背包格子 grid (4x5)
        self._bag_cells = []
        bag_grid = ft.GridView(
            child_aspect_ratio=3.5,
            spacing=4,
            padding=4,
        )
        for i in range(20):
            ridx = i  # will be updated by _refresh_bag
            cell = ft.Container(
                content=ft.Column([
                    self._ref(f"bag_lbl_{i}", ft.Text("\u7a7a", size=11, color=Cs("GREY_500"), text_align="center")),
                    ft.Row([
                        self._ref(f"bag_e_{i}", ft.Text("\u88c5", size=10)),
                        self._ref(f"bag_s_{i}", ft.Text("\u5356", size=10)),
                    ], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=2),
                border=ft.Border.all(1, Cs("OUTLINE_VARIANT")),
                border_radius=4,
                padding=4,
                ink=True,
            )
            # Store idx in bgcolor for use in callbacks
            cell.data = i
            cell.on_click = lambda e, idx=i: self._bag_cell_click(idx)
            self._bag_cells.append(cell)
            bag_grid.controls.append(cell)

        return ft.ListView([
            title_row,
            equip_ctr,
            ft.Divider(),
            bag_grid,
        ], spacing=6, expand=True)

    def _refresh_bag(self):
        inv = self.game.get_current_member().get_inventory()
        count = inv.count()
        self._refs["bag_count_lbl"].value = f"\u80cc\u5305: {count}/20"

        # 当前装备
        m = self.game.get_current_member()
        wpn = m.weapon
        arm = m.armor
        self._refs["eq_weapon_lbl"].value = (f"\u6b66\u5668: {wpn['name']}" if wpn else "\u6b66\u5668: \u672a\u88c5\u5907")
        self._refs["eq_armor_lbl"].value = (f"\u62a4\u7532: {arm['name']}" if arm else "\u62a4\u7532: \u672a\u88c5\u5907")

        # 刷新格子
        for i in range(20):
            item = inv.get(i)
            lbl = self._refs.get(f"bag_lbl_{i}")
            if not lbl:
                continue
            if item:
                t = item.get("type", "item")
                if t == "weapon":
                    lbl.value = item["name"][:6]
                    lbl.color = Cs("BLUE_400")
                elif t == "armor":
                    lbl.value = item["name"][:6]
                    lbl.color = Cs("GREEN_400")
                elif t == "novelty":
                    lbl.value = item["name"][:5]
                    lbl.color = NOVELTY_RARITY_COLORS[min(item.get("rarity_idx", 0), 4)]
                else:
                    lbl.value = item.get("name", "?")[:6]
                    lbl.color = Cs("GREY_300")
            else:
                lbl.value = "\u7a7a"
                lbl.color = Cs("GREY_500")

    def _bag_cell_click(self, idx):
        inv = self.game.get_current_member().get_inventory()
        item = inv.get(idx)
        if not item:
            self._show_toast("\u8be5\u6865\u4f4d\u4e3a\u7a7a")
            return
        item_type = item.get("type", "item")
        if item_type == "weapon":
            result = self.game.player.equip_item(idx)
            if result[0]:
                self.game.add_log(f"\u88c5\u5907\u6b66\u5668: {result[1]}")
            else:
                self.game.add_log(f"\u88c5\u5907\u5931\u8d25: {result[1]}")
        elif item_type == "armor":
            result = self.game.player.equip_item(idx)
            if result[0]:
                self.game.add_log(f"\u88c5\u5907\u62a4\u7532: {result[1]}")
            else:
                self.game.add_log(f"\u88c5\u5907\u5931\u8d25: {result[1]}")
        elif item_type == "novelty":
            # Show use/sell dialog
            self._use_novelty_in_bag(idx)
        else:
            self._show_toast("\u6682\u4e0d\u80fd\u64cd\u4f5c\u8be5\u7269\u54c1")
        self._refresh_bag()
        self._refresh_all_ui()

    def _use_novelty_in_bag(self, idx):
        ok, msg = self.game.use_novelty_item(idx)
        self.game.add_log(msg)
        self._refresh_bag()

    def _sell_bag_item(self, idx):
        ok, msg = self.game.sell_inventory_item(idx)
        self.game.add_log(msg)
        self._refresh_bag()
        self._refresh_all_ui()

    def _build_materials_tab(self):
        # 材料类型: Wood, Iron, Leather, Stone
        mat_rows = []
        mats = ["Wood", "Iron", "Leather", "Stone"]
        mat_buy_prices = {"Wood": 4, "Iron": 6, "Leather": 4, "Stone": 2}
        mat_sell_prices = {"Wood": 2, "Iron": 3, "Leather": 2, "Stone": 1}
        mat_names_cn = {"Wood": "\u6728\u6750", "Iron": "\u94c1\u77ff", "Leather": "\u76ae\u9769", "Stone": "\u77f3\u5934"}
        self._mat_buy_btns = {}
        self._mat_sell_btns = {}
        for mat in mats:
            ctr = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(mat_names_cn[mat], size=13, weight=ft.FontWeight.BOLD),
                        self._ref(f"mat_{mat}_cnt", ft.Text("x0", size=12, color=Cs("GREY_400"))),
                    ], spacing=8),
                    ft.Row([
                        ft.Text(f"\u5356: {mat_sell_prices[mat]}G / \u4e70: {mat_buy_prices[mat]}G", size=11, color=Cs("GREY_500")),
                    ], spacing=12),
                    ft.Row([
                        self._ref(f"mat_{mat}_buy_10", ft.Button(f"\u4e7010({mat_buy_prices[mat]*10}G)", scale=0.75, on_click=lambda e, m=mat: self._buy_mat(m, 10))),
                        self._ref(f"mat_{mat}_sell_10", ft.Button(f"\u535610({mat_sell_prices[mat]*10}G)", scale=0.75, on_click=lambda e, m=mat: self._sell_mat(m, 10))),
                    ], spacing=6),
                ], spacing=4),
                border=ft.Border.all(1, Cs("OUTLINE_VARIANT")),
                border_radius=6,
                padding=8,
            )
            self._ref(f"mat_{mat}_ctr", ctr)
            mat_rows.append(ctr)

        return ft.ListView(mat_rows, spacing=8, padding=8, expand=True)

    def _buy_mat(self, mat, amount):
        ok, msg = self.game.buy_material(mat, amount)
        self.game.add_log(msg)
        self._refresh_all_ui()

    def _sell_mat(self, mat, amount):
        ok, msg = self.game.sell_material(mat, amount)
        self.game.add_log(msg)
        self._refresh_all_ui()

    def _refresh_materials(self):
        mats = ["Wood", "Iron", "Leather", "Stone"]
        for mat in mats:
            cnt_lbl = self._refs.get(f"mat_{mat}_cnt")
            if cnt_lbl:
                cnt_lbl.value = "x" + str(self.game.player.resources.get(mat, 0))


    def _build_tavern_tab(self):
        self._ref("tavern_gold_lbl",
                  ft.Text("\U0001fa99 100G", size=13, weight=ft.FontWeight.BOLD))
        self._ref("tavern_timer_lbl", ft.Text("\u5237\u65b0: --:--", size=12))
        self._ref("tavern_roster_ctr", ft.Column([], spacing=4, scroll="auto"))
        self._ref("team_manage_ctr", ft.Column([], spacing=4, scroll="auto"))
        ctr = ft.Column([
            ft.Container(
                content=ft.Row([
                    self._refs["tavern_gold_lbl"],
                    self._refs["tavern_timer_lbl"],
                    ft.Container(expand=True),
                    ft.Button("\U0001f504 \u5237\u65b0 (50G)", scale=0.85,
                                       on_click=self._tavern_refresh),
                ], spacing=8),
                padding=6, bgcolor=Cs("BROWN_900"),
            ),
            ft.Text("\u2014\u2014 \u53ef\u62db\u52df\u89d2\u8272 \u2014\u2014",
                    size=13, weight=ft.FontWeight.BOLD),
            self._refs["tavern_roster_ctr"],
            ft.Divider(),
            ft.Text("\u2014\u2014 \u961f\u4f0d\u7ba1\u7406 \u2014\u2014",
                    size=13, weight=ft.FontWeight.BOLD),
            self._refs["team_manage_ctr"],
        ], scroll="auto", spacing=4)
        return ft.Container(content=ctr, padding=6)

    def _build_farm_tab(self):
        self._ref("farm_count_lbl", ft.Text("\U0001f331 \u6211\u7684\u519c\u573a: 0/10", size=13))
        self._ref("farm_plants_ctr", ft.Column([], spacing=4, scroll="auto"))
        self._ref("farm_seeds_ctr", ft.Column([], spacing=4, scroll="auto"))
        for pd in get_plant_catalog():
            rc = PLANT_RARITY_COLORS.get(pd["rarity"], "#888888")
            text = (f"{pd['icon']} {pd['name']}  "
                    f"\u4ea7{int(pd['harvest_gold'])}G/{int(pd['harvest_interval_s'])}s  "
                    f"{PLANT_RARITY_NAMES.get(pd['rarity'],'')} [{pd['seed_price']}G]")
            self._refs["farm_seeds_ctr"].controls.append(
                ft.ListTile(
                    title=ft.Text(text, size=11, color=rc),
                    trailing=ft.IconButton(icon=I.AGRICULTURE,
                                           on_click=lambda e, p=pd: self._plant_seed(p)),
                )
            )
        ctr = ft.Column([
            self._refs["farm_count_lbl"],
            ft.Container(content=self._refs["farm_plants_ctr"],
                         border=ft.Border.all(1, Cs("OUTLINE_VARIANT")),
                         border_radius=4, padding=4, height=180),
            ft.Text("\u2014\u2014 \u79cd\u5b50\u5546\u5e97 \u2014\u2014",
                    size=13, weight=ft.FontWeight.BOLD),
            ft.Container(content=self._refs["farm_seeds_ctr"],
                         border=ft.Border.all(1, Cs("OUTLINE_VARIANT")),
                         border_radius=4, padding=4, expand=True),
        ], scroll="auto", spacing=4)
        return ft.Container(content=ctr, padding=6)

    def _build_factory_tab(self):
        self._ref("factory_status_lbl",
                  ft.Text("\U0001f3ed \u672a\u5efa\u9020", size=13, color=ft.Colors.RED))
        self._ref("factory_info_lbl",
                  ft.Text("\u5efa\u9020\u8d39\u7528: " + ", ".join(f"{k}{v}" for k, v in FACTORY_BUILD_COST.items()) + "  |  \u57fa\u7840\u5229\u6da6: 50G/5min", size=11))
        self._ref("factory_build_btn",
                  ft.Button("\U0001f3d7 \u5efa\u9020\u5de5\u5382", on_click=self._build_factory_tab_action))
        self._ref("factory_depts_ctr", ft.Column([], spacing=4))
        self._ref("factory_workers_lbl",
                  ft.Text("\u52b3\u5de5: 0/5  (\u6bcf\u4eba+15%, 80G/\u4eba)", size=12))

        for dept in FACTORY_DEPTS:
            if dept["id"] == "basic":
                continue
            cost_str = f"{dept['cost_gold']}G"
            if dept["cost_resources"]:
                cost_str += ", " + ", ".join(f"{k}{v}" for k, v in dept["cost_resources"].items())
            self._ref(f"dept_card_{dept['id']}",
                      ft.Container(
                          content=ft.Column([
                              ft.Row([
                                  ft.Text(f"{dept['name']}", size=12, weight=ft.FontWeight.BOLD, expand=True),
                                  self._ref(f"dept_status_{dept['id']}", ft.Text("\u672a\u89e3\u9501", size=11, color=ft.Colors.RED)),
                              ], tight=True),
                              ft.Text(f"{dept['desc']}  |  \u8d39\u7528: {cost_str}", size=10, color=Cs("GREY_600")),
                              self._ref(f"dept_btn_{dept['id']}",
                                        ft.Button(f"\u89e3\u9501 {dept['name']}", scale=0.8,
                                                  on_click=lambda e, d=dept["id"]: self._buy_dept(d))),
                          ], spacing=2),
                          padding=4, border=ft.Border.all(1, Cs("OUTLINE_VARIANT")),
                          border_radius=4, bgcolor="#fafafa"))
            self._refs["factory_depts_ctr"].controls.append(self._refs[f"dept_card_{dept['id']}"])

        ctr = ft.Column([
            self._refs["factory_status_lbl"],
            self._refs["factory_info_lbl"],
            self._refs["factory_build_btn"],
            ft.Divider(),
            ft.Text("\u2014\u2014 \u90e8\u95e8 \u2014\u2014", size=13, weight=ft.FontWeight.BOLD),
            ft.Container(content=self._refs["factory_depts_ctr"],
                         border=ft.Border.all(1, Cs("OUTLINE_VARIANT")),
                         border_radius=4, padding=4),
            ft.Divider(),
            self._refs["factory_workers_lbl"],
            ft.Row([
                ft.Button("+ \u96c7\u4f63", scale=0.85, on_click=self._hire_factory_worker),
                ft.Button("- \u89e3\u96c7", scale=0.85, on_click=self._fire_factory_worker),
            ], spacing=8),
        ], scroll="auto", spacing=4)
        return ft.Container(content=ctr, padding=6)

    # ─── Bottom Bar ──────────────────────────────────────────────
    def _build_bottom_bar(self):
        self.page.add(ft.Container(
            content=ft.Row([
                ft.Container(expand=True),
                ft.Button("\U0001f4be \u5b58\u6863", on_click=self._save),
                ft.Button("\U0001f4c2 \u8bfb\u6863", on_click=self._load),
                ft.Button("\u2753 \u5e2e\u52a9", on_click=self._show_help),
                ft.Container(expand=True),
            ], spacing=8),
            padding=4, border=ft.Border.only(top=ft.BorderSide(color=Cs("OUTLINE_VARIANT"))),
        ))

    # ─── Update Loop ────────────────────────────────────────────
    async def _update_loop(self):
        last_log_len = 0
        battle_log_len = 0
        while True:
            await asyncio.sleep(0.3)
            self._refresh_all_ui()
            if len(self.game.logs) != last_log_len:
                self._refresh_log()
                last_log_len = len(self.game.logs)
                battle_log_len = len(self.game.logs)
            elif self.game.is_battling and len(self.game.logs) != battle_log_len:
                self._refresh_log()
                battle_log_len = len(self.game.logs)

    def _refresh_log(self):
        self.log_view.controls.clear()
        for msg in self.game.logs[-60:]:
            self.log_view.controls.append(ft.Text(msg, size=11))
        try:
            self.page.update()
        except Exception:
            pass

    def _refresh_all_ui(self):
        g = self.game
        p = g.get_current_member()

        self._refs["gold_label"].value = f"\U0001fa99 {g.player.gold}"
        self._refs["kills_label"].value = f"\u51fb\u6740: {g.player.kill_count}"

        for res, val in g.resources.items():
            ref = self._refs.get(f"res_{res}")
            if ref:
                ref.value = str(val)

        team = g.get_team()
        for i, btn in enumerate(self.team_btns):
            if i < len(team):
                m = team[i]
                btn.content = ft.Text(f"{m.role_name}\nLv.{m.level}", size=11)
                bg = Cs("ORANGE_600") if i == g.current_member_idx else (Cs("GREEN_600") if i == 0 else Cs("DEEP_PURPLE_600"))
                btn.style = ft.ButtonStyle(bgcolor=bg)
            else:
                btn.content = ft.Text("\u7a7a\u4f4d", size=11)
                btn.style = ft.ButtonStyle(bgcolor=Cs("GREY_600"))

        max_hp = p.get_max_hp_with_bonus()
        self._refs["hero_name_lbl"].value = f"\U0001f9d9 {p.role_name} Lv.{p.level}"
        self._refs["hp_lbl"].value = f"\u751f\u547d: {p.hp}/{max_hp}"
        self._refs["atk_lbl"].value = f"\u653b\u51fb: {p.get_total_attack()}"
        self._refs["def_lbl"].value = f"\u9632\u5fa1: {p.get_total_defense()}"
        self._refs["crit_lbl"].value = f"CRIT: {p.get_crit_rate()}%"
        self._refs["exp_lbl"].value = f"\u7ecf\u9a8c: {p.exp}/{p.level * 100}"
        wn = p.weapon["name"] if p.weapon and isinstance(p.weapon, dict) else "None"
        an = p.armor["name"] if p.armor and isinstance(p.armor, dict) else "None"
        self._refs["wpn_lbl"].value = f"\u6b66\u5668: {wn}"
        self._refs["arm_lbl"].value = f"\u62a4\u7532: {an}"

        self._refs["map_lbl"].value = g.current_map
        for mname in get_all_maps().keys():
            btn = self._refs.get(f"map_btn_{mname}")
            if btn:
                if mname in g.unlocked_maps:
                    btn.content = ft.Text(mname, size=11)
                    btn.style = ft.ButtonStyle(bgcolor=Cs("GREEN_600"))
                else:
                    cost = get_all_maps()[mname].get("unlock_cost", 0)
                    btn.content = ft.Text(f"{mname}({cost}G)", size=11)
                    btn.style = ft.ButtonStyle(bgcolor=Cs("GREY_600"))

        e = g.current_enemy
        if e:
            tag = " [BOSS]" if g.current_enemy_is_boss else ""
            self._refs["enemy_display"].value = f"\U0001f480 {e['name']}{tag}  HP:{e['hp']} ATK:{e['attack']}"
            self._refs["enemy_display"].color = ft.Colors.RED_800
        else:
            self._refs["enemy_display"].value = "\U0001f480 ???"
            self._refs["enemy_display"].color = Cs("GREY_500")

        self._refs["battle_btn"].disabled = g.is_battling
        self._refs["battle_btn"].content = ft.Text(
            "\u6218\u4e2d..." if g.is_battling else "\u2694 \u6218\u6597", size=13)
        self._refs["auto_status_lbl"].value = "\u81ea\u52a8: \u5f00" if g.auto_battle else "\u81ea\u52a8: \u5173"
        self._refs["auto_status_lbl"].color = ft.Colors.GREEN_600 if g.auto_battle else Cs("GREY_500")
        self._refs["auto_btn"].content = ft.Text(
            "\u23f9 \u505c\u6b62" if g.auto_battle else "\u26a1 \u81ea\u52a8\u6218\u6597", size=12)
        self._refs["auto_btn"].style = ft.ButtonStyle(
            bgcolor=Cs("RED_600") if g.auto_battle else Cs("ORANGE_600"))
        self._refs["potions_lbl"].value = f"\U0001f9ea \u836f\u6c34: x{p.potions}"

        for bname in get_all_building_names():
            levels = g.building_levels.get(bname, [])
            cnt_ref = self._refs.get(f"bld_count_{bname}")
            info_ref = self._refs.get(f"bld_info_{bname}")
            upg_btn = self._refs.get(f"bld_upg_btn_{bname}")
            if cnt_ref:
                cnt_ref.value = f"x{len(levels)}"
            if info_ref:
                if levels:
                    avg = int(sum(levels) / len(levels))
                    cfg = BUILDING_CONFIGS[bname]
                    info_ref.value = f"Lv{avg} {cfg.get_output(avg)}/{cfg.get_interval(avg)}s"
                else:
                    info_ref.value = "\u672a\u5efa\u9020"
            if upg_btn:
                upg_btn.disabled = not levels

        for wname, btn in self.wonder_btns.items():
            if wname in g.wonders:
                btn.content = ft.Text(f"\u2705 {wname}", size=12)
                btn.disabled = True

        # 更新农场状态
        flbl = self._refs.get("farm_count_lbl")
        if flbl:
            flbl.value = f"\U0001f331 \u6211\u7684\u519c\u573a: {len(g.plants)}/10"
        
        # 更新植物列表
        fctr = self._refs.get("farm_plants_ctr")
        if fctr:
            fctr.controls.clear()
            for plant in g.plants:
                pd = next((p for p in get_plant_catalog() if p["id"] == plant["id"]), None)
                if pd:
                    harvest_time = plant["harvest_time"]
                    remaining = max(0, harvest_time - time.time())
                    if remaining <= 0:
                        status = "\U0001f7e2 \u53ef\u6536\u83b7"
                        color = Cs("GREEN_600")
                        btn = ft.Button("\u6536\u83b7", scale=0.8, 
                                      on_click=lambda e, p=plant: self._harvest_plant(p))
                    else:
                        m, s = divmod(int(remaining), 60)
                        status = f"\U0001f7e0 {m:02d}:{s:02d}"
                        color = Cs("ORANGE_600")
                        btn = ft.Row([
                            ft.Text("\u79cd\u690d\u4e2d", size=11, color=Cs("GREY_500")),
                            ft.Button("\u26a1", scale=0.7,
                                      on_click=lambda e, p=plant: self._speedup(p)),
                        ], spacing=4)
                    
                    fctr.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(f"{pd['icon']} {pd['name']}", size=12, weight=ft.FontWeight.BOLD, expand=True),
                                    ft.Text(status, size=11, color=color)
                                ], tight=True),
                                ft.Container(content=btn, alignment=ft.alignment.Alignment(0.5, 0.5))
                            ], spacing=2),
                            padding=4, border=ft.Border.all(1, Cs("OUTLINE_VARIANT")), border_radius=4,
                            bgcolor="#fafafa"
                        )
                    )
        
        # 更新工厂状态
        fsl = self._refs.get("factory_status_lbl")
        if fsl:
            if self.game.factory:
                bonus = calc_fb(self.game.factory_departments, self.game.factory_workers)
                profit = int(FACTORY_BASE_PROFIT * bonus)
                fsl.value = f"\U0001f3ed \u8fd0\u8425\u4e2d | \u501f\u7387: x{bonus:.1f} | {profit}G/{int(FACTORY_BASE_INTERVAL_S)}s"
                fsl.color = ft.Colors.GREEN_700
            else:
                fsl.value = "\U0001f3ed \u672a\u5efa\u9020"
                fsl.color = ft.Colors.RED
        fbb = self._refs.get("factory_build_btn")
        if fbb:
            fbb.disabled = self.game.factory is not None
        fwl = self._refs.get("factory_workers_lbl")
        if fwl:
            fwl.value = f"\u52b3\u5de5: {self.game.factory_workers}/5  (\u6bcf\u4eba+15%, 80G/\u4eba)"
        for dept in FACTORY_DEPTS:
            if dept["id"] == "basic":
                continue
            st = self._refs.get(f"dept_status_{dept['id']}")
            bt = self._refs.get(f"dept_btn_{dept['id']}")
            if st:
                if dept["id"] in self.game.factory_departments:
                    st.value = "\u2705 \u5df2\u89e3\u9501"
                    st.color = ft.Colors.GREEN_700
                else:
                    st.value = "\u672a\u89e3\u9501"
                    st.color = ft.Colors.RED
            if bt:
                bt.disabled = dept["id"] in self.game.factory_departments or self.game.factory is None

        gl = self._refs.get("tavern_gold_lbl")
        if gl:
            gl.value = f"\U0001fa99 {g.player.gold}G"
        tl = self._refs.get("tavern_timer_lbl")
        if tl:
            left = max(0, 3600 - (time.time() - g.tavern_last_refresh))
            m, s = divmod(int(left), 60)
            tl.value = f"\u5237\u65b0: {m:02d}:{s:02d}"
        # 酒馆角色列表
        rctr = self._refs.get("tavern_roster_ctr")
        if rctr:
            rctr.controls.clear()
            roster = g.get_tavern_roster()
            for ch in roster:
                cost = ch.get("cost", g.player.level * 100)
                wn = ch.get("weapon", {}).get("name", "无") if ch.get("weapon") else "无"
                rctr.controls.append(ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"{ch.get('role_name','?')} Lv.{ch.get('level',1)}", size=12, weight=ft.FontWeight.BOLD, expand=True),
                            ft.Text(f"{cost}G", size=12, color=ft.Colors.AMBER_700),
                        ], tight=True),
                        ft.Text(f"\u6b66\u5668: {wn}", size=10, color=Cs("GREY_600")),
                        ft.Button("\u62db\u52df", scale=0.8, on_click=lambda e, c=ch: self._recruit_member(c)),
                    ], spacing=2), padding=4, border=ft.Border.all(1, Cs("OUTLINE_VARIANT")), border_radius=4))
            if not roster:
                rctr.controls.append(ft.Text("\u6682\u65e0\u53ef\u62db\u52df\u89d2\u8272", size=12, color=Cs("GREY_500")))
        # 队伍管理列表
        tctr = self._refs.get("team_manage_ctr")
        if tctr:
            tctr.controls.clear()
            team = g.get_team()
            for i, m in enumerate(team):
                tag = " \u2605\u961f\u957f" if i == 0 else f" #{i}"
                wn = m.weapon["name"] if m.weapon and isinstance(m.weapon, dict) else "无"
                tctr.controls.append(ft.Container(
                    content=ft.Row([
                        ft.Text(f"{m.role_name} Lv.{m.level}{tag}", size=12, weight=ft.FontWeight.BOLD, expand=True),
                        ft.Text(f"HP:{m.hp}/{m.get_max_hp_with_bonus()}", size=11),
                        ft.Button("\u5207\u6362", scale=0.75,
                                  on_click=lambda e, idx=i: self._switch_to(idx)) if i != g.current_member_idx else None,
                        ft.Button("\u8e22\u51fa", scale=0.75,
                                  on_click=lambda e, idx=i: self._kick_member_ui(idx)) if i > 0 else None,
                    ], spacing=4, alignment=ft.alignment.Alignment(-1, 0)),
                    padding=4, border=ft.Border.all(1, Cs("OUTLINE_VARIANT")), border_radius=4,
                    bgcolor="#fff8e1" if i == g.current_member_idx else None))

    # ─── Actions ────────────────────────────────────────────────
    def _do_battle(self, e=None):
        if self.game.is_battling:
            self.game.add_log("\u6218\u4e2d\u4e2d...")
            return
        enemy, is_boss = get_random_enemy(self.game.current_map)
        if not enemy:
            self.game.add_log("\u6ca1\u6709\u654c\u4eba!")
            return
        self.game.current_enemy = enemy
        self.game.current_enemy_is_boss = is_boss
        threading.Thread(target=self._battle_thread, args=(enemy, is_boss), daemon=True).start()

    def _battle_thread(self, enemy, is_boss):
        self.game.is_battling = True
        self._refresh_all_ui()
        try:
            result, msg = self.game.battle_team(enemy, is_boss=is_boss)
            self.game.add_log(msg)
        except Exception as ex:
            self.game.add_log(f"Battle error: {ex}")
        finally:
            self.game.is_battling = False
            e2 = self.game.current_enemy
            b2 = self.game.current_enemy_is_boss
            if e2:
                tag = " [BOSS]" if b2 else ""
                self.game.add_log("Next: " + e2["name"] + tag)
            self._refresh_all_ui()

    def _toggle_auto(self, e=None):
        self.game.auto_battle = not self.game.auto_battle
        if self.game.auto_battle:
            self.game.add_log("\u26a1 \u81ea\u52a8\u6218\u6597 ON!")
            self.game.start_auto_battle()
        else:
            self.game.add_log("\u23f9 \u81ea\u52a8\u6218\u6597 OFF.")

    def _refresh_enemy(self, e=None):
        if self.game.is_battling:
            self.game.add_log("\u6218\u4e2d\u65e0\u6cd5\u5237\u65b0!")
            return
        cost = 5 + random.randint(0, 5)
        if self.game.player.gold < cost:
            self.game.add_log("\u91d1\u5e01\u4e0d\u8db3! \u9700\u8981 " + str(cost) + "G")
            return
        self.game.player.gold -= cost
        enemy, is_boss = get_random_enemy(self.game.current_map)
        if enemy:
            self.game.current_enemy = enemy
            self.game.current_enemy_is_boss = is_boss
            tag = " [BOSS]" if is_boss else ""
            self.game.add_log("Refreshed: " + enemy["name"] + tag + " (-" + str(cost) + "G)")

    def _change_map(self, map_name):
        if map_name in self.game.unlocked_maps:
            ok, msg = self.game.change_map(map_name)
            self.game.add_log(msg)
        else:
            ok, msg = self.game.unlock_map(map_name)
            self.game.add_log(msg)
            if ok:
                enemy, is_boss = get_random_enemy(map_name)
                self.game.current_enemy = enemy
                self.game.current_enemy_is_boss = is_boss

    def _switch_member(self, idx):
        ok, msg = self.game.switch_member(idx)
        if not ok:
            self._show_toast(msg)
        else:
            self.game.add_log(f"\u5207\u6362\u5230: {self.game.get_current_member().role_name}")

    def _buy_potion(self, e=None):
        ok, msg = self.game.buy_potion()
        self.game.add_log(msg)

    def _use_potion(self, e=None):
        ok, msg = self.game.use_potion()
        self.game.add_log(msg)
        self._refresh_all_ui()


    def _on_auto_potion_change(self, e=None):
        val_str = self._refs["auto_potion_dd"].value
        if val_str == "OFF":
            val = 0
        else:
            val = int(val_str.replace("%", ""))
        self.game.set_auto_potion_threshold(val)
        self._update_auto_potion_label()

    def _update_auto_potion_label(self):
        t = self.game.auto_potion_threshold
        lbl = self._refs["auto_potion_lbl"]
        dd = self._refs["auto_potion_dd"]
        if t > 0:
            lbl.value = "Active (" + str(t) + "%)"
            lbl.color = Cs("GREEN_700")
        else:
            lbl.value = "已关闭"
            lbl.color = Cs("GREY_500")
            dd.value = "OFF"

    def _restore_auto_potion_ui(self):
        t = self.game.auto_potion_threshold
        rev = {0: "OFF", 30: "30%", 50: "50%", 80: "80%"}
        dd = self._refs["auto_potion_dd"]
        dd.value = rev.get(t, "OFF")
        self._update_auto_potion_label()
    def _build_building(self, name):
        ok, msg = self.game.build_building(name)
        self.game.add_log(msg)

    def _upgrade_building(self, name):
        levels = self.game.building_levels.get(name, [])
        if not levels:
            self.game.add_log("\u5148\u5efa\u9020!")
            return
        ok, msg = self.game.upgrade_building(name, len(levels) - 1)
        self.game.add_log(f"{name} \u5347\u7ea7\u6210\u529f!" if ok else f"\u5347\u7ea7: {msg}")

    def _build_wonder(self, name):
        ok, msg = self.game.build_wonder(name)
        self.game.add_log(msg)

    def _buy_weapon(self, wpn):
        ok, msg = self.game.buy_weapon(wpn)
        self.game.add_log(f"\u8d2d\u4e70\u6b66\u5668: {msg}" if ok else f"\u8d2d\u4e70\u5931\u8d25: {msg}")

    def _buy_armor(self, arm):
        ok, msg = self.game.buy_armor(arm)
        self.game.add_log(f"\u8d2d\u4e70\u62a4\u7532: {msg}" if ok else f"\u8d2d\u4e70\u5931\u8d25: {msg}")

    def _buy_novelty(self, item):
        ok, msg = self.game.buy_novelty_item(item)
        self.game.add_log(msg)

    def _recruit_member(self, ch):
        ok, msg = self.game.recruit_member(ch.get("role_name"), ch.get("level", 1), ch.get("cost", 100), ch.get("gear"))
        self.game.add_log(msg)

    def _switch_to(self, idx):
        ok, msg = self.game.switch_member(idx)

    def _kick_member_ui(self, idx):
        ok, msg = self.game.kick_member(idx)
        self.game.add_log(msg)

    def _tavern_refresh(self, e=None):
        ok, msg = self.game.manual_refresh_tavern()
        self.game.add_log(msg)

    def _open_tavern_tab(self, e=None):
        self.right_tabs.selected_index = 3

    def _plant_seed(self, pd):
        ok, msg = self.game.plant_seed(pd["id"], cost_gold=pd["seed_price"])
        self.game.add_log(msg)
        
    def _harvest_plant(self, plant):
        ok, msg = self.game.harvest_plant(plant["id"])
        self.game.add_log(msg)

    def _speedup(self, plant):
        ok, msg = self.game.speedup_plant(plant["id"])
        self.game.add_log(msg)

    def _build_factory_tab_action(self, e=None):
        ok, msg = self.game.build_factory()
        self.game.add_log(msg)

    def _buy_dept(self, dept_id):
        ok, msg = self.game.buy_factory_dept(dept_id)
        self.game.add_log(msg)

    def _hire_factory_worker(self, e=None):
        ok, msg = self.game.hire_factory_worker()
        self.game.add_log(msg)

    def _fire_factory_worker(self, e=None):
        ok, msg = self.game.fire_factory_worker()
        self.game.add_log(msg)

    def _hire_worker(self, building_name):
        ok, msg = self.game.hire_worker(building_name)
        self.game.add_log(msg)

    def _fire_worker(self, building_name):
        ok, msg = self.game.fire_worker(building_name)
        self.game.add_log(msg)

    # ─── Save / Load ────────────────────────────────────────────
    def _save(self, e=None):
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
            "team": self.game.team_to_dict(),
            "tavern": self.game.tavern_to_dict(),
            "current_member_idx": self.game.current_member_idx,
        }
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.game.add_log(f"\U0001f4be \u5df2\u5b58\u6863!")
        self._show_toast("\u5b58\u6863\u6210\u529f!")

    def _load(self, e=None):
        if not os.path.exists(SAVE_PATH):
            self.game.add_log("\u6ca1\u6709\u5b58\u6863\u6587\u4ef6!")
            return
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.game.resources = data.get("resources", {})
        self.game.buildings = data.get("buildings", {})
        self.game.building_levels = data.get("building_levels", {})
        self.game.building_workers = data.get("building_workers", {})
        self.game.player.from_dict(data.get("player", {}))
        self.game.current_map = data.get("current_map", "\u50b2\u6765\u56fd")
        self.game.unlocked_maps = set(data.get("unlocked_maps", ["\u50b2\u6765\u56fd"]))
        self.game.current_enemy_idx = data.get("current_enemy_idx", 0)
        self.game.wonders = {n: True for n in data.get("wonders", [])}
        self.game.plants = data.get("plants", [])
        self.game.factory = data.get("factory")
        self.game.factory_departments = data.get("factory_departments",
                                                  ["basic"] if data.get("factory") else [])
        self.game.factory_workers = data.get("factory_workers", 0)
        self.game.factory_last_profit_time = data.get("factory_last_profit_time", 0)
        self.game.auto_potion_threshold = data.get("auto_potion_threshold", 0)
        self.game.team_from_dict(data.get("team", []))
        self.game.tavern_from_dict(data.get("tavern", []))
        self.game.current_member_idx = data.get("current_member_idx", 0)
        for name, levels in self.game.building_levels.items():
            for idx in range(len(levels)):
                self.game.start_building_production(name, idx)
        self.game.add_log("\U0001f4c2 \u8bfb\u6863\u6210\u529f!")
        self._show_toast("\u8bfb\u6863\u6210\u529f!")

    def _show_help(self, e=None):
        self.page.dialog = ft.AlertDialog(
            title=ft.Text("\u5e2e\u52a9"),
            content=ft.Text(
                "\u52c7\u8005\u5de5\u574a v5.1\n\n"
                "\u2694 \u6218\u6597: \u961f\u4f0d\u5168\u5458\u968f\u673a\u653b\u51fb\n"
                "\u26a1 \u81ea\u52a8: \u6301\u7eed\u6218\u6597\n"
                "\U0001f3d7 \u5efa\u9020: \u6d88\u8017\u8d44\u6e90\n"
                "\U0001f5fa \u5730\u56fe: \u5207\u6362\u5730\u56fe\n"
            ),
            actions=[ft.TextButton("OK", on_click=lambda e: setattr(self.page, "dialog", None) or self.page.update())],
        )
        self.page.dialog.open = True
        self.page.update()

    def _show_toast(self, msg: str):
        sn = ft.SnackBar(ft.Text(msg), duration=2000)
        self.page.overlay.append(sn)
        sn.open = True
        self.page.update()


def main(page: ft.Page):
    HeroWorkshopApp(page)


if __name__ == "__main__":
    ft.run(main)
