import datetime

# Read the current dashboard file
with open('c:/workspace/Eroom-Studio/app/templates/admin/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix URLs in the non-branches part (contracts and requests)
content = content.replace("fetch('/api/admin/contracts'", "fetch('/admin/api/contracts'")
content = content.replace("fetch('/api/admin/requests'", "fetch('/admin/api/requests'")

# Also fix any other potential occurrences
content = content.replace("fetch('/api/admin/branches'", "fetch('/admin/api/branches'")
content = content.replace("fetch('/api/admin/rooms'", "fetch('/admin/api/rooms'")

# Read the fixed branches tab (which already has fixed URLs)
with open('C:/Users/gnswp/.gemini/antigravity/brain/5acbf384-3922-4496-b1f0-9865ad01ddae/branches_tab_fixed.html', 'r', encoding='utf-8') as f:
    fixed_branches = f.read()

# Split content into lines for structural replacement
lines = content.splitlines()

# Find the start of the Branches tab
branches_start_idx = -1
for i, line in enumerate(lines):
    if '<!-- Branches Tab -->' in line:
        branches_start_idx = i
        break

if branches_start_idx == -1:
    print("ERROR: Could not find Branches tab start")
    exit(1)

# Find the end of the main content
main_end_idx = -1
for i, line in enumerate(lines):
    if '</main>' in line:
        main_end_idx = i
        break

if main_end_idx == -1:
    print("ERROR: Could not find </main>")
    exit(1)

# Construct new content
timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
header_comment = f"<!-- FIXED VERSION: {timestamp} (URLs Updated) -->"

# We keep lines before branches_start_idx (which now have fixed URLs)
# We insert fixed_branches
# We keep lines from main_end_idx onwards
# Note: lines[1:] to skip the old timestamp line
new_content_lines = [header_comment] + lines[1:branches_start_idx] + [fixed_branches] + lines[main_end_idx:]

with open('c:/workspace/Eroom-Studio/app/templates/admin/dashboard.html', 'w', encoding='utf-8') as f:
    f.writelines(line + '\n' for line in new_content_lines)

print(f"✅ Fixed URLs and replaced content from line {branches_start_idx} to {main_end_idx}")
print(f"Added timestamp: {timestamp}")
