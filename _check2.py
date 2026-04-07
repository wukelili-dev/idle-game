# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('D:/pyproject/hero_workshop/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

count = content.count('"杂货"')
print(f'"杂货" occurrences in main.py: {count}')

count2 = content.count("'杂货'")
print(f"'杂货' occurrences in main.py: {count2}")
