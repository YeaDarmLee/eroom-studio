# Final fix for Alpine.js dashboard
# Read the files
with open('c:/workspace/Eroom-Studio/app/templates/admin/dashboard.html', 'r', encoding='utf-8') as f:
    dashboard_lines = f.readlines()

with open('C:/Users/gnswp/.gemini/antigravity/brain/5acbf384-3922-4496-b1f0-9865ad01ddae/branches_tab_fixed.html', 'r', encoding='utf-8') as f:
    fixed_branches = f.read()

# Find where to insert - line 321 is "<!-- Branches Tab -->"
# We need to find where the current broken Branches tab ends
# It should end before the modals section

# Find the line that starts the modals (after the broken branches tab)
# Look for "<!-- Room Management Modal" which should be around line 500+
for i, line in enumerate(dashboard_lines):
    if '<!-- Room Management Modal' in line or '<!-- Branch Create/Edit Modal' in line:
        if i > 400:  # Make sure we're past the broken branches section
            modal_start_line = i
            break
else:
    print("ERROR: Could not find modal section")
    exit(1)

# Now reconstruct the file:
# - Keep everything before line 321 (index 320)
# - Insert the fixed branches tab
# - Keep everything from the modals onwards

before_branches = ''.join(dashboard_lines[:320])  # Lines 1-320
after_branches = ''.join(dashboard_lines[modal_start_line:])  # From modals to end

# Reconstruct
new_content = before_branches + '\n            ' + fixed_branches + '\n\n            ' + after_branches

# Write the fixed file
with open('c:/workspace/Eroom-Studio/app/templates/admin/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"✅ Successfully fixed dashboard.html!")
print(f"- Kept lines 1-320")
print(f"- Inserted fixed Branches tab (537 lines)")
print(f"- Kept modals and closing tags from line {modal_start_line+1}")
print(f"Total lines in new file: {len(new_content.splitlines())}")
