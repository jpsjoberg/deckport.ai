#!/usr/bin/env python3
"""
Migration script to set up the admin system
Creates admin table and initial admin user
"""

import os
import sys
import getpass
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.database.connection import SessionLocal
from shared.models.base import Admin
from shared.utils.crypto import hash_password
from sqlalchemy import text

def create_admin_table():
    """Create admin table if it doesn't exist"""
    with SessionLocal() as session:
        # Check if admin table exists
        result = session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'admins'
            );
        """))
        
        table_exists = result.scalar()
        
        if not table_exists:
            print("Creating admin table...")
            session.execute(text("""
                CREATE TABLE admins (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    is_super_admin BOOLEAN DEFAULT FALSE NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    last_login TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
                );
            """))
            
            # Create index on email for faster lookups
            session.execute(text("""
                CREATE INDEX idx_admins_email ON admins(email);
            """))
            
            # Create index on username for faster lookups
            session.execute(text("""
                CREATE INDEX idx_admins_username ON admins(username);
            """))
            
            session.commit()
            print("✅ Admin table created successfully")
        else:
            print("ℹ️  Admin table already exists")

def create_initial_admin():
    """Create initial super admin user"""
    with SessionLocal() as session:
        # Check if any admin users exist
        admin_count = session.query(Admin).count()
        
        if admin_count > 0:
            print(f"ℹ️  {admin_count} admin user(s) already exist")
            return
        
        print("\n🔐 Creating initial super admin user...")
        
        # Get admin details
        while True:
            username = input("Enter admin username: ").strip()
            if username and len(username) >= 3:
                break
            print("Username must be at least 3 characters long")
        
        while True:
            email = input("Enter admin email: ").strip().lower()
            if email and '@' in email:
                break
            print("Please enter a valid email address")
        
        while True:
            password = getpass.getpass("Enter admin password: ")
            if len(password) >= 8:
                confirm_password = getpass.getpass("Confirm password: ")
                if password == confirm_password:
                    break
                else:
                    print("Passwords don't match. Please try again.")
            else:
                print("Password must be at least 8 characters long")
        
        # Create admin user
        password_hash = hash_password(password)
        
        admin = Admin(
            username=username,
            email=email,
            password_hash=password_hash,
            is_super_admin=True,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        session.add(admin)
        session.commit()
        
        print(f"✅ Super admin user '{username}' created successfully!")
        print(f"   Email: {email}")
        print(f"   Super Admin: Yes")
        print("\n🚀 You can now login to the admin panel with these credentials")

def main():
    """Main migration function"""
    print("🛡️  Setting up Deckport Admin System")
    print("=" * 50)
    
    try:
        # Create admin table
        create_admin_table()
        
        # Create initial admin user
        create_initial_admin()
        
        print("\n✅ Admin system setup completed successfully!")
        print("\n🔗 Next steps:")
        print("   1. Start the application")
        print("   2. Navigate to /admin/login")
        print("   3. Login with your admin credentials")
        
    except Exception as e:
        print(f"\n❌ Error setting up admin system: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
