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
from modules.plants import get_plant_catalog, get_plant_by_id, PLANT_RARITY_COLORS, PLANT_RARITY_NAMES
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
    m = {"金币": "金", "木材": "木", "铁矿": "铁",
         "皮革": "皮", "石头": "石"}
    return " ".join(f"{m.get(k, k)}{v}" for k, v in cost.items())


class HeroWorkshopApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "勇者工坊 v5.1"
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
        # 拖拽分栏属性
        self._dragging_divider = None
        self._left_width = 230
        self._right_width = 400

        self._drag_start_x = 0
        self._load_panel_widths()
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
        self._ref("kills_label", ft.Text("击杀: 0", size=13, color=Cs("GREY_500")))
        self._ref("gold_label", ft.Text("💡 100", size=15, weight=ft.FontWeight.BOLD, color="#B8860B"))
        ab = ft.AppBar(title=ft.Text("⚔ 勇者工坊 v5.1", size=18, weight=ft.FontWeight.BOLD), actions=[
            self._refs["kills_label"],
            ft.Container(width=20),
            self._refs["gold_label"],
            ft.Container(width=10),
            ft.IconButton(icon=I.MENU, icon_size=22, tooltip="菜单", on_click=lambda e: self._show_menu(e)),
        ])
        self.page.appbar = ab

    # ─── Body ──────────────────────────────────────────────────
    def _build_body(self):
        self.left_panel_ref = self._build_left()
        self.center_panel_ref = self._build_center()
        self.right_panel_ref = self._build_right()

        # 左-中分隔条
        self.divider1 = self._build_divider(on_drag=1)
        # 中-右分隔条
        self.divider2 = self._build_divider(on_drag=2)

        self.body = ft.Row(
            controls=[
                self.left_panel_ref,
                self.divider1,
                self.center_panel_ref,
                self.divider2,
                self.right_panel_ref,
            ],
            spacing=0, expand=True,
        )
        self.page.add(self.body)



    def _show_menu(self, e):
        def close_and(fn):
            def handler(ev):
                self.page.pop_dialog()
                fn()
            return handler
        self._menu_dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("⚙ 菜单", size=16, weight=ft.FontWeight.BOLD),
            content=ft.Column([
                ft.TextButton("💾 保存布局", on_click=close_and(self._save_layout)),
                ft.TextButton("🔄 重置布局", on_click=close_and(self._reset_layout)),
            ], spacing=5),
            actions=[ft.TextButton("关闭", on_click=lambda e: self.page.pop_dialog())],
        )
        self.page.show_dialog(self._menu_dlg)

    def _save_layout(self):
        self._save_panel_widths()
        self.page.show_snack_bar(ft.SnackBar(ft.Text("布局已保存"), open=True))

    def _reset_layout(self):
        self._left_width = 230
        self._right_width = 400
        self.left_panel_ref.width = self._left_width
        self.right_panel_ref.width = self._right_width
        self._save_panel_widths()
        self.page.update()
        self.page.show_snack_bar(ft.SnackBar(ft.Text("布局已重置"), open=True))

    def _build_divider(self, on_drag):
        bar = ft.Container(
            width=4, expand=True,
            bgcolor=ft.Colors.OUTLINE_VARIANT,
            border_radius=2,
        )
        g = ft.GestureDetector(
            content=ft.Container(
                width=20, expand=True,
                alignment=ft.alignment.Alignment(0.5, 0),
                content=bar,
            ),
            drag_interval=0,
            on_horizontal_drag_start=lambda e: self._on_divider_drag_start(e, on_drag),
            on_horizontal_drag_update=lambda e: self._on_divider_drag_update(e),
            on_horizontal_drag_end=lambda e: self._on_divider_drag_end(e),
            on_hover=lambda e: self._on_divider_hover(e, bar),
        )
        return g

    def _on_divider_hover(self, e, bar):
        bar.bgcolor = ft.Colors.PRIMARY if e.data == 'true' else ft.Colors.OUTLINE_VARIANT
        bar.update()

    def _on_divider_drag_start(self, e, on_drag):
        self._dragging_divider = on_drag
        self._drag_start_x = e.global_position.x

    def _on_divider_drag_update(self, e):
        if not self._dragging_divider:
            return
        dx = e.global_delta.x
        if self._dragging_divider == 1:
            self._left_width = max(150, min(400, self._left_width + dx))
            self.left_panel_ref.width = self._left_width
            self.left_panel_ref.update()
        else:
            self._right_width = max(150, min(600, self._right_width - dx))
            self.right_panel_ref.width = self._right_width
            self.right_panel_ref.update()
        self.body.update()

    def _on_divider_drag_end(self, e):
        self._dragging_divider = None
        self._save_panel_widths()

    def _load_panel_widths(self):
        try:
            if os.path.exists(SAVE_PATH):
                data = json.loads(open(SAVE_PATH, 'r', encoding='utf-8').read())
                pw = data.get('panel_widths', {})
                self._left_width = pw.get('left', 230)
                self._right_width = pw.get('right', 400)
        except:
            pass

    def _save_panel_widths(self):
        try:
            if os.path.exists(SAVE_PATH):
                data = json.loads(open(SAVE_PATH, 'r', encoding='utf-8').read())
            else:
                data = {}
            data['panel_widths'] = {'left': self._left_width, 'right': self._right_width}
            open(SAVE_PATH, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=2))
        except:
            pass

    # ─── Left Panel ─────────────────────────────────────────────
    def _build_left(self):
        col = ft.Column(spacing=0, scroll="auto", expand=True)

        # Resources
        col.controls.append(ft.Container(
            content=ft.Column([
                ft.Text("\U0001f4e6 资源", size=14, weight=ft.FontWeight.BOLD, color=Cs("GREY_700")),
                ft.Divider(height=1),
            ], spacing=4),
            padding=ft.Padding.all(8),
            border=ft.Border.all(1, Cs("OUTLINE")),
            border_radius=6,
            margin=ft.Margin.only(right=4, bottom=4),
        ))

        MATERIALS = [("木材", "\U0001f332"), ("铁矿", "⛏️"),
                     ("皮革", "\U0001f9e4"), ("石头", "⛰️")]
        for name, icon in MATERIALS:
            col.controls.append(ft.Row([
                ft.Text(f"{icon} {name}:", size=13, expand=2),
                self._ref(f"res_{name}", ft.Text("0", size=13, weight=ft.FontWeight.BOLD, expand=1)),
                ft.IconButton(icon=I.REMOVE, icon_size=15, on_click=lambda e, n=name: self._sell_mat(n, 1)),
                ft.Text("\xd7", size=12),
                ft.IconButton(icon=I.ADD, icon_size=15, on_click=lambda e, n=name: self._buy_mat(n, 1)),
            ], spacing=2, tight=True))

        # Buildings
        col.controls.append(ft.Container(
            content=ft.Text("\U0001f3d7 建筑", size=14, weight=ft.FontWeight.BOLD, color=Cs("GREY_700")),
            padding=ft.Padding.only(left=4, top=10, bottom=4),
        ))
        self.building_cards = ft.Column(spacing=4, scroll="auto")
        col.controls.append(self.building_cards)
        for bname in get_all_building_names():
            self.building_cards.controls.append(self._build_building_card(bname))

        # Wonders
        col.controls.append(ft.Container(
            content=ft.Text("✨ 奇观", size=14, weight=ft.FontWeight.BOLD, color=Cs("GREY_700")),
            padding=ft.Padding.only(left=4, top=8, bottom=4),
        ))
        self.wonder_cards = ft.Column(spacing=3, scroll="auto")
        col.controls.append(self.wonder_cards)
        for wname in get_wonder_names():
            self.wonder_cards.controls.append(self._build_wonder_card(wname))

        return self._ref("left_panel", ft.Container(content=col, width=self._left_width, padding=4, bgcolor=Cs("SURFACE_CONTAINER_LOWEST")))

    def _build_instance_card(self, name, idx, level, workers, max_workers, output, interval):
        cfg = BUILDING_CONFIGS[name]
        hire_cost = cfg.worker_cost.get("金币", 50)
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(f"  #{idx+1} Lv{level}", size=11, expand=True, color=Cs("GREY_700")),
                    ft.Text(f"{output}/{interval}s", size=10, color=Cs("BLUE_700")),
                ], spacing=2, tight=True),
                ft.Row([
                    ft.OutlinedButton("升级", scale=0.7,
                                      on_click=lambda e, n=name, i=idx: self._upgrade_building(n, i)),
                    ft.Text(f"工:{workers}/{max_workers}", size=10, expand=1, color=Cs("GREY_600")),
                    ft.IconButton(icon=I.REMOVE, icon_size=12,
                                   on_click=lambda e, n=name, i=idx: self._fire_worker(n, i)),
                    ft.Text("✕", size=9),
                    ft.IconButton(icon=I.ADD, icon_size=12,
                                   on_click=lambda e, n=name, i=idx: self._hire_worker(n, i)),
                ], spacing=2, tight=True),
            ], spacing=2),
            padding=ft.Padding.only(left=4, right=4, top=3, bottom=3),
            border=ft.Border.all(1, Cs("GREY_300")),
            border_radius=4,
            bgcolor="#fafafa",
        )

    def _build_building_card(self, name):
        """返回建筑标题卡片 + 实例容器。实例卡片在建造/升级时动态刷新。"""
        instance_ctr = self._ref(f"bld_instances_{name}", ft.Column(spacing=2))
        return ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Text(name, size=13, weight=ft.FontWeight.BOLD, expand=True),
                    ft.Container(
                        content=self._ref(f"bld_count_{name}", ft.Text("x0", size=12, color=Cs("GREY_500"))),
                        padding=ft.Padding.only(right=4),
                    ),
                ]),
                padding=ft.Padding.only(left=6, top=4, bottom=4),
                bgcolor=Cs("GREY_100"),
                border_radius=4,
            ),
            instance_ctr,
            ft.Container(
                content=ft.Row([
                    ft.Text("建造", size=11, expand=1),
                    ft.Button("建造 +1", scale=0.75,
                              on_click=lambda e, n=name: self._build_building(n)),
                ], spacing=4, tight=True),
                padding=ft.Padding.only(left=4, right=4, bottom=4),
            ),
        ], spacing=1)

    def _build_wonder_card(self, name):
        wonder_btn = ft.Button("建造奇观", scale=0.9, on_click=lambda e, n=name: self._build_wonder(n))
        self.wonder_btns[name] = wonder_btn
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(name, size=13, weight=ft.FontWeight.BOLD, expand=True),
                    self._ref(f"wonder_count_{name}", ft.Text("x0", size=12, color=Cs("GREY_500"))),
                ]),
                self._ref(f"wonder_info_{name}", ft.Text("未建造", size=11, color=Cs("GREY_400"))),
                ft.Container(
                    content=wonder_btn,
                    alignment=ft.alignment.Alignment(0.5, 0.5),
                ),
            ], spacing=3),
            padding=6, border=ft.Border.all(1, Cs("OUTLINE_VARIANT")), border_radius=6,
        )

    def _build_center(self):
        col = ft.Column(spacing=6, expand=True)

        # Team row
        team_row = ft.Row(spacing=6)
        self.team_btns = []
        for i in range(3):
            btn = ft.Button(
                ft.Text("..." * 3, size=14, weight=ft.FontWeight.W_500), width=120,
                on_click=lambda e, idx=i: self._switch_member(idx)
            )
            self.team_btns.append(btn)
            team_row.controls.append(btn)
        team_row.controls.append(
            ft.Button(ft.Text("\U0001f37a 酒馆", size=14, weight=ft.FontWeight.W_500),
                      on_click=self._open_tavern_tab)
        )
        col.controls.append(ft.Container(
            content=ft.Column([
                ft.Text("\U0001f465 队伍", size=14, weight=ft.FontWeight.BOLD),
                team_row,
            ], spacing=4),
            padding=6, border=ft.Border.all(1, Cs("OUTLINE_VARIANT")), border_radius=6,
        ))

        # Hero stats
        self.hero_stats = ft.Column(spacing=1)
        col.controls.append(ft.Container(
            content=ft.Column([
                self._ref("hero_name_lbl", ft.Text("\U0001f9d9 勇者 Lv.1", size=14, weight=ft.FontWeight.BOLD)),
                self.hero_stats,
            ], spacing=2),
            padding=6, border=ft.Border.all(1, Cs("OUTLINE_VARIANT")), border_radius=6,
        ))
        self._init_hero_stats()

        # Map + Enemy
        map_btns_row = ft.Row(wrap=True, spacing=6)
        for mname in get_all_maps().keys():
            btn = ft.Button(ft.Text(mname, size=14, weight=ft.FontWeight.W_500),
                             on_click=lambda e, m=mname: self._change_map(m),
                             style=ft.ButtonStyle(bgcolor=Cs("BLUE_600"), color=ft.Colors.WHITE))
            map_btns_row.controls.append(btn)
            self._ref(f"map_btn_{mname}", btn)

        col.controls.append(ft.Container(
            content=ft.Column([
                ft.Text("\U0001f5fa 地图", size=14, weight=ft.FontWeight.BOLD),
                self._ref("map_lbl", ft.Text("傲来国", size=13, color=Cs("BLUE_700"))),
                map_btns_row,
                ft.Divider(),
                self._ref("enemy_display",
                          ft.Text("\U0001f480 ??? HP:?? ATK:??", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_800)),
                ft.Row([
                    ft.Button("\U0001f504 刷新敌人", on_click=self._refresh_enemy),
                    self._ref("refresh_cost_lbl", ft.Text("", size=12)),
                ], spacing=4),
            ], spacing=4),
            padding=6, border=ft.Border.all(1, Cs("OUTLINE_VARIANT")), border_radius=6,
        ))

        # Battle buttons
        col.controls.append(ft.Container(
            content=ft.Column([
                self._ref("battle_btn",
                          ft.Button("⚔ 战斗", width=200, height=45,
                                            on_click=self._do_battle,
                                            style=ft.ButtonStyle(bgcolor=Cs("BLUE_600")))),
                self._ref("auto_btn",
                          ft.Button("⚡ 自动战斗", width=200,
                                            on_click=self._toggle_auto,
                                            style=ft.ButtonStyle(bgcolor=Cs("ORANGE_600")))),
                self._ref("auto_status_lbl",
                          ft.Text("自动: 关", size=12, color=Cs("GREY_500"))),
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
                ft.Text("\U0001f9ea 药水", size=14, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.Button("购买 (25G)", scale=0.85, on_click=self._buy_potion),
                    self._ref("potions_lbl", ft.Text("x0", size=13)),
                    ft.Button("使用 +20HP", scale=0.85, on_click=self._use_potion),
                ], spacing=4),
                ft.Row([
                    ft.Text("自动 HP<", size=12),
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
                ft.Text("\U0001f4cb 战斗日志", size=14, weight=ft.FontWeight.BOLD),
                ft.Container(content=self.log_view,
                             border=ft.Border.all(1, Cs("OUTLINE_VARIANT")),
                             border_radius=4, padding=4, expand=True),
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
            ("hp_lbl", "生命: 100/100"),
            ("atk_lbl", "攻击: 10"),
            ("def_lbl", "防御: 5"),
            ("crit_lbl", "CRIT: 0%"),
            ("exp_lbl", "经验: 0/100"),
            ("wpn_lbl", "武器: None"),
            ("arm_lbl", "护甲: None"),
        ]:
            ctrl = self._ref(key, ft.Text(default, size=12))
            self.hero_stats.controls.append(ctrl)

    # ─── Right Panel ─────────────────────────────────────────────
    def _build_right(self):
        self._tab_bar = ft.TabBar(
            tabs=[
                ft.Tab(label="⚔ 武器"),
                ft.Tab(label="\U0001f6e1 护甲"),
                ft.Tab(label="\U0001f381 杂货"),
                ft.Tab(label="\U0001f392 背包"),
                ft.Tab(label="⭐ 材料"),
                ft.Tab(label="\U0001f37a 酒馆"),
                ft.Tab(label="\U0001f331 农场"),
                ft.Tab(label="\U0001f3ed 工厂"),
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
        return self._ref("right_panel_ref", ft.Container(content=self.right_tabs, width=self._right_width, padding=4))

    def _build_weapon_tab(self):
        items = []
        for idx, w in enumerate(WEAPONS):
            crit = f" CRIT{w['crit_rate']}%" if w["crit_rate"] > 0 else ""
            ridx = min(idx // 4, 4)
            color = RARITY_COLORS[ridx]
            items.append(ft.ListTile(
                title=ft.Text(f"{w['name']}  ATK:{w['attack']}{crit}", size=13, color=color, weight=ft.FontWeight.W_500),
                subtitle=ft.Text(cost_str(w["cost"]), size=11, color=Cs("GREY_500")),
                trailing=ft.IconButton(icon=I.SHOPPING_CART,
                                       on_click=lambda e, wpn=w: self._buy_weapon(wpn)),
            ))
        return ft.ListView(items, spacing=2, expand=True)

    def _build_armor_tab(self):
        items = []
        for idx, a in enumerate(ARMORS):
            hp = f" HP+{a['hp_bonus']}" if a["hp_bonus"] > 0 else ""
            ridx = min(idx // 4, 4)
            color = RARITY_COLORS[ridx]
            items.append(ft.ListTile(
                title=ft.Text(f"{a['name']}  DEF:{a['defense']}{hp}", size=13, color=color, weight=ft.FontWeight.W_500),
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
        self._ref("bag_count_lbl", ft.Text("背包: 0/20", size=13, weight=ft.FontWeight.BOLD))
        title_row = ft.Row([
            self._refs["bag_count_lbl"],
            ft.Container(expand=True),
            ft.Text("点击装备名笱打拔或卖出", size=11, color=Cs("GREY_500")),
        ], spacing=8)

        # 当前装备区
        equip_ctr = ft.Column([
            ft.Text("-- 当前装备 --", size=13, weight=ft.FontWeight.BOLD),
            ft.Row([
                self._ref("eq_weapon_lbl", ft.Text("武器: 未装备", size=12)),
                ft.Container(expand=True),
                self._ref("eq_armor_lbl", ft.Text("护甲: 未装备", size=12)),
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
                    self._ref(f"bag_lbl_{i}", ft.Text("空", size=11, color=Cs("GREY_500"), text_align="center")),
                    ft.Row([
                        self._ref(f"bag_e_{i}", ft.Text("装", size=10)),
                        self._ref(f"bag_s_{i}", ft.Text("卖", size=10)),
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
        self._refs["bag_count_lbl"].value = f"背包: {count}/20"

        # 当前装备
        m = self.game.get_current_member()
        wpn = m.weapon
        arm = m.armor
        self._refs["eq_weapon_lbl"].value = (f"武器: {wpn['name']}" if wpn else "武器: 未装备")
        self._refs["eq_armor_lbl"].value = (f"护甲: {arm['name']}" if arm else "护甲: 未装备")

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
                lbl.value = "空"
                lbl.color = Cs("GREY_500")

    def _bag_cell_click(self, idx):
        inv = self.game.get_current_member().get_inventory()
        item = inv.get(idx)
        if not item:
            self._show_toast("该桥位为空")
            return
        item_type = item.get("type", "item")
        if item_type == "weapon":
            result = self.game.player.equip_item(idx)
            if result[0]:
                self.game.add_log(f"装备武器: {result[1]}")
            else:
                self.game.add_log(f"装备失败: {result[1]}")
        elif item_type == "armor":
            result = self.game.player.equip_item(idx)
            if result[0]:
                self.game.add_log(f"装备护甲: {result[1]}")
            else:
                self.game.add_log(f"装备失败: {result[1]}")
        elif item_type == "novelty":
            # Show use/sell dialog
            self._use_novelty_in_bag(idx)
        else:
            self._show_toast("暂不能操作该物品")
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
        mats = ["木材", "铁矿", "皮革", "石头"]
        mat_buy_prices = {"木材": 4, "铁矿": 6, "皮革": 4, "石头": 2}
        mat_sell_prices = {"木材": 2, "铁矿": 3, "皮革": 2, "石头": 1}
        self._mat_buy_btns = {}
        self._mat_sell_btns = {}
        for mat in mats:
            ctr = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(mat, size=13, weight=ft.FontWeight.BOLD),
                        self._ref(f"mat_{mat}_cnt", ft.Text("x0", size=12, color=Cs("GREY_400"))),
                    ], spacing=8),
                    ft.Row([
                        ft.Text(f"卖: {mat_sell_prices[mat]}G / 买: {mat_buy_prices[mat]}G", size=11, color=Cs("GREY_500")),
                    ], spacing=12),
                    ft.Row([
                        self._ref(f"mat_{mat}_buy_10", ft.Button(f"买10({mat_buy_prices[mat]*10}G)", scale=0.75, on_click=lambda e, m=mat: self._buy_mat(m, 10))),
                        self._ref(f"mat_{mat}_sell_10", ft.Button(f"卖10({mat_sell_prices[mat]*10}G)", scale=0.75, on_click=lambda e, m=mat: self._sell_mat(m, 10))),
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
        mats = ["木材", "铁矿", "皮革", "石头"]
        for mat in mats:
            cnt_lbl = self._refs.get(f"mat_{mat}_cnt")
            if cnt_lbl:
                cnt_lbl.value = "x" + str(self.game.resources.get(mat, 0))


    def _build_tavern_tab(self):
        self._ref("tavern_gold_lbl",
                  ft.Text("\U0001fa99 100G", size=13, weight=ft.FontWeight.BOLD))
        self._ref("tavern_timer_lbl", ft.Text("刷新: --:--", size=12))
        self._ref("tavern_roster_ctr", ft.Column([], spacing=4, scroll="auto"))
        self._ref("team_manage_ctr", ft.Column([], spacing=4, scroll="auto"))
        ctr = ft.Column([
            ft.Container(
                content=ft.Row([
                    self._refs["tavern_gold_lbl"],
                    self._refs["tavern_timer_lbl"],
                    ft.Container(expand=True),
                    ft.Button("\U0001f504 刷新 (50G)", scale=0.85,
                                       on_click=self._tavern_refresh),
                ], spacing=8),
                padding=6, bgcolor=Cs("BROWN_900"),
            ),
            ft.Text("-- 可招募角色 --",
                    size=13, weight=ft.FontWeight.BOLD),
            self._refs["tavern_roster_ctr"],
            ft.Divider(),
            ft.Text("-- 队伍管理 --",
                    size=13, weight=ft.FontWeight.BOLD),
            self._refs["team_manage_ctr"],
        ], scroll="auto", spacing=4)
        return ft.Container(content=ctr, padding=6)

    def _build_farm_tab(self):
        self._ref("farm_count_lbl", ft.Text("\U0001f331 我的农场: 0/10", size=13))
        self._ref("farm_plants_ctr", ft.Column([], spacing=4, scroll="auto"))
        self._ref("farm_seeds_ctr", ft.Column([], spacing=4, scroll="auto"))
        for pd in get_plant_catalog():
            rc = PLANT_RARITY_COLORS.get(pd["rarity"], "#888888")
            text = (f"{pd['icon']} {pd['name']}  "
                    f"产{int(pd['harvest_gold'])}G/{int(pd['harvest_interval_s'])}s  "
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
            ft.Text("-- 种子商店 --",
                    size=13, weight=ft.FontWeight.BOLD),
            ft.Container(content=self._refs["farm_seeds_ctr"],
                         border=ft.Border.all(1, Cs("OUTLINE_VARIANT")),
                         border_radius=4, padding=4, expand=True),
        ], scroll="auto", spacing=4)
        return ft.Container(content=ctr, padding=6)

    def _build_factory_tab(self):
        self._ref("factory_status_lbl",
                  ft.Text("\U0001f3ed 未建造", size=13, color=ft.Colors.RED))
        self._ref("factory_info_lbl",
                  ft.Text("建造费用: " + ", ".join(f"{k}{v}" for k, v in FACTORY_BUILD_COST.items()) + "  |  基础利润: 50G/5min", size=11))
        self._ref("factory_build_btn",
                  ft.Button("\U0001f3d7 建造工厂", on_click=self._build_factory_tab_action))
        self._ref("factory_depts_ctr", ft.Column([], spacing=4))
        self._ref("factory_workers_lbl",
                  ft.Text("劳工: 0/5  (每人+15%, 80G/人)", size=12))

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
                                  self._ref(f"dept_status_{dept['id']}", ft.Text("未解锁", size=11, color=ft.Colors.RED)),
                              ], tight=True),
                              ft.Text(f"{dept['desc']}  |  费用: {cost_str}", size=10, color=Cs("GREY_600")),
                              self._ref(f"dept_btn_{dept['id']}",
                                        ft.Button(f"解锁 {dept['name']}", scale=0.8,
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
            ft.Text("-- 部门 --", size=13, weight=ft.FontWeight.BOLD),
            ft.Container(content=self._refs["factory_depts_ctr"],
                         border=ft.Border.all(1, Cs("OUTLINE_VARIANT")),
                         border_radius=4, padding=4),
            ft.Divider(),
            self._refs["factory_workers_lbl"],
            ft.Row([
                ft.Button("+ 雇佣", scale=0.85, on_click=self._hire_factory_worker),
                ft.Button("- 解雇", scale=0.85, on_click=self._fire_factory_worker),
            ], spacing=8),
        ], scroll="auto", spacing=4)
        return ft.Container(content=ctr, padding=6)

    # ─── Bottom Bar ──────────────────────────────────────────────
    def _build_bottom_bar(self):
        self.page.add(ft.Container(
            content=ft.Row([
                ft.Container(expand=True),
                ft.Button("\U0001f4be 存档", on_click=self._save),
                ft.Button("\U0001f4c2 读档", on_click=self._load),
                ft.Button("❓ 帮助", on_click=self._show_help),
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
            self._refresh_materials()
            if len(self.game.logs) != last_log_len:
                self._refresh_log()
                last_log_len = len(self.game.logs)
                battle_log_len = len(self.game.logs)
            elif self.game.is_battling and len(self.game.logs) != battle_log_len:
                self._refresh_log()
                battle_log_len = len(self.game.logs)
            try:
                self.page.update()
            except Exception:
                pass

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
        self._refs["kills_label"].value = f"击杀: {g.player.kill_count}"

        for res, val in g.resources.items():
            ref = self._refs.get(f"res_{res}")
            if ref:
                ref.value = str(val)

        team = g.get_team()
        for i, btn in enumerate(self.team_btns):
            if i < len(team):
                m = team[i]
                btn.content = ft.Text(f"{m.role_name}\nLv.{m.level}", size=14, weight=ft.FontWeight.W_500)
                bg = Cs("ORANGE_600") if i == g.current_member_idx else (Cs("GREEN_600") if i == 0 else Cs("DEEP_PURPLE_600"))
                btn.style = ft.ButtonStyle(bgcolor=bg)
            else:
                btn.content = ft.Text("空位", size=14, weight=ft.FontWeight.W_500)
                btn.style = ft.ButtonStyle(bgcolor=Cs("GREY_600"))

        max_hp = p.get_max_hp_with_bonus()
        self._refs["hero_name_lbl"].value = f"\U0001f9d9 {p.role_name} Lv.{p.level}"
        self._refs["hp_lbl"].value = f"生命: {p.hp}/{max_hp}"
        self._refs["atk_lbl"].value = f"攻击: {p.get_total_attack()}"
        self._refs["def_lbl"].value = f"防御: {p.get_total_defense()}"
        self._refs["crit_lbl"].value = f"CRIT: {p.get_crit_rate()}%"
        self._refs["exp_lbl"].value = f"经验: {p.exp}/{p.level * 100}"
        wn = p.weapon["name"] if p.weapon and isinstance(p.weapon, dict) else "None"
        an = p.armor["name"] if p.armor and isinstance(p.armor, dict) else "None"
        self._refs["wpn_lbl"].value = f"武器: {wn}"
        self._refs["arm_lbl"].value = f"护甲: {an}"

        self._refs["map_lbl"].value = g.current_map
        for mname in get_all_maps().keys():
            btn = self._refs.get(f"map_btn_{mname}")
            if btn:
                if mname in g.unlocked_maps:
                    btn.content = ft.Text(mname, size=14, weight=ft.FontWeight.W_500)
                    btn.style = ft.ButtonStyle(bgcolor=Cs("GREEN_600"), color=ft.Colors.WHITE)
                else:
                    cost = get_all_maps()[mname].get("unlock_cost", 0)
                    btn.content = ft.Text(f"{mname}({cost}G)", size=14, weight=ft.FontWeight.W_500)
                    btn.style = ft.ButtonStyle(bgcolor=Cs("GREY_600"), color=ft.Colors.WHITE)

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
            "战中..." if g.is_battling else "⚔ 战斗", size=13)
        self._refs["auto_status_lbl"].value = "自动: 开" if g.auto_battle else "自动: 关"
        self._refs["auto_status_lbl"].color = ft.Colors.GREEN_600 if g.auto_battle else Cs("GREY_500")
        self._refs["auto_btn"].content = ft.Text(
            "⏹ 停止" if g.auto_battle else "⚡ 自动战斗", size=12)
        self._refs["auto_btn"].style = ft.ButtonStyle(
            bgcolor=Cs("RED_600") if g.auto_battle else Cs("ORANGE_600"))
        self._refs["potions_lbl"].value = f"\U0001f9ea 药水: x{p.potions}"

        # 建筑实例卡片列表（重新构建）
        for bname in get_all_building_names():
            levels = g.building_levels.get(bname, [])
            cnt_ref = self._refs.get(f"bld_count_{bname}")
            if cnt_ref:
                cnt_ref.value = f"x{len(levels)}"
            inst_ctr = self._refs.get(f"bld_instances_{bname}")
            if inst_ctr:
                inst_ctr.controls.clear()
                cfg = BUILDING_CONFIGS[bname]
                workers_list = g.building_workers.get(bname, [])
                for idx, lvl in enumerate(levels):
                    w = workers_list[idx] if idx < len(workers_list) else 0
                    max_w = cfg.get_max_workers(lvl)
                    out = cfg.get_output(lvl, w)
                    iv = cfg.get_interval(lvl)
                    inst_ctr.controls.append(
                        self._build_instance_card(bname, idx, lvl, w, max_w, out, iv))
                inst_ctr.update()

        for wname, btn in self.wonder_btns.items():
            if wname in g.wonders:
                btn.content = ft.Text(f"✅ {wname}", size=12)
                btn.disabled = True

        # 更新农场状态
        flbl = self._refs.get("farm_count_lbl")
        if flbl:
            flbl.value = f"\U0001f331 我的农场: {len(g.plants)}/10"

        # 更新植物列表
        fctr = self._refs.get("farm_plants_ctr")
        if fctr:
            fctr.controls.clear()
            for plant in g.plants:
                pd = get_plant_by_id(plant["plant_id"])
                if pd:
                    status_info = self.game.get_plant_status(plant["id"])
                    if status_info:
                        if status_info["adult"]:
                            status = "\U0001f7e2 可收获"
                            color = Cs("GREEN_600")
                            btn = ft.Button("收获", scale=0.8,
                                          on_click=lambda e, p=plant: self._harvest_plant(p))
                        else:
                            status = f"{status_info['progress']}"
                            color = Cs("ORANGE_600")
                            btn = ft.Row([
                                ft.Text("种植中", size=11, color=Cs("GREY_500")),
                                ft.Button("⚡", scale=0.7,
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
                fsl.value = f"\U0001f3ed 运营中 | 借率: x{bonus:.1f} | {profit}G/{int(FACTORY_BASE_INTERVAL_S)}s"
                fsl.color = ft.Colors.GREEN_700
            else:
                fsl.value = "\U0001f3ed 未建造"
                fsl.color = ft.Colors.RED
        fbb = self._refs.get("factory_build_btn")
        if fbb:
            fbb.disabled = self.game.factory is not None
        fwl = self._refs.get("factory_workers_lbl")
        if fwl:
            fwl.value = f"劳工: {self.game.factory_workers}/5  (每人+15%, 80G/人)"
        for dept in FACTORY_DEPTS:
            if dept["id"] == "basic":
                continue
            st = self._refs.get(f"dept_status_{dept['id']}")
            bt = self._refs.get(f"dept_btn_{dept['id']}")
            if st:
                if dept["id"] in self.game.factory_departments:
                    st.value = "✅ 已解锁"
                    st.color = ft.Colors.GREEN_700
                else:
                    st.value = "未解锁"
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
            tl.value = f"刷新: {m:02d}:{s:02d}"
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
                        ft.Text(f"武器: {wn}", size=10, color=Cs("GREY_600")),
                        ft.Button("招募", scale=0.8, on_click=lambda e, c=ch: self._recruit_member(c)),
                    ], spacing=2), padding=4, border=ft.Border.all(1, Cs("OUTLINE_VARIANT")), border_radius=4))
            if not roster:
                rctr.controls.append(ft.Text("暂无可招募角色", size=12, color=Cs("GREY_500")))
        # 队伍管理列表
        tctr = self._refs.get("team_manage_ctr")
        if tctr:
            tctr.controls.clear()
            team = g.get_team()
            for i, m in enumerate(team):
                tag = " ★队长" if i == 0 else f" #{i}"
                wn = m.weapon["name"] if m.weapon and isinstance(m.weapon, dict) else "无"
                tctr.controls.append(ft.Container(
                    content=ft.Row([
                        ft.Text(f"{m.role_name} Lv.{m.level}{tag}", size=12, weight=ft.FontWeight.BOLD, expand=True),
                        ft.Text(f"HP:{m.hp}/{m.get_max_hp_with_bonus()}", size=11),
                        ft.Button("切换", scale=0.75,
                                  on_click=lambda e, idx=i: self._switch_to(idx)) if i != g.current_member_idx else None,
                        ft.Button("踢出", scale=0.75,
                                  on_click=lambda e, idx=i: self._kick_member_ui(idx)) if i > 0 else None,
                    ], spacing=4, alignment=ft.alignment.Alignment(-1, 0)),
                    padding=4, border=ft.Border.all(1, Cs("OUTLINE_VARIANT")), border_radius=4,
                    bgcolor="#fff8e1" if i == g.current_member_idx else None))

        # 刷新背包和材料(修复战斗掉落后UI不同步)
        self._refresh_bag()
        self._refresh_materials()

    # ─── Actions ────────────────────────────────────────────────
    def _do_battle(self, e=None):
        if self.game.is_battling:
            self.game.add_log("战中中...")
            return
        enemy, is_boss = get_random_enemy(self.game.current_map)
        if not enemy:
            self.game.add_log("没有敌人!")
            return
        self.game.current_enemy = enemy
        self.game.current_enemy_is_boss = is_boss
        threading.Thread(target=self._battle_thread, args=(enemy, is_boss), daemon=True).start()

    def _battle_thread(self, enemy, is_boss):
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
            self.game.add_log("⚡ 自动战斗 ON!")
            self.game.start_auto_battle()
        else:
            self.game.add_log("⏹ 自动战斗 OFF.")

    def _refresh_enemy(self, e=None):
        if self.game.is_battling:
            self.game.add_log("战中无法刷新!")
            return
        cost = 5 + random.randint(0, 5)
        if self.game.player.gold < cost:
            self.game.add_log("金币不足! 需要 " + str(cost) + "G")
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
            self.game.add_log(f"切换到: {self.game.get_current_member().role_name}")

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

    def _upgrade_building(self, name, idx=None):
        levels = self.game.building_levels.get(name, [])
        if not levels:
            self.game.add_log("先建造!")
            return
        if idx is None:
            idx = len(levels) - 1
        ok, msg = self.game.upgrade_building(name, idx)
        self.game.add_log(f"{name} #{idx+1} 升级成功!" if ok else f"升级: {msg}")
        self._refresh_all_ui()

    def _build_wonder(self, name):
        ok, msg = self.game.build_wonder(name)
        self.game.add_log(msg)

    def _buy_weapon(self, wpn):
        ok, msg = self.game.buy_weapon(wpn)
        self.game.add_log(f"购买武器: {msg}" if ok else f"购买失败: {msg}")

    def _buy_armor(self, arm):
        ok, msg = self.game.buy_armor(arm)
        self.game.add_log(f"购买护甲: {msg}" if ok else f"购买失败: {msg}")

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
        ok, msg = self.game.buy_department(dept_id)
        self.game.add_log(msg)

    def _hire_factory_worker(self, e=None):
        ok, msg = self.game.hire_factory_worker()
        self.game.add_log(msg)

    def _fire_factory_worker(self, e=None):
        ok, msg = self.game.fire_factory_worker()
        self.game.add_log(msg)

    def _hire_worker(self, building_name, idx=None):
        levels = self.game.building_levels.get(building_name, [])
        if not levels:
            self.game.add_log("建筑未建造")
            return
        if idx is None:
            idx = len(levels) - 1
        ok, msg = self.game.hire_worker(building_name, idx)
        self.game.add_log(msg)
        self._refresh_all_ui()

    def _fire_worker(self, building_name, idx=None):
        levels = self.game.building_levels.get(building_name, [])
        if not levels:
            return
        if idx is None:
            idx = len(levels) - 1
        ok, msg = self.game.fire_worker(building_name, idx)
        self.game.add_log(msg)
        self._refresh_all_ui()

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
        self.game.add_log(f"\U0001f4be 已存档!")
        self._show_toast("存档成功!")

    def _load(self, e=None):
        if not os.path.exists(SAVE_PATH):
            self.game.add_log("没有存档文件!")
            return
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.game.resources = data.get("resources", {})
        self.game.buildings = data.get("buildings", {})
        self.game.building_levels = data.get("building_levels", {})
        self.game.building_workers = data.get("building_workers", {})
        self.game.player.from_dict(data.get("player", {}))
        self.game.current_map = data.get("current_map", "傲来国")
        self.game.unlocked_maps = set(data.get("unlocked_maps", ["傲来国"]))
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
        self.game.add_log("\U0001f4c2 读档成功!")
        self._show_toast("读档成功!")

    def _show_help(self, e=None):
        self.page.dialog = ft.AlertDialog(
            title=ft.Text("帮助"),
            content=ft.Text(
                "勇者工坊 v5.1\n\n"
                "⚔ 战斗: 队伍全员随机攻击\n"
                "⚡ 自动: 持续战斗\n"
                "\U0001f3d7 建造: 消耗资源\n"
                "\U0001f5fa 地图: 切换地图\n"
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
