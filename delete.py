import os
import pyexiv2


# modify this to change the required star
# count for images you want to delete
remove_stars = 1


def get_rating(filename):
    with pyexiv2.Image(filename) as image:
        return int(image.read_xmp()["Xmp.xmp.Rating"])

image_path = ""

if "trash" not in os.listdir("."):
    os.system("mkdir trash")

image_paths = [
    x for x in os.listdir(".")
    if x.lower().endswith(".arw")
]

image_paths.reverse()

for i, image_path in enumerate(image_paths):
    if get_rating(image_path) == remove_stars:
        os.system("mv " + image_path + " trash")

    print("Processing images: " + str(i + 1) + "/" + str(len(image_paths)))
