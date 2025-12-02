"""
Update public floor plan component to show rooms even without floor plan images
"""

with open('app/templates/public/public_floor_plan_component.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Change 1: Update the condition to check roomsByFloor instead of floorPlans
content = content.replace(
    '<!-- Check if any floor plans exist -->',
    '<!-- Check if any rooms with positions exist -->'
)

content = content.replace(
    '<template x-if="Object.keys(floorPlans).length === 0">',
    '<template x-if="Object.keys(roomsByFloor).length === 0">'
)

content = content.replace(
    '<p class="text-gray-500 font-medium mb-2">도면이 준비 중입니다</p>',
    '<p class="text-gray-500 font-medium mb-2">배치도가 준비 중입니다</p>'
)

# Change 2: Update the floor plan view condition
content = content.replace(
    '<!-- Floor Plan View -->',
    '<!-- Floor Plan View (Shows even without floor plan image if rooms have positions) -->'
)

content = content.replace(
    '<template x-if="Object.keys(floorPlans).length > 0">',
    '<template x-if="Object.keys(roomsByFloor).length > 0">'
)

# Change 3: Update floor tabs to use roomsByFloor
content = content.replace(
    '<template x-for="(planUrl, floor) in floorPlans" :key="floor">',
    '<template x-for="(rooms, floor) in roomsByFloor" :key="floor">'
)

# Change 4: Add info message when floor plan image is missing
info_message = '''                    
                    <!-- No Floor Plan Message (but rooms exist) -->
                    <div 
                        x-show="!floorPlans[selectedFloor] && (roomsByFloor[selectedFloor] || []).length > 0"
                        class="absolute top-4 left-4 bg-blue-50 border border-blue-200 rounded-lg px-4 py-2 text-sm text-blue-800 z-10">
                        <i class="ri-information-line mr-1"></i>
                        도면 이미지는 준비 중이며, 방 위치만 표시됩니다
                    </div>
'''

# Insert after the floor plan image
content = content.replace(
    '                    <!-- Room Boxes -->',
    info_message + '\n                    <!-- Room Boxes -->'
)

# Change 5: Add conditional instruction
old_instruction = '''                                <li><span class="text-gray-600 font-semibold">회색</span> 방은 이미 계약된 방입니다</li>
                            </ul>'''

new_instruction = '''                                <li><span class="text-gray-600 font-semibold">회색</span> 방은 이미 계약된 방입니다</li>
                                <li x-show="!floorPlans[selectedFloor]" class="text-blue-600">도면 이미지는 준비 중이며, 방 위치는 참고용입니다</li>
                            </ul>'''

content = content.replace(old_instruction, new_instruction)

# Change 6: Update init to select first floor from roomsByFloor if no floorPlans
old_init = '''                // Set first available floor as selected
                const availableFloors = Object.keys(this.floorPlans);
                if (availableFloors.length > 0) {
                    this.selectedFloor = availableFloors[0];
                }'''

new_init = '''                // Set first available floor as selected (prefer floorPlans, fallback to roomsByFloor)
                const availableFloors = Object.keys(this.floorPlans).length > 0 
                    ? Object.keys(this.floorPlans) 
                    : Object.keys(this.roomsByFloor);
                if (availableFloors.length > 0) {
                    this.selectedFloor = availableFloors[0];
                }'''

content = content.replace(old_init, new_init)

with open('app/templates/public/public_floor_plan_component.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Updated public floor plan component")
print("✓ Now shows room positions even without floor plan images")
print("\nChanges made:")
print("  1. Changed condition to check roomsByFloor instead of floorPlans")
print("  2. Floor tabs now show all floors with rooms")
print("  3. Added info message when floor plan image is missing")
print("  4. Added conditional instruction about missing floor plan")
print("  5. Updated init to select first floor from rooms if no floor plans")
