# AI Health Chatbot

An AI-powered multilingual health assistant that can:

- Answer health questions in **English, Telugu, Hindi, and Tamil**
- Accept **voice input** (speech-to-text)
- Provide **AI voice output** (text-to-speech)
- Accept **PDF/Image uploads** to scan medicine or reports
- Simplify medical explanations
- Check symptoms and provide risk levels

---

## Features

1. **Text Input:** Ask questions directly.  
2. **Voice Input:** Click the microphone 🎤 and speak your question.  
3. **Multilingual Support:** Translates your question and AI response automatically.  
4. **File Upload:** Upload PDF or image reports.  
5. **AI Voice Output:** Reads AI responses aloud.  
6. **Symptom Checker:** Detects possible diseases and risk levels.  

---

## Tech Stack

- **Backend:** Python, Flask, SQLAlchemy  
- **Frontend:** HTML, CSS, JavaScript  
- **AI:** RAG (Retrieval-Augmented Generation) engine  
- **OCR:** Tesseract OCR for images  
- **PDF Handling:** PyPDF2  
- **Translation:** deep-translator (GoogleTranslator)  
- **Database:** SQLite  

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/YourUsername/health_ai_chatbot.git
cd health_ai_chatbot

Create a virtual environment and activate:
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
Install dependencies:

pip install -r requirements.txt
Run the app:

python app.py
Open http://127.0.0.1:5000 in your browser.

Usage

Sign up / log in

Go to Chatbot → ask questions or speak

Upload medical reports for analysis

Check symptom reports and risk levels

