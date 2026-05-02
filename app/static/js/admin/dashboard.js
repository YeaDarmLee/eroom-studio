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
        expiringContracts: [],
        loading: false,

        // Vacant Rooms Modal
        vacantRoomsModalOpen: false,
        selectedBranchName: '',
        selectedVacantRooms: [],

        // Expiring Contracts Modal
        isDashboardExpiringModalVisible: false,

        init() {
            console.log('[Dashboard] init called. Current modal state:', this.isDashboardExpiringModalVisible);
            this.isDashboardExpiringModalVisible = false;
            this.loadStats();
        },

        toggleExpiringModalManual() {
            console.log('[Dashboard] toggleExpiringModalManual called. Status: opening');
            console.trace(); // Trace the caller
            this.isDashboardExpiringModalVisible = true;
        },

        handleStatCardClick(stat) {
            console.log('[Dashboard] handleStatCardClick called for type:', stat.actionType);
            if (stat.actionType === 'expiring') {
                this.toggleExpiringModalManual();
            } else if (stat.actionType === 'vacant') {
                this.openAllVacantRoomsModal();
            } else if (stat.actionType === 'requests') {
                // Navigate to contracts tab and set filter to 'requested'
                this.activeTab = 'contracts';
                window.dispatchEvent(new CustomEvent('set-contract-filter', { 
                    detail: { status: 'requested' } 
                }));
            }
        },

        async loadStats() {
            this.loading = true;
            console.log('[Dashboard] loadStats starting...');
            const token = localStorage.getItem('token');
            try {
                const response = await fetch('/admin/api/stats', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                if (response.ok) {
                    const data = await response.json();
                    this.stats = data.stats;
                    this.branchData = data.branchData || [];
                    this.expiringContracts = data.expiringContracts || [];
                    console.log('[Dashboard] Stats loaded. Expiring count:', this.expiringContracts.length);
                }
            } catch (error) {
                console.error('Error loading stats:', error);
            } finally {
                this.loading = false;
                // Final safety check - keep it for one more cycle
                if (this.isDashboardExpiringModalVisible) {
                    console.warn('[Dashboard] Modal became true during loadStats unexpectedly! Forcing false.');
                    this.isDashboardExpiringModalVisible = false;
                }
            }
        },

        openVacantRoomsModal(branch) {
            this.selectedBranchName = branch.name;
            this.selectedVacantRooms = branch.available_rooms_list || [];
            this.vacantRoomsModalOpen = true;
        },

        openAllVacantRoomsModal() {
            this.selectedBranchName = '전체 지점';
            this.selectedVacantRooms = this.branchData.reduce((acc, branch) => {
                const rooms = (branch.available_rooms_list || []).map(r => ({
                    ...r,
                    branch_name: branch.name
                }));
                return acc.concat(rooms);
            }, []);
            this.vacantRoomsModalOpen = true;
        }
    }));
});
