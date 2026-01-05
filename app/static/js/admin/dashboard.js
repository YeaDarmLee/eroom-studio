document.addEventListener('alpine:init', () => {
    Alpine.data('dashboardTab', () => ({
        stats: {
            totalUsers: 0,
            activeContracts: 0,
            pendingRequests: 0,
            monthlyRevenue: 0
        },
        roomStatusData: [],
        charts: {},
        loading: false,

        init() {
            this.loadStats();

            // Re-render charts when tab becomes active
            if (this.$parent) {
                this.$watch('$parent.activeTab', (value) => {
                    if (value === 'dashboard') {
                        this.$nextTick(() => {
                            this.resizeCharts();
                        });
                    }
                });
            }

            window.addEventListener('resize', () => {
                this.resizeCharts();
            });
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
                    this.roomStatusData = data.roomStatus;
                    this.$nextTick(() => {
                        this.initCharts();
                    });
                }
            } catch (error) {
                console.error('Error loading stats:', error);
            } finally {
                this.loading = false;
            }
        },

        initCharts() {
            // Revenue Chart (Example with empty/zero data if no history yet)
            const revenueEl = document.getElementById('revenueChart');
            if (revenueEl) {
                if (this.charts.revenue) this.charts.revenue.dispose();
                this.charts.revenue = echarts.init(revenueEl);
                const revenueOption = {
                    animation: true,
                    grid: { top: 10, left: 0, right: 0, bottom: 0, containLabel: true },
                    tooltip: { trigger: 'axis' },
                    xAxis: {
                        type: 'category',
                        data: ['현재'],
                        axisLine: { show: false },
                        axisTick: { show: false }
                    },
                    yAxis: {
                        type: 'value',
                        axisLine: { show: false },
                        axisTick: { show: false },
                        splitLine: { lineStyle: { color: '#f3f4f6' } }
                    },
                    series: [{
                        data: [this.stats.monthlyRevenue / 1000000], // Display in millions
                        type: 'line',
                        smooth: true,
                        symbol: 'circle',
                        lineStyle: { color: '#3b82f6', width: 3 },
                        areaStyle: {
                            color: {
                                type: 'linear',
                                x: 0, y: 0, x2: 0, y2: 1,
                                colorStops: [
                                    { offset: 0, color: 'rgba(59, 130, 246, 0.1)' },
                                    { offset: 1, color: 'rgba(59, 130, 246, 0.01)' }
                                ]
                            }
                        }
                    }]
                };
                this.charts.revenue.setOption(revenueOption);
            }

            // Room Status Chart
            const roomStatusEl = document.getElementById('roomStatusChart');
            if (roomStatusEl) {
                if (this.charts.roomStatus) this.charts.roomStatus.dispose();
                this.charts.roomStatus = echarts.init(roomStatusEl);

                const data = this.roomStatusData.length > 0 ? this.roomStatusData : [
                    { value: 0, name: '사용 중', itemStyle: { color: '#3b82f6' } },
                    { value: 0, name: '빈 방', itemStyle: { color: '#8b5cf6' } }
                ];

                const roomStatusOption = {
                    animation: true,
                    tooltip: { trigger: 'item' },
                    series: [{
                        type: 'pie',
                        radius: ['40%', '70%'],
                        center: ['50%', '50%'],
                        data: data.map(d => ({
                            ...d,
                            itemStyle: { color: d.name === '사용 중' ? '#3b82f6' : '#8b5cf6' }
                        })),
                        itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
                        label: { show: true, formatter: '{b}: {c}' }
                    }]
                };
                this.charts.roomStatus.setOption(roomStatusOption);
            }
        },

        resizeCharts() {
            if (this.charts.revenue) this.charts.revenue.resize();
            if (this.charts.roomStatus) this.charts.roomStatus.resize();
        }
    }));
});
