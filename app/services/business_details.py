import re

from werkzeug.exceptions import BadRequest


def parse_business_details(data):
    name = data.get('business_name')
    number = data.get('registration_number')
    if name is None:
        name = ''
    if number is None:
        number = ''
    if not isinstance(name, str) or not isinstance(number, str):
        raise BadRequest('상호와 사업자등록번호를 확인해주세요.')

    name, number = name.strip(), number.strip()
    if not name and not number:
        return None, None
    if not name or len(name) > 120:
        raise BadRequest('상호를 120자 이내로 입력해주세요.')
    if not re.fullmatch(r'(?:[0-9]{10}|[0-9]{3}-[0-9]{2}-[0-9]{5})', number):
        raise BadRequest('사업자등록번호 10자리를 입력해주세요.')

    digits = number.replace('-', '')
    return name, f'{digits[:3]}-{digits[3:5]}-{digits[5:]}'
