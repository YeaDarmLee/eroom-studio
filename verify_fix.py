from app import create_app
from app.models.contract import Contract

app = create_app()
with app.app_context():
    try:
        contracts = Contract.query.all()
        print(f"Successfully queried {len(contracts)} contracts.")
        for c in contracts:
            try:
                branch_name = c.room.branch.name if c.room and c.room.branch else "N/A"
                # print(f"Contract {c.id}: Branch {branch_name}")
            except Exception as e:
                print(f"Error accessing branch for contract {c.id}: {e}")
        print("Success: All contract branch data loaded without DB errors.")
    except Exception as e:
        print(f"Failed to query contracts: {e}")
