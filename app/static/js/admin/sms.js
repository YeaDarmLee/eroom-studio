document.addEventListener('alpine:init', () => {
    Alpine.data('smsTab', () => ({
        templates: [],
        logs: [],
        loading: false,
        activeSmsSubTab: 'templates', // 'templates' or 'logs'

        // Template Management
        editingTemplate: null,
        editModalOpen: false,
        submittingTemplate: false,

        // Preview
        previewContent: '',
        previewType: '',
        previewResult: '',
        previewMissing: [],

        // Manual Send State
        manualModalOpen: false,
        recipientSearchQuery: '',
        recipientSearchResults: [],
        manualSelectedRecipient: null,
        manualMsgType: 'MANUAL',
        manualContent: '',
        sendingManual: false,
        searchPerformed: false,

        init() {
            this.$watch('activeTab', (val) => {
                if (val === 'sms') {
                    this.loadTemplates();
                    this.loadLogs();
                }
            });
        },

        async loadTemplates() {
            this.loading = true;
            try {
                const response = await fetch('/admin/api/sms/templates', {
                    headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
                });
                this.templates = await response.json();
            } catch (error) {
                console.error('Error loading SMS templates:', error);
            } finally {
                this.loading = false;
            }
        },

        async loadLogs() {
            try {
                const response = await fetch('/admin/api/sms/logs', {
                    headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
                });
                this.logs = await response.json();
            } catch (error) {
                console.error('Error loading SMS logs:', error);
            }
        },

        // Manual Sending Logic
        openManualModal() {
            this.manualModalOpen = true;
            this.recipientSearchQuery = '';
            this.recipientSearchResults = [];
            this.manualSelectedRecipient = null;
            this.manualMsgType = 'MANUAL';
            this.manualContent = '';
            this.searchPerformed = false;
        },

        async searchRecipient() {
            if (this.recipientSearchQuery.length < 2) return;
            this.searchPerformed = true;
            try {
                const response = await fetch(`/admin/api/contracts/search?q=${encodeURIComponent(this.recipientSearchQuery)}`, {
                    headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
                });
                this.recipientSearchResults = await response.json();
            } catch (error) {
                console.error('Error searching recipient:', error);
                this.recipientSearchResults = [];
            }
        },

        selectRecipient(recipient) {
            this.manualSelectedRecipient = recipient;
            this.recipientSearchResults = [];
            this.recipientSearchQuery = '';
            this.searchPerformed = false;
            this.updateManualTemplate();
        },

        async updateManualTemplate() {
            if (this.manualMsgType === 'MANUAL') {
                this.manualContent = '';
                return;
            }
            const template = this.templates.find(t => t.type === this.manualMsgType);
            if (!template) return;

            if (this.manualSelectedRecipient) {
                try {
                    const response = await fetch('/admin/api/sms/preview', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': 'Bearer ' + localStorage.getItem('token')
                        },
                        body: JSON.stringify({
                            type: this.manualMsgType,
                            content: template.content,
                            contract_id: this.manualSelectedRecipient.id
                        })
                    });
                    const data = await response.json();
                    this.manualContent = data.rendered;
                } catch (error) {
                    console.error('Error rendering template:', error);
                    this.manualContent = template.content;
                }
            } else {
                this.manualContent = template.content;
            }
        },

        async sendManualSms() {
            if (!this.manualSelectedRecipient || !this.manualContent) return;

            if (!confirm(`${this.manualSelectedRecipient.user_name}님에게 문자를 발송하시겠습니까?`)) return;

            this.sendingManual = true;
            try {
                const response = await fetch('/admin/api/sms/manual', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + localStorage.getItem('token')
                    },
                    body: JSON.stringify({
                        contract_id: this.manualSelectedRecipient.id,
                        type: this.manualMsgType,
                        content: this.manualContent
                    })
                });

                if (response.ok) {
                    window.showAlert('성공', '문자가 발송되었습니다.', 'success');
                    this.manualModalOpen = false;
                    this.loadLogs();
                } else {
                    const data = await response.json();
                    window.showAlert('오류', data.error || '발송 실패', 'error');
                }
            } catch (error) {
                console.error('Error sending SMS:', error);
                window.showAlert('오류', '서버 통신 오류', 'error');
            } finally {
                this.sendingManual = false;
            }
        },

        openEditModal(template) {
            this.editingTemplate = { ...template };
            this.previewContent = template.content;
            this.previewType = template.type;
            this.editModalOpen = true;
            this.updatePreview();
        },

        async updatePreview() {
            if (!this.previewContent) return;
            try {
                const response = await fetch('/admin/api/sms/preview', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + localStorage.getItem('token')
                    },
                    body: JSON.stringify({
                        content: this.previewContent,
                        type: this.previewType
                    })
                });
                const data = await response.json();
                this.previewResult = data.rendered;
                this.previewMissing = data.missing;
            } catch (error) {
                console.error('Error previewing SMS:', error);
            }
        },

        async saveTemplate() {
            if (this.previewMissing.length > 0) {
                if (!confirm('치환되지 않은 변수가 있습니다. 그대로 저장하시겠습니까? (발송 시 FAILED 처리될 수 있습니다)')) {
                    return;
                }
            }

            this.submittingTemplate = true;
            try {
                const response = await fetch(`/admin/api/sms/templates/${this.editingTemplate.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + localStorage.getItem('token')
                    },
                    body: JSON.stringify({
                        title: this.editingTemplate.title,
                        content: this.previewContent,
                        is_active: this.editingTemplate.is_active,
                        schedule_offset: this.editingTemplate.schedule_offset, // Add offset
                        reason: 'Admin update via UI'
                    })
                });

                if (response.ok) {
                    window.showAlert('성공', '템플릿이 저장되었습니다.', 'success');
                    this.editModalOpen = false;
                    this.loadTemplates();
                } else {
                    const data = await response.json();
                    window.showAlert('오류', data.error || '저장 실패', 'error');
                }
            } catch (error) {
                console.error('Error saving template:', error);
                window.showAlert('오류', '서버 통신 오류', 'error');
            } finally {
                this.submittingTemplate = false;
            }
        },

        getStatusBadgeClass(status) {
            if (status.includes('SENT')) return 'bg-green-50 text-green-600 border-green-100';
            if (status === 'FAILED') return 'bg-red-50 text-red-600 border-red-100';
            if (status === 'SKIPPED') return 'bg-gray-50 text-gray-500 border-gray-100';
            return 'bg-blue-50 text-blue-600 border-blue-100';
        },

        getScheduleLabel(offset) {
            if (offset === 0) return 'D-Day (당일)';
            if (offset < 0) return `D${offset} (${Math.abs(offset)}일 전)`;
            return `D+${offset} (${offset}일 후)`;
        }
    }));
});
