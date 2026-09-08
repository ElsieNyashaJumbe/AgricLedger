import sqlite3

print("🔧 Fixing admin role...")

conn = sqlite3.connect('database/agricledger.db')
cursor = conn.cursor()

# Check if role column exists
cursor.execute("PRAGMA table_info(users)")
columns = [col[1] for col in cursor.fetchall()]

if 'role' not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'farmer'")
    print("✅ Added 'role' column")
else:
    print("ℹ️ 'role' column already exists")

if 'bio' not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN bio TEXT")
    print("✅ Added 'bio' column")
else:
    print("ℹ️ 'bio' column already exists")

# Update admin user
cursor.execute("UPDATE users SET role = 'admin' WHERE email = 'admin@agricledger.co.zw'")

if cursor.rowcount > 0:
    print("✅ Admin role updated successfully!")
else:
    print("⚠️ Admin user not found. Creating new admin...")
    
    # Create admin user
    import bcrypt
    import pyotp
    from datetime import datetime
    
    password_hash = bcrypt.hashpw('Admin@2026'.encode('utf-8'), bcrypt.gensalt())
    two_factor_secret = pyotp.random_base32()
    
    cursor.execute('''
        INSERT INTO users (
            first_name, last_name, email, phone, location,
            farmer_id, password_hash, two_factor_secret, role,
            created_at, is_active, bio
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Admin', 'AgricLedger', 'admin@agricledger.co.zw',
        '+263712345678', 'Harare', 'ADMIN001',
        password_hash, two_factor_secret, 'admin',
        datetime.now().isoformat(), 1, ''
    ))
    print("✅ Admin user created!")

conn.commit()

# Show all users
print("\n📋 Current Users:")
users = cursor.execute("SELECT id, email, role FROM users").fetchall()
for user in users:
    print(f"   {user[0]}. {user[1]} - Role: {user[2]}")

conn.close()
print("\n🎉 Done! Login with: admin@agricledger.co.zw / Admin@2026")