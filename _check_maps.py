# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('D:/pyproject/hero_workshop/modules/maps.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if hp/attack use Chinese keys
if '"hp"' in content or "'hp'" in content:
    print("HP uses Chinese key 'hp'")
if '"attack"' in content or "'attack'" in content:
    print("Attack uses Chinese key 'attack'")
if 'hp:' in content:
    print("HP uses English key hp:")
if 'attack:' in content:
    print("Attack uses English key attack:")

# Show first enemy dict
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'enemy' in line.lower() and ('{' in line or '[' in line):
        print(f"L{i+1}: {line.rstrip()}")
        # show next few lines
        for j in range(1, 8):
            if i+j < len(lines):
                print(f"L{i+1+j}: {lines[i+j].rstrip()}")
        break
