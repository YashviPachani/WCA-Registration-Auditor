import cv2
import easyocr

reader = easyocr.Reader(["en"], gpu=False)


import cv2


def preprocess(image_path):

    img = cv2.imread(image_path)

    if img is None:
        return None

    h, w = img.shape[:2]

    img = img[: int(h * 0.70), :]

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    return gray


def extract_text(image_path):

    img = preprocess(image_path)

    if img is None:
        return ""

    result = reader.readtext(img, detail=0)

    return " ".join(result)


import re


def extract_amount(text):

    if not isinstance(text, str):
        return None

    text = text.lower()

    text = text.replace("8oo", "800")
    text = text.replace("80o", "800")
    text = text.replace("6oo", "600")

    patterns = [
        r"800\.00",
        r"600\.00",
        r"\b800\b",
        r"\b600\b",
        r"r800",
        r"r600",
    ]

    for pattern in patterns:
        if re.search(pattern, text):
            if "800" in pattern:
                return 800

            return 600

    return None
