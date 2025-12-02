
import os

file_path = r'c:\workspace\Eroom-Studio\app\templates\public\branch_detail.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Define the target block to replace
target_start = """<!-- Hero Slider -->
<div class="relative h-[480px] overflow-hidden">
    <div class="slider-container flex w-full h-full overflow-x-auto">"""

target_end = """    <div class="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex space-x-2">
        <button class="w-2 h-2 rounded-full bg-white opacity-50"></button>
        <button class="w-2 h-2 rounded-full bg-white"></button>
        <button class="w-2 h-2 rounded-full bg-white opacity-50"></button>
    </div>
</div>"""

# Find start and end indices
start_idx = content.find(target_start)
if start_idx == -1:
    print("Start block not found")
    exit(1)

end_idx = content.find(target_end, start_idx)
if end_idx == -1:
    print("End block not found")
    exit(1)

# Include the end block in the replacement
end_idx += len(target_end)

# New content
new_block = """<!-- Hero Slider -->
<div class="relative h-[480px] overflow-hidden" x-data="{
    currentSlide: 0,
    images: [{% if branch.images %}{% for img in branch.images.all() %}{'id': {{ img.id }}, 'url': '{{ img.image_url }}'}{% if not loop.last %},{% endif %}{% endfor %}{% endif %}],
    init() {
        if (this.images.length === 0 && '{{ branch.image_url }}') {
            this.images.push({ id: 0, url: '{{ branch.image_url }}' });
        }
        // Fallback images if no images at all
        if (this.images.length === 0) {
            this.images = [
                { id: -1, url: 'https://readdy.ai/api/search-image?query=professional%20music%20practice%20room%20with%20high-end%20equipment%2C%20acoustic%20panels%2C%20modern%20lighting%2C%20clean%20and%20minimalist%20design%2C%20warm%20atmosphere%2C%20perfect%20for%20musicians&width=1920&height=480&seq=8&orientation=landscape' },
                { id: -2, url: 'https://readdy.ai/api/search-image?query=recording%20studio%20control%20room%20with%20mixing%20console%2C%20monitors%2C%20acoustic%20treatment%2C%20modern%20design%2C%20professional%20equipment&width=1920&height=480&seq=9&orientation=landscape' },
                { id: -3, url: 'https://readdy.ai/api/search-image?query=vocal%20recording%20booth%20with%20high-end%20microphone%2C%20acoustic%20panels%2C%20modern%20lighting%2C%20professional%20setup&width=1920&height=480&seq=10&orientation=landscape' }
            ];
        }
        
        // Auto slide
        setInterval(() => {
            this.currentSlide = (this.currentSlide + 1) % this.images.length;
        }, 5000);
    }
}">
    <div class="slider-container flex w-full h-full overflow-hidden relative">
        <template x-for="(img, index) in images" :key="img.id">
            <div class="slider-item w-full h-full flex-shrink-0 absolute top-0 left-0 transition-opacity duration-1000 ease-in-out"
                :class="currentSlide === index ? 'opacity-100 z-10' : 'opacity-0 z-0'"
                :style="`background-image: url('${img.url}'); background-size: cover; background-position: center;`">
                <!-- Dark overlay for better text visibility if needed -->
                <div class="absolute inset-0 bg-black/20"></div>
            </div>
        </template>
    </div>
    
    <!-- Navigation Dots -->
    <div class="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex space-x-2 z-20">
        <template x-for="(img, index) in images" :key="index">
            <button @click="currentSlide = index"
                class="w-2 h-2 rounded-full transition-all duration-300"
                :class="currentSlide === index ? 'bg-white w-6' : 'bg-white/50 hover:bg-white/80'">
            </button>
        </template>
    </div>
    
    <!-- Navigation Arrows -->
    <button @click="currentSlide = (currentSlide - 1 + images.length) % images.length"
        class="absolute left-4 top-1/2 transform -translate-y-1/2 z-20 w-10 h-10 rounded-full bg-black/30 hover:bg-black/50 text-white flex items-center justify-center backdrop-blur-sm transition-all hover:scale-110">
        <i class="ri-arrow-left-s-line text-2xl"></i>
    </button>
    <button @click="currentSlide = (currentSlide + 1) % images.length"
        class="absolute right-4 top-1/2 transform -translate-y-1/2 z-20 w-10 h-10 rounded-full bg-black/30 hover:bg-black/50 text-white flex items-center justify-center backdrop-blur-sm transition-all hover:scale-110">
        <i class="ri-arrow-right-s-line text-2xl"></i>
    </button>
</div>"""

# Replace content
new_content = content[:start_idx] + new_block + content[end_idx:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Successfully updated branch_detail.html")
