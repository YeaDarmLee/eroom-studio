// app/static/js/admin/dashboard.js

document.addEventListener('alpine:init', () => {
    Alpine.data('dashboardTab', () => ({
        stats: {
            totalUsers: 120,
            activeContracts: 45,
            pendingRequests: 3,
            monthlyRevenue: 12500000
        },
        charts: {},

        init() {
            this.$nextTick(() => {
                this.initCharts();
            });

            // Re-render charts when tab becomes active
            this.$watch('$parent.activeTab', (value) => {
                if (value === 'dashboard') {
                    this.$nextTick(() => {
                        this.resizeCharts();
                    });
                }
            });

            window.addEventListener('resize', () => {
                this.resizeCharts();
            });
        },

        initCharts() {
            // Revenue Chart
            const revenueEl = document.getElementById('revenueChart');
            if (revenueEl) {
                this.charts.revenue = echarts.init(revenueEl);
                const revenueOption = {
                    animation: true,
                    grid: { top: 10, left: 0, right: 0, bottom: 0, containLabel: true },
                    tooltip: { trigger: 'axis' },
                    xAxis: {
                        type: 'category',
                        data: ['7월', '8월', '9월', '10월', '11월', '12월', '1월'],
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
                        data: [38.5, 41.2, 39.8, 43.1, 44.6, 42.3, 45.2],
                        type: 'line',
                        smooth: true,
                        symbol: 'none',
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
                this.charts.roomStatus = echarts.init(roomStatusEl);
                const roomStatusOption = {
                    animation: true,
                    tooltip: { trigger: 'item' },
                    series: [{
                        type: 'pie',
                        radius: ['40%', '70%'],
                        center: ['50%', '50%'],
                        data: [
                            { value: 89, name: '사용 중', itemStyle: { color: '#3b82f6' } },
                            { value: 35, name: '빈 방', itemStyle: { color: '#8b5cf6' } }
                        ],
                        itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
                        label: { show: false }
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
