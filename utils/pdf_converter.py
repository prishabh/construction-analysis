from pdf2image import convert_from_path
import os

def convert_pdf_to_images(pdf_path, output_dir, dpi=300):
    images = convert_from_path(pdf_path, dpi=dpi)
    output_paths = []

    for i, image in enumerate(images):
        filename = os.path.join(output_dir, f"page_{i+1}.png")
        image.save(filename, "PNG")
        output_paths.append(filename)

    return output_paths
