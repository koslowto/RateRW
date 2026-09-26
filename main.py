import os
import rawpy
import pyexiv2
import tkinter as tk
from PIL import Image, ImageTk
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

image_format = "arw"

image_path = ""
executor = ThreadPoolExecutor(max_workers=2)
ratings = ["☆☆☆☆☆", "★☆☆☆☆", "★★☆☆☆", "★★★☆☆", "★★★★☆", "★★★★★"]

def load_image(image_path):
    with rawpy.imread(image_path) as raw:
        rgb = raw.postprocess()

    return Image.fromarray(rgb)

@lru_cache(maxsize=100)
def load_preview(path, max_size=2000):
    with rawpy.imread(path) as raw:
        rgb = raw.postprocess(
            use_camera_wb=True,
            half_size=True
        )

    image = Image.fromarray(rgb)
    image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    return image

def cache_album():
    for image_path in image_paths[:75]:
        executor.submit(load_preview, image_path)

def set_rating(filename, rating):
    with pyexiv2.Image(filename) as image:
        image.modify_xmp({
            "Xmp.xmp.Rating": str(rating)
        })

def get_rating(filename):
    with pyexiv2.Image(filename) as image:
        return int(image.read_xmp()["Xmp.xmp.Rating"])


def display_image():
    width = label.winfo_width()
    height = label.winfo_height()
    
    scale = min(
        width / image.width,
        height / image.height
    )

    new_width = int(image.width * scale)
    new_height = int(image.height * scale)

    resized = image.resize(
        (new_width, new_height),
        Image.Resampling.LANCZOS
    )

    photo = ImageTk.PhotoImage(resized)
    label.config(image=photo)
    label.image = photo
        
    root.title(image_path + "  –  " + ratings[get_rating(image_path)])

def resize_image(event):
    display_image()

def on_key(event):
    global image_path
    global image

    key = event.keysym

    if key in "012345":
        set_rating(image_path, key)

        root.title(image_path + "  –  " + ratings[int(key)])
    else:
        idx = image_paths.index(image_path)

        if key in "LeftUp":
            image_path = image_paths[
                idx - 1 if idx > 0 
                else max(0, len(image_paths) - 1)
            ]
            next_path = image_paths[
                idx - 2 if idx > 1
                else max(0, len(image_paths) - 2 + idx)
            ] 

            executor.submit(load_preview, next_path)

        elif key in "RightDown":
            image_path = image_paths[
                (idx + 1) % len(image_paths)
            ] 
            next_path = image_paths[
                (idx + 2) % len(image_paths)
            ]

            executor.submit(load_preview, next_path)

        image = load_preview(image_path)
        display_image()



image_paths = [
    x for x in os.listdir(".")
    if x.lower().endswith("." + image_format)
]

image_paths.sort()
image_path = image_paths[0]

image = load_preview(image_path)

executor.submit(load_preview, image_paths[max(0, len(image_paths) - 1)])
executor.submit(cache_album)

root = tk.Tk()
root.title(image_path + " – " + ratings[get_rating(image_path)])
root.geometry("1920x1080")

label = tk.Label(root)
label.pack(fill="both", expand=True)
label.bind("<Configure>", resize_image)
root.bind("<Key>", on_key)

label.configure(background='black')
root.configure(background='black')
root.mainloop()
