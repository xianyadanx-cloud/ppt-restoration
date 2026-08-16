from PIL import Image
img = Image.open("input/slide_02.png")
w, h = img.size
print("Corners:", [img.getpixel((0, 0)), img.getpixel((w-1, 0)), img.getpixel((0, h-1)), img.getpixel((w-1, h-1))])
