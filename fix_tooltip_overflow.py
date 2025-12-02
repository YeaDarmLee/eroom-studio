"""
Fix tooltip overflow issue - make it visible outside container
"""

with open('app/templates/public/public_floor_plan_component.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Change 1: Update container to allow overflow
old_container_css = '''    .public-floor-plan-container {
        position: relative;
        width: 100%;
        height: 480px;
        background-color: #f3f4f6;
        background-image:
            linear-gradient(rgba(0, 0, 0, .03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 0, 0, .03) 1px, transparent 1px);
        background-size: 20px 20px;
        overflow: hidden;
        border-radius: 0.5rem;
    }'''

new_container_css = '''    .public-floor-plan-container {
        position: relative;
        width: 100%;
        height: 480px;
        background-color: #f3f4f6;
        background-image:
            linear-gradient(rgba(0, 0, 0, .03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 0, 0, .03) 1px, transparent 1px);
        background-size: 20px 20px;
        overflow: visible;
        border-radius: 0.5rem;
    }
    
    .public-floor-plan-wrapper {
        position: relative;
        width: 100%;
        height: 480px;
        overflow: hidden;
        border-radius: 0.5rem;
    }'''

content = content.replace(old_container_css, new_container_css)

# Change 2: Increase tooltip z-index significantly
old_tooltip_css = '''    .room-tooltip {
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%) translateY(-8px);
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 0.75rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        white-space: nowrap;
        z-index: 1000;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.2s, transform 0.2s;
    }'''

new_tooltip_css = '''    .room-tooltip {
        position: fixed;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 0.75rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        white-space: nowrap;
        z-index: 9999;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.2s, transform 0.2s;
    }'''

content = content.replace(old_tooltip_css, new_tooltip_css)

# Change 3: Update room box to have higher z-index on hover
old_room_box_hover = '''    .public-room-box:hover {
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        background-color: rgba(59, 130, 246, 0.4);
        transform: translateY(-2px);
    }'''

new_room_box_hover = '''    .public-room-box:hover {
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        background-color: rgba(59, 130, 246, 0.4);
        transform: translateY(-2px);
        z-index: 100;
    }'''

content = content.replace(old_room_box_hover, new_room_box_hover)

# Change 4: Remove the arrow since we're using fixed positioning
old_arrow = '''    .room-tooltip::after {
        content: '';
        position: absolute;
        top: 100%;
        left: 50%;
        transform: translateX(-50%);
        border: 6px solid transparent;
        border-top-color: white;
    }'''

content = content.replace(old_arrow, '')

# Change 5: Update the tooltip to use Alpine.js for positioning
old_tooltip_div = '''                            <!-- Hover Tooltip -->
                            <div class="room-tooltip">'''

new_tooltip_div = '''                            <!-- Hover Tooltip -->
                            <div class="room-tooltip" 
                                x-ref="tooltip"
                                @mouseenter.window="
                                    const rect = $el.parentElement.getBoundingClientRect();
                                    $el.style.left = rect.left + (rect.width / 2) + 'px';
                                    $el.style.top = rect.top - 10 + 'px';
                                    $el.style.transform = 'translate(-50%, -100%)';
                                "
                                @mouseleave.window="
                                    $el.style.opacity = '0';
                                ">'''

content = content.replace(old_tooltip_div, new_tooltip_div)

# Change 6: Wrap the floor plan container
old_wrapper = '''                <!-- Floor Plan Canvas -->
                <div class="public-floor-plan-container">'''

new_wrapper = '''                <!-- Floor Plan Canvas -->
                <div class="public-floor-plan-wrapper">
                    <div class="public-floor-plan-container">'''

content = content.replace(old_wrapper, new_wrapper)

# Add closing wrapper div before the closing of floor plan container section
old_closing = '''                </div>

                <!-- Instructions -->'''

new_closing = '''                    </div>
                </div>

                <!-- Instructions -->'''

content = content.replace(old_closing, new_closing)

with open('app/templates/public/public_floor_plan_component.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Fixed tooltip overflow issue")
print("\nChanges made:")
print("  1. Changed container overflow to visible")
print("  2. Added wrapper with overflow hidden for floor plan")
print("  3. Changed tooltip to fixed positioning")
print("  4. Increased z-index to 9999")
print("  5. Room box gets z-index 100 on hover")
print("  6. Tooltip now appears above all other elements")
