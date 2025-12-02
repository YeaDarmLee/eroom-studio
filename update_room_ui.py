import sys

file_path = r'c:\workspace\Eroom-Studio\app\templates\admin\dashboard.html'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Insert after line 793 (index 792), before the closing </div> at line 794
insert_index = 793

new_content = """                                        <div>
                                            <label class="block text-sm font-medium text-gray-700 mb-2">방 이미지</label>
                                            
                                            <!-- Drag and Drop Zone -->
                                            <div class="flex justify-center px-6 pt-5 pb-6 border-2 border-dashed rounded-xl transition-all duration-200 mb-3"
                                                :class="isDraggingRoomImage ? 'border-primary bg-primary/5' : 'border-gray-300 hover:border-primary/50'"
                                                @dragover.prevent="isDraggingRoomImage = true"
                                                @dragleave.prevent="isDraggingRoomImage = false"
                                                @drop.prevent="handleRoomImageDrop($event)">
                                                <div class="space-y-1 text-center">
                                                    <i class="ri-image-add-line text-3xl text-gray-400"></i>
                                                    <div class="flex text-sm text-gray-600">
                                                        <label class="relative cursor-pointer bg-white rounded-md font-medium text-primary hover:text-primary/80">
                                                            <span>이미지 업로드</span>
                                                            <input type="file" class="sr-only" multiple
                                                                @change="handleRoomImageUpload($event)"
                                                                accept="image/*">
                                                        </label>
                                                        <p class="pl-1">또는 여기로 드래그</p>
                                                    </div>
                                                    <p class="text-xs text-gray-500">PNG, JPG (최대 5MB, 여러 장 가능)</p>
                                                </div>
                                            </div>

                                            <!-- Existing Images -->
                                            <template x-if="existingRoomImages.length > 0">
                                                <div class="mb-3">
                                                    <p class="text-xs font-medium text-gray-700 mb-2">기존 이미지</p>
                                                    <div class="grid grid-cols-3 gap-2">
                                                        <template x-for="img in existingRoomImages" :key="img.id">
                                                            <div class="relative group">
                                                                <img :src="img.url" class="w-full h-20 object-cover rounded-lg">
                                                                <button type="button" 
                                                                    @click="deleteExistingRoomImage(img.id, currentRoom.id)"
                                                                    class="absolute top-1 right-1 bg-red-500 text-white p-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
                                                                    <i class="ri-close-line text-xs"></i>
                                                                </button>
                                                            </div>
                                                        </template>
                                                    </div>
                                                </div>
                                            </template>

                                            <!-- New Images Preview -->
                                            <template x-if="roomImages.length > 0">
                                                <div>
                                                    <p class="text-xs font-medium text-gray-700 mb-2">새 이미지</p>
                                                    <div class="grid grid-cols-3 gap-2">
                                                        <template x-for="(img, index) in roomImages" :key="index">
                                                            <div class="relative group">
                                                                <img :src="img.preview" class="w-full h-20 object-cover rounded-lg">
                                                                <button type="button" 
                                                                    @click="removeRoomImage(index)"
                                                                    class="absolute top-1 right-1 bg-red-500 text-white p-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
                                                                    <i class="ri-close-line text-xs"></i>
                                                                </button>
                                                            </div>
                                                        </template>
                                                    </div>
                                                </div>
                                            </template>
                                        </div>
"""

lines.insert(insert_index, new_content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Room image upload UI added successfully!")
