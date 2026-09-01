document.addEventListener('alpine:init', () => {
    Alpine.data('dashboardTab', () => ({
        selectedBranch: '전체',
        stats: {
            totalUsers: 0,
            activeContracts: 0,
            expiringContracts: 0,
            pendingRequests: 0,
            monthlyRevenue: 0,
            totalDeposit: 0,
            totalRooms: 0,
            occupiedRooms: 0,
            availableRooms: 0,
            monthlyRooms: 0,
            waitingSignature: 0,
            maintenanceRooms: 0
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

        get currentStats() {
            if (this.selectedBranch === '전체' || !this.selectedBranch) {
                return this.stats;
            }
            const b = this.branchData.find(item => item.name === this.selectedBranch || item.id === this.selectedBranch);
            if (!b) return this.stats;
            return {
                totalRooms: b.total_rooms || 0,
                activeContracts: b.active_contracts || 0,
                waitingSignature: b.waiting_signature || 0,
                occupiedRooms: (b.occupied_rooms || 0) + (b.maintenance_rooms || 0),
                expiringContracts: b.expiring_contracts || 0,
                pendingRequests: b.pending_contracts || 0,
                availableRooms: b.available_rooms || 0,
                monthlyRooms: b.monthly_rooms || 0,
                monthlyRevenue: b.monthly_revenue || 0,
                totalDeposit: b.deposit || 0,
                maintenanceRooms: b.maintenance_rooms || 0
            };
        },

        get statCards() {
            const s = this.currentStats;
            return [
                { 
                    label: '총 방 개수', 
                    value: s.totalRooms, 
                    icon: 'ri-door-line', 
                    color: 'bg-blue-500',
                    tooltip: `이용중: ${s.activeContracts || 0}개\n서명대기: ${s.waitingSignature || 0}개\n공실: ${s.availableRooms || 0}개\n점검중: ${s.maintenanceRooms || 0}개`
                },
                { 
                    label: '점유 중 / 예약', 
                    value: s.occupiedRooms, 
                    icon: 'ri-file-text-line', 
                    color: 'bg-green-500',
                    tooltip: `이용 중(활성): ${s.activeContracts || 0}개\n서명/입금 대기: ${s.waitingSignature || 0}개\n점검 중: ${s.maintenanceRooms || 0}개`
                },
                { 
                    label: '만료 예정', 
                    value: s.expiringContracts, 
                    icon: 'ri-alarm-warning-line', 
                    color: 'bg-orange-500',
                    tooltip: `1개월 이내 종료 예정 계약`,
                    actionType: 'expiring'
                },
                { 
                    label: '승인 대기', 
                    value: s.pendingRequests, 
                    icon: 'ri-question-answer-line', 
                    color: 'bg-indigo-500',
                    tooltip: '문의/승인 대기 건',
                    actionType: 'requests'
                },
                { 
                    label: '공실 현황', 
                    value: `${s.availableRooms}/${s.monthlyRooms}`, 
                    icon: 'ri-door-open-line', 
                    color: 'bg-blue-500',
                    tooltip: '현재 즉시 입주 가능 방 / 전체 월결제 방',
                    actionType: 'vacant'
                },
                { 
                    label: '월세 합계', 
                    value: '₩' + Number(s.monthlyRevenue || 0).toLocaleString(), 
                    icon: 'ri-wallet-3-line', 
                    color: 'bg-purple-500',
                    tooltip: `현재 활성 계약의 총 월세 수입 예측`
                },
                { 
                    label: '보증금 합계', 
                    value: '₩' + Number(s.totalDeposit || 0).toLocaleString(), 
                    icon: 'ri-safe-2-line', 
                    color: 'bg-indigo-500',
                    tooltip: `현재 활성 계약의 총 보증금 합계`
                }
            ];
        },

        searchQuery: '',

        get filteredExpiringContracts() {
            let list = this.expiringContracts;
            if (this.selectedBranch !== '전체' && this.selectedBranch) {
                list = list.filter(c => c.branch_name === this.selectedBranch);
            }
            if (this.searchQuery && this.searchQuery.trim() !== '') {
                list = list.filter(c => window.matchSearchFields([c.user_name, c.room_name, c.branch_name, c.user_phone], this.searchQuery));
            }
            return list;
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
                if (this.selectedBranch === '전체' || !this.selectedBranch) {
                    this.openAllVacantRoomsModal();
                } else {
                    const branch = this.branchData.find(b => b.name === this.selectedBranch || b.id === this.selectedBranch);
                    if (branch) {
                        this.openVacantRoomsModal(branch);
                    } else {
                        this.openAllVacantRoomsModal();
                    }
                }
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
