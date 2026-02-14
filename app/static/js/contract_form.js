// Room Detail Contract Form - Advanced Features
// This file contains the contractForm() Alpine.js component
// with support for payment day selection, coupons, prorated calculations, and payment methods

window.contractFormConfig = {
    roomPrice: null,  // Will be set by HTML
    roomDeposit: null, // Will be set by HTML
    roomId: null       // Will be set by HTML  
};

function contractForm() {
    return {
        // 기본 속성
        months: 1,
        startDate: new Date().toISOString().split('T')[0],
        basePrice: 0, // Will be set in init()
        paymentDay: 1,
        paymentMethod: 'bank',

        // 쿠폰 상태
        couponCode: '',
        couponApplied: false,
        validatingCoupon: false,
        couponMessage: '',
        couponData: null,

        // UI 상태
        submitting: false,
        showInquiryModal: false,
        inquiryMessage: '',
        submittingInquiry: false,

        // 초기화
        init() {
            // Set basePrice from config after Alpine initializes
            this.basePrice = window.contractFormConfig.roomPrice || 0;
        },

        // 쿠폰 적용
        async applyCoupon() {
            if (!this.couponCode) return;
            this.validatingCoupon = true;
            this.couponMessage = '';

            try {
                const token = localStorage.getItem('token');
                if (!token) {
                    this.couponMessage = '로그인이 필요합니다.';
                    return;
                }

                const response = await fetch('/api/contracts/validate-coupon', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        room_id: window.contractFormConfig.roomId,
                        months: parseInt(this.months),
                        coupon_code: this.couponCode
                    })
                });

                const data = await response.json();
                if (response.ok) {
                    this.couponApplied = true;
                    this.couponData = data;
                    this.couponMessage = '쿠폰이 적용되었습니다.';
                } else {
                    this.couponApplied = false;
                    this.couponData = null;
                    this.couponMessage = data.error || '쿠폰 적용 실패';
                }
            } catch (e) {
                console.error(e);
                this.couponMessage = '오류가 발생했습니다.';
                this.couponApplied = false;
            } finally {
                this.validatingCoupon = false;
            }
        },

        // Getters - 기간 할인
        get durationDiscount() {
            const m = parseInt(this.months);
            if (m >= 12) return 50000;
            if (m >= 6) return 30000;
            if (m >= 3) return 20000;
            return 0;
        },

        // Getters - 쿠폰 할인
        get couponDiscount() {
            return (this.couponApplied && this.couponData) ? (this.couponData.coupon_discount || 0) : 0;
        },

        // Getters - 월요금 (기간 할인 + 쿠폰 할인 적용)
        get recurringPrice() {
            let price = this.basePrice - this.durationDiscount;
            if (this.couponApplied && this.couponData && this.couponData.cycle === 'every_month') {
                price -= this.couponDiscount;
            }
            return Math.max(0, price);
        },

        // Getters - 첫 달 기본 요금 (쿠폰 할인 포함)
        get firstMonthPrice() {
            let price = this.basePrice - this.durationDiscount - this.couponDiscount;
            return Math.max(0, price);
        },

        // Getters - 일할 계산
        get proratedAmount() {
            if (!this.startDate) return 0;
            const start = new Date(this.startDate);
            const year = start.getFullYear();
            const month = start.getMonth();
            const anchorDate = new Date(year, month, this.paymentDay);
            const diffDays = Math.ceil((anchorDate - start) / (1000 * 60 * 60 * 24));
            const daysInMonth = new Date(year, month + 1, 0).getDate();
            const dailyRate = this.recurringPrice / daysInMonth;
            return Math.round((diffDays * dailyRate) / 1000) * 1000;
        },

        // Getters - 첫 달 최종 결제 금액 (보증금 포함, 부가세 포함)
        get finalFirstPayment() {
            let price = this.firstMonthPrice + this.proratedAmount;
            if (this.paymentMethod === 'card') price = Math.round(price * 1.1);
            return price + window.contractFormConfig.roomDeposit;
        },

        // Getters - 이후 월 최종 결제 금액 (부가세 포함)
        get finalRecurringPayment() {
            let price = this.recurringPrice;
            if (this.paymentMethod === 'card') price = Math.round(price * 1.1);
            return price;
        },

        // 계약 신청
        async applyItem() {
            const token = localStorage.getItem('token');
            if (!token) {
                window.showAlert('로그인 필요', '계약 신청을 위해 로그인이 필요합니다.', 'warning', () => {
                    window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
                });
                return;
            }

            if (!this.startDate) {
                window.showAlert('알림', '입주 희망일을 선택해주세요.', 'warning');
                return;
            }

            this.submitting = true;
            try {
                const response = await fetch('/api/contracts', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        room_id: window.contractFormConfig.roomId,
                        start_date: this.startDate,
                        months: parseInt(this.months),
                        payment_day: this.paymentDay,
                        payment_method: this.paymentMethod,
                        coupon_code: this.couponApplied ? this.couponCode : null
                    })
                });

                if (response.ok) {
                    window.showAlert('신청 완료', '계약 신청이 완료되었습니다. 담당자 확인 후 연락드리겠습니다.', 'success', () => {
                        window.location.href = '/my/room';
                    });
                } else {
                    const data = await response.json();
                    window.showAlert('신청 실패', data.message || '계약 신청 중 오류가 발생했습니다.', 'error');
                    if (response.status === 401) {
                        localStorage.removeItem('token');
                        window.location.href = '/login';
                    }
                }
            } catch (error) {
                console.error('Error applying for contract:', error);
                window.showAlert('오류', '서버와의 통신 중 오류가 발생했습니다.', 'error');
            } finally {
                this.submitting = false;
            }
        },

        // 문의 모달 열기
        openInquiry() {
            const token = localStorage.getItem('token');
            if (!token) {
                window.showAlert('로그인 필요', '문의를 위해 로그인이 필요합니다.', 'warning', () => {
                    window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
                });
                return;
            }
            this.showInquiryModal = true;
        },

        // 문의 제출
        async submitInquiry() {
            if (!this.inquiryMessage.trim()) return;
            const token = localStorage.getItem('token');
            this.submittingInquiry = true;

            try {
                const response = await fetch('/api/requests', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        type: 'inquiry',
                        details: {
                            message: this.inquiryMessage,
                            room_id: window.contractFormConfig.roomId
                        }
                    })
                });

                if (response.ok) {
                    window.showAlert('문의 완료', '문의가 성공적으로 전달되었습니다.', 'success');
                    this.showInquiryModal = false;
                    this.inquiryMessage = '';
                } else {
                    window.showAlert('전송 실패', '문의 전송 중 오류가 발생했습니다.', 'error');
                }
            } catch (error) {
                console.error('Error submitting inquiry:', error);
                window.showAlert('오류', '서버와의 통신 중 오류가 발생했습니다.', 'error');
            } finally {
                this.submittingInquiry = false;
            }
        }
    };
}
