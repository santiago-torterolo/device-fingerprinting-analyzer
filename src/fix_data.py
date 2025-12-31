import duckdb
import random

def fix():
    try:
        conn = duckdb.connect('data/device_fp.db')
        
        # Get all device IDs
        devices = conn.execute("SELECT device_id FROM devices").fetchall()
        print(f"Fixing {len(devices)} devices...")
        
        for (d_id,) in devices:
            # Assign a random score between 10 and 95
            score = random.uniform(10.0, 98.0)
            level = 'high' if score > 70 else 'medium' if score > 40 else 'low'
            conn.execute("UPDATE devices SET risk_score = ?, risk_level = ? WHERE device_id = ?", [score, level, d_id])
            
        # Also fix counts just in case
        print("Fixing crossing counts...")
        conn.execute("""
            UPDATE devices SET account_count = (
                SELECT COUNT(DISTINCT account_id) 
                FROM device_account_crossings 
                WHERE device_account_crossings.device_id = devices.device_id
            )
        """)
        
        conn.commit()
        conn.close()
        print("Successfully fixed database scores and counts.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix()
