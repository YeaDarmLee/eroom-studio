// app/static/js/admin/contracts.js

document.addEventListener('alpine:init', () => {
    Alpine.data('contractsTab', () => ({
        contracts: [],
        loading: false,
        filterStatus: 'all',
        filterBranchId: 'all',

        // Detailed Modal state
        detailModalOpen: false,
        selectedContract: null,
        submittingUpdate: false,

        // Edit Modal State
        editModalOpen: false,
        editingContract: {},
        editingBranchId: '',

        // Create Contract Modal State
        createModalOpen: false,
        users: [],
        rooms: [],
        newContract: {
            user_id: '',
            room_id: '',
            start_date: '',
            end_date: '',
            deposit: '',
            price: '',
            payment_day: 1,
            is_indefinite: false
        },
        searchUserQuery: '',

        init() {
            // Lazy load when tab is active
            this.$watch('activeTab', (value) => {
                if (value === 'contracts') {
                    if (this.contracts.length === 0) this.loadContracts();
                    if (this.branches.length === 0) this.loadBranches();
                }
            });

            // If loaded directly via hash, load immediately
            if (this.activeTab === 'contracts') {
                this.loadContracts();
                this.loadBranches();
            }

            this.$watch('createModalOpen', value => {
                if (value) {
                    this.loadBranches();
                    if (this.users.length === 0) this.loadUsers();
                }
            });
            this.$watch('selectedBranchId', () => {
                this.newContract.room_id = '';
                this.newContract.price = '';
                this.newContract.deposit = '';
            });
        },

        selectRoom(roomId) {
            const room = this.availableRooms.find(r => r.id == roomId);
            if (room) {
                this.newContract.price = room.price;
                this.newContract.deposit = room.deposit;
            }
        },

        async loadUsers() {
            try {
                const token = localStorage.getItem('token');
                const response = await fetch('/admin/api/users', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                if (response.ok) {
                    this.users = await response.json();
                }
            } catch (error) {
                console.error('Error loading users:', error);
            }
        },

        branches: [],
        selectedBranchId: '',

        async loadBranches() {
            try {
                const token = localStorage.getItem('token');
                const response = await fetch('/admin/api/branches', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });

                if (response.ok) {
                    this.branches = await response.json();
                }
            } catch (error) {
                console.error('Error loading branches:', error);
            }
        },

        get availableRooms() {
            if (!this.selectedBranchId && !this.editingBranchId) return [];
            const branchId = this.editModalOpen ? this.editingBranchId : this.selectedBranchId;
            const branch = this.branches.find(b => b.id == branchId);
            if (!branch) return [];

            return branch.rooms
                .filter(room => {
                    // Only show 'monthly' rooms for contracts
                    if (room.room_type && room.room_type !== 'monthly') return false;

                    if (room.status === 'available') return true;
                    // If editing, include the room already assigned to this contract
                    if (this.editModalOpen && this.editingContract && room.id == this.editingContract.room_id) return true;
                    return false;
                })
                .map(room => ({
                    id: room.id,
                    name: room.name,
                    price: room.price,
                    deposit: room.deposit
                }));
        },

        get filteredUsers() {
            if (!this.searchUserQuery) return this.users;
            const lower = this.searchUserQuery.toLowerCase();
            return this.users.filter(u =>
                u.name.toLowerCase().includes(lower) ||
                u.email.toLowerCase().includes(lower) ||
                (u.phone && u.phone.includes(lower))
            );
        },

        openCreateModal() {
            this.newContract = {
                user_id: '',
                room_id: '',
                start_date: new Date().toISOString().split('T')[0],
                end_date: '',
                deposit: '',
                price: '',
                payment_day: 1,
                is_indefinite: false
            };
            this.createModalOpen = true;
        },


        async createContract() {
            if (!this.newContract.room_id || !this.newContract.start_date || (!this.newContract.is_indefinite && !this.newContract.end_date)) {
                window.showAlert?.('입력 오류', '방, 시작일, 종료일(또는 무기한)은 필수입니다.', 'warning');
                return;
            }

            this.submittingUpdate = true; // Reuse loading state
            const token = localStorage.getItem('token');
            try {
                const response = await fetch('/admin/api/contracts', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token
                    },
                    body: JSON.stringify(this.newContract)
                });

                if (response.ok) {
                    await this.loadContracts();
                    this.createModalOpen = false;
                    window.showAlert?.('성공', '계약이 등록되었습니다.', 'success');
                } else {
                    const data = await response.json();
                    window.showAlert?.('실패', data.error || '등록 실패', 'error');
                }
            } catch (error) {
                window.showAlert?.('오류', '오류가 발생했습니다.', 'error');
            } finally {
                this.submittingUpdate = false;
            }
        },

        async loadContracts() {
            this.loading = true;
            const token = localStorage.getItem('token');
            try {
                const response = await fetch('/admin/api/contracts', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                if (response.ok) {
                    this.contracts = await response.json();

                    // Sort by Branch Name then Room Name (Numeric)
                    this.contracts.sort((a, b) => {
                        // 1. Branch Name
                        if (a.branch_name < b.branch_name) return -1;
                        if (a.branch_name > b.branch_name) return 1;

                        // 2. Room Name (Natural Sort)
                        const roomA = String(a.room_name);
                        const roomB = String(b.room_name);

                        // Check if both are numeric-ish
                        const numA = parseInt(roomA.replace(/[^0-9]/g, ''));
                        const numB = parseInt(roomB.replace(/[^0-9]/g, ''));

                        // If both have numbers, sort by number
                        if (!isNaN(numA) && !isNaN(numB)) {
                            if (numA !== numB) return numA - numB;
                        }

                        // Fallback/Tie-breaker: String comparison
                        return roomA.localeCompare(roomB, undefined, { numeric: true, sensitivity: 'base' });
                    });
                }
            } catch (error) {
                console.error('Error loading contracts:', error);
            } finally {
                this.loading = false;
            }
        },

        getContractCount(status) {
            let list = this.contracts;
            if (this.filterBranchId !== 'all') {
                list = list.filter(c => c.branch_id == this.filterBranchId);
            }

            if (status === 'all') return list.length;
            if (status === 'expiring_soon') {
                return list.filter(c => this.isExpiringSoon(c)).length;
            }
            return list.filter(c => c.status === status).length;
        },

        isExpiringSoon(contract) {
            if (contract.status !== 'active') return false;
            if (contract.is_indefinite) return false; // 무기한 계약은 만료 예정 없음
            if (!contract.end_date) return false;

            const end = new Date(contract.end_date);
            const now = new Date();
            now.setHours(0, 0, 0, 0);

            const diffTime = end - now;
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

            return diffDays >= 0 && diffDays <= 30;
        },

        get filteredContracts() {
            let list = this.contracts;

            // Branch Filter
            if (this.filterBranchId !== 'all') {
                list = list.filter(c => c.branch_id == this.filterBranchId);
            }

            // Status Filter
            if (this.filterStatus === 'all') return list;
            if (this.filterStatus === 'expiring_soon') {
                return list.filter(c => this.isExpiringSoon(c));
            }
            return list.filter(c => c.status === this.filterStatus);
        },

        openDetailModal(contract) {
            this.selectedContract = contract;
            this.detailModalOpen = true;
        },

        async openEditModal(contract) {
            if (this.branches.length === 0) await this.loadBranches();
            if (this.users.length === 0) await this.loadUsers();

            this.editingBranchId = contract.branch_id || '';

            this.editingContract = {
                id: contract.id,
                user_id: contract.user_id || '',
                user_name: contract.user_name,
                user_phone: contract.user_phone,
                user_email: contract.user_email,
                room_id: contract.room_id || '',
                room_type: contract.room_type,
                start_date: contract.start_date,
                end_date: contract.end_date,
                start_time: contract.start_time || '',
                end_time: contract.end_time || '',
                price: contract.price,
                deposit: contract.deposit,
                payment_day: contract.payment_day || 1,
                is_indefinite: contract.is_indefinite || false
            };

            this.editModalOpen = true;
            this.detailModalOpen = false;
        },

        async updateContract() {
            if (!this.editingContract.room_id || !this.editingContract.start_date || (!this.editingContract.is_indefinite && !this.editingContract.end_date)) {
                window.showAlert?.('입력 오류', '방, 시작일, 종료일(또는 무기한)은 필수입니다.', 'warning');
                return;
            }

            this.submittingUpdate = true;
            const token = localStorage.getItem('token');
            try {
                const response = await fetch(`/admin/api/contracts/${this.editingContract.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token
                    },
                    body: JSON.stringify(this.editingContract)
                });

                if (response.ok) {
                    await this.loadContracts();
                    this.editModalOpen = false;
                    window.showAlert?.('성공', '계약 정보가 수정되었습니다.', 'success');
                } else {
                    const data = await response.json();
                    window.showAlert?.('실패', data.error || '수정 실패', 'error');
                }
            } catch (error) {
                window.showAlert?.('오류', '오류가 발생했습니다.', 'error');
            } finally {
                this.submittingUpdate = false;
            }
        },

        async applyTerminationNotice(contract) {
            if (!confirm('이 계약에 대해 한 달 후 퇴실 통보를 접수하시겠습니까? 종료일이 오늘로부터 30일 후로 설정됩니다.')) return;

            this.submittingUpdate = true;
            const token = localStorage.getItem('token');

            // Calculate 30 days later
            const today = new Date();
            today.setDate(today.getDate() + 30);
            const targetDate = today.toISOString().split('T')[0];

            try {
                const response = await fetch(`/admin/api/contracts/${contract.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token
                    },
                    body: JSON.stringify({
                        is_indefinite: false,
                        end_date: targetDate
                    })
                });

                if (response.ok) {
                    await this.loadContracts();
                    this.detailModalOpen = false;
                    window.showAlert?.('성공', '퇴실 통보가 접수되었습니다. 종료일이 설정되었습니다.', 'success');
                } else {
                    const data = await response.json();
                    window.showAlert?.('실패', data.error || '접수 실패', 'error');
                }
            } catch (error) {
                console.error(error);
                window.showAlert?.('오류', '오류가 발생했습니다.', 'error');
            } finally {
                this.submittingUpdate = false;
            }
        },

        async updateStatus(id, newStatus) {
            // If called from modal, we use submittingUpdate for loading state
            if (this.detailModalOpen) this.submittingUpdate = true;

            const token = localStorage.getItem('token');
            try {
                const response = await fetch(`/admin/api/contracts/${id}/status`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token
                    },
                    body: JSON.stringify({ status: newStatus })
                });

                if (response.ok) {
                    await this.loadContracts();
                    if (this.detailModalOpen) {
                        this.detailModalOpen = false;
                        window.showAlert?.('success', '계약 상태가 성공적으로 업데이트되었습니다.');
                    }
                } else {
                    window.showAlert?.('업데이트 실패', '계약 상태 변경에 실패했습니다.', 'error');
                }
            } catch (error) {
                console.error('Error updating status:', error);
                window.showAlert?.('오류', '오류가 발생했습니다. 잠시 후 다시 시도해주세요.', 'error');
            } finally {
                this.submittingUpdate = false;
            }
        },

        formatPrice(price) {
            return new Intl.NumberFormat('ko-KR').format(price) + '원';
        },

        getStatusBadgeClass(status) {
            const classes = {
                'active': 'bg-green-100 text-green-800 border-green-200',
                'requested': 'bg-yellow-100 text-yellow-800 border-yellow-200',
                'terminated': 'bg-gray-100 text-gray-800 border-gray-200',
                'cancelled': 'bg-red-100 text-red-800 border-red-200'
            };
            return classes[status] || 'bg-gray-100 text-gray-800';
        },

        getStatusLabel(status) {
            const labels = {
                'active': '이용 중',
                'requested': '승인 대기',
                'terminated': '종료됨',
                'cancelled': '취소됨'
            };
            return labels[status] || status;
        }
    }));
});
