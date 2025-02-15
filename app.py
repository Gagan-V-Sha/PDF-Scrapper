import os
from dotenv import load_dotenv

import google.generativeai as genai
import PyPDF2
from gtts import gTTS  # Google Text-to-Speech
import speech_recognition as sr  # Speech Recognition
import tempfile

# Load environment variables
load_dotenv()

# Configure the Gemini Pro model
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to load Gemini Pro model and get responses
model = genai.GenerativeModel("gemini-2.0-flash")
chat = model.start_chat(history=[])

def extract_text_from_pdf(file):
    """Extracts text from the provided PDF file using PyPDF2."""
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def get_gemini_response(question, context):
    """Gets a response from the Gemini model, including the provided context in the question."""
    full_message = context + "\n\n" + question
    response = chat.send_message(full_message, stream=True)
    return response

def text_to_speech(text):
    """Converts text to speech and returns the path to the audio file."""
    # Show "Generating Audio..." message
    st.info("Generating Audio...")
    
    # Convert text to speech
    tts = gTTS(text=text, lang='en')
    temp_file_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
    tts.save(temp_file_path)
    
    # Update the status to "Audio generated!"
    st.success("Audio generated!")
    
    return temp_file_path

def recognize_speech():
    """Captures voice input from the user and returns it as text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening... Please speak into the microphone.")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            st.success(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            st.error("Sorry, I could not understand the audio.")
        except sr.RequestError:
            st.error("Error with the Speech Recognition service.")

def extract_texts_from_folder(folder):
    """Extracts and concatenates text from all PDF files in the given folder."""
    combined_text = ""
    for filename in os.listdir(folder):
        if filename.endswith(".pdf"):
            with open(os.path.join(folder, filename), "rb") as file:
                combined_text += extract_text_from_pdf(file)
    return combined_text

def store_feedback(user_input, bot_response):
    """Stores user input and bot response to the backend (e.g., database)."""
    # Implement the logic to store the conversation data
    # in your backend system (e.g., a database or an API endpoint).
    pass

def main():
    print("\n==== SmartBot PDF Assistant (CLI) ====")
    print("Enter the full path to your PDF files, separated by commas:")
    pdf_paths = input("PDF file paths: ").split(',')
    pdf_paths = [p.strip() for p in pdf_paths if p.strip()]
    if not pdf_paths:
        print("No PDF files provided. Exiting.")
        return

    # Extract and combine text from all PDFs
    combined_text = ""
    for path in pdf_paths:
        if os.path.exists(path) and path.endswith(".pdf"):
            with open(path, "rb") as f:
                combined_text += extract_text_from_pdf(f)
        else:
            print(f"File not found or not a PDF: {path}")
    if not combined_text:
        print("No valid PDF content extracted. Exiting.")
        return

    print("PDFs loaded successfully! You can now ask questions about their content.")
    while True:
        print("\nChoose input method:")
        print("1. Type your question")
        print("2. Speak your question (microphone)")
        print("3. Exit")
        choice = input("Select (1/2/3): ").strip()
        if choice == '1':
            question = input("Your question: ").strip()
        elif choice == '2':
            print("Listening...")
            question = recognize_speech_cli()
            if not question:
                print("Could not recognize speech. Try again.")
                continue
            print(f"You said: {question}")
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Try again.")
            continue
        if not question:
            print("No question entered. Try again.")
            continue
        response = get_gemini_response(question, context=combined_text)
        response_text = ''.join([chunk.text for chunk in response])
        print(f"\nResponse: {response_text}\n")
        tts_choice = input("Would you like to hear the answer? (y/n): ").strip().lower()
        if tts_choice == 'y':
            audio_path = text_to_speech_cli(response_text)
            print(f"Audio saved to: {audio_path}")

# CLI-friendly TTS (no Streamlit)
def text_to_speech_cli(text):
    tts = gTTS(text=text, lang='en')
    temp_file_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
    tts.save(temp_file_path)
    try:
        # Try to play audio automatically (cross-platform)
        import platform
        import subprocess
        if platform.system() == "Windows":
            os.startfile(temp_file_path)
        elif platform.system() == "Darwin":
            subprocess.call(['open', temp_file_path])
        else:
            subprocess.call(['xdg-open', temp_file_path])
    except Exception:
        pass
    return temp_file_path

# CLI-friendly speech recognition (no Streamlit)
def recognize_speech_cli():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Please speak into the microphone...")
        audio = recognizer.listen(source)
        try:
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            print("Sorry, could not understand the audio.")
        except sr.RequestError:
            print("Error with the Speech Recognition service.")
    return None

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading

class SmartBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SmartBot PDF Assistant")
        self.pdf_paths = []
        self.combined_text = ""
        self.response_text = ""
        self.audio_path = None
        self.setup_gui()

    def setup_gui(self):
        # PDF selection
        self.select_btn = tk.Button(self.root, text="Select PDF(s)", command=self.select_pdfs)
        self.select_btn.pack(pady=5)
        self.pdf_label = tk.Label(self.root, text="No PDFs selected.")
        self.pdf_label.pack(pady=2)

        # Question input
        self.question_entry = tk.Entry(self.root, width=80)
        self.question_entry.pack(pady=5)
        self.ask_btn = tk.Button(self.root, text="Ask Question", command=self.ask_question)
        self.ask_btn.pack(pady=2)
        self.voice_btn = tk.Button(self.root, text="🎤 Speak Question", command=self.voice_question)
        self.voice_btn.pack(pady=2)

        # Response display
        self.response_box = scrolledtext.ScrolledText(self.root, height=10, width=80, state='disabled')
        self.response_box.pack(pady=5)
        self.tts_btn = tk.Button(self.root, text="🔊 Play Answer", command=self.play_answer, state='disabled')
        self.tts_btn.pack(pady=2)

    def select_pdfs(self):
        paths = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
        if paths:
            self.pdf_paths = list(paths)
            self.pdf_label.config(text=f"{len(self.pdf_paths)} PDF(s) selected.")
            self.combined_text = ""
            for path in self.pdf_paths:
                with open(path, "rb") as f:
                    self.combined_text += extract_text_from_pdf(f)
            messagebox.showinfo("PDFs Loaded", "PDFs loaded and processed successfully!")
        else:
            self.pdf_label.config(text="No PDFs selected.")

    def ask_question(self):
        question = self.question_entry.get().strip()
        if not self.combined_text:
            messagebox.showwarning("No PDFs", "Please select PDF(s) first.")
            return
        if not question:
            messagebox.showwarning("No Question", "Please enter a question.")
            return
        self.display_response("Thinking...")
        threading.Thread(target=self._get_answer, args=(question,)).start()

    def _get_answer(self, question):
        response = get_gemini_response(question, context=self.combined_text)
        self.response_text = ''.join([chunk.text for chunk in response])
        self.display_response(self.response_text)
        self.tts_btn.config(state='normal')

    def voice_question(self):
        if not self.combined_text:
            messagebox.showwarning("No PDFs", "Please select PDF(s) first.")
            return
        self.display_response("Listening...")
        threading.Thread(target=self._voice_ask).start()

    def _voice_ask(self):
        question = recognize_speech_cli()
        if question:
            self.question_entry.delete(0, tk.END)
            self.question_entry.insert(0, question)
            self._get_answer(question)
        else:
            self.display_response("Sorry, could not recognize your speech.")

    def display_response(self, text):
        self.response_box.config(state='normal')
        self.response_box.delete(1.0, tk.END)
        self.response_box.insert(tk.END, text)
        self.response_box.config(state='disabled')

    def play_answer(self):
        if not self.response_text:
            return
        threading.Thread(target=self._tts_play).start()

    def _tts_play(self):
        audio_path = text_to_speech_cli(self.response_text)
        self.audio_path = audio_path

if __name__ == "__main__":
    root = tk.Tk()
    app = SmartBotApp(root)
    root.mainloop()

