// app/static/js/admin/coupons.js

document.addEventListener('alpine:init', () => {
    Alpine.data('couponsTab', () => ({
        coupons: [],
        loading: false,
        submitting: false,
        createModalOpen: false,

        newCoupon: {
            code: '',
            discount_type: 'fixed', // 'fixed', 'percentage'
            discount_value: 0,
            discount_cycle: 'once', // 'once', 'monthly'
            stack_policy: 'STACK_WITH_MONTHLY_PROMO', // 'STACK_WITH_MONTHLY_PROMO', 'EXCLUSIVE'
            valid_from: new Date().toISOString().split('T')[0],
            valid_until: new Date(new Date().setMonth(new Date().getMonth() + 1)).toISOString().split('T')[0],
            min_months: '',
            usage_limit: ''
        },

        init() {
            this.$watch('activeTab', (value) => {
                if (value === 'coupons' && this.coupons.length === 0) {
                    this.loadCoupons();
                }
            });

            if (this.activeTab === 'coupons') {
                this.loadCoupons();
            }
        },

        async loadCoupons() {
            this.loading = true;
            const token = localStorage.getItem('token');
            try {
                const response = await fetch('/admin/api/coupons', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                if (response.ok) {
                    this.coupons = await response.json();
                } else {
                    console.error('Failed to load coupons');
                }
            } catch (error) {
                console.error('Error loading coupons:', error);
            } finally {
                this.loading = false;
            }
        },

        openCreateModal() {
            this.newCoupon = {
                code: '',
                discount_type: 'fixed',
                discount_value: 0,
                discount_cycle: 'once',
                stack_policy: 'STACK_WITH_MONTHLY_PROMO',
                valid_from: new Date().toISOString().split('T')[0],
                valid_until: new Date(new Date().setMonth(new Date().getMonth() + 1)).toISOString().split('T')[0],
                min_months: '',
                usage_limit: ''
            };
            this.createModalOpen = true;
        },

        generateCode() {
            const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
            let result = '';
            for (let i = 0; i < 8; i++) {
                result += chars.charAt(Math.floor(Math.random() * chars.length));
            }
            this.newCoupon.code = result;
        },

        async createCoupon() {
            if (!this.newCoupon.code || !this.newCoupon.discount_value || !this.newCoupon.valid_from || !this.newCoupon.valid_until) {
                window.showAlert?.('입력 오류', '필수 항목을 모두 입력해주세요.', 'warning');
                return;
            }

            this.submitting = true;
            const token = localStorage.getItem('token');

            // Prepare payload
            const payload = { ...this.newCoupon };
            if (payload.min_months === '') payload.min_months = null;
            if (payload.usage_limit === '') payload.usage_limit = null;

            try {
                const response = await fetch('/admin/api/coupons', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token
                    },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    await this.loadCoupons();
                    this.createModalOpen = false;
                    window.showAlert?.('성공', '쿠폰이 생성되었습니다.', 'success');
                } else {
                    const data = await response.json();
                    window.showAlert?.('실패', data.error || '쿠폰 생성 실패', 'error');
                }
            } catch (error) {
                window.showAlert?.('오류', '오류가 발생했습니다.', 'error');
            } finally {
                this.submitting = false;
            }
        },

        async deleteCoupon(id) {
            if (!confirm('정말로 이 쿠폰을 삭제하시겠습니까? (이미 사용된 쿠폰은 삭제할 수 없습니다)')) return;

            const token = localStorage.getItem('token');
            try {
                const response = await fetch(`/admin/api/coupons/${id}`, {
                    method: 'DELETE',
                    headers: { 'Authorization': 'Bearer ' + token }
                });

                if (response.ok) {
                    await this.loadCoupons();
                    window.showAlert?.('성공', '쿠폰이 삭제되었습니다.', 'success');
                } else {
                    const data = await response.json();
                    window.showAlert?.('삭제 실패', data.error || '삭제 실패', 'error');
                }
            } catch (error) {
                window.showAlert?.('오류', '오류가 발생했습니다.', 'error');
            }
        },

        getDiscountLabel(coupon) {
            let label = '';
            if (coupon.discount_type === 'fixed') {
                label = `₩${coupon.discount_value.toLocaleString()}`;
            } else {
                label = `${coupon.discount_value}%`;
            }

            if (coupon.discount_cycle === 'monthly') {
                label += ' (매월)';
            } else {
                label += ' (1회)';
            }
            return label;
        }
    }));
});
