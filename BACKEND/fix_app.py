
import os

file_path = r'c:/Users/Kayrie/tests2/SRET/BACKEND/app.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_code = """        # Get last 7 days of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)"""

new_code = """        # Get last 7 days of data (inclusive of today)
        now = datetime.now()
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        start_date = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)"""

if old_code in content:
    new_content = content.replace(old_code, new_code)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully replaced code.")
else:
    print("Could not find target code.")
    # Print the section to debug
    start_marker = "def get_chart_data(user_id):"
    start_idx = content.find(start_marker)
    if start_idx != -1:
        print("Found function, printing first 20 lines:")
        print(content[start_idx:start_idx+500])
