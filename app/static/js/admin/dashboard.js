document.addEventListener('alpine:init', () => {
    Alpine.data('dashboardTab', () => ({
        stats: {
            totalUsers: 0,
            activeContracts: 0,
            expiringContracts: 0,
            pendingRequests: 0,
            monthlyRevenue: 0,
            totalDeposit: 0,
            totalRooms: 0,
            occupiedRooms: 0,
            availableRooms: 0
        },
        branchData: [],
        loading: false,

        init() {
            this.loadStats();
        },

        async loadStats() {
            this.loading = true;
            const token = localStorage.getItem('token');
            try {
                const response = await fetch('/admin/api/stats', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                if (response.ok) {
                    const data = await response.json();
                    this.stats = data.stats;
                    this.branchData = data.branchData || [];
                }
            } catch (error) {
                console.error('Error loading stats:', error);
            } finally {
                this.loading = false;
            }
        }
    }));
});
