"""
Add Floor Plan Management UI to Admin Dashboard
This script adds floor plan upload and drag & drop room positioning features
"""

import re

# Read the current dashboard.html
with open('app/templates/admin/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the Alpine.js data section for branches tab
# We need to add new state variables after roomFormData

new_state_vars = """    roomFormData: { name: '', price: '', description: '', floor: '1F' },
    
    // Floor Plan Management State
    selectedFloor: '1F',
    floorPlans: {},
    roomsByFloor: {},
    viewMode: 'list', // 'list' or 'floorplan'
    isDragging: false,
    draggedRoom: null,
    dragStartX: 0,
    dragStartY: 0,
    isResizing: false,
    resizeHandle: null,
    uploadingFloor: null,"""

# Replace the old roomFormData line
content = content.replace(
    "    roomFormData: { name: '', address: '', facilities: '', description: '', floor: '1F' },",
    new_state_vars
)

# Add new methods after loadBranchRooms
new_methods = """
    
    async loadBranchRooms(branch) {
        const token = localStorage.getItem('token');
        this.currentBranch = branch;
        try {
            const response = await fetch(`/admin/api/branches/${branch.id}`, {
                headers: { 'Authorization': 'Bearer ' + token }
            });
            if (response.ok) {
                const data = await response.json();
                this.branchRooms = data.rooms || [];
                this.roomsByFloor = data.rooms_by_floor || {};
                this.floorPlans = data.floor_plans || {};
                this.showRoomModal = true;
            }
        } catch (error) {
            console.error('Error loading rooms:', error);
        }
    },
    
    closeRoomModal() {
        this.showRoomModal = false;
        this.branchRooms = [];
        this.currentBranch = null;
        this.viewMode = 'list';
        this.selectedFloor = '1F';
    },
    
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
                headers: {
                    'Authorization': 'Bearer ' + token
                },
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
        const container = event.currentTarget.parentElement.getBoundingClientRect();
        
        this.dragStartX = event.clientX - rect.left;
        this.dragStartY = event.clientY - rect.top;
        
        event.currentTarget.style.cursor = 'grabbing';
    },
    
    onDrag(event) {
        if (!this.isDragging || !this.draggedRoom) return;
        
        const container = event.currentTarget.getBoundingClientRect();
        const x = event.clientX - container.left - this.dragStartX;
        const y = event.clientY - container.top - this.dragStartY;
        
        // Convert to percentage
        const xPercent = (x / container.width) * 100;
        const yPercent = (y / container.height) * 100;
        
        // Update room position
        this.draggedRoom.position_x = Math.max(0, Math.min(95, xPercent));
        this.draggedRoom.position_y = Math.max(0, Math.min(95, yPercent));
    },
    
    endDrag(event) {
        if (this.isDragging) {
            this.isDragging = false;
            if (event.currentTarget) {
                event.currentTarget.style.cursor = 'grab';
            }
            this.draggedRoom = null;
        }
    },
    
    startResize(room, handle, event) {
        event.stopPropagation();
        this.isResizing = true;
        this.draggedRoom = room;
        this.resizeHandle = handle;
        
        const rect = event.currentTarget.parentElement.getBoundingClientRect();
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
        
        // Update room size based on handle
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
    },"""

# Find and replace the loadBranchRooms and closeRoomModal methods
old_load_pattern = r"async loadBranchRooms\(branch\) \{[^}]+\}[^}]+closeRoomModal\(\) \{[^}]+\},"
content = re.sub(old_load_pattern, new_methods[5:], content, flags=re.DOTALL)

print("Floor plan management methods added successfully!")
print("File updated: app/templates/admin/dashboard.html")
