// app/static/js/admin/requests.js

document.addEventListener('alpine:init', () => {
    Alpine.data('requestsTab', () => ({
        requests: [],
        loading: false,

        init() {
            this.loadRequests();
        },

        async loadRequests() {
            this.loading = true;
            const token = localStorage.getItem('token');
            try {
                const response = await fetch('/admin/api/requests', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                if (response.ok) {
                    this.requests = await response.json();
                }
            } catch (error) {
                console.error('Error loading requests:', error);
            } finally {
                this.loading = false;
            }
        },

        async updateStatus(id, newStatus) {
            const token = localStorage.getItem('token');
            try {
                const response = await fetch(`/admin/api/requests/${id}/status`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token
                    },
                    body: JSON.stringify({ status: newStatus })
                });

                if (response.ok) {
                    await this.loadRequests();
                } else {
                    alert('상태 변경 실패');
                }
            } catch (error) {
                console.error('Error updating status:', error);
                alert('오류가 발생했습니다.');
            }
        },

        getTypeLabel(type) {
            const labels = {
                'repair': '수리 요청',
                'supplies': '비품 요청',
                'complaint': '민원 접수',
                'other': '기타'
            };
            return labels[type] || type;
        },

        getStatusBadgeClass(status) {
            const classes = {
                'submitted': 'bg-yellow-100 text-yellow-800',
                'processing': 'bg-blue-100 text-blue-800',
                'done': 'bg-green-100 text-green-800'
            };
            return classes[status] || 'bg-gray-100 text-gray-800';
        }
    }));
});
