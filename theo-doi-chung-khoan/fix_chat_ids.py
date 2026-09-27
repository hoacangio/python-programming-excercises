import sqlite3

conn = sqlite3.connect('data/portfolio.db')
cursor = conn.cursor()

# Fix chat IDs - remove quotes completely
cursor.execute("""UPDATE users SET telegram_chat_id = '791360434' WHERE id IN (1, 2)""")
cursor.execute("""UPDATE users SET telegram_chat_id = '987654321' WHERE id = 3""")

conn.commit()

# Verify
cursor.execute("SELECT id, username, telegram_chat_id FROM users WHERE telegram_chat_id IS NOT NULL")
print("✅ Updated chat IDs:")
for row in cursor.fetchall():
    user_id, username, chat_id = row
    # Show both raw value and the value after stripping
    print(f"  User {user_id} ({username}): raw={repr(chat_id)}, stripped={repr(chat_id.strip().strip(chr(39)))}")

conn.close()
