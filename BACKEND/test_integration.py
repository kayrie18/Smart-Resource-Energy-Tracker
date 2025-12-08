import urllib.request
import urllib.parse
import json
import sys
import datetime

BASE_URL = "http://localhost:5000/api"
COOKIES = {}

def print_pass(msg):
    print(f"[PASS]: {msg}")

def print_fail(msg):
    print(f"[FAIL]: {msg}")
    sys.exit(1)

def request(method, endpoint, data=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {'Content-Type': 'application/json'}
    
    if data:
        data_bytes = json.dumps(data).encode('utf-8')
    else:
        data_bytes = None

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    
    # Add cookies
    cookie_str = "; ".join([f"{k}={v}" for k, v in COOKIES.items()])
    if cookie_str:
        req.add_header('Cookie', cookie_str)

    try:
        with urllib.request.urlopen(req) as response:
            # Capture cookies
            if 'Set-Cookie' in response.headers:
                for cookie in response.headers.get_all('Set-Cookie'):
                    parts = cookie.split(';')[0].split('=')
                    if len(parts) == 2:
                        COOKIES[parts[0]] = parts[1]
            
            resp_body = response.read().decode('utf-8')
            if resp_body:
                return json.loads(resp_body)
            return {}
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode()}")
        print_fail(f"Request to {endpoint} failed")
    except Exception as e:
        print_fail(f"Request error: {str(e)}")

def run_tests():
    print("Starting Comprehensive System Check...\n")

    # 1. Registration
    timestamp = datetime.datetime.now().strftime("%H%M%S")
    username = f"testuser_{timestamp}"
    password = "securepassword123"
    
    print(f"1. Testing Registration for '{username}'...")
    reg_data = {
        "username": username,
        "email": f"{username}@test.com",
        "password": password,
        "user_category": "single",
        "phone_number": "1234567890",
        "custom_energy_limit": 90, # 3 kWh/day
        "custom_water_limit": 3000 # 100 L/day
    }
    resp = request("POST", "/register", reg_data)
    if resp.get('message') == 'User created successfully':
        print_pass("User registered successfully")
    else:
        print_fail("Registration failed")

    # 2. Login
    print("\n2. Testing Login...")
    login_data = {"username": username, "password": password}
    resp = request("POST", "/login", login_data)
    user_id = resp.get('user_id')
    if user_id:
        print_pass(f"Logged in successfully. User ID: {user_id}")
    else:
        print_fail("Login failed")

    # 3. Add Entries
    print("\n3. Testing Entry Creation...")
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Energy Entry (2.5 kWh)
    energy_data = {
        "user_id": user_id,
        "electricity_usage": 2.5,
        "reading_date": today
    }
    resp = request("POST", "/energy-entries", energy_data)
    if "Energy entry added" in resp.get('message', ''):
        print_pass(f"Energy entry added (2.5 kWh)")
    else:
        print_fail(f"Failed to add energy entry")

    # Water Entry (50 L)
    water_data = {
        "user_id": user_id,
        "water_usage": 50,
        "reading_date": today
    }
    resp = request("POST", "/water-entries", water_data)
    if "Water entry added" in resp.get('message', ''):
        print_pass(f"Water entry added (50 L)")
    else:
        print_fail("Failed to add water entry")

    # 4. Dashboard Data & Logic Check
    print("\n4. Verifying Dashboard Logic...")
    dash_data = request("GET", f"/dashboard/{user_id}")
    
    # Check Totals
    if float(dash_data['monthly_energy_used']) == 2.5:
        print_pass("Monthly Energy Calculation Correct")
    else:
        print_fail(f"Energy Total Mismatch: got {dash_data['monthly_energy_used']}")
        
    if float(dash_data['monthly_water_used']) == 50:
        print_pass("Monthly Water Calculation Correct")
    else:
        print_fail(f"Water Total Mismatch: got {dash_data['monthly_water_used']}")

    # 5. Chart Data (Daily Limits Check)
    print("\n5. Verifying Chart Data (Daily Logic)...")
    chart_data = request("GET", f"/chart-data/{user_id}")
    
    # Verify Limits are daily (Monthly 90 / 30 = 3 kWh)
    daily_energy_limit = chart_data['energy_limit']
    if abs(daily_energy_limit - 3.0) < 0.1:
        print_pass(f"Energy Limit is correctly DAILY ({daily_energy_limit} kWh)")
    else:
        print_fail(f"Energy Limit Logic Error. Expected ~3.0, got {daily_energy_limit}")

    # Verify Data Arrays
    if len(chart_data['energy_data']) == 7:
        print_pass("Chart Data returns 7 days")
    else:
        print_fail("Chart Data length mismatch")

    # 6. Profile Update
    print("\n6. Testing Profile Update...")
    update_data = {"custom_energy_limit": 120}
    request("PUT", f"/user/{user_id}/profile", update_data)
    
    # Verify Update in Dashboard
    chart_data = request("GET", f"/chart-data/{user_id}")
    new_limit = chart_data['energy_limit'] # Should be 120/30 = 4
    if abs(new_limit - 4.0) < 0.1:
        print_pass(f"Profile Update Successful (New Daily Limit: {new_limit} kWh)")
    else:
        print_fail(f"Profile Update Failed. Expected ~4.0, got {new_limit}")

    # 7. CSV Export Logic verify (Download)
    print("\n7. Testing CSV Export...")
    try:
        url = f"{BASE_URL}/export/{user_id}?start_date={today}&end_date={today}"
        with urllib.request.urlopen(url) as response:
            csv_content = response.read().decode('utf-8')
            if "Date,Type,Usage" in csv_content and "2.5" in csv_content:
                print_pass("CSV Export generated and contains correct data")
            else:
                print_fail("CSV Export content mismatch")
    except Exception as e:
        print_fail(f"CSV Export failed: {e}")

    print("\nALL SYSTEMS GO! The project works properly.")

if __name__ == "__main__":
    run_tests()
