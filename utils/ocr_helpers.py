import cv2
import pytesseract

def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY, 11, 2)

def ocr_image(image_path):
    image = cv2.imread(image_path)
    processed = preprocess_image(image)
    return pytesseract.image_to_string(processed, config="--psm 6")
