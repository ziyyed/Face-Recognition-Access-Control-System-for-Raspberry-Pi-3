from app import app, db, Employee

with app.app_context():
    employees = Employee.query.all()
    print(f"Found {len(employees)} employees:")
    for emp in employees:
        print(f"ID: {emp.id}, Name: {emp.name}, Position: {emp.position}")
