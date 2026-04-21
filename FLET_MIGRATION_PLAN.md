# 勇者工坊 — Tkinter → Flet UI 重构规划

> 重构目标：用 Flet 重写 `main.py`，生成 `main_flet.py`，保留所有 `modules/` 逻辑不变。
> 当前状态：`main_flet.py` 已有基础框架（43 方法/736 行），需补充缺失 UI 和功能连接。

---

## 一、项目现状

### 源码规模

| 文件 | 行数 | 字符数 | 说明 |
|------|------|--------|------|
| `main.py` | 1423 | 62,095 | 完整 Tkinter UI（参考基准） |
| `main_flet.py` | 736 | 32,917 | Flet 基础框架（部分功能已连） |
| `modules/game_core.py` | — | — | 游戏逻辑，无 UI 依赖 ✅ |
| `modules/hero.py` | — | — | 英雄/队伍，无 UI 依赖 ✅ |
| `modules/tavern.py` | — | — | 酒馆，无 UI 依赖 ✅ |
| `modules/buildings.py` | — | — | 建筑/奇观，无 UI 依赖 ✅ |
| `modules/equipment.py` | — | — | 装备定义，无 UI 依赖 ✅ |
| `modules/maps.py` | — | — | 地图/怪物，无 UI 依赖 ✅ |
| `modules/plants.py` | — | — | 农场，无 UI 依赖 ✅ |
| `modules/factory.py` | — | — | 工坊，无 UI 依赖 ✅ |
| `modules/inventory.py` | — | — | 杂货物品，无 UI 依赖 ✅ |
| `modules/equipment_drops.py` | — | — | 掉落生成，无 UI 依赖 ✅ |

**核心原则**：`modules/` 目录零改动，全部复用。

---

## 二、方法对照（main.py 55 → main_flet.py 43）

### 2.1 已实现（main_flet.py 有对应方法，逻辑可能未连接）

| main.py 方法 | main_flet.py 方法 | 状态 |
|---|---|---|
| `_build_left` | `_build_left` | ⚠️ 框架有，内容待验证 |
| `_build_center` | `_build_center` | ⚠️ 框架有，战斗按钮未测试 |
| `_build_right` | `_build_right` | ⚠️ Tab 结构需按 Flet 0.84 重构 |
| `_build_bottom_bar` | `_build_bottom_bar` | ⚠️ 存档/读档/帮助按钮有 |
| `_build_top_bar` | `_build_top_bar` | ✅ 金币显示已有 |
| `_build_tavern_tab` | `_build_tavern_tab` | ⚠️ 部分框架，需补充 |
| `_build_farm_tab` | `_build_farm_tab` | ⚠️ 框架有，植物种植逻辑未连 |
| `_build_factory_tab` | `_build_factory_tab` | ⚠️ 框架有，雇佣逻辑未连 |
| `_open_tavern_tab` | `_open_tavern_tab` | ⚠️ 需测试 Tab 切换 |
| `_change_map` | `_change_map` | ⚠️ 地图按钮有，切换逻辑未测 |
| `_refresh_enemy` | `_refresh_enemy` | ⚠️ 按钮有，逻辑未测 |
| `_switch_member` | `_switch_member` | ⚠️ 框架有，切换逻辑未测 |
| `_buy_potion` / `_use_potion` | `_buy_potion` / `_use_potion` | ⚠️ 有框架，未连接 game_core |
| `_buy_mat` / `_sell_mat` | `_buy_mat` / `_sell_mat` | ⚠️ 有框架，未连接 game_core |
| `_save` / `_load` | `_save` / `_load` | ⚠️ 有框架，未连接 game_core |
| `_show_help` | `_show_help` | ⚠️ 有框架，对话框未测 |
| `_show_toast` | `_show_toast` | ✅ 有实现 |

### 2.2 未实现（main_flet.py 缺失，需新增）

| main.py 方法 | 说明 | 优先级 |
|---|---|---|
| `setup_ui` | Tkinter 主窗口初始化 → 改为 Flet page setup | P0 |
| `_build_shop` / `_build_novelty_shop` | 杂货铺完整 UI | P1 | ✅ |
| `buy_novelty` | 杂货购买逻辑 | P1 | ✅ |
| `_build_inventory` | 背包标签页完整实现 | P1 | ✅ |
| `equip_item` | 装备穿戴（右键/双击） | P1 | ✅ |
| `do_refresh_enemy` | 刷新敌人（包含费用扣除） | P1 | ✅ |
| `do_battle` / `_battle_wrapper` | 手动战斗（单次） | P0 | ✅ |
| `_battle_thread` | 自动战斗线程 | P0 | ✅ |
| `toggle_auto` | 自动战斗开关 | P0 | ✅ |
| `do_buy_potion` / `do_use_potion` | 药水购买/使用 | P1 | ✅ |
| `_on_auto_potion_change` / `_restore_auto_potion_ui` | 自动药水阈值 UI | P1 | ✅ |
| `hire_worker` / `fire_worker` | 劳工雇佣/解雇（资源区） | P1 | ✅ |
| `build_wonder` | 奇观建造 | P1 | ✅ |
| `use_novelty_item` | 杂货物品使用 | P1 | ✅ |
| `sell_item` | 物品出售 | P1 | ✅ |
| `buy_material` / `sell_material` | 材料买卖 | P1 | ✅ |
| `refresh_buildings` | 建筑刷新（UI） | P1 | ✅ |
| `refresh_ui` | 全量 UI 刷新（game loop） | P0 | ✅ |
| `update_loop` | Tkinter after 循环 → 改为 Flet timer | P0 | ✅ |
| `save_game` / `load_game` | 存档/读档逻辑 | P1 | ✅ |
| `_buy_dept` | 工坊部门解锁 | P1 | ✅ |
| `_refresh_factory_ui` | 工坊 UI 刷新 | P1 | ✅ |
| `refresh_farm_ui` | 农场 UI 刷新 | P1 | ✅ |
| `_speedup` | 加速（用金币） | P2 | ✅ |
| `_build_factory` | 工坊建造/升级卡片 | P1 | ✅ |
| `_cost_str` | 花费显示字符串 | P1 | ✅ |
| `_recruit_from_tavern` | 酒馆招募 | P1 | ✅ |
| `_kick_member` | 踢出队友 | P1 | ✅ |
| `_do_tavern_refresh` | 酒馆手动刷新（含费用） | P1 | ✅ |
| `_refresh_team_manage` | 队伍管理面板刷新 | P1 | ✅ |
| `_build_weapon_tab` / `_build_armor_tab` | 武器/护甲商店 Tab | P1 | ✅ |
| `_build_building_card` | 建筑卡片构建 | P1 |
| `_build_wonder` | 奇观卡片构建 | P1 |
| `_buy_weapon` / `_buy_armor` | 武器/护甲购买 | P1 |
| `_upgrade_building` | 建筑升级 | P1 |

---

## 三、Flet 0.84 API 迁移重点

### 3.1 Tabs 组件（三件套，必改）

Flet 0.84 重构了 Tab 机制，旧的 `Tab(content=...)` 写法无效。

```python
# ✅ 正确架构
tabs_list = [
    ft.Tab(label="⚔️ 武器", icon=ft.icons.Icons.IRON),
    ft.Tab(label="🛡️ 护甲", icon=ft.icons.Icons.SHIELD),
    ft.Tab(label="🎒 背包", icon=ft.icons.Icons.INVENTORY_2),
    ft.Tab(label="🏪 杂货", icon=ft.icons.Icons.STOREFRONT),
    ft.Tab(label="🍺 酒馆", icon=ft.icons.Icons_LOCAL_BAR),
    ft.Tab(label="🌱 农场", icon=ft.icons.Icons.AGRICULTURE),
]
tab_content = ft.TabBarView(controls=[weapon_list, armor_list, ...])
right_panel.content = ft.Tabs(
    content=tab_content,
    tabs=tabs_list,
    selected_index=0,
)
```

> `_build_right()` 需整体重写，按此架构重构所有 6 个标签页。

### 3.2 ElevatedButton → Button

```python
# 批量替换
ft.ElevatedButton  →  Button
```

### 3.3 padding / border / margin 命名空间

```python
# 头部 import
from flet import Padding, Border, Margin

# 替换规则
ft.padding.all(x)  →  Padding.all(x)  或直接 padding=x
ft.border.all(w, c) →  Border.all(w, c)
ft.margin.only(...)  →  Margin.only(...)
```

### 3.4 scroll 模式

```python
Row(..., scroll="auto")  →  Row(..., scroll=ft.ScrollMode.AUTO)
Column(..., scroll="auto") →  Column(..., scroll=ft.ScrollMode.AUTO)
```

### 3.5 AppBar actions（构造后赋值）

```python
# ✅ 正确
bar = ft.AppBar(title=ft.Text("勇者工坊"))
bar.actions = [save_btn, load_btn, help_btn]

# ❌ 错误（actions= 是无效 kwarg）
bar = ft.AppBar(title=..., actions=[...])
```

### 3.6 启动入口

```python
# ✅ Flet 0.84 推荐写法
def main(page: ft.Page):
    app = HeroWorkshopApp(page)

ft.app(main)  # 不再推荐 ft.run(target=main)
```

### 3.7 SnackBar / AlertDialog

```python
# SnackBar
page.show_snack_bar(ft.SnackBar(ft.Text(msg), duration=2000))

# AlertDialog
dlg = ft.AlertDialog(title=ft.Text("标题"), content=ft.Text("内容"))
page.dialog = dlg
dlg.open = True
page.update()
```

---

## 四、分阶段重构计划

### Phase 0：环境 & 基础框架 ✅
- [x] 安装 Flet (`pip install flet`)
- [x] 创建 `main_flet.py` 基础结构
- [x] Flet CDN 下载成功，桌面应用可启动
- [x] 消除语法错误（括号结构、border API）
- [x] Flet 0.84 API 模式确认

### Phase 1：核心战斗闭环 ✅
- [x] `_do_battle()` 手动战斗：主角 vs 怪物，伤害计算正确
- [x] `_battle_thread()` 自动战斗：主角 vs 怪物，循环扣血
- [x] `battle_team()` 队伍战斗（多人）：主角+队友 vs 怪物，随机出手顺序
- [x] 战斗日志正确滚动显示在中间面板（每 0.3s 刷新，战斗中实时追加）
- [x] 敌人死亡后自动切换下一只（game_core 已实现）
- [x] `_refresh_enemy()` 刷新敌人（消耗 5~10G 金币）
- [x] `_change_map()` 解锁地图后自动刷新该地图敌人

**验收标准**：打开应用 → 点击自动战斗 → 每秒扣血 → 怪物死亡后换下一只 → 循环不停
> ✅ 2026-04-21 验证通过

### Phase 2：地图 & 药水 ✅
- [x] 4 张地图按钮正确切换（ft.Wrap）
- [x] 切换地图后刷新敌人
- [x] 药水购买（25G）和使用（+20HP）
- [x] 自动药水阈值下拉 OFF/30%/50%/80%
- [x] 战斗中自动药水循环（game_core）

### Phase 3：商店 & 背包 ✅
- [x] 武器 Tab：20 种武器列表 + 购买按钮
- [x] 护甲 Tab：20 种护甲列表 + 购买按钮
- [x] 背包 Tab：当前装备 + 背包 20 格
- [x] 装备穿戴（点击背包格子 → 装备到对应位置）
- [x] 物品出售（点击背包格子 → 选择出售）
- [x] 杂货 Tab：26 种随机趣味物品购买 + 使用（5 个稀有度等级）

**验收标准**：商店购买功能正常 → 背包显示正确 → 装备/出售操作正常
> ✅ 2026-04-21 验证通过

### Phase 4：建筑 & 农场 & 工坊 ✅
- [x] 建筑面板：4 种建筑 + 升级按钮 + 劳工控制
- [x] 奇观面板：6 种奇观 + 建造按钮
- [x] 农场 Tab：种植/收获循环 + 实时状态更新
- [x] 工坊 Tab：部门解锁(4 个可解锁) + 劳工雇佣 + 实时利润显示

### Phase 5：酒馆 & 队伍 ✅
- [x] 酒馆 Tab：角色列表 + 刷新 + 招募
- [x] 队伍管理：切换队长/踢出成员
- [x] 精英角色等级限制（player_level >= 5，tavern.py:56）

### Phase 6：存档 & 其他 ✅
- [x] 存档 save_game / load_game
- [x] 帮助对话框
- [x] 主循环 update_loop（资源生产/自动战斗）

### Phase 7：打磨 & 发布 ✅
- [x] 消除所有 DeprecationWarning
- [x] 窗口自适应大小（中栏 expand，最小 960×640）
- [x] 主窗口标题设置（图标无本地文件跳过）

---

## 五、Tkinter → Flet UI 组件对照

| Tkinter | Flet | 说明 |
|---|---|---|
| `PanedWindow` | `Row` / `Column` + 可拖拽 Container | 三栏布局用 `Row([left, center, right], expand=True)` |
| `Frame` | `Container` + `Border` | 带边框的分组容器 |
| `Label` | `Text` | 文字标签 |
| `Button` | `Button` | 按钮 |
| `ttk.Combobox` | `Dropdown` | 下拉选择 |
| `Listbox` | `ListView` + `Row` | 列表/日志 |
| `ttk.Treeview` | `DataTable` 或自定义 Column | 表格数据 |
| `PanedWindow`（可拖拽）| `VerticalDraggable` 或固定 Column | 可拖拽分隔 |
| `Canvas` + `Scrollbar` | `Column(scroll=ft.ScrollMode.AUTO)` | 滚动区域 |
| `messagebox.showinfo` | `SnackBar` | 短暂提示 |
| `Toplevel` | `AlertDialog` | 弹窗 |
| `PhotoImage` | `Image` | 图片 |
| `StringVar` + `Label` | `Text(ref=...)` + `_ref` | 动态文字 |

---

## 六、main_flet.py 当前方法签名（已实现）

```
HeroWorkshopApp:
  __init__(page)              — 初始化 app、game_core、page、refs、定时器
  _ref(key, ctrl)             — 注册动态控件引用
  _build_top_bar()            — AppBar：标题、击杀数、金币
  _build_body()               — 三栏 Row 组装（左/中/右）
  _build_left()               — 资源+建筑+奇观+酒馆按钮面板
  _build_building_card(name)  — 单个建筑卡片（建造/升级/工人）
  _build_wonder_card(name)    — 单个奇观卡片
  _build_center()             — 队伍+英雄属性+地图+敌人+战斗+药水
  _init_hero_stats()          — 初始化英雄属性 Label
  _build_right()              — Tabs 8页（武器/护甲/杂货/背包/材料/酒馆/农场/工厂）
  _build_weapon_tab()         — 武器商店
  _build_armor_tab()          — 护甲商店
  _build_novelty_tab()        — 杂货商店
  _build_bag_tab()            — 背包 5×4 网格
  _refresh_bag()              — 刷新背包显示
  _bag_cell_click(idx)        — 背包点击选中
  _use_novelty_in_bag(idx)    — 背包中使用杂货
  _sell_bag_item(idx)         — 背包出售物品
  _build_materials_tab()      — 材料买卖（4种材料×3档）
  _buy_mat(mat, amount)       — 购买材料 ✅
  _sell_mat(mat, amount)      — 出售材料 ✅
  _refresh_materials()        — 刷新材料显示
  _build_tavern_tab()         — 酒馆列表+招募+刷新
  _build_farm_tab()           — 农场种植/收获
  _build_factory_tab()        — 工坊部门/工人/利润
  _build_bottom_bar()         — 存档/读档/帮助按钮
  _refresh_log()              — 战斗日志刷新
  _refresh_all_ui()           — 全量 UI 刷新（0.3s 定时）
  _update_loop()              — 主循环（异步）
  _do_battle(e)               — 手动战斗 ✅
  _battle_thread(enemy, boss) — 战斗线程 ✅
  _toggle_auto(e)             — 自动战斗开关 ✅
  _refresh_enemy(e)           — 刷新敌人 ✅
  _change_map(map_name)       — 切换地图 ✅
  _switch_member(idx)         — 切换队伍成员 ✅
  _buy_potion(e)              — 购买药水 ✅
  _use_potion(e)              — 使用药水 ✅
  _on_auto_potion_change(e)   — 自动药水阈值切换 ✅
  _update_auto_potion_label() — 更新药水标签
  _restore_auto_potion_ui()   — 恢复药水 UI 状态
  _build_building(name)       — 建造建筑 ✅
  _upgrade_building(name)     — 升级建筑 ✅
  _build_wonder(name)         — 建造奇观 ✅
  _buy_weapon(wpn)            — 购买武器 ✅
  _buy_armor(arm)             — 购买护甲 ✅
  _buy_novelty(item)          — 购买杂货 ✅
  _recruit_member(ch)         — 招募队友 ✅
  _switch_to(idx)             — 切换到队友 ✅
  _kick_member_ui(idx)        — 踢出队友 ✅
  _tavern_refresh(e)          — 刷新酒馆 ✅
  _open_tavern_tab(e)         — 打开酒馆 Tab ✅
  _plant_seed(pd)             — 种植作物 ✅
  _harvest_plant(plant)       — 收获作物 ✅
  _build_factory_tab_action(e)— 工坊面板动作 ✅
  _buy_dept(dept_id)          — 购买部门 ✅
  _hire_factory_worker(e)     — 工坊雇工 ✅
  _fire_factory_worker(e)     — 工坊解工 ✅
  _hire_worker(name)          — 建筑雇工 ✅
  _fire_worker(name)          — 建筑解工 ✅
  _save(e)                    — 存档 ✅
  _load(e)                    — 读档 ✅
  _show_help(e)               — 帮助对话框
  _show_toast(msg)            — SnackBar 提示
```

---

## 七、关键连接点（game_core.py 方法）

| 功能 | game_core 方法 | 实际签名 |
|---|---|---|
| 战斗 | `battle()` / `battle_team()` | `battle(enemy_data, is_boss)` / `battle_team(enemy_data, is_boss)` |
| 刷新敌人 | `refresh_enemy()` | `refresh_enemy()` |
| 切换地图 | `change_map()` | `change_map(map_name)` |
| 购买药水 | `buy_potion()` | `buy_potion()` |
| 使用药水 | `use_potion()` | `use_potion()` |
| 自动药水阈值 | `set_auto_potion_threshold()` | `set_auto_potion_threshold(value)` |
| 招募队员 | `recruit_member()` | `recruit_member(role_name, level, cost, gear)` |
| 刷新酒馆 | `manual_refresh_tavern()` | `manual_refresh_tavern()` |
| 购买武器 | `buy_weapon()` | `buy_weapon(wpn)` |
| 购买护甲 | `buy_armor()` | `buy_armor(arm)` |
| 购买杂货 | `buy_novelty_item()` | `buy_novelty_item(item)` |
| 装备道具 | `hero.equip_item()` | `equip_item(index)` — 定义在 hero.py |
| 出售道具 | `hero.sell_item()` | `sell_item(index)` — 定义在 hero.py |
| 购买材料 | `buy_material()` | `buy_material(material, amount)` |
| 出售材料 | `sell_material()` | `sell_material(material, amount)` |
| 建造建筑 | `build_building()` | `build_building(name)` |
| 升级建筑 | `upgrade_building()` | `upgrade_building(name, idx)` |
| 建造奇观 | `build_wonder()` | `build_wonder(wonder_name)` |
| 雇佣劳工 | `hire_worker()` | `hire_worker(name, idx)` |
| 解雇劳工 | `fire_worker()` | `fire_worker(name, idx)` |
| 建造工坊 | `build_factory()` | `build_factory()` |
| 工坊部门解锁 | `buy_department()` | `buy_department(dept_id)` |
| 工坊雇工 | `hire_factory_worker()` | `hire_factory_worker()` |
| 工坊解工 | `fire_factory_worker()` | `fire_factory_worker()` |
| 工坊信息 | `get_factory_info()` | `get_factory_info()` |
| 存档/读档 | main_flet 直接 JSON | 不经过 game_core，`_save()` / `_load()` 内联实现 |

---

*最后更新：2026-04-22 00:53 (全部 Phase 完成)*
