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
            description: '',
            image_url: ''
        },
        newFloorInput: '', // For inline floor addition
        imageFile: null,
        imagePreview: null,
        branchImages: [], // Array of {file: File, preview: string}
        existingBranchImages: [], // Array of {id: number, url: string}
        isDraggingBranchImage: false,
        loadingData: false, // Global loading state for async actions

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
            deposit: '',
            area: '',
            description: '',
            floor: '1F'
        },
        roomImages: [], // Array of {file: File, preview: string}
        existingRoomImages: [], // Array of {id: number, url: string}
        isDraggingRoomImage: false,

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
                description: '',
                image_url: ''
            }
            this.imageFile = null
            this.imagePreview = null
            this.branchImages = []
            this.existingBranchImages = []
            this.showModal = true
        },

        openEditModal(branch) {
            this.editMode = true
            this.currentBranch = branch
            this.formData = { ...branch }
            this.imageFile = null
            this.imagePreview = null
            this.branchImages = []
            this.existingBranchImages = branch.images ? [...branch.images] : []
            this.showModal = true
        },

        async saveBranch() {
            const token = localStorage.getItem('token')
            const url = this.editMode
                ? `/admin/api/branches/${this.currentBranch.id}`
                : '/admin/api/branches'
            const method = this.editMode ? 'PUT' : 'POST'

            try {
                const formData = new FormData()
                formData.append('name', this.formData.name)
                formData.append('address', this.formData.address || '')
                formData.append('facilities', this.formData.facilities || '')
                formData.append('description', this.formData.description || '')

                if (this.imageFile) {
                    formData.append('image', this.imageFile)
                }

                const response = await fetch(url, {
                    method,
                    headers: {
                        Authorization: 'Bearer ' + token
                    },
                    body: formData
                })

                if (response.ok) {
                    const data = await response.json()
                    const branchId = this.editMode ? this.currentBranch.id : data.id

                    // Upload images if any
                    if (this.branchImages.length > 0) {
                        await this.uploadBranchImages(branchId)
                    }

                    this.showModal = false
                    this.imageFile = null
                    this.imagePreview = null
                    this.branchImages = []
                    this.existingBranchImages = []
                    await this.loadBranches()
                    window.showAlert?.('성공', '지점 정보가 저장되었습니다.', 'success');
                } else {
                    const data = await response.json()
                    window.showAlert?.('저장 실패', data.error || '지점 저장에 실패했습니다.', 'error')
                }
            } catch (error) {
                console.error('Error saving branch:', error)
                window.showAlert?.('오류', '오류가 발생했습니다.', 'error')
            }
        },

        isDraggingImage: false, // For drag and drop UI state

        handleImageUpload(event) {
            const file = event.target.files[0]
            this.processImageFile(file)
            // Reset input value to allow selecting the same file again if needed
            event.target.value = ''
        },

        handleImageDrop(event) {
            this.isDraggingImage = false
            const file = event.dataTransfer.files[0]
            this.processImageFile(file)
        },

        processImageFile(file) {
            if (!file) return

            // Validate file size (5MB)
            if (file.size > 5 * 1024 * 1024) {
                window.showAlert?.('파일 크기 초과', '파일 크기는 5MB를 초과할 수 없습니다.', 'warning')
                return
            }

            // Validate file type
            if (!file.type.startsWith('image/')) {
                window.showAlert?.('형식 오류', '이미지 파일만 업로드 가능합니다.', 'warning')
                return
            }

            this.imageFile = file

            // Create preview
            const reader = new FileReader()
            reader.onload = (e) => {
                this.imagePreview = e.target.result
            },
                reader.readAsDataURL(file)
        },

        // ==================== Branch Multi-Image Methods ====================

        handleBranchImageUpload(event) {
            const files = Array.from(event.target.files)
            this.processBranchImageFiles(files)
            event.target.value = ''
        },

        handleBranchImageDrop(event) {
            this.isDraggingBranchImage = false
            const files = Array.from(event.dataTransfer.files)
            this.processBranchImageFiles(files)
        },

        processBranchImageFiles(files) {
            files.forEach(file => {
                if (!file.type.startsWith('image/')) {
                    window.showAlert?.('형식 오류', '이미지 파일만 업로드 가능합니다.', 'warning')
                    return
                }
                if (file.size > 5 * 1024 * 1024) {
                    window.showAlert?.('파일 크기 초과', '파일 크기는 5MB를 초과할 수 없습니다.', 'warning')
                    return
                }

                const reader = new FileReader()
                reader.onload = (e) => {
                    this.branchImages.push({
                        file: file,
                        preview: e.target.result
                    })
                }
                reader.readAsDataURL(file)
            })
        },

        removeBranchImage(index) {
            this.branchImages.splice(index, 1)
        },

        async deleteExistingBranchImage(imageId, branchId) {
            if (!confirm('이 이미지를 삭제하시겠습니까?')) return

            const token = localStorage.getItem('token')
            try {
                const response = await fetch(`/admin/api/branches/${branchId}/images/${imageId}`, {
                    method: 'DELETE',
                    headers: { Authorization: 'Bearer ' + token }
                })

                if (response.ok) {
                    this.existingBranchImages = this.existingBranchImages.filter(img => img.id !== imageId)
                    window.showAlert?.('성공', '이미지가 삭제되었습니다.', 'success');
                } else {
                    window.showAlert?.('삭제 실패', '이미지 삭제에 실패했습니다.', 'error')
                }
            } catch (error) {
                console.error('Error deleting image:', error)
                window.showAlert?.('오류', '오류가 발생했습니다.', 'error')
            }
        },

        async uploadBranchImages(branchId) {
            const token = localStorage.getItem('token')
            const formData = new FormData()

            this.branchImages.forEach(img => {
                formData.append('images', img.file)
            })

            try {
                const response = await fetch(`/admin/api/branches/${branchId}/images`, {
                    method: 'POST',
                    headers: { Authorization: 'Bearer ' + token },
                    body: formData
                })

                if (!response.ok) {
                    console.error('Failed to upload images')
                }
            } catch (error) {
                console.error('Error uploading images:', error)
            }
        },

        // ==================== Room Image Methods ====================

        handleRoomImageUpload(event) {
            const files = Array.from(event.target.files)
            this.processRoomImageFiles(files)
            event.target.value = ''
        },

        handleRoomImageDrop(event) {
            this.isDraggingRoomImage = false
            const files = Array.from(event.dataTransfer.files)
            this.processRoomImageFiles(files)
        },

        processRoomImageFiles(files) {
            files.forEach(file => {
                if (!file.type.startsWith('image/')) {
                    window.showAlert?.('형식 오류', '이미지 파일만 업로드 가능합니다.', 'warning')
                    return
                }
                if (file.size > 5 * 1024 * 1024) {
                    window.showAlert?.('파일 크기 초과', '파일 크기는 5MB를 초과할 수 없습니다.', 'warning')
                    return
                }

                const reader = new FileReader()
                reader.onload = (e) => {
                    this.roomImages.push({
                        file: file,
                        preview: e.target.result
                    })
                }
                reader.readAsDataURL(file)
            })
        },

        removeRoomImage(index) {
            this.roomImages.splice(index, 1)
        },

        async deleteExistingRoomImage(imageId, roomId) {
            if (!confirm('이 이미지를 삭제하시겠습니까?')) return

            const token = localStorage.getItem('token')
            try {
                const response = await fetch(`/admin/api/rooms/${roomId}/images/${imageId}`, {
                    method: 'DELETE',
                    headers: { Authorization: 'Bearer ' + token }
                })

                if (response.ok) {
                    this.existingRoomImages = this.existingRoomImages.filter(img => img.id !== imageId)
                    window.showAlert?.('성공', '이미지가 삭제되었습니다.', 'success');
                } else {
                    window.showAlert?.('삭제 실패', '이미지 삭제에 실패했습니다.', 'error')
                }
            } catch (error) {
                console.error('Error deleting image:', error)
                window.showAlert?.('오류', '오류가 발생했습니다.', 'error')
            }
        },

        async uploadRoomImages(roomId) {
            const token = localStorage.getItem('token')
            const formData = new FormData()

            this.roomImages.forEach(img => {
                formData.append('images', img.file)
            })

            try {
                const response = await fetch(`/admin/api/rooms/${roomId}/images`, {
                    method: 'POST',
                    headers: { Authorization: 'Bearer ' + token },
                    body: formData
                })

                if (!response.ok) {
                    console.error('Failed to upload images')
                }
            } catch (error) {
                console.error('Error uploading images:', error)
            }
        },

        removeImage() {
            this.imageFile = null
            this.imagePreview = null
            this.formData.image_url = ''
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
                    window.showAlert?.('성공', '지점이 삭제되었습니다.', 'success');
                } else {
                    const data = await response.json()
                    window.showAlert?.('삭제 실패', data.error || '지점 삭제에 실패했습니다.', 'error')
                }
            } catch (error) {
                console.error('Error deleting branch:', error)
                window.showAlert?.('오류', '오류가 발생했습니다.', 'error')
            }
        },

        // ==================== Floor Management Methods ====================

        async addFloor() {
            const floor = this.newFloorInput.trim()
            if (!floor) return

            const token = localStorage.getItem('token')
            try {
                const response = await fetch(`/admin/api/branches/${this.currentBranch.id}/floors`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        Authorization: 'Bearer ' + token
                    },
                    body: JSON.stringify({ floor })
                })

                if (response.ok) {
                    await this.loadBranches() // Reload to get updated floors
                    // Also update currentBranch.floors locally if needed
                    const updatedBranch = this.branches.find(b => b.id === this.currentBranch.id)
                    if (updatedBranch) {
                        this.currentBranch = updatedBranch
                        this.formData = { ...updatedBranch }
                    }
                    this.newFloorInput = '' // Clear input
                    window.showAlert?.('성공', '층이 추가되었습니다.', 'success');
                } else {
                    const data = await response.json()
                    window.showAlert?.('추가 실패', data.error || '층 추가에 실패했습니다.', 'error')
                }
            } catch (error) {
                console.error('Error adding floor:', error)
                window.showAlert?.('오류', '오류가 발생했습니다.', 'error')
            }
        },

        async removeFloor(floor) {
            if (!confirm(`"${floor}" 층을 삭제하시겠습니까?`)) return

            const token = localStorage.getItem('token')
            try {
                const response = await fetch(`/admin/api/branches/${this.currentBranch.id}/floors/${floor}`, {
                    method: 'DELETE',
                    headers: { Authorization: 'Bearer ' + token }
                })

                if (response.ok) {
                    await this.loadBranches()
                    const updatedBranch = this.branches.find(b => b.id === this.currentBranch.id)
                    if (updatedBranch) {
                        this.currentBranch = updatedBranch
                        this.formData = { ...updatedBranch }
                    }
                    window.showAlert?.('성공', '층이 삭제되었습니다.', 'success');
                } else {
                    const data = await response.json()
                    window.showAlert?.('삭제 실패', data.error || '층 삭제에 실패했습니다.', 'error')
                }
            } catch (error) {
                console.error('Error deleting floor:', error)
                window.showAlert?.('오류', '오류가 발생했습니다.', 'error')
            }
        },

        // ==================== Room Management Methods ====================

        async loadBranchRooms(branch) {
            // OPEN IMMEDIATELY
            this.showModal = false;
            this.showServicesModal = false;
            this.showRoomModal = true;
            this.loadingData = true;
            this.currentBranch = branch;
            this.branchRooms = [];

            const token = localStorage.getItem('token');
            try {
                const response = await fetch(`/admin/api/branches/${branch.id}`, {
                    headers: { Authorization: 'Bearer ' + token }
                });
                if (response.ok) {
                    const data = await response.json();
                    this.branchRooms = data.rooms || [];
                    this.roomsByFloor = data.rooms_by_floor || {};
                    this.floorPlans = data.floor_plans || {};
                    this.currentBranch = { ...branch, floors: data.floors || [] };
                    this.selectedFloor = (data.floors && data.floors.length > 0) ? data.floors[0] : '1F';
                }
            } catch (error) {
                console.error('Error loading rooms:', error);
            } finally {
                this.loadingData = false;
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
                deposit: '',
                area: '',
                description: '',
                floor: this.selectedFloor || '1F'
            }
            this.showRoomFormModal = true
        },

        openEditRoomModal(room) {
            this.roomEditMode = true
            this.currentRoom = room
            this.roomFormData = { ...room }
            this.roomImages = []
            this.existingRoomImages = room.images ? [...room.images] : []
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
                    const data = await response.json()
                    const roomId = this.roomEditMode ? this.currentRoom.id : data.id

                    // Upload images if any
                    if (this.roomImages.length > 0) {
                        await this.uploadRoomImages(roomId)
                    }

                    this.showRoomFormModal = false
                    this.roomImages = []
                    this.existingRoomImages = []
                    await this.loadBranchRooms(this.currentBranch)
                    window.showAlert?.('성공', '방 정보가 저장되었습니다.', 'success');
                } else {
                    const data = await response.json()
                    window.showAlert?.('저장 실패', data.error || '방 저장에 실패했습니다.', 'error')
                }
            } catch (error) {
                console.error('Error saving room:', error)
                window.showAlert?.('오류', '오류가 발생했습니다.', 'error')
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
                    window.showAlert?.('성공', '방이 삭제되었습니다.', 'success');
                } else {
                    const data = await response.json()
                    window.showAlert?.('삭제 실패', data.error || '방 삭제에 실패했습니다.', 'error')
                }
            } catch (error) {
                console.error('Error deleting room:', error)
                window.showAlert?.('오류', '오류가 발생했습니다.', 'error')
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
                    window.showAlert?.('성공', '도면이 업로드되었습니다.', 'success');
                } else {
                    window.showAlert?.('업로드 실패', '도면 업로드에 실패했습니다.', 'error')
                }
            } catch (error) {
                console.error('Error uploading floor plan:', error)
                window.showAlert?.('오류', '오류가 발생했습니다.', 'error')
            } finally {
                this.uploadingFloor = null
                event.target.value = ''
            }
        },

        startDrag(room, event) {
            if (event.target.classList.contains('resize-handle')) return
            this.isDragging = true
            this.draggedRoom = room

            // Get the container (floor plan div) to calculate relative offsets
            const container = event.currentTarget.parentElement.getBoundingClientRect()
            const rect = event.currentTarget.getBoundingClientRect()

            // Calculate where inside the room the user clicked (in pixels)
            const offsetX = event.clientX - rect.left
            const offsetY = event.clientY - rect.top

            // Convert room's current % position to absolute pixels in the container
            const currentRoomX = (room.position_x / 100) * container.width
            const currentRoomY = (room.position_y / 100) * container.height

            // dragStartX/Y should be the difference between cursor and room's top-left
            this.dragStartX = offsetX
            this.dragStartY = offsetY

            event.currentTarget.style.cursor = 'grabbing'
        },

        onDrag(event) {
            if (!this.isDragging || !this.draggedRoom) return
            // The event listener is on the container (800x600 div)
            const container = event.currentTarget.getBoundingClientRect()

            // Current cursor position relative to container
            const cursorX = event.clientX - container.left
            const cursorY = event.clientY - container.top

            // Desired room top-left in pixels
            const newX = cursorX - this.dragStartX
            const newY = cursorY - this.dragStartY

            // Convert to percentage
            let xPercent = (newX / container.width) * 100
            let yPercent = (newY / container.height) * 100

            // Boundary checks (0 to 100 - room size)
            const roomWidth = this.draggedRoom.width || 10
            const roomHeight = this.draggedRoom.height || 10

            xPercent = Math.max(0, Math.min(100 - roomWidth, xPercent))
            yPercent = Math.max(0, Math.min(100 - roomHeight, yPercent))

            // Update state
            this.draggedRoom.position_x = parseFloat(xPercent.toFixed(2))
            this.draggedRoom.position_y = parseFloat(yPercent.toFixed(2))
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
                    window.showAlert?.('성공', '방 위치가 저장되었습니다.', 'success');
                } else {
                    window.showAlert?.('저장 실패', '저장에 실패했습니다.', 'error')
                }
            } catch (error) {
                console.error('Error saving positions:', error)
                window.showAlert?.('오류', '오류가 발생했습니다.', 'error')
            }
        },

        // ==================== Services Management Methods ====================

        async loadBranchServices(branch) {
            // OPEN IMMEDIATELY
            this.showModal = false;
            this.showRoomModal = false;
            this.showServicesModal = true;
            this.loadingData = true;
            this.currentBranch = branch;
            this.commonServices = [];
            this.specializedServices = [];

            const token = localStorage.getItem('token');
            try {
                const response = await fetch(`/admin/api/branches/${branch.id}`, {
                    headers: { Authorization: 'Bearer ' + token }
                });
                if (response.ok) {
                    const data = await response.json();
                    this.commonServices = data.common_services || [];
                    this.specializedServices = data.specialized_services || [];
                    this.currentBranch = { ...branch, floors: data.floors || [] };
                }
            } catch (error) {
                console.error('Error loading services:', error);
            } finally {
                this.loadingData = false;
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
