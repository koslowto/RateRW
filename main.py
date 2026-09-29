import os
import rawpy
import pyexiv2
import tkinter as tk
from PIL import Image, ImageTk
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from itertools import islice

IMAGE_FORMAT = "arw"
CACHE_RANGE = 50
PREVIEW_SIZE = 2000
RATINGS = ["☆☆☆☆☆", "★☆☆☆☆", "★★☆☆☆", "★★★☆☆", "★★★★☆", "★★★★★"]

image_path = ""
image_paths = []

cache_executor = ThreadPoolExecutor(max_workers=1)
preload_executor = ThreadPoolExecutor(max_workers=12)

cache = []
def load_preview (path):
    global cache

    for item in cache:
            if item["path"] == path:
                return item["image"]

    with rawpy.imread(path) as raw:
        rgb = raw.postprocess(
            use_camera_wb=True,
            half_size=True
        )

    image = Image.fromarray(rgb)
    image.thumbnail((PREVIEW_SIZE, PREVIEW_SIZE), Image.Resampling.LANCZOS)

    return image 

def preload_cache (paths):
    global cache

    futures = [preload_executor.submit(load_preview, path) for path in paths]

    results = [
        {"path": path, "image": future.result()}
        for path, future in zip(paths, futures)
    ]

    cache = results

    print("cached album")
    for i, c in enumerate(cache):
        print(str(i+1) + ": " + c["path"])

def cache_album(path, paths):
    global cache

    idx = paths.index(path)

    print(paths)
    print(idx)

    if idx < CACHE_RANGE:
        cache = cache[1:] + [{
            "path": paths[-1],
            "image": load_preview(paths[-1])
        }]

    elif idx > CACHE_RANGE:
        cache = [{
            "path": paths[0],
            "image": load_preview(paths[0])
        }] + cache[:-1]

    else:
        cache = [
            {"path": path, "image": load_preview(path)}
            for path in paths
        ]

    print("cached album")
    for i, c in enumerate(cache):
        print(str(i+1) + ": " + c["path"])


def set_rating (filename, rating):
    with pyexiv2.Image(filename) as image:
        image.modify_xmp({
            "Xmp.xmp.Rating": str(rating)
        })

def get_rating (filename):
    with pyexiv2.Image(filename) as image:
        return int(image.read_xmp()["Xmp.xmp.Rating"])


def display_image ():
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
        
    root.title(image_path + "  –  " + RATINGS[get_rating(image_path)])

def resize_image (event):
    display_image()

def on_key(event):
    global image_path
    global image
    global cache

    key = event.keysym

    if key in "012345":
        set_rating(image_path, key)
        root.title(image_path + "  –  " + RATINGS[int(key)])
        return

    if key in ("Left", "Up"):
        old_image_path = image_path

        image_paths.rotate(1)
        image_path = image_paths[CACHE_RANGE % len(image_paths)]

    elif key in ("Right", "Down"):
        old_image_path = image_path

        image_paths.rotate(-1)
        image_path = image_paths[CACHE_RANGE % len(image_paths)]

    else:
        return

    paths = list(islice(image_paths, 0, 2 * CACHE_RANGE + 1))
    cache_executor.submit( cache_album, old_image_path, paths)

    image = load_preview(image_path)
    display_image()




image_paths = deque(sorted([
    x for x in os.listdir(".")
    if x.lower().endswith("." + IMAGE_FORMAT)
]))

CACHE_RANGE = min(CACHE_RANGE, int(len(image_paths) / 2))

image_paths.rotate(CACHE_RANGE)
image_path = image_paths[CACHE_RANGE % len(image_paths)]


paths = list(islice(
    image_paths,
    0,
    2 * CACHE_RANGE + 1
))

cache_executor.submit(preload_cache, paths)
image = load_preview(image_path)

root = tk.Tk()
root.title(image_path + " – " + RATINGS[get_rating(image_path)])
root.geometry("1920x1080")

label = tk.Label(root)
label.pack(fill="both", expand=True)
label.bind("<Configure>", resize_image)
root.bind("<Key>", on_key)

label.configure(background='black')
root.configure(background='black')
root.mainloop()
