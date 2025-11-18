import pymongo
from pymongo import MongoClient
import socket

# MongoDB connection strings to try
CONNECTION_STRINGS = [
    "mongodb+srv://larabaseggio2000_db_user:3B36ycsXvgFU2xRi@ros-data.ujsrakb.mongodb.net/data_phase1?ssl=true&ssl_cert_reqs=CERT_NONE",
    "mongodb+srv://larabaseggio2000_db_user:3B36ycsXvgFU2xRi@ros-data.ujsrakb.mongodb.net/data_phase1?retryWrites=true&w=majority",
    "mongodb+srv://larabaseggio2000_db_user:3B36ycsXvgFU2xRi@ros-data.ujsrakb.mongodb.net/data_phase1",
]

print("Testing MongoDB connection...")
print("=" * 50)

# Get current IP address
try:
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"Your hostname: {hostname}")
    print(f"Your local IP: {local_ip}")
    print("\n⚠ Make sure this IP (or 0.0.0.0/0 for all IPs) is whitelisted in MongoDB Atlas")
    print("  Go to: Network Access → Add IP Address")
    print()
except:
    pass

success = False
for i, MONGO_URI in enumerate(CONNECTION_STRINGS, 1):
    print(f"Trying connection string {i}/{len(CONNECTION_STRINGS)}...")
    try:
        # Connect to MongoDB with shorter timeout for testing
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
        
        # Test connection with ping
        client.admin.command('ping')
        print("✓ Connection successful!")
        print()
        
        # Get database info
        db = client.data_phase1
        print(f"✓ Connected to database: {db.name}")
        print()
        
        # List existing collections
        collections = db.list_collection_names()
        if collections:
            print(f"Existing collections ({len(collections)}):")
            for collection_name in collections:
                count = db[collection_name].count_documents({})
                print(f"  - {collection_name}: {count} documents")
        else:
            print("No collections found (database is empty)")
        
        print()
        print("=" * 50)
        print("Connection test passed! ✓")
        print(f"Working connection string: {MONGO_URI}")
        success = True
        break
        
    except pymongo.errors.ServerSelectionTimeoutError as e:
        print(f"✗ Connection failed: Timeout")
        if i < len(CONNECTION_STRINGS):
            print("  Trying next connection string...\n")
        else:
            print("  Possible causes:")
            print("  - IP address not whitelisted in MongoDB Atlas (MOST LIKELY)")
            print("  - Network connectivity issues")
            print("  - Firewall blocking connection")
            print(f"  - Error details: {str(e)[:200]}")
        
    except pymongo.errors.OperationFailure as e:
        print("✗ Authentication failed")
        print("  Possible causes:")
        print("  - Incorrect username or password")
        print("  - User doesn't have access to the database")
        print(f"  - Error: {e}")
        break
        
    except Exception as e:
        error_msg = str(e)
        if "SSL" in error_msg or "handshake" in error_msg:
            print(f"✗ SSL handshake failed")
            if i < len(CONNECTION_STRINGS):
                print("  Trying next connection string...\n")
            else:
                print("  This often indicates IP whitelist issue")
                print("  Make sure your IP is whitelisted in MongoDB Atlas")
        else:
            print(f"✗ Connection failed: {error_msg[:200]}")
            print(f"  Error type: {type(e).__name__}")
        if i >= len(CONNECTION_STRINGS):
            break

if not success:
    print("\n" + "=" * 50)
    print("TROUBLESHOOTING STEPS:")
    print("1. Go to MongoDB Atlas → Network Access")
    print("2. Click 'Add IP Address'")
    print("3. Click 'Add Current IP Address' (or use 0.0.0.0/0 for testing)")
    print("4. Wait a few minutes for changes to propagate")
    print("5. Run this test again")

