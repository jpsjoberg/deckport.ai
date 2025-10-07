#!/usr/bin/env python3
"""
Reset Admin Password
Creates or updates admin password for login access
"""

import sys
sys.path.append('/home/jp/deckport.ai')

from shared.database.connection import SessionLocal
from shared.models.base import Admin
from shared.utils.crypto import hash_password
from datetime import datetime, timezone
import getpass

def reset_admin_password():
    """Reset admin password"""
    
    print("🔐 Deckport Admin Password Reset")
    print("=" * 40)
    
    # Get admin email
    email = input("Admin email (default: admin@deckport.ai): ").strip()
    if not email:
        email = "admin@deckport.ai"
    
    # Get new password
    password = getpass.getpass("New password: ")
    if not password:
        print("❌ Password cannot be empty")
        return False
    
    confirm_password = getpass.getpass("Confirm password: ")
    if password != confirm_password:
        print("❌ Passwords don't match")
        return False
    
    try:
        with SessionLocal() as session:
            # Find admin
            admin = session.query(Admin).filter(Admin.email == email).first()
            
            if admin:
                print(f"✅ Found admin: {admin.username} ({admin.email})")
                
                # Update password
                admin.password_hash = hash_password(password)
                admin.updated_at = datetime.now(timezone.utc)
                admin.is_active = True  # Ensure account is active
                
                session.commit()
                
                print("✅ Password updated successfully!")
                print(f"   Email: {admin.email}")
                print(f"   Username: {admin.username}")
                print(f"   Super Admin: {admin.is_super_admin}")
                print(f"   Active: {admin.is_active}")
                
            else:
                print(f"❌ Admin not found: {email}")
                
                # Ask if we should create new admin
                create = input("Create new admin account? (y/n): ").strip().lower()
                if create == 'y':
                    username = input("Username: ").strip()
                    if not username:
                        print("❌ Username cannot be empty")
                        return False
                    
                    # Create new admin
                    new_admin = Admin(
                        username=username,
                        email=email,
                        password_hash=hash_password(password),
                        is_super_admin=True,
                        is_active=True
                    )
                    
                    session.add(new_admin)
                    session.commit()
                    
                    print("✅ New admin created successfully!")
                    print(f"   Email: {email}")
                    print(f"   Username: {username}")
                    print(f"   Super Admin: True")
                
                else:
                    return False
            
            print("\n🎯 Login Information:")
            print(f"   URL: https://deckport.ai/admin/login")
            print(f"   Email: {email}")
            print(f"   Password: [the password you just set]")
            
            return True
            
    except Exception as e:
        print(f"❌ Error updating admin password: {e}")
        return False

def list_admins():
    """List all admin accounts"""
    print("📋 Current Admin Accounts")
    print("=" * 40)
    
    try:
        with SessionLocal() as session:
            admins = session.query(Admin).all()
            
            if not admins:
                print("No admin accounts found")
                return
            
            for admin in admins:
                status = "🟢 Active" if admin.is_active else "🔴 Inactive"
                role = "👑 Super Admin" if admin.is_super_admin else "👤 Admin"
                
                print(f"{status} {role}")
                print(f"   ID: {admin.id}")
                print(f"   Username: {admin.username}")
                print(f"   Email: {admin.email}")
                print(f"   Created: {admin.created_at.strftime('%Y-%m-%d %H:%M') if admin.created_at else 'Unknown'}")
                print()
            
    except Exception as e:
        print(f"❌ Error listing admins: {e}")

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == 'list':
        list_admins()
    else:
        reset_admin_password()

if __name__ == "__main__":
    main()
