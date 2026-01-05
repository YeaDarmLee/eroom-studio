// app/static/js/admin/contracts.js

document.addEventListener('alpine:init', () => {
    Alpine.data('contractsTab', () => ({
        contracts: [],
        loading: false,
        filterStatus: 'all',

        // Detailed Modal state
        detailModalOpen: false,
        selectedContract: null,
        submittingUpdate: false,

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

        openDetailModal(contract) {
            this.selectedContract = contract;
            this.detailModalOpen = true;
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
