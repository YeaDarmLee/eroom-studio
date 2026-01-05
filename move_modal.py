
import os

filepath = r"c:\workspace\Eroom-Studio\app\templates\admin\dashboard.html"
with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Room Modal starts at 1106 (index 1105)
# Room Modal ends at 1637 (index 1636)
# Branch Modal ends at 1638 (index 1637)

room_modal_chunk = lines[1105:1637]
remaining_lines_before = lines[:1105]
remaining_lines_after = lines[1637:]

# The Branch Modal end is the first line of remaining_lines_after (index 1637 originally, now index 0)
branch_modal_end = remaining_lines_after[0]
the_rest = remaining_lines_after[1:]

new_lines = remaining_lines_before + [branch_modal_end] + ["\n"] + room_modal_chunk + the_rest

with open(filepath, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Moved Room Modal chunk successfully.")
