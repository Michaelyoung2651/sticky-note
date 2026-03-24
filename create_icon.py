from PIL import Image, ImageDraw

# 创建 256x256 的图标
size = 256
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# 便利贴主体 - 黄色正方形，带一点阴影效果
margin = 20
# 主黄色背景
draw.rectangle([margin, margin, size-margin, size-margin-20], fill='#FFF8C6', outline='#E0D080', width=3)

# 顶部深色条（像便利贴的胶条）
top_bar_height = 35
draw.rectangle([margin, margin, size-margin, margin+top_bar_height], fill='#F4E79E', outline='#E0D080', width=2)

# 画几条横线表示文字
line_color = '#C0B060'
line_start_x = margin + 15
line_end_x = size - margin - 15
line_y_start = margin + 50
line_spacing = 18
line_width = 2

for i in range(5):
    y = line_y_start + i * line_spacing
    draw.line([(line_start_x, y), (line_end_x, y)], fill=line_color, width=line_width)

# 右下角小三角装饰，增加立体感
corner_size = 25
corner_points = [
    (size - margin - corner_size, size - margin - 20 - corner_size),
    (size - margin, size - margin - 20),
    (size - margin - corner_size, size - margin - 20)
]
draw.polygon(corner_points, fill='#E8D880')

# 保存为多尺寸 ICO
img.save('sticky.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])

print('图标已生成：sticky.ico')
