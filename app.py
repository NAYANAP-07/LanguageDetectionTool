from flask import Flask, render_template, request, jsonify
import os
from langdetect import detect
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import langid
import speech_recognition as sr
from pydub import AudioSegment

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Map ISO codes to full language names
LANGUAGE_MAP = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    # add more if needed
}

def get_full_language_name(code):
    return LANGUAGE_MAP.get(code, code)  # fallback to code if unknown

# Detect script for Indian languages
def detect_indian_script(text):
    for ch in text:
        if '\u0900' <= ch <= '\u097F':  # Devanagari
            return "hindi"  # Hindi / Marathi
        if '\u0A00' <= ch <= '\u0A7F':  # Gurmukhi
            return "punjabi"  # Punjabi
        if '\u0B80' <= ch <= '\u0BFF':  # Tamil
            return "tamil"
        if '\u0C00' <= ch <= '\u0C7F':  # Telugu
            return "telugu"
        if '\u0980' <= ch <= '\u09FF':  # Bengali
            return "bengali"
        if '\u0C80' <= ch <= '\u0CFF':  # Kannada
            return "kannada"
        if '\u0D00' <= ch <= '\u0D7F':  # Malayalam
            return "malyalam"
        if '\u0B00' <= ch <= '\u0B7F':  # Oriya
            return "oriya"
        if '\u0A80' <= ch <= '\u0AFF':  # Gujarati
            return "gujrati"
    return "english"  # default


# Preprocess image for better OCR
def preprocess_image(path):
    img = Image.open(path).convert('L')  # grayscale
    img = img.filter(ImageFilter.SHARPEN)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2)  # increase contrast
    return img

# --------------------
# Routes
# --------------------

# Detect language from text
@app.route('/detect_text', methods=['POST'])
def detect_text():
    text = request.json.get('text', '')
    if not text.strip():
        return jsonify({"error": "Empty text"}), 400
    lang_code = detect(text)
    full_name = get_full_language_name(lang_code)
    return jsonify({"language": full_name})

# Detect language from image
@app.route('/detect_image', methods=['POST'])
def detect_image():
    file = request.files['image']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    try:
        image = preprocess_image(file_path)
        detected_text = pytesseract.image_to_string(image, lang='eng+hin+tam+tel+ben+kan+mal+pan+mar+fra+spa+deu')


        if not detected_text.strip():
            return jsonify({"error": "No text detected"}), 400

        # First check Indian script
        lang_code = detect_indian_script(detected_text)

        # If not detected, fallback to langid
        if not lang_code:
            lang_code, confidence = langid.classify(detected_text)

        full_name = get_full_language_name(lang_code)
        return jsonify({"language": full_name})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Detect language from audio
@app.route('/detect_audio', methods=['POST'])
def detect_audio():
    file = request.files['audio']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    try:
        # Convert to wav if needed
        audio = AudioSegment.from_file(file_path)
        wav_path = file_path.rsplit('.',1)[0]+'.wav'
        audio.export(wav_path, format="wav")

        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data)
            lang_code = detect(text)
            full_name = get_full_language_name(lang_code)
            return jsonify({"language": full_name, "text": text})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Main page
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
