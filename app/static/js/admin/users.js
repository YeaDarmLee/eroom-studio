// app/static/js/admin/users.js

document.addEventListener('alpine:init', () => {
    Alpine.data('usersTab', () => ({
        users: [],
        loading: false,
        searchQuery: '',
        filterBranchId: 'all',
        branches: [],

        // Edit Modal
        editModalOpen: false,
        editingUser: null,
        submitting: false,

        // Create Modal
        createModalOpen: false,
        newUser: {
            name: '',
            email: '',
            phone: '',
            password: '',
            role: 'user'
        },

        init() {
            this.$watch('activeTab', (value) => {
                if (value === 'users') {
                    if (this.users.length === 0) this.loadUsers();
                    if (this.branches.length === 0) this.loadBranches();
                }
            });

            if (this.activeTab === 'users') {
                this.loadUsers();
                this.loadBranches();
            }
        },

        openCreateModal() {
            this.newUser = {
                name: '',
                email: '',
                phone: '',
                password: '',
                role: 'user'
            };
            this.createModalOpen = true;
        },

        generateEmail() {
            const randomString = Math.random().toString(36).substring(2, 8);
            const timestamp = Date.now().toString().substring(8);
            this.newUser.email = `temp_${timestamp}_${randomString}@eroom.studio`;
        },

        async createUser() {
            if (!this.newUser.name || !this.newUser.email || !this.newUser.password) {
                window.showAlert?.('입력 오류', '이름, 이메일, 비밀번호는 필수입니다.', 'warning');
                return;
            }

            this.submitting = true;
            const token = localStorage.getItem('token');
            try {
                const response = await fetch('/admin/api/users', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token
                    },
                    body: JSON.stringify(this.newUser)
                });

                if (response.ok) {
                    await this.loadUsers();
                    this.createModalOpen = false;
                    window.showAlert?.('성공', '회원이 등록되었습니다.', 'success');
                } else {
                    const data = await response.json();
                    window.showAlert?.('실패', data.error || '등록 실패', 'error');
                }
            } catch (error) {
                window.showAlert?.('오류', '오류가 발생했습니다.', 'error');
            } finally {
                this.submitting = false;
            }
        },

        async loadUsers() {
            this.loading = true;
            const token = localStorage.getItem('token');
            try {
                const response = await fetch('/admin/api/users', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                if (response.ok) {
                    this.users = await response.json();
                }
            } catch (error) {
                console.error('Error loading users:', error);
            } finally {
                this.loading = false;
            }
        },

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

        get filteredUsers() {
            let list = this.users;

            // Branch Filter (users associated with the branch via active contracts)
            if (this.filterBranchId !== 'all') {
                list = list.filter(u => u.branch_ids && u.branch_ids.map(String).includes(String(this.filterBranchId)));
            }

            if (!this.searchQuery) return list;
            const lowerQuery = this.searchQuery.toLowerCase();
            return list.filter(u =>
                (u.name && u.name.toLowerCase().includes(lowerQuery)) ||
                (u.email && u.email.toLowerCase().includes(lowerQuery)) ||
                (u.phone && u.phone.includes(lowerQuery))
            );
        },

        openEditModal(user) {
            this.editingUser = { ...user }; // Clone
            this.editModalOpen = true;
        },

        async updateUser() {
            this.submitting = true;
            const token = localStorage.getItem('token');
            try {
                const response = await fetch(`/admin/api/users/${this.editingUser.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token
                    },
                    body: JSON.stringify(this.editingUser)
                });

                if (response.ok) {
                    await this.loadUsers();
                    this.editModalOpen = false;
                    window.showAlert?.('성공', '회원 정보가 수정되었습니다.', 'success');
                } else {
                    window.showAlert?.('실패', '수정 실패', 'error');
                }
            } catch (error) {
                window.showAlert?.('오류', '오류가 발생했습니다.', 'error');
            } finally {
                this.submitting = false;
            }
        },

        async deleteUser(id) {
            if (!confirm('정말로 이 회원을 삭제하시겠습니까?')) return;

            const token = localStorage.getItem('token');
            try {
                const response = await fetch(`/admin/api/users/${id}`, {
                    method: 'DELETE',
                    headers: { 'Authorization': 'Bearer ' + token }
                });

                if (response.ok) {
                    await this.loadUsers();
                    window.showAlert?.('성공', '회원이 삭제되었습니다.', 'success');
                } else {
                    const data = await response.json();
                    window.showAlert?.('삭제 실패', data.error || '삭제 실패', 'error');
                }
            } catch (error) {
                window.showAlert?.('오류', '오류가 발생했습니다.', 'error');
            }
        },

        getRoleLabel(role) {
            return role === 'admin' ? '관리자' : '일반 회원';
        },

        getOnboardingLabel(status) {
            const labels = {
                'not_started': '미시작',
                'new_user_done': '신규완료',
                'existing_pending': '기존(대기)',
                'existing_linked': '기존(연동됨)'
            };
            return labels[status] || status;
        }
    }));
});
