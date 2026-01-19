import pytesseract
from PIL import Image
import re
from PyPDF2 import PdfReader
from reports_db import init_db, add_report, get_all_reports
from datetime import datetime
from deep_translator import GoogleTranslator


init_db()

#pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
import shutil
pytesseract.pytesseract.tesseract_cmd = shutil.which("tesseract")

from flask import Flask, render_template, request, jsonify, redirect, session
from flask_sqlalchemy import SQLAlchemy
from rag_engine import get_disease_with_explanation, load_rag
import nltk
from nltk.tokenize import sent_tokenize

nltk.download('punkt')

# ---------------- APP CONFIG ----------------
app = Flask(__name__)
import os
app.secret_key = os.getenv("FLASK_SECRET_KEY", "healthsecret")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ---------------- DATABASE ----------------
db = SQLAlchemy(app)

# ---------------- LOAD RAG ----------------
rag_db = load_rag()  # FAISS / RAG database

# ---------------- UTILITIES ----------------
def ai_simplify(text, num_sentences=2):
    """Simplify long text to first few sentences"""
    text = text.replace("\n", " ").strip()
    sentences = sent_tokenize(text)
    return ". ".join(sentences[:num_sentences]).strip()

# ---------------- RISK LEVEL ----------------
SYMPTOM_WEIGHTS = {
    "fever": 3,
    "headache": 2,
    "cough": 2,
    "fatigue": 1
}

def calculate_risk_level(symptoms):
    score = sum(SYMPTOM_WEIGHTS.get(s.lower(), 0) for s in symptoms)
    if score <= 2:
        return "Low"
    elif score <= 5:
        return "Medium"
    else:
        return "High"

# ---------------- USER MODEL ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))

with app.app_context():
    db.create_all()

# ---------------- ROUTES ----------------
@app.route('/')
def home():
    if 'user' in session:
        return render_template('index.html', name=session['user'])
    return redirect('/login')

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        user = User(
            name=request.form['name'],
            email=request.form['email'],
            password=request.form['password']
        )
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email'], password=request.form['password']).first()
        if user:
            session['user'] = user.name
            return redirect('/')
        return "Invalid Login"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------------- CHATBOT ----------------
@app.route('/chatbot')
def chatbot():
    if 'user' not in session:
        return redirect('/login')
    return render_template('chatbot.html')



@app.route('/get_response', methods=['POST'])
def get_response():
    data = request.get_json()
    user_msg = data.get("message", "").strip()
    lang = data.get("lang", "en")

    if not user_msg:
        return jsonify({"answer": "Please ask a question."})

    try:
        docs = rag_db.similarity_search(user_msg, k=2)
        if not docs:
            reply = "Sorry, I don't have medical info for this."
        else:
            pdf_text = " ".join([d.page_content for d in docs])
            reply = ai_simplify(pdf_text)

    except Exception as e:
        reply = "System is busy. Please try again."

    return jsonify({"answer": reply})

@app.route("/translate", methods=["POST"])
def translate_text():
    data = request.get_json()
    text = data.get("text","")
    target_lang = data.get("target_lang","en")

    try:
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
    except Exception:
        translated = text

    return jsonify({"text": translated})
@app.route("/upload_media", methods=["POST"])
def upload_media():
    if "file" not in request.files:
        return jsonify({"answer":"No file received"})

    file = request.files["file"]
    return jsonify({"answer":"File received: "+file.filename})


# ---------------- SYMPTOM CHECKER ----------------
@app.route('/symptom_checker')
def symptom_checker_page():
    if 'user' not in session:
        return redirect('/login')
    return render_template('symptom_checker.html')

@app.route('/check_symptoms', methods=['POST'])
def check_symptoms():
    data = request.get_json()
    symptoms = data.get("symptoms", [])

    if not symptoms:
        return jsonify({
            "diseases": {},
            "risk_level": "None"
        })

    # Get simplified disease explanations from RAG engine
    diseases_with_explanation = get_disease_with_explanation(symptoms, rag_db=rag_db)
    simplified_diseases = {}
    for disease, text in diseases_with_explanation.items():
        simplified_diseases[disease] = ai_simplify(text, num_sentences=2)

    # Calculate risk level
    risk_level = calculate_risk_level(symptoms)

    # ✅ Save symptom report
    today = datetime.now().strftime("%d-%m-%Y")
    add_report(today, "Symptom Check", ", ".join(simplified_diseases.keys()))

    return jsonify({
        "diseases": simplified_diseases,
        "risk_level": risk_level
    })

# ---------------- MEDICAL SCANNER ----------------
@app.route('/medical_scanner')
def medical_scanner():
    if 'user' not in session:
        return redirect('/login')
    return render_template('medical_scanner.html')

@app.route('/scan_medicine', methods=['POST'])
def scan_medicine():
    file = request.files['report']
    text = ""

    # PDF Scan
    if file.filename.lower().endswith(".pdf"):
        reader = PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""
    # Image Scan
    else:
        img = Image.open(file)
        text = pytesseract.image_to_string(img)

    # Extract Medicine Name
    med = re.findall(r'\b[A-Z][a-zA-Z]{3,}\b', text)
    medicine = med[0] if med else "Not Detected"

    # Extract Expiry Date
    exp = re.findall(r'(?:EXP|Expiry|Exp)\s*[:\-]?\s*(\d{2}[\/\-]\d{4})', text, re.I)
    expiry = exp[0] if exp else "Not Found"

    # Medicine Purpose Database
    medicine_uses = {
        "Paracetamol": "Fever and pain relief",
        "Ibuprofen": "Pain and inflammation",
        "Amoxicillin": "Bacterial infection",
        "Cetirizine": "Allergy relief",
        "Azithromycin": "Bacterial infection"
    }

    # ✅ Correct purpose detection (case-insensitive, partial match)
    purpose = "General medicine – consult doctor"
    for med_name, use in medicine_uses.items():
        if med_name.lower() in medicine.lower():
            purpose = use
            break

    # ✅ Save Report
    today = datetime.now().strftime("%d-%m-%Y")
    result_text = f"{medicine} | Exp: {expiry} | Use: {purpose}"
    add_report(today, "Medicine Scan", result_text)

    return jsonify({
        "medicine": medicine,
        "expiry": expiry,
        "purpose": purpose
    })

# ---------------- REPORTS PAGE ----------------
@app.route("/reports")
def reports():
    if 'user' not in session:
        return redirect('/login')
    data = get_all_reports()
    return render_template("reports.html", reports=data)

# ---------------- RUN ----------------
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

