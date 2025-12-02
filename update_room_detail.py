import sys

file_path = r'c:\workspace\Eroom-Studio\app\templates\public\room_detail.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the image gallery section
old_text = """            <!-- Image gallery -->
            <div class="flex flex-col-reverse">
                <div class="w-full aspect-w-1 aspect-h-1">
                    <img src="https://via.placeholder.com/600x400" alt="{{ room.name }}"
                        class="w-full h-full object-center object-cover sm:rounded-lg">
                </div>
            </div>"""

new_text = """            <!-- Image gallery -->
            <div class="flex flex-col-reverse" x-data="{ currentImage: 0, images: {{ room.images | tojson if room.images else '[]' }} }">
                <!-- Main Image -->
                <div class="w-full aspect-w-1 aspect-h-1 relative">
                    <template x-if="images.length > 0">
                        <img :src="images[currentImage].url" :alt="'{{ room.name }} - Image ' + (currentImage + 1)"
                            class="w-full h-full object-center object-cover sm:rounded-lg">
                    </template>
                    <template x-if="images.length === 0">
                        <div class="w-full h-full bg-gray-200 flex items-center justify-center sm:rounded-lg">
                            <div class="text-center">
                                <i class="ri-image-line text-6xl text-gray-400 mb-2"></i>
                                <p class="text-gray-500">이미지가 없습니다</p>
                            </div>
                        </div>
                    </template>
                    
                    <!-- Navigation Arrows -->
                    <template x-if="images.length > 1">
                        <div>
                            <button @click="currentImage = (currentImage - 1 + images.length) % images.length"
                                class="absolute left-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white rounded-full p-2 shadow-lg transition-all">
                                <i class="ri-arrow-left-s-line text-2xl text-gray-800"></i>
                            </button>
                            <button @click="currentImage = (currentImage + 1) % images.length"
                                class="absolute right-2 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white rounded-full p-2 shadow-lg transition-all">
                                <i class="ri-arrow-right-s-line text-2xl text-gray-800"></i>
                            </button>
                        </div>
                    </template>
                </div>
                
                <!-- Thumbnail Gallery -->
                <template x-if="images.length > 1">
                    <div class="mt-4 grid grid-cols-4 gap-2">
                        <template x-for="(img, index) in images" :key="img.id">
                            <button @click="currentImage = index"
                                :class="currentImage === index ? 'ring-2 ring-indigo-500' : 'ring-1 ring-gray-200'"
                                class="aspect-w-1 aspect-h-1 rounded-lg overflow-hidden hover:opacity-75 transition-all">
                                <img :src="img.url" :alt="'{{ room.name }} thumbnail ' + (index + 1)"
                                    class="w-full h-full object-center object-cover">
                            </button>
                        </template>
                    </div>
                </template>
            </div>"""

if old_text in content:
    content = content.replace(old_text, new_text)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ Room detail image gallery updated successfully!")
else:
    print("✗ Could not find the target text")
    print("\nSearching for similar text...")
    if "Image gallery" in content:
        print("Found 'Image gallery' comment")
