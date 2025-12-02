import sys

file_path = r'c:\workspace\Eroom-Studio\app\templates\admin\dashboard.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add empty state for floor plan view when there's a floor plan but no rooms
old_text = """                                                        </template>
                                                    </div>
                                                </template>
                                                <template x-if="!floorPlans[selectedFloor]">"""

new_text = """                                                        </template>
                                                        <!-- Empty State: Floor plan exists but no rooms -->
                                                        <template x-if="(!roomsByFloor[selectedFloor] || roomsByFloor[selectedFloor].length === 0)">
                                                            <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
                                                                <div class="bg-white/90 backdrop-blur-sm rounded-xl p-6 shadow-lg text-center">
                                                                    <i class="ri-inbox-line text-4xl text-gray-400 mb-2"></i>
                                                                    <p class="text-lg font-medium text-gray-900">이 층에 등록된 방이 없습니다</p>
                                                                    <p class="text-sm text-gray-500 mt-1">방을 추가하고 도면 위에 배치하세요.</p>
                                                                </div>
                                                            </div>
                                                        </template>
                                                    </div>
                                                </template>
                                                <template x-if="!floorPlans[selectedFloor]">"""

if old_text in content:
    content = content.replace(old_text, new_text)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ Floor plan view empty state added successfully!")
else:
    print("✗ Could not find the target text in the file")
