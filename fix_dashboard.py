import re

# Read the clean dashboard file
with open('c:/workspace/Eroom-Studio/app/templates/admin/dashboard_clean.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Read the fixed branches tab
with open('C:/Users/gnswp/.gemini/antigravity/brain/5acbf384-3922-4496-b1f0-9865ad01ddae/branches_tab_fixed.html', 'r', encoding='utf-8') as f:
    branches_tab = f.read()

# Find the end of Requests tab - look for the closing </div> after the requests list
# The Requests tab should end with </ul></div></div></div>
requests_end_pattern = r'(<!-- Requests Tab -->.*?</template>\s*</ul>\s*</div>\s*</div>\s*</div>)'

# Find where the corrupted part starts (the orphaned branch code in requests tab)
# We'll replace everything from line 312 onwards until we find the modals

# Split at the Requests tab
parts = content.split('<!-- Requests Tab -->')
before_requests = parts[0]

# Find the proper end of requests tab (before the corrupted branch code)
requests_section = parts[1]

# The requests tab should end after the empty template
# Find the position right after "</template>" and the closing tags
proper_requests_end = requests_section.find('</template>')
if proper_requests_end != -1:
    # Find the closing </ul></div></div></div> after the template
    search_start = proper_requests_end
    ul_close = requests_section.find('</ul>', search_start)
    if ul_close != -1:
        # Find the three closing </div> tags
        div_close1 = requests_section.find('</div>', ul_close)
        div_close2 = requests_section.find('</div>', div_close1 + 6)
        div_close3 = requests_section.find('</div>', div_close2 + 6)
        
        # This is where requests tab properly ends
        requests_proper = requests_section[:div_close3 + 6]
        
        # Now find where the modals start (they should be outside any tab div)
        # Look for "<!-- Room Management Modal" or similar
        after_requests = requests_section[div_close3 + 6:]
        
        # Find the start of modals or closing main/body tags
        modal_start = after_requests.find('</div>')
        if modal_start != -1:
            # Skip to after all the corrupted content
            # Find "</main>" which should come after all tabs
            main_close = after_requests.find('</main>')
            if main_close != -1:
                after_tabs = after_requests[main_close:]
                
                # Reconstruct the file
                new_content = before_requests + '<!-- Requests Tab -->' + requests_proper + '\n\n            ' + branches_tab + '\n        ' + after_tabs
                
                # Write the new file
                with open('c:/workspace/Eroom-Studio/app/templates/admin/dashboard.html', 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print("Successfully reconstructed dashboard.html")
                print(f"Total length: {len(new_content)} characters")
            else:
                print("Could not find </main> tag")
        else:
            print("Could not find modal section")
else:
    print("Could not find </template> in requests section")
