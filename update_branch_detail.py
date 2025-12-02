import sys

file_path = r'c:\workspace\Eroom-Studio\app\templates\public\branch_detail.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add image column to the room table
old_text = """                    <tr class="border-b border-gray-200">
                        <th class="py-4 px-6 text-left font-medium text-gray-500">룸 타입</th>
                        <th class="py-4 px-6 text-left font-medium text-gray-500">월 임대료</th>"""

new_text = """                    <tr class="border-b border-gray-200">
                        <th class="py-4 px-6 text-left font-medium text-gray-500">이미지</th>
                        <th class="py-4 px-6 text-left font-medium text-gray-500">룸 타입</th>
                        <th class="py-4 px-6 text-left font-medium text-gray-500">월 임대료</th>"""

if old_text in content:
    content = content.replace(old_text, new_text)
    print("✓ Added image column header")
else:
    print("✗ Could not find table header")

# Add image cell to room rows
old_text2 = """                    <tr class="border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
                        onclick="location.href='/rooms/{{ room.id }}'">
                        <td class="py-4 px-6">
                            <div class="font-medium">{{ room.name }}</div>"""

new_text2 = """                    <tr class="border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
                        onclick="location.href='/rooms/{{ room.id }}'">
                        <td class="py-4 px-6">
                            {% if room.images and room.images|length > 0 %}
                            <img src="{{ room.images[0].url }}" alt="{{ room.name }}" class="w-16 h-16 object-cover rounded-lg">
                            {% else %}
                            <div class="w-16 h-16 bg-gray-200 rounded-lg flex items-center justify-center">
                                <i class="ri-image-line text-gray-400"></i>
                            </div>
                            {% endif %}
                        </td>
                        <td class="py-4 px-6">
                            <div class="font-medium">{{ room.name }}</div>"""

if old_text2 in content:
    content = content.replace(old_text2, new_text2)
    print("✓ Added image cell to room rows")
else:
    print("✗ Could not find room row")

# Also update the fallback static row
old_text3 = """                    <tr class="border-b border-gray-100 hover:bg-gray-50 cursor-pointer">
                        <td class="py-4 px-6">
                            <div class="font-medium">A타입</div>"""

new_text3 = """                    <tr class="border-b border-gray-100 hover:bg-gray-50 cursor-pointer">
                        <td class="py-4 px-6">
                            <div class="w-16 h-16 bg-gray-200 rounded-lg flex items-center justify-center">
                                <i class="ri-image-line text-gray-400"></i>
                            </div>
                        </td>
                        <td class="py-4 px-6">
                            <div class="font-medium">A타입</div>"""

if old_text3 in content:
    content = content.replace(old_text3, new_text3)
    print("✓ Added image cell to fallback row")
else:
    print("✗ Could not find fallback row")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✓ Branch detail page updated successfully!")
