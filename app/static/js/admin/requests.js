// app/static/js/admin/requests.js

document.addEventListener('alpine:init', () => {
    Alpine.data('requestsTab', () => ({
        allData: [],
        loading: false,
        filterBranchId: 'all',
        branches: [],

        // Modal state
        responseModalOpen: false,
        selectedRequest: null,
        adminResponseText: '',
        submittingResponse: false,

        init() {
            this.loadRequests();
            this.loadBranches();
        },

        async loadRequests() {
            this.loading = true;
            const token = localStorage.getItem('token');
            try {
                const response = await fetch('/admin/api/requests', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                if (response.ok) {
                    this.allData = await response.json();
                }
            } catch (error) {
                console.error('Error loading requests:', error);
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

        get requests() {
            let list = this.allData.filter(r => r.type !== 'inquiry');
            if (this.filterBranchId !== 'all') {
                list = list.filter(r => r.branch_id == this.filterBranchId);
            }
            return list;
        },

        get inquiries() {
            let list = this.allData.filter(r => r.type === 'inquiry');
            if (this.filterBranchId !== 'all') {
                list = list.filter(r => r.branch_id == this.filterBranchId);
            }
            return list;
        },

        openResponseModal(req) {
            this.selectedRequest = req;
            this.adminResponseText = req.details.admin_response || '';
            this.responseModalOpen = true;
        },

        async submitResponse() {
            if (!this.selectedRequest || !this.adminResponseText.trim()) {
                window.showAlert?.('입력 필요', '답변 내용을 입력해주세요.', 'warning');
                return;
            }

            this.submittingResponse = true;
            const token = localStorage.getItem('token');
            try {
                const response = await fetch(`/admin/api/requests/${this.selectedRequest.id}/status`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token
                    },
                    body: JSON.stringify({
                        status: 'done',
                        admin_response: this.adminResponseText
                    })
                });

                if (response.ok) {
                    this.responseModalOpen = false;
                    await this.loadRequests();
                    window.showAlert?.('성공', '답변이 등록되었습니다.', 'success');
                } else {
                    window.showAlert?.('등록 실패', '답변 등록에 실패했습니다.', 'error');
                }
            } catch (error) {
                console.error('Error submitting response:', error);
                window.showAlert?.('오류', '오류가 발생했습니다.', 'error');
            } finally {
                this.submittingResponse = false;
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
                    window.showAlert?.('상태 변경 실패', '상태 변경에 실패했습니다.', 'error');
                }
            } catch (error) {
                console.error('Error updating status:', error);
                window.showAlert?.('오류', '오류가 발생했습니다.', 'error');
            }
        },

        getTypeLabel(type) {
            const labels = {
                'repair': '수리 요청',
                'supplies': '비품 요청',
                'extension': '연장 신청',
                'termination': '퇴실 신청',
                'complaint': '민원 접수',
                'inquiry': '예약 문의',
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
        },

        getStatusLabel(status) {
            const labels = {
                'submitted': '대기 중',
                'processing': '처리 중',
                'done': '완료'
            };
            return labels[status] || status;
        }
    }));
});
