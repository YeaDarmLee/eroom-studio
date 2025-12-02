import datetime

# Read the current dashboard file
with open('c:/workspace/Eroom-Studio/app/templates/admin/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Read the fixed branches tab
with open('C:/Users/gnswp/.gemini/antigravity/brain/5acbf384-3922-4496-b1f0-9865ad01ddae/branches_tab_fixed.html', 'r', encoding='utf-8') as f:
    fixed_branches = f.read()

# Find the start of the Branches tab
branches_start_idx = -1
for i, line in enumerate(lines):
    if '<!-- Branches Tab -->' in line:
        branches_start_idx = i
        break

if branches_start_idx == -1:
    print("ERROR: Could not find Branches tab start")
    exit(1)

# Find the end of the main content (where we want to stop replacing)
# We assume everything after the Branches tab until </main> is part of the Branches tab (including modals)
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
header_comment = f"<!-- FIXED VERSION: {timestamp} -->\n"

# We keep lines before branches_start_idx
# We insert fixed_branches
# We keep lines from main_end_idx onwards
new_content_lines = [header_comment] + lines[:branches_start_idx] + [fixed_branches + '\n'] + lines[main_end_idx:]

with open('c:/workspace/Eroom-Studio/app/templates/admin/dashboard.html', 'w', encoding='utf-8') as f:
    f.writelines(new_content_lines)

print(f"✅ Replaced content from line {branches_start_idx} to {main_end_idx}")
print(f"Added timestamp: {timestamp}")
