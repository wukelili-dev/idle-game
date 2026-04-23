# 勇者工坊 — 使用与维护手册

> 勇者工坊 v5.x（Flet UI），Python + Flet 0.84 放置类挂机游戏。
> 迁移完成日期：2026-04-22。原 Tkinter 版本归档为 `main_tkinter.py`。

---

## 一、项目结构

```
D:\pyproject\hero_workshop\
├── main.py              # 当前唯一入口（Flet UI），约 1400 行
├── main_tkinter.py      # 归档：原 Tkinter UI，保留供参考
├── modules\
│   ├── game_core.py     # 游戏核心逻辑（无 UI 依赖）
│   ├── hero.py          # 英雄属性、背包、队伍
│   ├── tavern.py        # 酒馆招募系统
│   ├── buildings.py     # 建筑、奇观配置
│   ├── equipment.py     # 装备定义（20 武器 + 20 护甲）
│   ├── equipment_drops.py  # 装备掉落生成
│   ├── maps.py          # 地图和怪物数据
│   ├── plants.py        # 农场种植系统
│   ├── factory.py       # 工坊系统
│   └── inventory.py     # 杂货物品定义
└── README.md            # changelog（当前 v5.4）
```

**核心原则**：`modules/` 目录零 UI 依赖，全部复用。游戏逻辑改动直接改 modules/，无需碰 main.py。

---

## 二、运行方式

```bash
cd D:\pyproject\hero_workshop
python main.py
```

- 首次运行 Flet 会下载 Chromium（约 150MB），后续启动即开即用
- 调试输出（print）会打印到终端，不是 Flet 窗口内

---

## 三、当前功能一览

| 模块 | 状态 | 说明 |
|------|------|------|
| 资源生产 | ✅ | 木材/铁矿/皮革/石头自动产出 |
| 战斗系统 | ✅ | 主角 + 队友自动战斗，队伍随机出手顺序 |
| 装备商店 | ✅ | 20 武器 + 20 护甲，支持稀有度颜色 |
| 背包系统 | ✅ | 20 格，装备/出售/使用杂货 |
| 地图探索 | ✅ | 4 张地图，17 种怪物 + 8 个 BOSS（装备掉率×2）|
| 酒馆系统 | ✅ | 招募队友，精英角色需 player_level >= 5 |
| 建筑系统 | ✅ | 4 种建筑，多实例独立卡片，每工人 +50% 产量 |
| 奇观系统 | ✅ | 6 种奇观，建造后持续产出 |
| 农场 | ✅ | 种植/收获循环 |
| 工坊 | ✅ | 部门解锁 + 劳工雇佣 |
| 存档/读档 | ✅ | JSON 文件，自动存档路径 |
| 材料买卖 | ✅ | 买价 = 卖价 × 2 |

---

## 四、Flet 0.84 API 速查

> 踩过的坑，记录在此，避免重蹈覆辙。

### 对话框

```python
# 弹出
page.show_dialog(dlg)
# 关闭
page.pop_dialog()
# ❌ 旧写法（Flet 0.84 不生效）
page.dialog = dlg; page.update()
```

### 拖拽事件

```python
# 坐标
e.global_position.x        # ❌ e.global_x 已废弃
# 增量（直接用）
e.global_delta.x
```

### 颜色枚举

```python
ft.Colors.XXX              # ✅ 大写 C
ft.colors.XXX              # ❌ 小写 c 报错
ft.Colors.SURFACE_VARIANT  # ❌ 此颜色不存在
ft.Colors.SURFACE_CONTAINER_LOW  # ✅ 替代方案
```

### ElevatedButton

```python
Button("文本")             # ✅ Flet 0.84 移除了 text= 参数
ft.ElevatedButton          # ✅ 已 alias 为 Button
```

### Tabs 组件

```python
# ✅ 三件套写法
tab_content = ft.TabBarView(controls=[weapon_list, armor_list, ...])
right_panel.content = ft.Tabs(
    content=tab_content,
    tabs=[
        ft.Tab(label="武器", icon=ft.icons.Icons.XXX),
        ...
    ],
    selected_index=0,
)
# ❌ 旧写法（Tab(content=...)）已完全废弃
```

### padding / border / margin

```python
ft.padding.all(x)      # ❌
Padding.all(x)          # ✅ 或直接 padding=x
ft.border.all(w, c)    # ❌
Border.all(w, c)        # ✅
```

### SnackBar

```python
page.show_snack_bar(ft.SnackBar(ft.Text(msg), duration=2000))
```

### AppBar actions

```python
# ✅ 构造后赋值
bar = ft.AppBar(title=ft.Text("勇者工坊"))
bar.actions = [save_btn, help_btn]
# ❌ 构造时传 actions=（无效 kwarg）
```

### 启动入口

```python
def main(page: ft.Page):
    app = HeroWorkshopApp(page)
ft.app(main)
```

### Icons

```python
ft.icons.Icons.XXX     # ✅ 带 .Icons. 前缀
ft.icons.XXX           # ❌ 部分图标不存在
# 常用确认
ft.icons.Icons.MENU, SHOPPING_CART, ADD, REMOVE, AGRICULTURE, SAVE, HELP
```

---

## 五、Changelog

### v5.4 — 2026-04-23
- **Flet 迁移完成**：`main.py` 替换为 Flet UI，`main_tkinter.py` 归档
- **UI 重构**：三栏可拖拽布局（Row + GestureDetector 分隔条）
- **酒馆系统**：酒馆 Tab 重写，支持招募、刷新、踢出队友
- **自动药水**：可配置阈值（关闭/30%/50%/80%）
- **Boss 机制**：5% 概率出现，装备掉率 × 2
- **杂货铺**：26 种随机趣味物品，5 个稀有度等级
- **对话 API 迁移**：旧 `page.dialog=` → `show_dialog()/pop_dialog()`
- **拖拽 API 迁移**：`e.global_x` → `e.global_position.x / e.global_delta.x`
- **建筑多实例**：每种建筑独立卡片，工人数量/升级独立
- **工人产量加成**：`game_core.produce_resource()` 传入 `worker_count`
- **session 崩溃修复**：`_update_loop` 末尾加 `page.update()`

### v5.3 — 2026-04-22
- **酒馆分级限制**：精英角色需 player_level >= 5
- **UI 全汉化**：所有 UI 文本、装备名、建筑名、地图名汉化
- **存档/帮助/主循环**：完善存档/读档功能，帮助弹窗

### v5.2 — 2026-04-21
- **Bug 修复**：自动战斗敌人切换、材料数量刷新
- **出售功能**：商店装备 80% 原价，掉落装备按属性计算

### v5.1 — 2026-04-21
- **Flet 迁移 Phase 1-7 完成**
- **Tkinter → Flet 迁移**：UI 全面重写
- **PopupMenuButton 替换**：改用 IconButton + AlertDialog

### v5.0 — 2026-04-21
- **酒馆/队友系统**：5 种职业，队伍战斗（最多 3 人），随机出手顺序
- **招募系统**：普通/精英分级，酒馆每小时刷新

---

## 六、已知问题 / 待处理

- 🔴 **全屏左栏顶部大空白** — Row 三栏布局高度分配问题，原因仍在排查
- 🟡 **_update_loop session 销毁崩溃** — 窗口关闭后循环未退出，`RuntimeError: session destroyed`，方案：循环体包 try/except + `break`
- 🟡 **酒馆标签顶栏底色** — `_build_tavern_tab()` 内棕色背景待改为浅色（`ft.Colors.SURFACE_CONTAINER_LOW`）

---

## 七、游戏数据速查

### 装备稀有度与售价系数

| 稀有度 | 售价系数 |
|--------|---------|
| 普通 | × 0.8 |
| 稀有 | × 1.0 |
| 史诗 | × 1.3 |
| 传说 | × 1.8 |
| 极品 | × 2.5 |

### 材料价格

| 材料 | 卖价 | 买价 |
|------|------|------|
| 木材 | 2G | 4G |
| 铁矿 | 3G | 6G |
| 皮革 | 2G | 4G |
| 石头 | 1G | 2G |

### 招募费用

- 普通角色：主角等级 × 100G
- 精英角色：主角等级 × 200G（需等级 ≥ 5）

### 工人加成

- 每工人：对应建筑产量 +50%
- `BuildingConfig.get_output(level, worker_count)` 计算

---

*最后更新：2026-04-23 16:21*
