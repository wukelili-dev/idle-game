# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('D:/pyproject/hero_workshop/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    stripped = line.rstrip()
    if any(x in stripped for x in ['item_type', 'novelty', '杂货', 'plant_seed', 'E', 'S', '装备', 'type_lbl']):
        print(f'L{i}: {stripped}')
