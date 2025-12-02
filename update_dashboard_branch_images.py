
import os

file_path = r'c:\workspace\Eroom-Studio\app\templates\admin\dashboard.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Define the target block to replace (Branch Image Section)
target_start = """                                            <label class="block text-sm font-medium text-gray-700">지점 이미지</label>
                                            <div class="mt-1">
                                                <div class="flex justify-center px-6 pt-5 pb-6 border-2 border-dashed rounded-xl transition-all duration-200"
                                                    :class="isDraggingImage ? 'border-primary bg-primary/5' : 'border-gray-300 hover:border-primary/50'"
                                                    @dragover.prevent="isDraggingImage = true"
                                                    @dragleave.prevent="isDraggingImage = false"
                                                    @drop.prevent="handleImageDrop($event)">"""

target_end = """                                            </div>
                                        </div>"""

# Find start and end indices
start_idx = content.find(target_start)
if start_idx == -1:
    print("Start block not found")
    exit(1)

# Find the end of the div block. This is tricky with nested divs.
# We'll look for the closing tag of the outer div.
# Based on the view_file output, the block ends at line 531.
# Let's try to find the specific closing sequence.

# The block ends with:
#                                                     </div>
#                                                 </div>
#                                             </div>
#                                         </div>

end_sequence = """                                                    </div>
                                                </div>
                                            </div>
                                        </div>"""

end_idx = content.find(end_sequence, start_idx)
if end_idx == -1:
    print("End block not found")
    # Try a more robust search or manual line counting if needed
    # Let's try to find the next section header as a delimiter
    next_section = """                                        <!-- Floor Management Section (Only in Edit Mode) -->"""
    end_idx = content.find(next_section, start_idx)
    if end_idx == -1:
        print("Next section not found")
        exit(1)
    # Adjust end_idx to include the closing divs before the next section
    # We need to replace up to the line before next_section
    end_idx = content.rfind("</div>", start_idx, end_idx) # This might be risky
    # Let's use the line numbers from view_file.
    # Lines 488 to 531.
    
    lines = content.splitlines()
    # Verify lines
    if "지점 이미지" not in lines[488]:
        print(f"Line 488 mismatch: {lines[488]}")
        exit(1)
    
    # Construct new content
    new_block = """                                            <label class="block text-sm font-medium text-gray-700">지점 이미지</label>
                                            <div class="mt-1">
                                                <!-- Drag & Drop Zone -->
                                                <div class="flex justify-center px-6 pt-5 pb-6 border-2 border-dashed rounded-xl transition-all duration-200 mb-4"
                                                    :class="isDraggingBranchImage ? 'border-primary bg-primary/5' : 'border-gray-300 hover:border-primary/50'"
                                                    @dragover.prevent="isDraggingBranchImage = true"
                                                    @dragleave.prevent="isDraggingBranchImage = false"
                                                    @drop.prevent="handleBranchImageDrop($event)">
                                                    <div class="space-y-1 text-center">
                                                        <i class="ri-image-add-line text-4xl text-gray-400 mb-2"></i>
                                                        <div class="flex text-sm text-gray-600 justify-center">
                                                            <label
                                                                class="relative cursor-pointer bg-white rounded-md font-medium text-primary hover:text-primary/80 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary">
                                                                <span>이미지 업로드</span>
                                                                <input type="file" class="sr-only" multiple
                                                                    @change="handleBranchImageUpload($event)"
                                                                    accept="image/*">
                                                            </label>
                                                            <p class="pl-1">또는 여기로 드래그</p>
                                                        </div>
                                                        <p class="text-xs text-gray-500">PNG, JPG, GIF (최대 5MB)</p>
                                                    </div>
                                                </div>

                                                <!-- New Images Preview -->
                                                <template x-if="branchImages.length > 0">
                                                    <div class="mb-4">
                                                        <h4 class="text-sm font-medium text-gray-700 mb-2">새로 추가할 이미지</h4>
                                                        <div class="grid grid-cols-4 gap-4">
                                                            <template x-for="(img, index) in branchImages" :key="index">
                                                                <div class="relative group aspect-square">
                                                                    <img :src="img.preview" class="w-full h-full object-cover rounded-lg">
                                                                    <button type="button" @click="removeBranchImage(index)"
                                                                        class="absolute top-1 right-1 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                        <i class="ri-close-line"></i>
                                                                    </button>
                                                                </div>
                                                            </template>
                                                        </div>
                                                    </div>
                                                </template>

                                                <!-- Existing Images -->
                                                <template x-if="existingBranchImages.length > 0">
                                                    <div>
                                                        <h4 class="text-sm font-medium text-gray-700 mb-2">등록된 이미지</h4>
                                                        <div class="grid grid-cols-4 gap-4">
                                                            <template x-for="img in existingBranchImages" :key="img.id">
                                                                <div class="relative group aspect-square">
                                                                    <img :src="img.url" class="w-full h-full object-cover rounded-lg">
                                                                    <button type="button" @click="deleteExistingBranchImage(img.id, currentBranch.id)"
                                                                        class="absolute top-1 right-1 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                        <i class="ri-delete-bin-line"></i>
                                                                    </button>
                                                                </div>
                                                            </template>
                                                        </div>
                                                    </div>
                                                </template>
                                            </div>"""
    
    # Replace lines 488-531 (inclusive, 0-indexed is 488-532)
    # Line 532 is "                                        <!-- Floor Management Section (Only in Edit Mode) -->"
    
    # Check line 532 content
    if "Floor Management Section" not in lines[532]:
         print(f"Line 532 mismatch: {lines[532]}")
         # Try to find it
         for i, line in enumerate(lines):
             if "Floor Management Section" in line:
                 print(f"Found Floor Management at line {i}")
                 end_line_idx = i
                 break
    else:
        end_line_idx = 532

    # Replace lines
    new_lines = lines[:488] + [new_block] + lines[end_line_idx:]
    new_content = '\n'.join(new_lines)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Successfully updated dashboard.html")

