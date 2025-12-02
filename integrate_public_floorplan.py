"""
Integrate Public Floor Plan Component into Branch Detail Page
"""

# Read branch_detail.html
with open('app/templates/public/branch_detail.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Read the new component
with open('app/templates/public/public_floor_plan_component.html', 'r', encoding='utf-8') as f:
    new_component = f.read()

# Find and replace the old floor plan section
# The section starts with <!-- Floor Plan Section --> and ends before <!-- Traffic & Parking -->

import re

# Pattern to match the entire floor plan section
pattern = r'<!-- Floor Plan Section -->.*?(?=<!-- Traffic & Parking -->)'

# Replace with the new component include
replacement = """<!-- Floor Plan Section (Real Admin-Configured Data) -->
    {% include 'public/public_floor_plan_component.html' %}

    """

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back
with open('app/templates/public/branch_detail.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Successfully integrated public floor plan component into branch_detail.html")
print("✓ Old SVG-based floor plan replaced with admin-configured data")
