"""
Add hover tooltip to public floor plan component
"""

with open('app/templates/public/public_floor_plan_component.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Add tooltip CSS styles
tooltip_css = """
    .public-room-box.occupied:hover {
        background-color: rgba(127, 140, 141, 0.25);
        transform: none;
    }

    .room-tooltip {
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
    }

    .public-room-box:hover .room-tooltip {
        opacity: 1;
        transform: translateX(-50%) translateY(-12px);
    }

    .room-tooltip::after {
        content: '';
        position: absolute;
        top: 100%;
        left: 50%;
        transform: translateX(-50%);
        border: 6px solid transparent;
        border-top-color: white;
    }

    .room-tooltip-title {
        font-weight: 600;
        font-size: 0.875rem;
        color: #111827;
        margin-bottom: 0.5rem;
    }

    .room-tooltip-info {
        font-size: 0.75rem;
        color: #6b7280;
        line-height: 1.5;
    }

    .room-tooltip-status {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 500;
        margin-top: 0.5rem;
    }

    .room-tooltip-status.available {
        background-color: #dcfce7;
        color: #166534;
    }

    .room-tooltip-status.occupied {
        background-color: #f3f4f6;
        color: #6b7280;
    }

    .public-room-box.occupied .public-room-label {
        color: #7F8C8D;
    }
"""

# Insert tooltip CSS before the closing </style> tag
content = content.replace('</style>', tooltip_css + '\n</style>')

# Update the room box HTML to include tooltip
old_room_box = '''                        <div class="public-room-box" :class="getRoomStatusClass(room.status)"
                            :style="`left: ${room.position_x || 0}%; top: ${room.position_y || 0}%; width: ${room.width || 10}%; height: ${room.height || 10}%;`"
                            @click="room.status !== 'occupied' ? viewRoomDetail(room.id) : null">

                            <div class="public-room-label">
                                <div x-text="room.name"></div>
                                <div class="text-xs opacity-75" x-text="'₩' + (room.price / 10000) + '만'"></div>
                                <div class="text-xs mt-1" x-show="room.status === 'available'">
                                    <span class="bg-green-500 text-white px-2 py-0.5 rounded-full">계약가능</span>
                                </div>
                                <div class="text-xs mt-1" x-show="room.status === 'occupied'">
                                    <span class="bg-gray-500 text-white px-2 py-0.5 rounded-full">계약완료</span>
                                </div>
                            </div>
                        </div>'''

new_room_box = '''                        <div class="public-room-box" :class="getRoomStatusClass(room.status)"
                            :style="`left: ${room.position_x || 0}%; top: ${room.position_y || 0}%; width: ${room.width || 10}%; height: ${room.height || 10}%;`"
                            @click="room.status !== 'occupied' ? viewRoomDetail(room.id) : null">

                            <!-- Hover Tooltip -->
                            <div class="room-tooltip">
                                <div class="room-tooltip-title" x-text="room.name"></div>
                                <div class="room-tooltip-info">
                                    <div>월 임대료: <span class="font-semibold" x-text="'₩' + room.price.toLocaleString()"></span></div>
                                    <div x-show="room.description">설명: <span x-text="room.description"></span></div>
                                    <div>층: <span x-text="room.floor"></span></div>
                                </div>
                                <div class="room-tooltip-status" :class="room.status">
                                    <span x-show="room.status === 'available'">✓ 계약 가능</span>
                                    <span x-show="room.status === 'occupied'">✕ 계약 완료</span>
                                    <span x-show="room.status === 'reserved'">⏳ 검토 중</span>
                                </div>
                            </div>

                            <!-- Room Label -->
                            <div class="public-room-label">
                                <div x-text="room.name"></div>
                                <div class="text-xs opacity-75" x-text="'₩' + (room.price / 10000) + '만'"></div>
                            </div>
                        </div>'''

content = content.replace(old_room_box, new_room_box)

with open('app/templates/public/public_floor_plan_component.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Added hover tooltip to public floor plan component")
print("\nTooltip shows:")
print("  - Room name")
print("  - Monthly rent (formatted)")
print("  - Description (if available)")
print("  - Floor")
print("  - Status badge (available/occupied/reserved)")
print("\nTooltip appears on hover with smooth animation!")
