"""
DB 마이그레이션 스크립트: 미매핑 계약 지원
- Contract 테이블에 임시 사용자 정보 컬럼 추가
- Contract.user_id를 nullable로 변경
- User 테이블에 phone 컬럼 추가
"""
from app import create_app
from app.extensions import db
from sqlalchemy import text

def migrate_unmapped_contracts():
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 미매핑 계약 지원을 위한 DB 마이그레이션 시작...")
            
            # 1. User 테이블에 phone 컬럼 추가
            print("\n1️⃣ User 테이블에 phone 컬럼 추가...")
            try:
                db.session.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN phone VARCHAR(20) UNIQUE DEFAULT NULL
                """))
                print("✅ phone 컬럼 추가 완료")
            except Exception as e:
                if "Duplicate column" in str(e):
                    print("ℹ️  phone 컬럼이 이미 존재합니다")
                else:
                    raise
            
            # 2. Contract 테이블에 임시 사용자 정보 컬럼 추가
            print("\n2️⃣ Contract 테이블에 임시 사용자 정보 컬럼 추가...")
            
            columns_to_add = [
                ("temp_user_name", "VARCHAR(64)"),
                ("temp_user_phone", "VARCHAR(20)"),
                ("temp_user_email", "VARCHAR(120)")
            ]
            
            for col_name, col_type in columns_to_add:
                try:
                    db.session.execute(text(f"""
                        ALTER TABLE contracts 
                        ADD COLUMN {col_name} {col_type} DEFAULT NULL
                    """))
                    print(f"✅ {col_name} 컬럼 추가 완료")
                except Exception as e:
                    if "Duplicate column" in str(e):
                        print(f"ℹ️  {col_name} 컬럼이 이미 존재합니다")
                    else:
                        raise
            
            # 3. Contract.user_id를 nullable로 변경
            print("\n3️⃣ Contract.user_id를 nullable로 변경...")
            try:
                db.session.execute(text("""
                    ALTER TABLE contracts 
                    MODIFY COLUMN user_id INT DEFAULT NULL
                """))
                print("✅ user_id nullable 변경 완료")
            except Exception as e:
                print(f"⚠️  user_id 변경 중 오류 (이미 nullable일 수 있음): {e}")
            
            # 변경사항 커밋
            db.session.commit()
            print("\n✅ 마이그레이션 완료!")
            
            # 4. 테이블 구조 확인
            print("\n📋 Contract 테이블 구조 확인:")
            result = db.session.execute(text("DESCRIBE contracts"))
            for row in result:
                print(f"  {row[0]:<20} {row[1]:<15} {row[2]:<5} {row[3]}")
            
            print("\n📋 User 테이블 구조 확인:")
            result = db.session.execute(text("DESCRIBE users"))
            for row in result:
                print(f"  {row[0]:<20} {row[1]:<15} {row[2]:<5} {row[3]}")
                
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 마이그레이션 실패: {e}")
            raise

if __name__ == "__main__":
    migrate_unmapped_contracts()
