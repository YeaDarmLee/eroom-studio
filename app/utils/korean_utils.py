"""
Hangul Choseong & Hybrid Search Utilities for Python Backend
"""
import re
import unicodedata

CHOSEONG = [
    'ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ',
    'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ',
    'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ',
    'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'
]

def normalize_search_text(val):
    """NFC 유니코드 정규화, strip, 소문자화, whitespace(\\s+) 제거"""
    if val is None:
        return ""
    normalized = unicodedata.normalize('NFC', str(val)).strip().lower()
    return re.sub(r'\s+', '', normalized)

def normalize_phone(val):
    """전화번호/구분자 제거 Normalization"""
    if val is None:
        return ""
    return re.sub(r'\D', '', str(val))

def get_choseong(val):
    """문자열에서 초성 추출"""
    if not val:
        return ""
    normalized = unicodedata.normalize('NFC', str(val))
    result = []
    for char in normalized:
        code = ord(char)
        if 0xAC00 <= code <= 0xD7A3:
            index = (code - 0xAC00) // 588
            result.append(CHOSEONG[index] if 0 <= index < len(CHOSEONG) else char)
        else:
            result.append(char)
    return "".join(result)

def is_choseong_query(query):
    """쿼리가 순수 초성으로만 구성되었는지 검사"""
    if not query:
        return False
    chars = list(query)
    return len(chars) > 0 and all(char in CHOSEONG for char in chars)

def match_korean(target, query):
    """target 문자열과 query 간의 하이브리드 매칭 (일반, 전화번호, 초성)"""
    normalized_target = normalize_search_text(target)
    normalized_query = normalize_search_text(query)

    if not normalized_query:
        return True
    if not normalized_target:
        return False

    # 1. 일반 문자열 Substring 검사
    if normalized_query in normalized_target:
        return True

    # 2. 전화번호/구분자 제거 Normalization 검사
    phone_target = normalize_phone(target)
    phone_query = normalize_phone(query)
    if phone_query and phone_target and phone_query in phone_target:
        return True

    # 3. 한글 초성 Substring 검사
    if is_choseong_query(normalized_query):
        choseong_target = get_choseong(normalized_target)
        if normalized_query in choseong_target:
            return True

    return False

def match_search_fields(fields, query):
    """여러 필드 중 하나라도 query와 매칭되면 True 반환"""
    if not query or str(query).strip() == '':
        return True
    if not isinstance(fields, (list, tuple)):
        return False
    return any(match_korean(field, query) for field in fields)
