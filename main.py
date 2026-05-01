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
from modules.maps import get_all_maps, get_random_enemy, get_all_enemies
from modules.inventory import NOVELTY_ITEMS, NOVELTY_RARITY_COLORS, NOVELTY_RARITY_NAMES
from modules.plants import get_plant_catalog, get_plant_by_id, PLANT_RARITY_COLORS, PLANT_RARITY_NAMES
from modules.ranch import RANCH_CATALOG
from modules.forge import (FORGE_RECIPES, FORTIFY_CONFIG, PROTECT_CHARM_COST,
                            FORGE_RARITY_COLORS, get_all_forge_recipes,
                            get_fortify_info, get_forge_recipes_by_rarity)
from modules.tavern import generate_tavern_roster
from modules.factory import DEPARTMENTS as FACTORY_DEPTS, FACTORY_BUILD_COST, calc_factory_bonus as calc_fb, FACTORY_BASE_PROFIT, FACTORY_BASE_INTERVAL_S
from modules.codex import CODEX_BOOKS

SAVE_PATH = "D:\\pyproject\\hero_workshop\\save.json"
I = ft.icons.Icons  # Flet 0.84: icons are at ft.icons.Icons.XXX
RARITY_COLORS = ["#cccccc", "#4FC3F7", "#BA68C8", "#FFA726", "#EF5350"]
RANCH_RARITY_COLORS = {1: "#4caf50", 2: "#2196f3", 3: "#9c27b0", 4: "#ff9800", 5: "#f44336"}
MONSTER_RARITY_COLORS = {1: "#4caf50", 2: "#2196f3", 3: "#9c27b0", 4: "#ff9800", 5: "#f44336"}

# ═══════════════ 视觉常量 ═══════════════
# 字体层级
F_XS, F_SM, F_BASE, F_MD, F_LG, F_XL, F_XXL = 10, 11, 12, 13, 14, 16, 18
# 主题色
CLR_PRIMARY = "#1565C0"
CLR_ACCENT = "#B8860B"
CLR_SECTION_BG = "#F8F9FA"
CLR_CARD_BG = "#FFFFFF"
CLR_BODY_BG = "#F0F2F5"

def Cs(name):
    return getattr(ft.Colors, name, ft.Colors.GREY_500)

def section_header(text, icon=""):
    """统一区域标题"""
    return ft.Container(
        content=ft.Row([
            ft.Text(f"{icon} {text}", size=F_MD, weight=ft.FontWeight.BOLD,
                    color="#37474F"),
        ]),
        padding=ft.Padding.only(left=4, top=8, bottom=6),
    )

def styled_card(content, padding=8, accent_left=None, expand=False):
    """统一卡片容器：白底、微阴影、圆角、可选左侧强调色"""
    border = None
    if accent_left:
        border = ft.Border.only(left=ft.BorderSide(color=accent_left, width=3))
    return ft.Container(
        content=content,
        padding=padding,
        bgcolor=CLR_CARD_BG,
        border_radius=8,
        border=border,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=4, color="#18000000"),
        expand=expand,
    )

def divider_h():
    return ft.Container(height=1, bgcolor="#E8ECF0")

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
        self._ref("kills_label", ft.Text("击杀: 0", size=F_SM, color=Cs("GREY_400")))
        self._ref("gold_label", ft.Text("\U0001fa99 100", size=F_MD, weight=ft.FontWeight.BOLD, color=CLR_ACCENT))
        ab = ft.AppBar(
            title=ft.Text("⚔ 勇者工坊 v5.1", size=F_XL, weight=ft.FontWeight.BOLD),
            bgcolor=CLR_PRIMARY,
            color=ft.Colors.WHITE,
            actions=[
                self._refs["kills_label"],
                ft.Container(width=16),
                ft.Container(
                    content=self._refs["gold_label"],
                    bgcolor="#FFFFFF20",
                    border_radius=20,
                    padding=ft.Padding.only(left=12, right=12, top=4, bottom=4),
                ),
                ft.Container(width=8),
                ft.IconButton(icon=I.MENU, icon_size=20, icon_color=ft.Colors.WHITE,
                              tooltip="菜单", on_click=lambda e: self._show_menu(e)),
            ],
        )
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
        col = ft.Column(spacing=2, expand=True)

        # Resources — styled card
        res_header = ft.Row([
            ft.Text("\U0001f4e6 资源", size=F_MD, weight=ft.FontWeight.BOLD, color="#37474F"),
        ])
        res_rows = []
        MATERIALS = [("木材", "\U0001f332"), ("铁矿", "⛏️"),
                     ("皮革", "\U0001f9e4"), ("石头", "⛰️")]
        for name, icon in MATERIALS:
            res_rows.append(ft.Row([
                ft.Text(f"{icon} {name}:", size=F_BASE, expand=2),
                self._ref(f"res_{name}", ft.Text("0", size=F_MD, weight=ft.FontWeight.BOLD, expand=1)),
                ft.IconButton(icon=I.REMOVE, icon_size=14, on_click=lambda e, n=name: self._sell_mat(n, 1)),
                ft.IconButton(icon=I.ADD, icon_size=14, on_click=lambda e, n=name: self._buy_mat(n, 1)),
            ], spacing=1, tight=True))
        res_inner = ft.Column([res_header, divider_h()] + res_rows, spacing=4)
        col.controls.append(styled_card(res_inner, padding=ft.Padding.all(10), accent_left=CLR_PRIMARY))

        # Buildings
        col.controls.append(section_header("\U0001f3d7 建筑"))
        self.building_cards = ft.Column(spacing=4, scroll="auto")
        col.controls.append(self.building_cards)
        for bname in get_all_building_names():
            self.building_cards.controls.append(self._build_building_card(bname))

        # Wonders
        col.controls.append(section_header("✨ 奇观"))
        self.wonder_cards = ft.Column(spacing=3, scroll="auto")
        col.controls.append(self.wonder_cards)
        for wname in get_wonder_names():
            self.wonder_cards.controls.append(self._build_wonder_card(wname))

        ret = self._ref("left_panel", ft.Container(content=col, width=self._left_width, expand=True, padding=6, bgcolor=CLR_BODY_BG))

        return ret

    def _build_instance_card(self, name, idx, level, workers, max_workers, output, interval):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(f"#{idx+1} Lv{level}", size=F_XS, expand=True, color="#546E7A"),
                    ft.Text(f"{output}/{interval}s", size=F_XS, color="#1565C0"),
                ], spacing=2, tight=True),
                ft.Row([
                    ft.OutlinedButton("升级", scale=0.7,
                                      on_click=lambda e, n=name, i=idx: self._upgrade_building(n, i)),
                    ft.Text(f"工:{workers}/{max_workers}", size=F_XS, expand=1, color=Cs("GREY_600")),
                    ft.IconButton(icon=I.REMOVE, icon_size=12,
                                   on_click=lambda e, n=name, i=idx: self._fire_worker(n, i)),
                    ft.IconButton(icon=I.ADD, icon_size=12,
                                   on_click=lambda e, n=name, i=idx: self._hire_worker(n, i)),
                ], spacing=1, tight=True),
            ], spacing=2),
            padding=ft.Padding.only(left=6, right=4, top=3, bottom=3),
            border_radius=4,
            bgcolor="#F5F7FA",
            margin=ft.Margin.only(left=8, bottom=1),
        )

    @staticmethod
    def _fmt_build_cost(name):
        from modules.buildings import get_building_config
        cfg = get_building_config(name)
        if not cfg or not cfg.build_cost:
            return ""
        return "需要: " + ", ".join(f"{m}×{v}" for m, v in cfg.build_cost.items())

    def _build_building_card(self, name):
        """返回建筑标题卡片 + 实例容器。实例卡片在建造/升级时动态刷新。"""
        instance_ctr = self._ref(f"bld_instances_{name}", ft.Column(spacing=1))
        return ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Text(name, size=F_BASE, weight=ft.FontWeight.BOLD, expand=True),
                    self._ref(f"bld_count_{name}", ft.Text("x0", size=F_SM, color=Cs("GREY_500"))),
                ]),
                padding=ft.Padding.only(left=6, top=4, bottom=4),
                bgcolor="#E3F2FD",
                border_radius=ft.BorderRadius.only(top_left=6, top_right=6),
            ),
            instance_ctr,
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("建造", size=F_XS, expand=1),
                        ft.Button("建造 +1", scale=0.75,
                                  on_click=lambda e, n=name: self._build_building(n)),
                    ], spacing=4, tight=True),
                    ft.Text(self._fmt_build_cost(name), size=F_XS, color=Cs("GREY_500")),
                ], spacing=2),
                padding=ft.Padding.only(left=4, right=4, top=2, bottom=4),
            ),
        ], spacing=0)

    def _build_wonder_card(self, name):
        wonder_btn = ft.Button("建造奇观", scale=0.85, on_click=lambda e, n=name: self._build_wonder(n))
        self.wonder_btns[name] = wonder_btn
        return styled_card(
            ft.Column([
                ft.Row([
                    ft.Text(name, size=F_BASE, weight=ft.FontWeight.BOLD, expand=True),
                    self._ref(f"wonder_count_{name}", ft.Text("x0", size=F_SM, color=Cs("GREY_500"))),
                ]),
                self._ref(f"wonder_info_{name}", ft.Text("未建造", size=F_SM, color=Cs("GREY_400"))),
                ft.Container(content=wonder_btn, alignment=ft.alignment.Alignment(0.5, 0.5)),
            ], spacing=3),
            padding=8, accent_left="#FFA726",
        )

    def _build_center(self):
        col = ft.Column(spacing=6, expand=True)

        # Team row
        team_row = ft.Row(spacing=6)
        self.team_btns = []
        for i in range(3):
            btn = ft.Button(
                ft.Text("..." * 3, size=F_MD, weight=ft.FontWeight.W_500), width=110,
                on_click=lambda e, idx=i: self._switch_member(idx)
            )
            self.team_btns.append(btn)
            team_row.controls.append(btn)
        team_row.controls.append(
            ft.Button(ft.Text("\U0001f37a 酒馆", size=F_MD, weight=ft.FontWeight.W_500),
                      on_click=self._open_tavern_tab)
        )
        col.controls.append(styled_card(
            ft.Column([
                ft.Text("\U0001f465 队伍", size=F_MD, weight=ft.FontWeight.BOLD, color="#37474F"),
                team_row,
            ], spacing=4),
            padding=8,
        ))

        # Hero stats
        self.hero_stats = ft.Column(spacing=1)
        col.controls.append(styled_card(
            ft.Column([
                self._ref("hero_name_lbl", ft.Text("\U0001f9d9 勇者 Lv.1", size=F_LG, weight=ft.FontWeight.BOLD, color=CLR_PRIMARY)),
                divider_h(),
                self.hero_stats,
            ], spacing=4),
            padding=8, accent_left=CLR_PRIMARY,
        ))
        self._init_hero_stats()

        # Map + Enemy
        map_btns_row = ft.Row(wrap=True, spacing=6)
        for mname in get_all_maps().keys():
            btn = ft.Button(ft.Text(mname, size=F_MD, weight=ft.FontWeight.W_500),
                             on_click=lambda e, m=mname: self._change_map(m),
                             style=ft.ButtonStyle(bgcolor=Cs("BLUE_600"), color=ft.Colors.WHITE))
            map_btns_row.controls.append(btn)
            self._ref(f"map_btn_{mname}", btn)

        col.controls.append(styled_card(
            ft.Column([
                ft.Text("\U0001f5fa 地图", size=F_MD, weight=ft.FontWeight.BOLD, color="#37474F"),
                self._ref("map_lbl", ft.Text("傲来国", size=F_MD, color=Cs("BLUE_700"), weight=ft.FontWeight.W_500)),
                map_btns_row,
                divider_h(),
                self._ref("enemy_display",
                          ft.Text("\U0001f480 ??? HP:?? ATK:??", size=F_MD, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_800)),
                ft.Row([
                    ft.Button("\U0001f504 刷新敌人", on_click=self._refresh_enemy),
                    self._ref("refresh_cost_lbl", ft.Text("", size=F_BASE)),
                ], spacing=4),
            ], spacing=4),
            padding=8,
        ))

        # Battle buttons
        col.controls.append(styled_card(
            ft.Column([
                self._ref("battle_btn",
                          ft.Button("⚔ 战斗", width=200, height=45,
                                            on_click=self._do_battle,
                                            style=ft.ButtonStyle(bgcolor="#C62828", color=ft.Colors.WHITE))),
                self._ref("auto_btn",
                          ft.Button("⚡ 自动战斗", width=200,
                                            on_click=self._toggle_auto,
                                            style=ft.ButtonStyle(bgcolor=Cs("ORANGE_600")))),
                self._ref("auto_status_lbl",
                          ft.Text("自动: 关", size=F_SM, color=Cs("GREY_500"))),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
            padding=10,
        ))

        # Potions
        thresh_opts = ["OFF", "30%", "50%", "80%"]
        self._ref("auto_potion_dd", ft.Dropdown(
            options=[ft.dropdown.Option(o) for o in thresh_opts],
            value="OFF", width=80, height=32,
        ))
        self._ref("auto_potion_lbl", ft.Text("已关闭", size=F_SM, color=Cs("GREY_500")))
        col.controls.append(styled_card(
            ft.Column([
                ft.Text("\U0001f9ea 药水", size=F_MD, weight=ft.FontWeight.BOLD, color="#37474F"),
                ft.Row([
                    ft.Button("购买 (25G)", scale=0.85, on_click=self._buy_potion),
                    self._ref("potions_lbl", ft.Text("x0", size=F_MD)),
                    ft.Button("使用 +20HP", scale=0.85, on_click=self._use_potion),
                ], spacing=6),
                ft.Row([
                    ft.Text("自动 HP<", size=F_BASE),
                    self._refs["auto_potion_dd"],
                    self._refs["auto_potion_lbl"],
                ], spacing=4, alignment=ft.MainAxisAlignment.START),
            ], spacing=4),
            padding=8,
        ))

        # Battle log
        self.battle_log_view = ft.ListView(expand=True, spacing=2, auto_scroll=True)
        col.controls.append(styled_card(
            ft.Column([
                ft.Text("\U0001f4cb 战斗日志", size=F_MD, weight=ft.FontWeight.BOLD, color="#C62828"),
                ft.Container(content=self.battle_log_view,
                             bgcolor="#FFF5F5", border_radius=4, padding=6, expand=True),
            ], spacing=4),
            padding=8, expand=True,
        ))
        # Misc log (farm/ranch/system)
        self.misc_log_view = ft.ListView(expand=True, spacing=2, auto_scroll=True)
        col.controls.append(styled_card(
            ft.Column([
                ft.Text("\U0001f4dc 杂项日志", size=F_MD, weight=ft.FontWeight.BOLD, color="#37474F"),
                ft.Container(content=self.misc_log_view,
                             bgcolor="#F5F7FA", border_radius=4, padding=6, expand=True),
            ], spacing=4),
            padding=8, expand=True,
        ))
        self._restore_auto_potion_ui()

        # Add dropdown change handler after UI is built
        def on_auto_potion_change(e):
            self._on_auto_potion_change()
        self._refs["auto_potion_dd"].on_change = on_auto_potion_change

        return ft.Container(content=col, expand=True, padding=6, bgcolor=CLR_BODY_BG)

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
            ctrl = self._ref(key, ft.Text(default, size=F_BASE))
            self.hero_stats.controls.append(ctrl)

    # ─── Right Panel ─────────────────────────────────────────────
    def _build_right(self):
        TABS = [
            ("⚔ 武器", I.BUILD),
            ("\U0001f6e1 护甲", I.SHIELD),
            ("\U0001f381 杂货", I.REDEEM),
            ("\U0001f392 背包", I.WORK),
            ("⭐ 材料", I.DIAMOND),
            ("\U0001f37a 酒馆", I.LOCAL_DRINK),
            ("\U0001f331 农场", I.GRASS),
            ("\U0001f3ed 工厂", I.FACTORY),
            ("\U0001f43e 牧场", I.PETS),
            ("\U0001f528 锻造", I.BUILD_CIRCLE),
        ]
        self._tab_bar = ft.TabBar(
            tabs=[ft.Tab(label, icon=icon) for label, icon in TABS],
            scrollable=True,
            indicator_color=CLR_PRIMARY,
            label_color=CLR_PRIMARY,
            unselected_label_color=Cs("GREY_500"),
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
            self._build_ranch_tab(),
            self._build_forge_tab(),
        ]
        self._tab_view = ft.TabBarView(controls=self._tab_contents, expand=True)
        self.right_tabs = ft.Tabs(
            content=ft.Column([self._tab_bar, self._tab_view], spacing=0, expand=True),
            length=10,
            expand=True,
        )
        return self._ref("right_panel_ref", ft.Container(
            content=self.right_tabs, width=self._right_width, expand=True,
            padding=ft.Padding.only(top=4, left=2, right=2, bottom=2),
        ))

    def _build_main_city_tab(self) -> ft.Stack:
        """白玉京主城 — 仙侠地图质感 v2"""

        CARD_W = 155
        CARD_H = 138
        ROW_SPACING = 14

        # ── 配色 ───────────────────────────────────────────────────
        BG_TOP = "#060E1C"
        BG_MID = "#0A1E36"
        BG_BOT = "#112244"
        ACCENT = "#C8A44A"  # 金色
        TEXT_W = "#D8EEFF"  # 主文字
        TEXT_D = "#7AAAC8"  # 副文字
        GLOW = "#1A6FCC"  # 蓝辉光

        # ── Layer 1: 深蓝渐变背景 ──────────────────────────────────
        bg = ft.Container(expand=True, gradient=ft.LinearGradient(
            colors=[BG_TOP, BG_MID, BG_BOT],
            begin=ft.alignment.Alignment(0, -1), end=ft.alignment.Alignment(0, 1)))

        # ── Layer 2: 云雾层（Stack 内绝对定位 blob）─────────────────
        def _blob(cx, cy, w, h, fill, radius_ratio=0.5):
            """用圆角 Container 模拟云团 blob"""
            return ft.Container(
                left=cx - w * radius_ratio,
                top=cy - h * radius_ratio,
                width=w, height=h,
                border_radius=int(min(w, h) * radius_ratio),
                bgcolor=fill,
            )

        mist_layer = ft.Stack([
            # 底层大雾团
            _blob(80, 430, 260, 90, "#1A4080", 0.6),
            _blob(380, 460, 220, 80, "#1A4080", 0.55),
            _blob(700, 440, 280, 100, "#1A4080", 0.6),
            _blob(900, 420, 200, 70, "#1A4080", 0.5),
            # 中层雾气
            _blob(160, 280, 180, 60, "#1E5090", 0.55),
            _blob(480, 300, 200, 65, "#1E5090", 0.5),
            _blob(760, 270, 170, 55, "#1E5090", 0.55),
            # 顶层薄纱
            _blob(280, 120, 150, 50, "#2560A8", 0.5),
            _blob(620, 110, 180, 55, "#2560A8", 0.5),
            # 散落光点（小星星）
            _blob(50, 80, 6, 6, "#FFFFFF", 1.0),
            _blob(210, 60, 5, 5, "#FFFFFF", 1.0),
            _blob(450, 90, 6, 6, "#FFFFFF", 1.0),
            _blob(600, 50, 4, 4, "#FFFFFF", 1.0),
            _blob(840, 70, 5, 5, "#FFFFFF", 1.0),
            _blob(950, 55, 6, 6, "#FFFFFF", 1.0),
            _blob(1000, 95, 4, 4, "#FFFFFF", 1.0),
        ])

        # ── 建筑卡片 ───────────────────────────────────────────────
        def _card(name, subtitle, icon, accent_color):
            """单个建筑入口卡片"""
            badge = ft.Container(
                content=ft.Text(icon, size=28),
                alignment=ft.alignment.Alignment(0,0),
                padding=8,
            )
            # 卡片本体
            card = ft.Container(
                content=ft.Column([
                    badge,
                    ft.Text(name, size=13, weight=ft.FontWeight.W_600, color=accent_color),
                    ft.Text(subtitle, size=9, color=TEXT_D, text_align=ft.TextAlign.CENTER,
                            max_lines=2),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3),
                width=CARD_W, height=CARD_H,
                padding=8,
                border_radius=16,
                bgcolor="#0A1E3A",
                border=ft.Border(
                    ft.BorderSide(1, "#1E4070"),
                    ft.BorderSide(1, "#1E4070"),
                    ft.BorderSide(2, accent_color + "60"),
                    ft.BorderSide(1, "#1E4070"),
                ),
                # 外发光：多层 shadow 叠加
                shadow=ft.BoxShadow(blur_radius=20, color=accent_color + "30", offset=ft.Offset(0, 0)),
            )

            # 悬停效果
            def _on_hover(e):
                if e.data == "true":
                    card.bgcolor = "#0E2860"
                    card.shadow = ft.BoxShadow(blur_radius=30, color=accent_color + "50", offset=ft.Offset(0, 0))
                    card.border = ft.Border(
                        ft.BorderSide(1, "#1E4070"),
                        ft.BorderSide(1, "#1E4070"),
                        ft.BorderSide(3, accent_color + "CC"),
                        ft.BorderSide(1, "#1E4070"),
                    )
                else:
                    card.bgcolor = "#0A1E3A"
                    card.shadow = ft.BoxShadow(blur_radius=20, color=accent_color + "30", offset=ft.Offset(0, 0))
                    card.border = ft.Border(
                        ft.BorderSide(1, "#1E4070"),
                        ft.BorderSide(1, "#1E4070"),
                        ft.BorderSide(2, accent_color + "60"),
                        ft.BorderSide(1, "#1E4070"),
                    )
                card.update()

            card.on_hover = _on_hover
            return card

        # ── 建筑数据 ──────────────────────────────────────────────
        buildings = [
            # row 0: 北天门 + 中天殿
            dict(name="北天门", subtitle="踏云归上界\n入阙即仙乡", icon="🚪", accent_color="#60A8E0"),
            dict(name="中天殿", subtitle="四海仙朋聚\n八方消息来", icon="🏛", accent_color="#80C8A0"),
            # row 1: 璇玑阁 + 仙禽阁 + 天工坊
            dict(name="璇玑阁", subtitle="万宝归璇玑\n珍奇入画图", icon="💎", accent_color="#D8A0E8"),
            dict(name="仙禽阁", subtitle="灵兽栖云阁\n奇珍上玉台", icon="🦅", accent_color="#60E8A0"),
            dict(name="天工坊", subtitle="炉火淬神器\n天工炼奇珍", icon="⚒", accent_color="#E8A060"),
            # row 2: 瑶池宫 + 藏珍洞 + 聚元阁 + 如梦令
            dict(name="瑶池宫", subtitle="瑶池洗尘虑\n玉露润仙心", icon="🛁", accent_color="#60E8E8"),
            dict(name="藏珍洞", subtitle="洞纳乾坤物\n囊藏千万珍", icon="💰", accent_color="#E8D060"),
            dict(name="聚元阁", subtitle="聚元凝宝气\n炼器铸锋芒", icon="⬆", accent_color="#E86060"),
            dict(name="如梦令", subtitle="一枕清梦远\n半世从头来", icon="🛏", accent_color="#C8A8E8"),
        ]

        def _card_row(indices):
            return ft.Row(
                [ft.Container(_card(**buildings[i]), margin=6) for i in indices],
                spacing=0, alignment=ft.MainAxisAlignment.CENTER,
            )

        # ── 顶部题字 ─────────────────────────────────────────────
        title_bar = ft.Container(
            content=ft.Column([
                ft.Text("白玉京阙", size=26, weight=ft.FontWeight.BOLD,
                        color=ACCENT, font_family="SimHei"),
                ft.Text("白玉为阶云为伴，仙友初临白玉京",
                        size=10, color=TEXT_D, italic=True),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            alignment=ft.alignment.Alignment(0, -1),
            padding=ft.padding.only(top=14, bottom=8),
        )

        # ── 底部注释 ─────────────────────────────────────────────
        footer = ft.Container(
            content=ft.Text("点击建筑进入对应功能", size=9, color=TEXT_D + "80"),
            alignment=ft.alignment.Alignment(0, 1),
            padding=ft.padding.only(bottom=12),
        )

        # ── 组装 Stack ───────────────────────────────────────────
        content = ft.Column([title_bar, _card_row([0, 1]), _card_row([2, 3, 4]), _card_row([5, 6, 7, 8]), footer],
                            spacing=ROW_SPACING, alignment=ft.MainAxisAlignment.START)

        stack = ft.Stack(
            controls=[bg, mist_layer, content],
        )
        stack.expand = True
        return stack

    def _build_weapon_tab(self):
        items = []
        for idx, w in enumerate(WEAPONS):
            crit = f" CRIT{w['crit_rate']}%" if w["crit_rate"] > 0 else ""
            ridx = min(idx // 4, 4)
            color = RARITY_COLORS[ridx]
            items.append(ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(f"{w['name']}  ATK:{w['attack']}{crit}", size=F_BASE, color=color, weight=ft.FontWeight.W_500),
                        ft.Text(cost_str(w["cost"]), size=F_XS, color=Cs("GREY_500")),
                    ], spacing=2, expand=True),
                    ft.IconButton(icon=I.SHOPPING_CART, icon_size=18,
                                  on_click=lambda e, wpn=w: self._buy_weapon(wpn)),
                ], spacing=4),
                padding=ft.Padding.only(left=8, right=4, top=4, bottom=4),
            ))
        return ft.ListView(items, spacing=2, expand=True)

    def _build_armor_tab(self):
        items = []
        for idx, a in enumerate(ARMORS):
            hp = f" HP+{a['hp_bonus']}" if a["hp_bonus"] > 0 else ""
            ridx = min(idx // 4, 4)
            color = RARITY_COLORS[ridx]
            items.append(ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(f"{a['name']}  DEF:{a['defense']}{hp}", size=F_BASE, color=color, weight=ft.FontWeight.W_500),
                        ft.Text(cost_str(a["cost"]), size=F_XS, color=Cs("GREY_500")),
                    ], spacing=2, expand=True),
                    ft.IconButton(icon=I.SHOPPING_CART, icon_size=18,
                                  on_click=lambda e, arm=a: self._buy_armor(arm)),
                ], spacing=4),
                padding=ft.Padding.only(left=8, right=4, top=4, bottom=4),
            ))
        return ft.ListView(items, spacing=2, expand=True)

    def _build_novelty_tab(self):
        items = []
        for item in sorted(NOVELTY_ITEMS, key=lambda x: x["price"]):
            ridx = min(item.get("rarity_idx", 0), 4)
            color = NOVELTY_RARITY_COLORS[ridx]
            items.append(ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(item["name"], size=F_BASE, color=color, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{NOVELTY_RARITY_NAMES[ridx]} \xb7 {item['desc']}", size=F_XS, color=Cs("GREY_500")),
                    ], spacing=2, expand=True),
                    ft.Text(f"{item['price']}G", size=F_MD, weight=ft.FontWeight.BOLD, color=CLR_ACCENT),
                ], spacing=4),
                padding=ft.Padding.only(left=8, right=8, top=5, bottom=5),
                on_click=lambda e, it=item: self._buy_novelty(it),
            ))
        return ft.ListView(items, spacing=2, expand=True)


    def _build_bag_tab(self):
        self._ref("bag_count_lbl", ft.Text("背包: 0/20", size=F_BASE, weight=ft.FontWeight.BOLD))
        title_row = ft.Row([
            self._refs["bag_count_lbl"],
            ft.Container(expand=True),
            ft.Text("点击装备/使用 | 右键卖出", size=F_XS, color=Cs("GREY_500")),
        ], spacing=8)

        equip_ctr = styled_card(ft.Column([
            ft.Text("当前装备", size=F_BASE, weight=ft.FontWeight.BOLD, color="#37474F"),
            ft.Row([
                self._ref("eq_weapon_lbl", ft.Text("武器: 未装备", size=F_BASE)),
                ft.Container(expand=True),
                self._ref("eq_armor_lbl", ft.Text("护甲: 未装备", size=F_BASE)),
            ], spacing=12),
        ], spacing=4), padding=ft.Padding.only(left=8, right=8, top=6, bottom=6), accent_left=CLR_PRIMARY)

        self._bag_cells = []
        bag_grid = ft.GridView(
            child_aspect_ratio=3.8,
            spacing=3,
            padding=4,
        )
        for i in range(20):
            cell = ft.Container(
                content=ft.Column([
                    self._ref(f"bag_lbl_{i}", ft.Text("空", size=F_XS, color=Cs("GREY_500"), text_align="center")),
                    ft.Row([
                        self._ref(f"bag_e_{i}", ft.Text("装", size=F_XS)),
                        self._ref(f"bag_s_{i}", ft.Text("卖", size=F_XS)),
                    ], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=2),
                border=ft.Border.all(1, Cs("OUTLINE_VARIANT")),
                border_radius=4,
                padding=4,
                ink=True,
            )
            cell.data = i
            cell.on_click = lambda e, idx=i: self._bag_cell_click(idx)
            self._bag_cells.append(cell)
            bag_grid.controls.append(cell)

        return ft.Column([
            title_row,
            equip_ctr,
            ft.Container(height=4),
            bag_grid,
        ], spacing=4, expand=True)

    def _refresh_bag(self):
        inv = self.game.get_current_member().get_inventory()
        count = inv.count()
        self._refs["bag_count_lbl"].value = f"背包: {count}/20"

        # 当前装备
        m = self.game.get_current_member()
        wpn = m.weapon
        arm = m.armor
        if wpn:
            fl = wpn.get("forge_level", 0)
            ftag = f" +{fl}" if fl > 0 else ""
            self._refs["eq_weapon_lbl"].value = f"武器: {wpn['name']}{ftag}"
        else:
            self._refs["eq_weapon_lbl"].value = "武器: 未装备"
        if arm:
            fl = arm.get("forge_level", 0)
            ftag = f" +{fl}" if fl > 0 else ""
            self._refs["eq_armor_lbl"].value = f"护甲: {arm['name']}{ftag}"
        else:
            self._refs["eq_armor_lbl"].value = "护甲: 未装备"

        # 刷新格子
        for i in range(20):
            item = inv.get(i)
            lbl = self._refs.get(f"bag_lbl_{i}")
            if not lbl:
                continue
            if item:
                t = item.get("type", "item")
                fl = item.get("forge_level", 0)
                ftag = f"+{fl}" if fl > 0 else ""
                name = item["name"][:5] + ftag
                if t == "weapon":
                    lbl.value = name
                    lbl.color = Cs("BLUE_400")
                elif t == "armor":
                    lbl.value = name
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
        mats = ["木材", "铁矿", "皮革", "石头"]
        mat_icons = ["\U0001f332", "⛏️", "\U0001f9e4", "⛰️"]
        mat_buy_prices = {"木材": 4, "铁矿": 6, "皮革": 4, "石头": 2}
        mat_sell_prices = {"木材": 2, "铁矿": 3, "皮革": 2, "石头": 1}
        mat_rows = []
        for mat, icon in zip(mats, mat_icons):
            mat_rows.append(styled_card(ft.Column([
                ft.Row([
                    ft.Text(f"{icon} {mat}", size=F_MD, weight=ft.FontWeight.BOLD),
                    self._ref(f"mat_{mat}_cnt", ft.Text("x0", size=F_BASE, color=Cs("GREY_500"))),
                ], spacing=8),
                ft.Text(f"卖 {mat_sell_prices[mat]}G / 买 {mat_buy_prices[mat]}G", size=F_XS, color=Cs("GREY_500")),
                ft.Row([
                    ft.Button(f"买10 ({mat_buy_prices[mat]*10}G)", scale=0.75, on_click=lambda e, m=mat: self._buy_mat(m, 10)),
                    ft.Button(f"卖10 ({mat_sell_prices[mat]*10}G)", scale=0.75, on_click=lambda e, m=mat: self._sell_mat(m, 10)),
                ], spacing=6),
            ], spacing=4), padding=10))
        return ft.ListView(mat_rows, spacing=8, expand=True)

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
                  ft.Text("\U0001fa99 100G", size=F_MD, weight=ft.FontWeight.BOLD))
        self._ref("tavern_timer_lbl", ft.Text("刷新: --:--", size=F_SM))
        self._ref("tavern_roster_ctr", ft.Column([], spacing=4, scroll="auto"))
        self._ref("team_manage_ctr", ft.Column([], spacing=4, scroll="auto"))
        ctr = ft.Column([
            styled_card(ft.Row([
                self._refs["tavern_gold_lbl"],
                self._refs["tavern_timer_lbl"],
                ft.Container(expand=True),
                ft.Button("\U0001f504 刷新 (50G)", scale=0.85, on_click=self._tavern_refresh),
            ], spacing=8), padding=8),
            ft.Text("可招募角色", size=F_MD, weight=ft.FontWeight.BOLD, color="#37474F"),
            self._refs["tavern_roster_ctr"],
            divider_h(),
            ft.Text("队伍管理", size=F_MD, weight=ft.FontWeight.BOLD, color="#37474F"),
            self._refs["team_manage_ctr"],
        ], scroll="auto", spacing=6)
        return ft.Container(content=ctr)

    def _build_farm_tab(self):
        self._ref("farm_count_lbl", ft.Text("\U0001f331 我的农场: 0/10", size=13))
        self._ref("farm_feed_lbl", ft.Text("🌾 饲料: -", size=F_BASE, color="#795548"))
        self._ref("farm_fert_lbl", ft.Text("🧪 肥料: -", size=F_BASE, color="#6A1B9A"))
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
            ft.Row([
                self._refs["farm_count_lbl"],
                ft.Container(width=12),
                self._refs["farm_feed_lbl"],
                ft.Container(width=12),
                self._refs["farm_fert_lbl"],
            ], wrap=True, spacing=4),
            styled_card(ft.Container(content=self._refs["farm_plants_ctr"], height=180), padding=6),
            ft.Text("种子商店", size=F_MD, weight=ft.FontWeight.BOLD, color="#37474F"),
            styled_card(self._refs["farm_seeds_ctr"], padding=6, expand=True),
        ], scroll="auto", spacing=6)
        return ft.Container(content=ctr)

    def _build_ranch_tab(self):
        """牧场Tab: 商店区 / 牧场库存 / 产出仓库"""
        # 商店区
        shop_ctr = ft.Column([
            ft.Text("🐾 生物商店", size=13, weight=ft.FontWeight.BOLD),
            ft.Divider(height=1),
        ], spacing=2)
        self._ref("ranch_shop_ctr", shop_ctr)
        for creature in RANCH_CATALOG:
            ridx = min(creature.get("rarity", 1) - 1, 4)
            rcolor = RANCH_RARITY_COLORS.get(creature.get("rarity", 1), "#888888")
            price = creature.get("price", 0)
            feed = creature.get("feed_cost", 0)
            pers = creature.get("personality", "")
            text = (f"{creature.get('icon','?')} {creature.get('name','?')}  "
                    f"[{rcolor}]{creature.get('rarity_name','')}[/{rcolor}]"
                    f" {price}G  饲料{feed}G/次  {pers}")
            shop_ctr.controls.append(
                ft.ListTile(
                    title=ft.Text(f"{creature.get('icon','?')} {creature.get('name','?')}",
                                  size=12, color=rcolor, weight=ft.FontWeight.BOLD),
                    subtitle=ft.Text(f"{creature.get('rarity_name','')} · 售价{price}G · 饲料{feed}G/次 · {pers}",
                                    size=10),
                    trailing=ft.Button("购买", scale=0.75,
                                       on_click=lambda e, c=creature: self.game.buy_ranch_creature(c["id"])),
                )
            )

        # 牧场库存
        self._ref("ranch_inventory_ctr", ft.Column([], spacing=4, scroll="auto"))
        self._ref("ranch_inventory_lbl", ft.Text("🐄 牧场库存: 0", size=13, weight=ft.FontWeight.BOLD))

        # 产出仓库
        self._ref("ranch_warehouse_ctr", ft.Column([], spacing=4, scroll="auto"))
        self._ref("ranch_warehouse_lbl", ft.Text("📦 产出仓库", size=13, weight=ft.FontWeight.BOLD))

        ctr = ft.Column([
            styled_card(ft.Row([
                self._refs["ranch_inventory_lbl"],
                ft.Container(expand=True),
                self._ref("ranch_gold_lbl", ft.Text("\U0001fa99 100G", size=F_MD, color=CLR_ACCENT)),
            ], spacing=8), padding=8),
            styled_card(ft.Container(content=self._refs["ranch_inventory_ctr"], height=200), padding=6),
            ft.Text("产出仓库", size=F_MD, weight=ft.FontWeight.BOLD, color="#37474F"),
            styled_card(self._refs["ranch_warehouse_ctr"], padding=6, expand=True),
            ft.Text("生物商店", size=F_MD, weight=ft.FontWeight.BOLD, color="#37474F"),
            styled_card(ft.ListView([shop_ctr], spacing=2, expand=True), padding=6, expand=True),
        ], scroll="auto", spacing=6)
        return ft.Container(content=ctr)

    def _build_forge_tab(self):
        """锻造与强化Tab"""
        # ── 强化区域 ──
        self._ref("fortify_select_lbl", ft.Text("选择装备: 未选择", size=F_BASE))
        self._ref("fortify_info_lbl", ft.Text("", size=F_SM, color=Cs("GREY_600")))
        self._ref("fortify_cost_lbl", ft.Text("", size=F_SM, color=CLR_ACCENT))
        self._ref("fortify_btn", ft.Button("🔨 强化", scale=0.85, on_click=self._do_fortify))
        self._ref("fortify_charm_btn", ft.Button("🛡 护锻符强化", scale=0.85,
                    on_click=lambda e: self._do_fortify(e, use_charm=True)))

        equip_opts = []
        self._ref("fortify_dd", ft.Dropdown(
            options=equip_opts,
            hint_text="选择要强化的装备",
            expand=True,
        ))
        self._refs["fortify_dd"].on_change = self._on_fortify_select

        fortify_ctr = styled_card(ft.Column([
            ft.Text("【强化装备】", size=F_MD, weight=ft.FontWeight.BOLD, color="#37474F"),
            ft.Text("消耗铁矿+金币提升装备属性(+1~+10)，+6起失败掉级", size=F_XS, color=Cs("GREY_500")),
            ft.Divider(height=1),
            self._refs["fortify_dd"],
            self._refs["fortify_select_lbl"],
            self._refs["fortify_info_lbl"],
            self._refs["fortify_cost_lbl"],
            ft.Row([
                self._refs["fortify_btn"],
                self._refs["fortify_charm_btn"],
            ], spacing=8),
        ], spacing=4), padding=10)

        # ── 锻造区域 ──
        self._ref("forge_recipes_ctr", ft.Column([], spacing=4, scroll="auto"))
        self._ref("forge_select_lbl", ft.Text("选择材料品质:", size=F_SM))
        rarity_btns = ft.Row([
            ft.Button("白", scale=0.8, on_click=lambda e: self._show_forge_recipes(0)),
            ft.Button("绿", scale=0.8, on_click=lambda e: self._show_forge_recipes(1)),
            ft.Button("蓝", scale=0.8, on_click=lambda e: self._show_forge_recipes(2)),
            ft.Button("紫", scale=0.8, on_click=lambda e: self._show_forge_recipes(3)),
            ft.Button("橙", scale=0.8, on_click=lambda e: self._show_forge_recipes(4)),
        ], spacing=4, alignment=ft.MainAxisAlignment.CENTER)

        forge_ctr = styled_card(ft.Column([
            ft.Text("【锻造装备】", size=F_MD, weight=ft.FontWeight.BOLD, color="#37474F"),
            ft.Text("消耗牧场产出物+铁矿+金币锻造独特装备，自带被动技能", size=F_XS, color=Cs("GREY_500")),
            ft.Divider(height=1),
            self._refs["forge_select_lbl"],
            rarity_btns,
            self._refs["forge_recipes_ctr"],
        ], spacing=4), padding=10, expand=True)

        ctr = ft.Column([
            fortify_ctr,
            forge_ctr,
        ], scroll="auto", spacing=8, expand=True)
        return ft.Container(content=ctr)

    def _show_forge_recipes(self, rarity):
        """展示指定品质的锻造配方"""
        g = self.game
        wh = g.ranch.get_warehouse_summary()
        recipes = get_forge_recipes_by_rarity(rarity)
        ctr = self._refs.get("forge_recipes_ctr")
        if not ctr:
            return
        ctr.controls.clear()
        rarity_names = ["白", "绿", "蓝", "紫", "橙"]
        self._refs["forge_select_lbl"].value = f"品质: {rarity_names[rarity]} ({len(recipes)}件)"
        for r in recipes:
            mat_ok = wh.get(r["material"], 0) >= r["material_count"]
            iron_ok = g.resources.get("铁矿", 0) >= r["iron"]
            gold_ok = g.player.gold >= r["gold"]
            can_forge = mat_ok and iron_ok and gold_ok
            p = r["passive"]
            passive_text = f"[{p['name']}] {p['desc']}" if p else ""
            color = FORGE_RARITY_COLORS.get(r["rarity"], "#cccccc")
            ctr.controls.append(ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(r["name"], size=F_BASE, weight=ft.FontWeight.BOLD, color=color),
                        ft.Text(f"{r['material']}×{r['material_count']} + 铁矿×{r['iron']} + {r['gold']}G  |  {passive_text}",
                                size=F_XS, color=Cs("GREY_600")),
                    ], spacing=2, expand=True),
                    ft.Button("锻造", scale=0.75, disabled=not can_forge,
                              on_click=lambda e, rn=r["name"]: self._do_forge(rn)),
                ], spacing=8),
                padding=6, border=ft.Border.all(1, Cs("OUTLINE_VARIANT")), border_radius=4,
            ))

    def _do_forge(self, recipe_name):
        ok, msg, equip = self.game.forge_equipment(recipe_name)
        self.game.add_log(msg)
        self._refresh_forge_tab()
        self._refresh_all_ui()

    def _on_fortify_select(self, e):
        """当选择要强化的装备时更新信息"""
        self._update_fortify_info()

    def _update_fortify_info(self):
        """更新强化信息显示"""
        dd = self._refs.get("fortify_dd")
        info_lbl = self._refs.get("fortify_info_lbl")
        cost_lbl = self._refs.get("fortify_cost_lbl")
        select_lbl = self._refs.get("fortify_select_lbl")
        if not dd or not info_lbl or not cost_lbl:
            return
        val = dd.value
        if not val:
            info_lbl.value = ""
            cost_lbl.value = ""
            select_lbl.value = "选择装备: 未选择"
            return
        g = self.game
        equip = None
        if val == "__weapon__":
            equip = g.player.weapon
        elif val == "__armor__":
            equip = g.player.armor
        elif val.startswith("bag_"):
            idx = int(val.split("_")[1])
            equip = g.player.inventory.get(idx)
        if not equip:
            info_lbl.value = ""
            cost_lbl.value = ""
            return
        info = g.get_fortify_info_for_ui(equip)
        select_lbl.value = f"选中: {equip['name']} +{info['current']}"
        if info.get("maxed"):
            info_lbl.value = "已达到最高强化等级 +10!"
            cost_lbl.value = ""
        else:
            info_lbl.value = (f"下级: +{info['next_level']}  属性+{info['next_bonus']}%  "
                            f"成功率: {int(info['success_rate']*100)}%")
            cost_lbl.value = f"消耗: 铁矿×{info['cost']['铁矿']} + {info['cost']['金币']}G"

    def _do_fortify(self, e=None, use_charm=False):
        dd = self._refs.get("fortify_dd")
        if not dd or not dd.value:
            self._show_toast("请选择要强化的装备")
            return
        g = self.game
        val = dd.value
        if val == "__weapon__":
            equip_ref = g.player.weapon
        elif val == "__armor__":
            equip_ref = g.player.armor
        elif val.startswith("bag_"):
            idx = int(val.split("_")[1])
            equip_ref = g.player.inventory.get(idx)
        else:
            return
        if not equip_ref:
            self._show_toast("装备不存在")
            return
        ok, msg = g.fortify_equipment(equip_ref, use_charm)
        g.add_log(msg)
        self._update_fortify_info()
        self._refresh_all_ui()

    def _refresh_forge_tab(self):
        """刷新锻造Tab"""
        g = self.game
        # 更新强化下拉
        dd = self._refs.get("fortify_dd")
        if dd:
            opts = []
            p = g.player
            if p.weapon and isinstance(p.weapon, dict):
                lvl = p.weapon.get("forge_level", 0)
                opts.append(ft.dropdown.Option("__weapon__", f"⚔ 武器: {p.weapon['name']} +{lvl}"))
            if p.armor and isinstance(p.armor, dict):
                lvl = p.armor.get("forge_level", 0)
                opts.append(ft.dropdown.Option("__armor__", f"🛡 护甲: {p.armor['name']} +{lvl}"))
            inv = p.get_inventory()
            for i in range(inv.count()):
                item = inv.get(i)
                if item and item.get("type") in ("weapon", "armor"):
                    lvl = item.get("forge_level", 0)
                    opts.append(ft.dropdown.Option(f"bag_{i}", f"🎒 {item['name']} +{lvl}"))
            dd.options = opts
        # 首次显示时展示白品质配方
        ctr = self._refs.get("forge_recipes_ctr")
        if ctr and len(ctr.controls) == 0:
            self._show_forge_recipes(0)
        self._update_fortify_info()

    def _build_factory_tab(self):
        self._ref("factory_status_lbl",
                  ft.Text("\U0001f3ed 未建造", size=F_MD, color=ft.Colors.RED))
        self._ref("factory_info_lbl",
                  ft.Text("建造费用: " + ", ".join(f"{k}{v}" for k, v in FACTORY_BUILD_COST.items()) + "  |  基础利润: 50G/5min", size=F_SM))
        self._ref("factory_build_btn",
                  ft.Button("\U0001f3d7 建造工厂", on_click=self._build_factory_tab_action))
        self._ref("factory_depts_ctr", ft.Column([], spacing=4))
        self._ref("factory_workers_lbl",
                  ft.Text("劳工: 0/5  (每人+15%, 80G/人)", size=F_BASE))

        for dept in FACTORY_DEPTS:
            if dept["id"] == "basic":
                continue
            cost_str = f"{dept['cost_gold']}G"
            if dept["cost_resources"]:
                cost_str += ", " + ", ".join(f"{k}{v}" for k, v in dept["cost_resources"].items())
            self._ref(f"dept_card_{dept['id']}",
                      styled_card(ft.Column([
                          ft.Row([
                              ft.Text(f"{dept['name']}", size=F_BASE, weight=ft.FontWeight.BOLD, expand=True),
                              self._ref(f"dept_status_{dept['id']}", ft.Text("未解锁", size=F_SM, color=ft.Colors.RED)),
                          ], tight=True),
                          ft.Text(f"{dept['desc']}  |  费用: {cost_str}", size=F_XS, color=Cs("GREY_600")),
                          self._ref(f"dept_btn_{dept['id']}",
                                    ft.Button(f"解锁 {dept['name']}", scale=0.8,
                                              on_click=lambda e, d=dept["id"]: self._buy_dept(d))),
                      ], spacing=2), padding=6))
            self._refs["factory_depts_ctr"].controls.append(self._refs[f"dept_card_{dept['id']}"])

        ctr = ft.Column([
            self._refs["factory_status_lbl"],
            self._refs["factory_info_lbl"],
            self._refs["factory_build_btn"],
            divider_h(),
            ft.Text("部门", size=F_MD, weight=ft.FontWeight.BOLD, color="#37474F"),
            self._refs["factory_depts_ctr"],
            divider_h(),
            self._refs["factory_workers_lbl"],
            ft.Row([
                ft.Button("+ 雇佣", scale=0.85, on_click=self._hire_factory_worker),
                ft.Button("- 解雇", scale=0.85, on_click=self._fire_factory_worker),
            ], spacing=8),
        ], scroll="auto", spacing=6)
        return ft.Container(content=ctr)

    # ─── Bottom Bar ──────────────────────────────────────────────
    def _build_bottom_bar(self):
        BTN_STYLE = ft.ButtonStyle(
            bgcolor=CLR_PRIMARY, color=ft.Colors.WHITE,
            padding=ft.Padding.only(left=16, right=16, top=8, bottom=8),
        )
        self.page.add(ft.Container(
            content=ft.Row([
                ft.Container(expand=True),
                ft.Button("\U0001f4be 存档", on_click=self._save, style=BTN_STYLE),
                ft.Button("\U0001f4c2 读档", on_click=self._load, style=BTN_STYLE),
                ft.Button("📖 图鉴", on_click=self._show_codex, style=BTN_STYLE),
                ft.Button("❓ 帮助", on_click=self._show_help, style=BTN_STYLE),
                ft.Container(expand=True),
            ], spacing=12),
            padding=ft.Padding.only(top=8, bottom=8, left=12, right=12),
            bgcolor="#FFFFFF",
            border=ft.Border.only(top=ft.BorderSide(color="#E0E0E0", width=1)),
        ))

    # ─── Update Loop ────────────────────────────────────────────
    async def _update_loop(self):
        last_misc_len = 0
        last_battle_len = 0
        while True:
            await asyncio.sleep(0.3)
            try:
                self._refresh_all_ui()
                self._refresh_materials()
                self.game.ranch_tick()
                if len(self.game.logs) != last_misc_len:
                    self._refresh_misc_log()
                    last_misc_len = len(self.game.logs)
                if len(self.game.battle_logs) != last_battle_len:
                    self._refresh_battle_log()
                    last_battle_len = len(self.game.battle_logs)
                self.page.update()
            except RuntimeError:
                break

    def _refresh_battle_log(self):
        self.battle_log_view.controls.clear()
        for msg in self.game.battle_logs[-60:]:
            self.battle_log_view.controls.append(ft.Text(msg, size=F_SM))
        try:
            self.page.update()
        except Exception:
            pass

    def _refresh_misc_log(self):
        self.misc_log_view.controls.clear()
        for msg in self.game.logs[-60:]:
            self.misc_log_view.controls.append(ft.Text(msg, size=F_SM))
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
                btn.content = ft.Text(f"{m.role_name}\nLv.{m.level}", size=F_MD, weight=ft.FontWeight.W_500)
                bg = Cs("ORANGE_600") if i == g.current_member_idx else (Cs("GREEN_600") if i == 0 else Cs("DEEP_PURPLE_600"))
                btn.style = ft.ButtonStyle(bgcolor=bg, color=ft.Colors.WHITE)
            else:
                btn.content = ft.Text("空位", size=F_MD, weight=ft.FontWeight.W_500)
                btn.style = ft.ButtonStyle(bgcolor=Cs("GREY_600"))

        max_hp = p.get_max_hp_with_bonus()
        self._refs["hero_name_lbl"].value = f"\U0001f9d9 {p.role_name} Lv.{p.level}"
        self._refs["hp_lbl"].value = f"生命: {p.hp}/{max_hp}"
        self._refs["atk_lbl"].value = f"攻击: {p.get_total_attack()}"
        self._refs["def_lbl"].value = f"防御: {p.get_total_defense()}"
        self._refs["crit_lbl"].value = f"CRIT: {p.get_crit_rate()}%"
        self._refs["exp_lbl"].value = f"经验: {p.exp}/{p.level * 100}"
        if p.weapon and isinstance(p.weapon, dict):
            fl = p.weapon.get("forge_level", 0)
            ftag = f" +{fl}" if fl > 0 else ""
            wn = f"{p.weapon['name']}{ftag}"
        else:
            wn = "None"
        if p.armor and isinstance(p.armor, dict):
            fl = p.armor.get("forge_level", 0)
            ftag = f" +{fl}" if fl > 0 else ""
            an = f"{p.armor['name']}{ftag}"
        else:
            an = "None"
        self._refs["wpn_lbl"].value = f"武器: {wn}"
        self._refs["arm_lbl"].value = f"护甲: {an}"

        self._refs["map_lbl"].value = g.current_map
        for mname in get_all_maps().keys():
            btn = self._refs.get(f"map_btn_{mname}")
            if btn:
                if mname in g.unlocked_maps:
                    btn.content = ft.Text(mname, size=F_MD, weight=ft.FontWeight.W_500)
                    btn.style = ft.ButtonStyle(bgcolor=Cs("GREEN_600"), color=ft.Colors.WHITE)
                else:
                    cost = get_all_maps()[mname].get("unlock_cost", 0)
                    btn.content = ft.Text(f"{mname}({cost}G)", size=F_MD, weight=ft.FontWeight.W_500)
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
            "战中..." if g.is_battling else "⚔ 战斗", size=F_MD)
        self._refs["auto_status_lbl"].value = "自动: 开" if g.auto_battle else "自动: 关"
        self._refs["auto_status_lbl"].color = ft.Colors.GREEN_600 if g.auto_battle else Cs("GREY_500")
        self._refs["auto_btn"].content = ft.Text(
            "⏹ 停止" if g.auto_battle else "⚡ 自动战斗", size=F_BASE)
        self._refs["auto_btn"].style = ft.ButtonStyle(
            bgcolor=Cs("RED_600") if g.auto_battle else Cs("ORANGE_600"))
        self._refs["potions_lbl"].value = f"\U0001f9ea 药水: x{p.potions}"

        # 建筑实例卡片列表(重新构建)
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

        # 刷新饲料/肥料库存
        feed_lbl = self._refs.get("farm_feed_lbl")
        if feed_lbl:
            parts = [f"{k}×{v}" for k, v in g.feed_bag.items()] if g.feed_bag else ["无"]
            feed_lbl.value = "🌾 饲料: " + ", ".join(parts)
        fert_lbl = self._refs.get("farm_fert_lbl")
        if fert_lbl:
            parts = [f"{k}×{v}" for k, v in g.fertilizer_bag.items()] if g.fertilizer_bag else ["无"]
            fert_lbl.value = "🧪 肥料: " + ", ".join(parts)

        # 更新植物列表
        fctr = self._refs.get("farm_plants_ctr")
        if fctr:
            fctr.controls.clear()
            for plant in g.plants:
                pd = get_plant_by_id(plant["plant_id"])
                if pd:
                    status_info = self.game.get_plant_status(plant["id"])
                    if status_info:
                        # 变异植物显示 🌟 前缀
                        is_mutated = plant["id"] in self.game.mutated_plants
                        icon_display = f"🌟{pd['icon']}" if is_mutated else pd['icon']

                        if status_info["adult"]:
                            status = f"\U0001f7e2 {status_info['progress']}"
                            color = Cs("GREEN_600")
                            # 成年：显示产金+产饲料信息
                            feed_info = ""
                            if g.feed_bag:
                                feed_info = " | " + " ".join(f"{k}×{v}" for k, v in g.feed_bag.items())
                            btn = ft.Text(f"自动产金中{feed_info}", size=11, color=Cs("GREEN_600"))
                        else:
                            status = f"{status_info['progress']}"
                            color = Cs("ORANGE_600")
                            fert_count = len(plant.get("fertilizers", []))
                            mut_bonus = plant.get("mutation_bonus", 0.0)
                            fert_text = f" | 施肥×{fert_count}" if fert_count > 0 else ""
                            if mut_bonus > 0:
                                fert_text += f" 变异+{mut_bonus*100:.1f}%"
                            btn_children = [
                                ft.Text(f"种植中{fert_text}", size=11, color=Cs("GREY_500")),
                                ft.Button("⚡", scale=0.7,
                                          on_click=lambda e, p=plant: self._speedup(p)),
                            ]
                            # 肥料按钮
                            if g.fertilizer_bag.get("普通肥料", 0) > 0:
                                btn_children.append(
                                    ft.Button("🧪普肥", scale=0.7,
                                              on_click=lambda e, p=plant: self._use_fertilizer(p, "普通肥料")))
                            if g.fertilizer_bag.get("精制肥料", 0) > 0:
                                btn_children.append(
                                    ft.Button("🧪精肥", scale=0.7,
                                              on_click=lambda e, p=plant: self._use_fertilizer(p, "精制肥料")))
                            btn = ft.Row(btn_children, spacing=4)

                        fctr.controls.append(
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Text(f"{icon_display} {pd['name']}", size=12, weight=ft.FontWeight.BOLD, expand=True),
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
                rctr.controls.append(styled_card(ft.Column([
                    ft.Row([
                        ft.Text(f"{ch.get('role_name','?')} Lv.{ch.get('level',1)}", size=F_BASE, weight=ft.FontWeight.BOLD, expand=True),
                        ft.Text(f"{cost}G", size=F_BASE, color=CLR_ACCENT),
                    ], tight=True),
                    ft.Text(f"武器: {wn}", size=F_XS, color=Cs("GREY_600")),
                    ft.Button("招募", scale=0.8, on_click=lambda e, c=ch: self._recruit_member(c)),
                ], spacing=2), padding=6))
            if not roster:
                rctr.controls.append(ft.Text("暂无可招募角色", size=F_BASE, color=Cs("GREY_500")))
        # 队伍管理列表
        tctr = self._refs.get("team_manage_ctr")
        if tctr:
            tctr.controls.clear()
            team = g.get_team()
            for i, m in enumerate(team):
                tag = " ★队长" if i == 0 else f" #{i}"
                tctr.controls.append(styled_card(ft.Row([
                    ft.Text(f"{m.role_name} Lv.{m.level}{tag}", size=F_BASE, weight=ft.FontWeight.BOLD, expand=True),
                    ft.Text(f"HP:{m.hp}/{m.get_max_hp_with_bonus()}", size=F_SM),
                    ft.Button("切换", scale=0.75,
                              on_click=lambda e, idx=i: self._switch_to(idx)) if i != g.current_member_idx else None,
                    ft.Button("踢出", scale=0.75,
                              on_click=lambda e, idx=i: self._kick_member_ui(idx)) if i > 0 else None,
                ], spacing=4, alignment=ft.alignment.Alignment(-1, 0)),
                padding=6, accent_left="#FFA726" if i == g.current_member_idx else None,
                ))

        # 刷新牧场
        inv_ctr = self._refs.get("ranch_inventory_ctr")
        if inv_ctr:
            inv_ctr.controls.clear()
            inv_summary = g.ranch.get_inventory_summary()
            for item in inv_summary:
                inv_ctr.controls.append(ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(item["name"], size=12, weight=ft.FontWeight.BOLD, expand=True),
                            ft.Text(item["status"], size=10, color=Cs("ORANGE_600")),
                        ], tight=True),
                        ft.Button("🍖 饲养", scale=0.7, on_click=lambda e, idx=item["index"]: self.game.feed_ranch_creature(idx)),
                    ], spacing=2),
                    padding=4, border=ft.Border.all(1, Cs("OUTLINE_VARIANT")), border_radius=4,
                ))
        inv_lbl = self._refs.get("ranch_inventory_lbl")
        if inv_lbl:
            inv_lbl.value = f"\U0001f42c 牧场库存: {len(g.ranch.ranch_inventory)}"
        rg_lbl = self._refs.get("ranch_gold_lbl")
        if rg_lbl:
            rg_lbl.value = f"\U0001fa99 {g.player.gold}"
        wh_ctr = self._refs.get("ranch_warehouse_ctr")
        if wh_ctr:
            wh_ctr.controls.clear()
            wh = g.ranch.get_warehouse_summary()
            for otype, count in wh.items():
                if count > 0:
                    wh_ctr.controls.append(ft.Container(
                        content=ft.Row([
                            ft.Text(f"{otype} x{count}", size=12, expand=True),
                            ft.Button("售出", scale=0.7, on_click=lambda e, ot=otype: self.game.sell_ranch_output(ot, 1)),
                        ], tight=True),
                        padding=4, border=ft.Border.all(1, Cs("OUTLINE_VARIANT")), border_radius=4,
                    ))

        # 刷新背包和材料(修复战斗掉落后UI不同步)
        self._refresh_bag()
        self._refresh_materials()
        self._refresh_forge_tab()

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

    def _speedup(self, plant):
        ok, msg = self.game.speedup_plant(plant["id"])
        self.game.add_log(msg)

    def _use_fertilizer(self, plant, fertilizer_type):
        ok, msg = self.game.use_fertilizer(plant["id"], fertilizer_type)
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
        self.game.save_to_file(SAVE_PATH)
        self.game.add_log(f"\U0001f4be 已存档!")
        self._show_toast("存档成功!")

    def _load(self, e=None):
        if not self.game.load_from_file(SAVE_PATH):
            self.game.add_log("没有存档文件!")
            return
        self.game.add_log("\U0001f4c2 读档成功!")
        self._show_toast("读档成功!")

    def _show_codex(self, e=None):
        """图鉴弹窗 - 5个分册tab"""
        tabs = []
        tab_contents = []
        for kind, book in CODEX_BOOKS.items():
            tabs.append(ft.Tab(label=book["name"]))
            discovered, total = self.game.codex.get_progress(kind)
            entries = self.game.codex.get_all_by_kind(kind)
            # 进度
            progress_txt = ft.Text(f"已发现 {discovered}/{total}", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_700)
            # 条目网格
            is_icon_grid = kind in ("ranch", "plants")
            grid = ft.GridView(max_extent=60 if is_icon_grid else 150, child_aspect_ratio=1.2 if is_icon_grid else 2.5, spacing=4, padding=4, expand=True, run_spacing=4)
            if entries:
                for entry in entries:
                    rc = PLANT_RARITY_COLORS.get(entry.get("rarity", 0), "#888888")
                    if is_icon_grid:
                        grid.controls.append(ft.Container(
                            content=ft.Column([
                                ft.Text(entry["icon"], size=22, text_align="center"),
                                ft.Text(entry["name"], size=8, color=rc, weight=ft.FontWeight.W_500, text_align="center", max_lines=1, overflow="ellipsis"),
                            ], alignment=ft.MainAxisAlignment.CENTER, spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            border=ft.Border.all(1, rc),
                            border_radius=6,
                            padding=ft.Padding.symmetric(horizontal=4, vertical=3),
                            bgcolor="#fafafa",
                        ))
                    else:
                        grid.controls.append(ft.Container(
                            content=ft.Column([
                                ft.Text(entry["icon"], size=20, text_align="center"),
                                ft.Text(entry["name"], size=10, color=rc, weight=ft.FontWeight.W_500, text_align="center", max_lines=1, overflow="ellipsis"),
                            ], alignment=ft.MainAxisAlignment.CENTER, spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            border=ft.Border.all(1, rc),
                            border_radius=6,
                            padding=4,
                            bgcolor="#fafafa",
                        ))
            else:
                grid.controls.append(ft.Container(
                    content=ft.Text("尚未发现任何条目", size=12, color=ft.Colors.GREY_500, text_align="center"),
                    alignment=ft.alignment.Alignment(0.5, 0.5),
                ))
            tab_contents.append(ft.Column([
                ft.Container(content=progress_txt, padding=ft.Padding.only(bottom=6)),
                grid,
            ], spacing=4, expand=True))

        tab_bar = ft.TabBar(tabs=tabs)
        tab_view = ft.TabBarView(controls=tab_contents, expand=True)
        codex_tabs = ft.Tabs(
            content=ft.Column([tab_bar, tab_view], spacing=0, expand=True),
            length=len(tabs),
            expand=True,
        )
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("📖 图鉴", size=16, weight=ft.FontWeight.BOLD),
            content=ft.Container(content=codex_tabs, width=500, height=450),
            actions=[ft.TextButton("关闭", on_click=lambda e: self.page.pop_dialog())],
        )
        self.page.show_dialog(dlg)

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
