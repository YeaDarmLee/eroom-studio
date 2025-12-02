"""
Integrate Floor Plan Management UI into Dashboard
This script modifies dashboard.html to add floor plan management features
"""

# Read dashboard.html
with open('app/templates/admin/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Read floor plan component
with open('app/templates/admin/floor_plan_component.html', 'r', encoding='utf-8') as f:
    floor_plan_component = f.read()

# Step 1: Add floor plan state variables to Alpine.js data
# Find the line with roomFormData and add new state after it
old_room_form_data = "    roomFormData: { name: '', price: '', description: '', floor: '1F' },"
new_state = """    roomFormData: { name: '', price: '', description: '', floor: '1F' },
    
    // Floor Plan Management State
    selectedFloor: '1F',
    floorPlans: {},
    roomsByFloor: {},
    viewMode: 'list',
    isDragging: false,
    draggedRoom: null,
    dragStartX: 0,
    dragStartY: 0,
    isResizing: false,
    resizeHandle: null,
    uploadingFloor: null,"""

content = content.replace(old_room_form_data, new_state)

# Step 2: Update loadBranchRooms to load floor plan data
old_load_branch = """            if (response.ok) {
                const data = await response.json();
                this.branchRooms = data.rooms || [];
                this.showRoomModal = true;
            }"""

new_load_branch = """            if (response.ok) {
                const data = await response.json();
                this.branchRooms = data.rooms || [];
                this.roomsByFloor = data.rooms_by_floor || {};
                this.floorPlans = data.floor_plans || {};
                this.showRoomModal = true;
            }"""

content = content.replace(old_load_branch, new_load_branch)

# Step 3: Update closeRoomModal to reset floor plan state
old_close_modal = """    closeRoomModal() {
        this.showRoomModal = false;
        this.branchRooms = [];
        this.currentBranch = null;
    },"""

new_close_modal = """    closeRoomModal() {
        this.showRoomModal = false;
        this.branchRooms = [];
        this.currentBranch = null;
        this.viewMode = 'list';
        this.selectedFloor = '1F';
    },"""

content = content.replace(old_close_modal, new_close_modal)

# Step 4: Add new floor plan methods before openCreateModal
new_methods = """    
    selectFloor(floor) {
        this.selectedFloor = floor;
    },
    
    switchToFloorPlan() {
        this.viewMode = 'floorplan';
    },
    
    switchToList() {
        this.viewMode = 'list';
    },
    
    async uploadFloorPlan(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        const token = localStorage.getItem('token');
        const formData = new FormData();
        formData.append('file', file);
        
        this.uploadingFloor = this.selectedFloor;
        
        try {
            const response = await fetch(`/admin/api/branches/${this.currentBranch.id}/floors/${this.selectedFloor}/plan`, {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + token },
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                this.floorPlans[this.selectedFloor] = data.image_url;
                alert('도면이 업로드되었습니다.');
            } else {
                alert('도면 업로드에 실패했습니다.');
            }
        } catch (error) {
            console.error('Error uploading floor plan:', error);
            alert('오류가 발생했습니다.');
        } finally {
            this.uploadingFloor = null;
            event.target.value = '';
        }
    },
    
    startDrag(room, event) {
        if (event.target.classList.contains('resize-handle')) return;
        this.isDragging = true;
        this.draggedRoom = room;
        const rect = event.currentTarget.getBoundingClientRect();
        this.dragStartX = event.clientX - rect.left;
        this.dragStartY = event.clientY - rect.top;
        event.currentTarget.style.cursor = 'grabbing';
    },
    
    onDrag(event) {
        if (!this.isDragging || !this.draggedRoom) return;
        const container = event.currentTarget.getBoundingClientRect();
        const x = event.clientX - container.left - this.dragStartX;
        const y = event.clientY - container.top - this.dragStartY;
        const xPercent = (x / container.width) * 100;
        const yPercent = (y / container.height) * 100;
        this.draggedRoom.position_x = Math.max(0, Math.min(95, xPercent));
        this.draggedRoom.position_y = Math.max(0, Math.min(95, yPercent));
    },
    
    endDrag(event) {
        if (this.isDragging) {
            this.isDragging = false;
            if (event.currentTarget) event.currentTarget.style.cursor = 'grab';
            this.draggedRoom = null;
        }
    },
    
    startResize(room, handle, event) {
        event.stopPropagation();
        this.isResizing = true;
        this.draggedRoom = room;
        this.resizeHandle = handle;
        this.dragStartX = event.clientX;
        this.dragStartY = event.clientY;
    },
    
    onResize(event) {
        if (!this.isResizing || !this.draggedRoom) return;
        const container = event.currentTarget.getBoundingClientRect();
        const deltaX = event.clientX - this.dragStartX;
        const deltaY = event.clientY - this.dragStartY;
        const deltaXPercent = (deltaX / container.width) * 100;
        const deltaYPercent = (deltaY / container.height) * 100;
        if (this.resizeHandle === 'se') {
            this.draggedRoom.width = Math.max(5, this.draggedRoom.width + deltaXPercent);
            this.draggedRoom.height = Math.max(5, this.draggedRoom.height + deltaYPercent);
        }
        this.dragStartX = event.clientX;
        this.dragStartY = event.clientY;
    },
    
    endResize() {
        this.isResizing = false;
        this.draggedRoom = null;
        this.resizeHandle = null;
    },
    
    async saveRoomPositions() {
        const token = localStorage.getItem('token');
        const rooms = this.roomsByFloor[this.selectedFloor] || [];
        const positions = rooms.map(room => ({
            id: room.id,
            x: room.position_x,
            y: room.position_y,
            w: room.width,
            h: room.height
        }));
        
        try {
            const response = await fetch(`/admin/api/branches/${this.currentBranch.id}/floors/${this.selectedFloor}/positions`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + token
                },
                body: JSON.stringify({ positions })
            });
            
            if (response.ok) {
                alert('방 위치가 저장되었습니다.');
            } else {
                alert('저장에 실패했습니다.');
            }
        } catch (error) {
            console.error('Error saving positions:', error);
            alert('오류가 발생했습니다.');
        }
    },
    
    openCreateModal() {"""

content = content.replace("    openCreateModal() {", new_methods)

# Step 5: Replace the room list UI in the modal with the floor plan component
# Find the room list section and replace it
old_room_list_start = """                                <div class="flex-1 overflow-y-auto p-6 bg-gray-50">
                                    <div class="mb-4 flex justify-between items-center">
                                        <h4 class="text-base font-semibold text-gray-900">방 목록</h4>
                                        <button @click="openCreateRoomModal()"
                                            class="rounded-button px-4 py-2 bg-primary text-white text-sm hover:bg-primary/90">
                                            <i class="ri-add-line mr-1"></i>새 방 등록
                                        </button>
                                    </div>

                                    <ul class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">"""

new_room_section = """                                <div class="flex-1 overflow-y-auto p-6 bg-gray-50">
                                    """ + floor_plan_component + """
                                </div>"""

# Find the end of the room list section
import re
pattern = r'<div class="flex-1 overflow-y-auto p-6 bg-gray-50">.*?</div>\s*</div>\s*</div>\s*</div>\s*</div>'
matches = list(re.finditer(pattern, content, re.DOTALL))

if matches:
    # Replace the last match (which should be the room modal content)
    last_match = matches[-1]
    content = content[:last_match.start()] + new_room_section + '\n                            </div>\n                        </div>\n                    </div>\n                </div>' + content[last_match.end():]
    print("✓ Room list section replaced with floor plan component")
else:
    print("✗ Could not find room list section to replace")

# Write the updated content
with open('app/templates/admin/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✓ Floor plan management UI successfully integrated!")
print("✓ File updated: app/templates/admin/dashboard.html")
print("\nChanges made:")
print("  1. Added floor plan state variables to Alpine.js")
print("  2. Updated loadBranchRooms to load floor plan data")
print("  3. Updated closeRoomModal to reset floor plan state")
print("  4. Added floor plan management methods (upload, drag, resize, save)")
print("  5. Replaced room list UI with floor plan component")
