// app/static/js/admin/app.js

document.addEventListener('alpine:init', () => {
    Alpine.data('adminApp', () => ({
        sidebarOpen: true,
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
            console.log('Admin checkAuth - Token exists:', token ? 'Yes' : 'No');
            console.log('Admin checkAuth - Token value:', token ? token.substring(0, 20) + '...' : 'null');

            if (!token) {
                console.log('No token found, redirecting to login...');
                window.location.href = '/login';
                return;
            }
            try {
                console.log('Calling /api/auth/me with token...');
                const response = await fetch('/api/auth/me', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                console.log('Response status:', response.status);

                if (!response.ok) throw new Error('Invalid token');
                const data = await response.json();
                console.log('User data received:', data);

                if (data.role !== 'admin') {
                    window.showAlert?.('권한 부족', '관리자 권한이 필요합니다.', 'warning');
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
