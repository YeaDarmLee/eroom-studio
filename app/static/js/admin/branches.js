// app/static/js/admin/branches.js

document.addEventListener('alpine:init', () => {
    Alpine.data('branchesPage', () => ({
        // ==================== State Variables ====================

        // Branch Management
        branches: [],
        showModal: false,
        showDeleteConfirm: false,
        editMode: false,
        currentBranch: null,
        formData: {
            name: '',
            address: '',
            facilities: '',
            description: ''
        },

        // Room Management
        showRoomModal: false,
        showRoomFormModal: false,
        showRoomDeleteConfirm: false,
        roomEditMode: false,
        currentRoom: null,
        branchRooms: [],
        roomFormData: {
            name: '',
            price: '',
            description: '',
            floor: '1F'
        },

        // Floor Plan Management
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
        uploadingFloor: null,

        // Services Management
        showServicesModal: false,
        showServiceFormModal: false,
        serviceEditMode: false,
        currentService: null,
        commonServices: [],
        specializedServices: [],
        serviceFormData: {
            name: '',
            description: '',
            icon: '',
            service_type: 'common'
        },

        // ==================== Initialization ====================

        init() {
            this.loadBranches()
        },

        // ==================== Branch Management Methods ====================

        async loadBranches() {
            const token = localStorage.getItem('token')
            try {
                const response = await fetch('/admin/api/branches', {
                    headers: { Authorization: 'Bearer ' + token }
                })
                if (response.ok) {
                    this.branches = await response.json()
                }
            } catch (error) {
                console.error('Error loading branches:', error)
            }
        },

        openCreateModal() {
            this.editMode = false
            this.formData = {
                name: '',
                address: '',
                facilities: '',
                description: ''
            }
            this.showModal = true
        },

        openEditModal(branch) {
            this.editMode = true
            this.currentBranch = branch
            this.formData = { ...branch }
            this.showModal = true
        },

        async saveBranch() {
            const token = localStorage.getItem('token')
            const url = this.editMode
                ? `/admin/api/branches/${this.currentBranch.id}`
                : '/admin/api/branches'
            const method = this.editMode ? 'PUT' : 'POST'

            try {
                const response = await fetch(url, {
                    method,
                    headers: {
                        'Content-Type': 'application/json',
                        Authorization: 'Bearer ' + token
                    },
                    body: JSON.stringify(this.formData)
                })

                if (response.ok) {
                    this.showModal = false
                    await this.loadBranches()
                } else {
                    const data = await response.json()
                    alert(data.error || '지점 저장에 실패했습니다.')
                }
            } catch (error) {
                console.error('Error saving branch:', error)
                alert('오류가 발생했습니다.')
            }
        },

        confirmDelete(branch) {
            this.currentBranch = branch
            this.showDeleteConfirm = true
        },

        async deleteBranch() {
            const token = localStorage.getItem('token')
            try {
                const response = await fetch(`/admin/api/branches/${this.currentBranch.id}`, {
                    method: 'DELETE',
                    headers: { Authorization: 'Bearer ' + token }
                })

                if (response.ok) {
                    this.showDeleteConfirm = false
                    await this.loadBranches()
                } else {
                    const data = await response.json()
                    alert(data.error || '지점 삭제에 실패했습니다.')
                }
            } catch (error) {
                console.error('Error deleting branch:', error)
                alert('오류가 발생했습니다.')
            }
        },

        // ==================== Room Management Methods ====================

        async loadBranchRooms(branch) {
            const token = localStorage.getItem('token')
            this.currentBranch = branch
            try {
                const response = await fetch(`/admin/api/branches/${branch.id}`, {
                    headers: { Authorization: 'Bearer ' + token }
                })
                if (response.ok) {
                    const data = await response.json()
                    this.branchRooms = data.rooms || []
                    this.roomsByFloor = data.rooms_by_floor || {}
                    this.floorPlans = data.floor_plans || {}
                    this.showRoomModal = true
                }
            } catch (error) {
                console.error('Error loading rooms:', error)
            }
        },

        closeRoomModal() {
            this.showRoomModal = false
            this.branchRooms = []
            this.currentBranch = null
            this.viewMode = 'list'
            this.selectedFloor = '1F'
        },

        openCreateRoomModal() {
            this.roomEditMode = false
            this.roomFormData = {
                name: '',
                price: '',
                description: '',
                floor: '1F'
            }
            this.showRoomFormModal = true
        },

        openEditRoomModal(room) {
            this.roomEditMode = true
            this.currentRoom = room
            this.roomFormData = { ...room }
            this.showRoomFormModal = true
        },

        confirmDeleteRoom(room) {
            this.currentRoom = room
            this.showRoomDeleteConfirm = true
        },

        async saveRoom() {
            const token = localStorage.getItem('token')
            const url = this.roomEditMode
                ? `/admin/api/rooms/${this.currentRoom.id}`
                : '/admin/api/rooms'
            const method = this.roomEditMode ? 'PUT' : 'POST'
            const payload = this.roomEditMode
                ? this.roomFormData
                : { ...this.roomFormData, branch_id: this.currentBranch.id }

            try {
                const response = await fetch(url, {
                    method,
                    headers: {
                        'Content-Type': 'application/json',
                        Authorization: 'Bearer ' + token
                    },
                    body: JSON.stringify(payload)
                })

                if (response.ok) {
                    this.showRoomFormModal = false
                    await this.loadBranchRooms(this.currentBranch)
                } else {
                    const data = await response.json()
                    alert(data.error || '방 저장에 실패했습니다.')
                }
            } catch (error) {
                console.error('Error saving room:', error)
                alert('오류가 발생했습니다.')
            }
        },

        async deleteRoom() {
            const token = localStorage.getItem('token')
            try {
                const response = await fetch(`/admin/api/rooms/${this.currentRoom.id}`, {
                    method: 'DELETE',
                    headers: { Authorization: 'Bearer ' + token }
                })

                if (response.ok) {
                    this.showRoomDeleteConfirm = false
                    await this.loadBranchRooms(this.currentBranch)
                } else {
                    const data = await response.json()
                    alert(data.error || '방 삭제에 실패했습니다.')
                }
            } catch (error) {
                console.error('Error deleting room:', error)
                alert('오류가 발생했습니다.')
            }
        },

        // ==================== Floor Plan Methods ====================

        selectFloor(floor) {
            this.selectedFloor = floor
        },

        switchToFloorPlan() {
            this.viewMode = 'floorplan'
        },

        switchToList() {
            this.viewMode = 'list'
        },

        async uploadFloorPlan(event) {
            const file = event.target.files[0]
            if (!file) return

            const token = localStorage.getItem('token')
            const formData = new FormData()
            formData.append('file', file)

            this.uploadingFloor = this.selectedFloor

            try {
                const response = await fetch(
                    `/admin/api/branches/${this.currentBranch.id}/floors/${this.selectedFloor}/plan`,
                    {
                        method: 'POST',
                        headers: { Authorization: 'Bearer ' + token },
                        body: formData
                    }
                )

                if (response.ok) {
                    const data = await response.json()
                    this.floorPlans[this.selectedFloor] = data.image_url
                    alert('도면이 업로드되었습니다.')
                } else {
                    alert('도면 업로드에 실패했습니다.')
                }
            } catch (error) {
                console.error('Error uploading floor plan:', error)
                alert('오류가 발생했습니다.')
            } finally {
                this.uploadingFloor = null
                event.target.value = ''
            }
        },

        startDrag(room, event) {
            if (event.target.classList.contains('resize-handle')) return
            this.isDragging = true
            this.draggedRoom = room
            const rect = event.currentTarget.getBoundingClientRect()
            this.dragStartX = event.clientX - rect.left
            this.dragStartY = event.clientY - rect.top
            event.currentTarget.style.cursor = 'grabbing'
        },

        onDrag(event) {
            if (!this.isDragging || !this.draggedRoom) return
            const container = event.currentTarget.getBoundingClientRect()
            const x = event.clientX - container.left - this.dragStartX
            const y = event.clientY - container.top - this.dragStartY
            const xPercent = (x / container.width) * 100
            const yPercent = (y / container.height) * 100
            this.draggedRoom.position_x = Math.max(0, Math.min(95, xPercent))
            this.draggedRoom.position_y = Math.max(0, Math.min(95, yPercent))
        },

        endDrag(event) {
            if (this.isDragging) {
                this.isDragging = false
                if (event.currentTarget) event.currentTarget.style.cursor = 'grab'
                this.draggedRoom = null
            }
        },

        startResize(room, handle, event) {
            event.stopPropagation()
            this.isResizing = true
            this.draggedRoom = room
            this.resizeHandle = handle
            this.dragStartX = event.clientX
            this.dragStartY = event.clientY
        },

        onResize(event) {
            if (!this.isResizing || !this.draggedRoom) return
            const container = event.currentTarget.getBoundingClientRect()
            const deltaX = event.clientX - this.dragStartX
            const deltaY = event.clientY - this.dragStartY
            const deltaXPercent = (deltaX / container.width) * 100
            const deltaYPercent = (deltaY / container.height) * 100

            if (this.resizeHandle === 'se') {
                this.draggedRoom.width = Math.max(5, (this.draggedRoom.width || 10) + deltaXPercent)
                this.draggedRoom.height = Math.max(5, (this.draggedRoom.height || 10) + deltaYPercent)
            }

            this.dragStartX = event.clientX
            this.dragStartY = event.clientY
        },

        endResize() {
            this.isResizing = false
            this.draggedRoom = null
            this.resizeHandle = null
        },

        async saveRoomPositions() {
            const token = localStorage.getItem('token')
            const rooms = this.roomsByFloor[this.selectedFloor] || []
            const positions = rooms.map(room => ({
                id: room.id,
                x: room.position_x,
                y: room.position_y,
                w: room.width,
                h: room.height
            }))

            try {
                const response = await fetch(
                    `/admin/api/branches/${this.currentBranch.id}/floors/${this.selectedFloor}/positions`,
                    {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: 'Bearer ' + token
                        },
                        body: JSON.stringify({ positions })
                    }
                )

                if (response.ok) {
                    alert('방 위치가 저장되었습니다.')
                } else {
                    alert('저장에 실패했습니다.')
                }
            } catch (error) {
                console.error('Error saving positions:', error)
                alert('오류가 발생했습니다.')
            }
        },

        // ==================== Services Management Methods ====================

        async loadBranchServices(branch) {
            const token = localStorage.getItem('token')
            this.currentBranch = branch

            try {
                const response = await fetch(`/admin/api/branches/${branch.id}`, {
                    headers: { Authorization: 'Bearer ' + token }
                })
                if (response.ok) {
                    const data = await response.json()
                    this.commonServices = data.common_services || []
                    this.specializedServices = data.specialized_services || []
                    this.showServicesModal = true
                }
            } catch (error) {
                console.error('Error loading services:', error)
            }
        },

        closeServicesModal() {
            this.showServicesModal = false
            this.commonServices = []
            this.specializedServices = []
            this.currentBranch = null
        },

        openServiceForm(type) {
            this.serviceEditMode = false
            this.serviceFormData = {
                name: '',
                description: '',
                icon: '',
                service_type: type
            }
            this.showServiceFormModal = true
        },

        editService(service) {
            this.serviceEditMode = true
            this.currentService = service
            this.serviceFormData = { ...service }
            this.showServiceFormModal = true
        },

        async saveService() {
            const token = localStorage.getItem('token')
            const url = this.serviceEditMode
                ? `/admin/api/branches/${this.currentBranch.id}/services/${this.currentService.id}`
                : `/admin/api/branches/${this.currentBranch.id}/services`
            const method = this.serviceEditMode ? 'PUT' : 'POST'

            try {
                const response = await fetch(url, {
                    method,
                    headers: {
                        'Content-Type': 'application/json',
                        Authorization: 'Bearer ' + token
                    },
                    body: JSON.stringify(this.serviceFormData)
                })

                if (response.ok) {
                    this.showServiceFormModal = false
                    await this.loadBranchServices(this.currentBranch)
                    alert(this.serviceEditMode ? '서비스가 수정되었습니다.' : '서비스가 추가되었습니다.')
                } else {
                    alert('저장에 실패했습니다.')
                }
            } catch (error) {
                console.error('Error saving service:', error)
                alert('오류가 발생했습니다.')
            }
        },

        async deleteService(service) {
            if (!confirm(`"${service.name}" 서비스를 삭제하시겠습니까?`)) return

            const token = localStorage.getItem('token')
            try {
                const response = await fetch(
                    `/admin/api/branches/${this.currentBranch.id}/services/${service.id}`,
                    {
                        method: 'DELETE',
                        headers: { Authorization: 'Bearer ' + token }
                    }
                )

                if (response.ok) {
                    await this.loadBranchServices(this.currentBranch)
                    alert('서비스가 삭제되었습니다.')
                } else {
                    alert('삭제에 실패했습니다.')
                }
            } catch (error) {
                console.error('Error deleting service:', error)
                alert('오류가 발생했습니다.')
            }
        }
    }));
});
