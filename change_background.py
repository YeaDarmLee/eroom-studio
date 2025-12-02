"""
Change grid background to plain gray when no floor plan image exists
"""

with open('app/templates/public/public_floor_plan_component.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Add new CSS class for no-image state
new_css = '''    .public-floor-plan-wrapper {
        position: relative;
        width: 100%;
        height: 480px;
        overflow: hidden;
        border-radius: 0.5rem;
    }

    .public-floor-plan-container.no-image {
        background-color: #e5e7eb;
        background-image: none;
    }
'''

old_css = '''    .public-floor-plan-wrapper {
        position: relative;
        width: 100%;
        height: 480px;
        overflow: hidden;
        border-radius: 0.5rem;
    }
'''

content = content.replace(old_css, new_css)

# Update the container div to conditionally add 'no-image' class
old_container = '''                    <div class="public-floor-plan-container">'''

new_container = '''                    <div class="public-floor-plan-container" :class="{ 'no-image': !floorPlans[selectedFloor] }">'''

content = content.replace(old_container, new_container)

with open('app/templates/public/public_floor_plan_component.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Updated floor plan background")
print("\nChanges:")
print("  - With floor plan image: Grid background (existing)")
print("  - Without floor plan image: Plain gray background (#e5e7eb)")
print("\nThe background now dynamically changes based on whether a floor plan exists!")
