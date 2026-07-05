import os
import re

template_dir = r'c:\workspace\Eroom-Studio\mule-crawler\template'
for filename in os.listdir(template_dir):
    if filename.startswith('source_template_') and filename.endswith('.html') and 'incheon' not in filename:
        filepath = os.path.join(template_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 12개월 혜택 변경
        content = content.replace(
            '<div style="font-size: 14px; color: #2A423A; font-weight: 800;">매월 -5만 원</div>',
            '<div style="font-size: 14px; color: #2A423A; font-weight: 800;">매월 -5만 원 <span style="color: #ef4444;">+ 1달 무료</span></div>'
        )
        
        # 공식 홈페이지 카드 삭제 (정규식)
        pattern = re.compile(r'\s*<!-- 공식 홈페이지 링크 카드 -->[\s\S]*?</div>\s*(?=<p style="margin: 20px 0 0 0;)', re.IGNORECASE)
        content = pattern.sub('\n        ', content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Processed {filename}')
