import numpy as np
from PIL import Image


def read_rle_bytes(ods_bytes):
    pixels = []
    line_builder = []

    i = 0
    while i < len(ods_bytes):
        if ods_bytes[i]:
            incr = 1
            color = ods_bytes[i]
            length = 1
        else:
            check = ods_bytes[i + 1]
            if check == 0:
                incr = 2
                color = 0
                length = 0
                pixels.append(line_builder)
                line_builder = []
            elif check < 64:
                incr = 2
                color = 0
                length = check
            elif check < 128:
                incr = 3
                color = 0
                length = ((check - 64) << 8) + ods_bytes[i + 2]
            elif check < 192:
                incr = 3
                color = ods_bytes[i + 2]
                length = check - 128
            else:
                incr = 4
                color = ods_bytes[i + 3]
                length = ((check - 192) << 8) + ods_bytes[i + 2]
        line_builder.extend([color] * length)
        i += incr

    if line_builder:
        print(f"Probably an error; hanging pixels: {line_builder}")

    return pixels


def ycbcr2rgb(ar):
    xform = np.array([[1, 0, 1.402], [1, -0.34414, -0.71414], [1, 1.772, 0]])
    rgb = ar.astype(float)
    # Subtracting by 128 the R and G channels
    rgb[:, [1, 2]] -= 128
    # .dot is multiplication of the matrices and xform.T is a transpose of the array axes
    rgb = rgb.dot(xform.T)
    # Makes any pixel value greater than 255 just be 255 (Max for RGB colorspace)
    np.putmask(rgb, rgb > 255, 255)
    # Sets any pixel value less than 0 to 0 (Min for RGB colorspace)
    np.putmask(rgb, rgb < 0, 0)
    return np.uint8(rgb)


def px_rgb_a(ods, pds, swap):
    px = read_rle_bytes(ods.img_data)
    px = np.array([[255] * (ods.width - len(l)) + l for l in px], dtype=np.uint8)

    # Extract the YCbCrA palette data, swapping channels if requested.
    if swap:
        ycbcr = np.array([(entry.Y, entry.Cb, entry.Cr) for entry in pds.palette])
    else:
        ycbcr = np.array([(entry.Y, entry.Cr, entry.Cb) for entry in pds.palette])
    try:
        rgb = ycbcr2rgb(ycbcr)
    except AttributeError:
        print("Error: The image is not in YCbCr format.")
        exit(1)
    # Separate the Alpha channel from the YCbCr palette data
    a = [entry.Alpha for entry in pds.palette]
    a = np.array([[a[x] for x in l] for l in px], dtype=np.uint8)

    return px, rgb, a


def make_image(ods, pds, swap=False):
    px, rgb, a = px_rgb_a(ods, pds, swap)
    alpha = Image.fromarray(a, mode="L")
    img = Image.fromarray(px, mode="P")
    img.putalpha(alpha)
    img.putpalette(rgb)
    return img
