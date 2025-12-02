// app/static/js/admin/contracts.js

document.addEventListener('alpine:init', () => {
    Alpine.data('contractsTab', () => ({
        contracts: [],
        loading: false,
        filterStatus: 'all',

        init() {
            this.loadContracts();
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
                }
            } catch (error) {
                console.error('Error loading contracts:', error);
            } finally {
                this.loading = false;
            }
        },

        get filteredContracts() {
            if (this.filterStatus === 'all') return this.contracts;
            return this.contracts.filter(c => c.status === this.filterStatus);
        },

        async updateStatus(id, newStatus) {
            if (!confirm('상태를 변경하시겠습니까?')) return;

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
                    alert('상태가 변경되었습니다.');
                } else {
                    alert('상태 변경 실패');
                }
            } catch (error) {
                console.error('Error updating status:', error);
                alert('오류가 발생했습니다.');
            }
        },

        getStatusBadgeClass(status) {
            const classes = {
                'active': 'bg-green-100 text-green-800',
                'requested': 'bg-yellow-100 text-yellow-800',
                'terminated': 'bg-gray-100 text-gray-800',
                'cancelled': 'bg-red-100 text-red-800'
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
