// app/static/js/admin/requests.js

document.addEventListener('alpine:init', () => {
    Alpine.data('requestsTab', () => ({
        allData: [],
        loading: false,
        filterBranchId: 'all',
        branches: [],
        
        // Pagination
        inquiriesCurrentPage: 1,
        requestsCurrentPage: 1,
        itemsPerPage: 15,

        // Modal state
        responseModalOpen: false,
        selectedRequest: null,
        adminResponseText: '',
        submittingResponse: false,

        init() {
            this.$watch('activeTab', (value) => {
                if (value === 'requests' || value === 'inquiries') {
                    if (this.allData.length === 0) this.loadRequests();
                    if (this.branches.length === 0) this.loadBranches();
                }
            });

            this.$watch('filterBranchId', () => {
                this.inquiriesCurrentPage = 1;
                this.requestsCurrentPage = 1;
            });

            if (this.activeTab === 'requests' || this.activeTab === 'inquiries') {
                this.loadRequests();
                this.loadBranches();
            }
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

        // Pagination for Inquiries
        get totalInquiriesPages() { return Math.ceil(this.inquiries.length / this.itemsPerPage) || 1; },
        get paginatedInquiries() {
            const start = (this.inquiriesCurrentPage - 1) * this.itemsPerPage;
            return this.inquiries.slice(start, start + this.itemsPerPage);
        },
        nextInquiriesPage() { if (this.inquiriesCurrentPage < this.totalInquiriesPages) this.inquiriesCurrentPage++; },
        prevInquiriesPage() { if (this.inquiriesCurrentPage > 1) this.inquiriesCurrentPage--; },
        goToInquiriesPage(page) { if (page >= 1 && page <= this.totalInquiriesPages) this.inquiriesCurrentPage = page; },

        // Pagination for Requests
        get totalRequestsPages() { return Math.ceil(this.requests.length / this.itemsPerPage) || 1; },
        get paginatedRequests() {
            const start = (this.requestsCurrentPage - 1) * this.itemsPerPage;
            return this.requests.slice(start, start + this.itemsPerPage);
        },
        nextRequestsPage() { if (this.requestsCurrentPage < this.totalRequestsPages) this.requestsCurrentPage++; },
        prevRequestsPage() { if (this.requestsCurrentPage > 1) this.requestsCurrentPage--; },
        goToRequestsPage(page) { if (page >= 1 && page <= this.totalRequestsPages) this.requestsCurrentPage = page; },

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
            if (this.selectedRequest.type === 'account_link' && !confirm('신청자의 본인 확인을 완료했습니까? 승인하면 기존 계약이 연결됩니다.')) {
                this.submittingResponse = false;
                return;
            }
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
                        identity_verified: this.selectedRequest.type === 'account_link',
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
            const req = this.allData.find(r => r.id === id);
            if (req?.type === 'account_link' && newStatus === 'done' && !confirm('신청자의 본인 확인을 완료했습니까? 승인하면 기존 계약이 연결됩니다.')) return;
            const token = localStorage.getItem('token');
            try {
                const response = await fetch(`/admin/api/requests/${id}/status`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token
                    },
                    body: JSON.stringify({ status: newStatus, identity_verified: req?.type === 'account_link' && newStatus === 'done' })
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
                'account_link': '기존 계약 연결 (본인 확인 필요)',
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
