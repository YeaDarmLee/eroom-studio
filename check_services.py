from app import create_app
from app.models.branch import BranchService, Branch

app = create_app()

with app.app_context():
    services = BranchService.query.all()
    print(f'\n총 {len(services)}개의 서비스가 DB에 등록되어 있습니다:\n')
    
    for s in services:
        branch = Branch.query.get(s.branch_id)
        print(f'- [{branch.name if branch else "Unknown"}] {s.name} ({s.service_type}) - {s.description}')
    
    # 지점별로 그룹화
    print('\n\n=== 지점별 서비스 ===\n')
    branches = Branch.query.all()
    for branch in branches:
        print(f'\n📍 {branch.name}:')
        common = [s for s in branch.services if s.service_type == 'common']
        specialized = [s for s in branch.services if s.service_type == 'specialized']
        
        if common:
            print('  공통 서비스:')
            for s in common:
                print(f'    • {s.name} - {s.description}')
        else:
            print('  공통 서비스: 없음')
            
        if specialized:
            print('  특화 서비스:')
            for s in specialized:
                print(f'    • {s.name} - {s.description}')
        else:
            print('  특화 서비스: 없음')
