/**
 * Hangul Choseong & Hybrid Search Utilities for Admin Panel
 */

const CHOSEONG = [
    'ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ',
    'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ',
    'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ',
    'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'
];

/**
 * NFC 유니코드 정규화, 소문자화, 공백 제거
 */
function normalizeSearchText(val) {
    if (val === null || val === undefined) return '';
    return String(val)
        .normalize('NFC')
        .trim()
        .toLowerCase()
        .replace(/\s+/g, '');
}

/**
 * 전화번호 구분자 제거 Normalization
 */
function normalizePhone(val) {
    if (val === null || val === undefined) return '';
    return String(val).replace(/\D/g, '');
}

/**
 * 문자열에서 초성을 추출
 */
function getChoseong(str) {
    if (!str) return '';
    let result = '';
    const normalized = String(str).normalize('NFC');

    for (let i = 0; i < normalized.length; i++) {
        const code = normalized.charCodeAt(i);
        if (code >= 0xAC00 && code <= 0xD7A3) {
            const index = Math.floor((code - 0xAC00) / 588);
            result += CHOSEONG[index] || normalized[i];
        } else {
            result += normalized[i];
        }
    }
    return result;
}

/**
 * 쿼리가 순수 초성으로만 구성되었는지 검사
 */
function isChoseongQuery(query) {
    if (!query) return false;
    const chars = [...query];
    return chars.length > 0 && chars.every(char => CHOSEONG.includes(char));
}

/**
 * target 문자열과 query 간의 하이브리드 검색 (일반, 전화번호, 초성)
 */
function matchKorean(target, query) {
    const normalizedTarget = normalizeSearchText(target);
    const normalizedQuery = normalizeSearchText(query);

    if (!normalizedQuery) return true;
    if (!normalizedTarget) return false;

    // 1. 일반 문자열 Substring 검사
    if (normalizedTarget.includes(normalizedQuery)) return true;

    // 2. 전화번호/구분자 제거 Normalization 검사
    const phoneTarget = normalizePhone(target);
    const phoneQuery = normalizePhone(query);
    if (phoneQuery && phoneTarget && phoneTarget.includes(phoneQuery)) return true;

    // 3. 한글 초성 Substring 검사
    if (isChoseongQuery(normalizedQuery)) {
        const choseongTarget = getChoseong(normalizedTarget);
        if (choseongTarget.includes(normalizedQuery)) {
            return true;
        }
    }

    return false;
}

/**
 * 여러 필드 중 하나라도 query와 매칭되면 true 반환
 */
function matchSearchFields(fields, query) {
    if (!query || String(query).trim() === '') return true;
    if (!Array.isArray(fields)) return false;
    return fields.some(field => matchKorean(field, query));
}

// Global Export
window.normalizeSearchText = normalizeSearchText;
window.normalizePhone = normalizePhone;
window.getChoseong = getChoseong;
window.isChoseongQuery = isChoseongQuery;
window.matchKorean = matchKorean;
window.matchSearchFields = matchSearchFields;
