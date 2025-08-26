#!/usr/bin/env python3
"""
Test authentication with database directly
"""
import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

# Activate virtual environment
activate_this = os.path.join(backend_dir, 'venv', 'bin', 'activate_this.py')
if os.path.exists(activate_this):
    with open(activate_this) as f:
        exec(f.read(), dict(__file__=activate_this))

from sqlalchemy import create_engine, text
from app.models.user import User, MembershipType
from sqlalchemy.orm import sessionmaker

# Create database connection
DATABASE_URL = "mysql+pymysql://root:Pp123456@127.0.0.1:3306/stock_analysis_dev"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Test 1: Check if we can query the admin user
    print("Testing database connection and user query...")
    admin_user = session.query(User).filter(User.username == "admin").first()
    
    if admin_user:
        print(f"Found admin user: {admin_user.username}")
        print(f"Membership type: {admin_user.membership_type}")
        print(f"Membership type value: {admin_user.membership_type.value if admin_user.membership_type else 'None'}")
    else:
        print("Admin user not found")
    
    # Test 2: Create a new test user to see if the enum works
    print("\nTesting user creation...")
    test_user = User(
        username="testuser2",
        email="test2@example.com", 
        password_hash="dummy_hash",
        membership_type=MembershipType.FREE
    )
    
    session.add(test_user)
    session.commit()
    
    print("Test user created successfully")
    
    # Test 3: Query the new test user
    retrieved_user = session.query(User).filter(User.username == "testuser2").first()
    if retrieved_user:
        print(f"Retrieved test user: {retrieved_user.username}")
        print(f"Membership type: {retrieved_user.membership_type}")
        print(f"Membership type value: {retrieved_user.membership_type.value}")
    
    # Cleanup
    session.delete(retrieved_user)
    session.commit()
    print("Test user cleaned up")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    session.close()