// app/static/js/admin/app.js

document.addEventListener('alpine:init', () => {
    Alpine.data('adminApp', () => ({
        sidebarOpen: false,
        activeTab: 'dashboard',
        user: {
            name: '관리자',
            email: 'admin@eroom.kr'
        },

        init() {
            // Check auth
            this.checkAuth();

            // Handle URL hash for deep linking
            const hash = window.location.hash.substring(1);
            if (['dashboard', 'contracts', 'requests', 'branches'].includes(hash)) {
                this.activeTab = hash;
            }

            // Watch for tab changes to update URL
            this.$watch('activeTab', value => {
                window.location.hash = value;
            });
        },

        async checkAuth() {
            const token = localStorage.getItem('token');
            if (!token) {
                window.location.href = '/login';
                return;
            }
            try {
                const response = await fetch('/api/auth/me', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                if (!response.ok) throw new Error('Invalid token');
                const data = await response.json();
                if (data.role !== 'admin') {
                    alert('관리자 권한이 필요합니다.');
                    window.location.href = '/my/room';
                }
                this.user.name = data.name || '관리자';
                this.user.email = data.email || 'admin@eroom.kr';
            } catch (error) {
                console.error('Auth error:', error);
                localStorage.removeItem('token');
                window.location.href = '/login';
            }
        },

        logout() {
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
    }));
});
