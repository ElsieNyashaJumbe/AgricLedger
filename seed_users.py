"""
Seed Users Script for AgricLedger
Creates demo accounts for testing and demonstration
"""

import os
import sys
import bcrypt
import sqlite3
from datetime import datetime

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.user_model import get_db_connection, init_db


def seed_users():
    """Create demo user accounts"""
    
    # Initialize database
    init_db()
    
    # Demo users
    demo_users = [
        {
            'first_name': 'Admin',
            'last_name': 'AgricLedger',
            'email': 'admin@agricledger.co.zw',
            'phone': '+263712345678',
            'location': 'Harare',
            'password': 'Admin@2026',
            'farmer_id': 'ADMIN001',
            'role': 'admin'
        },
        {
            'first_name': 'John',
            'last_name': 'Moyo',
            'email': 'john.moyo@example.com',
            'phone': '+263712345679',
            'location': 'Binga',
            'password': 'Farmer@2026',
            'farmer_id': 'F0002'
        },
        {
            'first_name': 'Sarah',
            'last_name': 'Ncube',
            'email': 'sarah.ncube@example.com',
            'phone': '+263712345680',
            'location': 'Murehwa',
            'password': 'Farmer@2026',
            'farmer_id': 'F0003'
        },
        {
            'first_name': 'Tendai',
            'last_name': 'Mukai',
            'email': 'tendai.mukai@example.com',
            'phone': '+263712345681',
            'location': 'Gweru',
            'password': 'Farmer@2026',
            'farmer_id': 'F0004'
        },
        {
            'first_name': 'Robert',
            'last_name': 'Sibanda',
            'email': 'robert.sibanda@example.com',
            'phone': '+263712345682',
            'location': 'Bulawayo',
            'password': 'Farmer@2026',
            'farmer_id': 'F0005'
        }
    ]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    users_created = 0
    users_skipped = 0
    
    for user in demo_users:
        # Check if user already exists
        existing = cursor.execute(
            'SELECT id FROM users WHERE email = ?', 
            (user['email'],)
        ).fetchone()
        
        if existing:
            print(f"⚠️  User {user['email']} already exists - skipping")
            users_skipped += 1
            continue
        
        # Hash password
        password_hash = bcrypt.hashpw(
            user['password'].encode('utf-8'), 
            bcrypt.gensalt()
        )
        
        # Generate 2FA secret (for demo, we'll use a default one)
        import pyotp
        two_factor_secret = pyotp.random_base32()
        
        try:
            cursor.execute('''
                INSERT INTO users (
                    first_name, last_name, email, phone, location,
                    farmer_id, password_hash, two_factor_secret,
                    two_factor_enabled, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user['first_name'],
                user['last_name'],
                user['email'],
                user['phone'],
                user['location'],
                user['farmer_id'],
                password_hash,
                two_factor_secret,
                0,  # 2FA disabled by default for demo
                datetime.now().isoformat(),
                1   # Active
            ))
            
            conn.commit()
            users_created += 1
            print(f"✅ Created user: {user['first_name']} {user['last_name']} ({user['email']})")
            
        except Exception as e:
            print(f"❌ Error creating user {user['email']}: {e}")
    
    conn.close()
    
    print("\n" + "="*60)
    print("📋 DEMO USERS SUMMARY")
    print("="*60)
    print(f"✅ Users created: {users_created}")
    print(f"⚠️  Users skipped (already exist): {users_skipped}")
    print("")
    print("🔑 LOGIN CREDENTIALS:")
    print("-"*40)
    print("👤 ADMIN:")
    print("   Email: admin@agricledger.co.zw")
    print("   Password: Admin@2026")
    print("")
    print("👨‍🌾 FARMERS:")
    for user in demo_users:
        if user['email'] != 'admin@agricledger.co.zw':
            print(f"   {user['first_name']} {user['last_name']}:")
            print(f"      Email: {user['email']}")
            print(f"      Password: {user['password']}")
            print(f"      Farmer ID: {user['farmer_id']}")
    print("")
    print("📍 After login, go to: http://127.0.0.1:5000/dashboard")
    print("="*60)


if __name__ == '__main__':
    print("🌾 AgricLedger - Demo User Seeder")
    print("="*60)
    seed_users()
    print("\n✅ Seed process complete!")