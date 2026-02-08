🚀 IntelliPrep – Smart AI Quiz & Interview Prep Platform

IntelliPrep is a Django-based AI-powered learning and assessment platform that helps students identify knowledge gaps through adaptive quizzes and AI-driven questioning. The system uses Gemini API to generate intelligent, nested follow-up questions based on user responses and uploaded documents.

It also includes peer learning features like chatting with placed students and document-based AI questioning.

🧠 Core Idea

Instead of static quizzes, IntelliPrep creates a dynamic AI quiz experience:

Understands user answers

Detects weak areas

Asks nested follow-up questions

Generates contextual questions using AI

Learns from uploaded documents

✨ Features
🤖 AI Adaptive Quiz

AI-generated quiz questions using Gemini API

Nested follow-up questions based on user answers

Knowledge gap detection approach

Context-aware questioning flow

📄 Document-Based AI Questions

Upload your documents

AI reads and analyzes content

Generates questions based on uploaded material

Useful for resume prep, notes, or study PDFs

💬 Student Placement Chat

Chat feature to interact with placed students

Peer learning and guidance

Experience sharing support

🧩 Smart Interview Mode

AI asks interview-style questions

Follow-up questions based on responses

Useful for interview preparation

🛠 Tech Stack

Backend: Django

Language: Python

AI Integration: Google Gemini API

Database: SQLite (default, can be changed)

Frontend: Django Templates (HTML/CSS/JS)

Document Processing: AI-based content questioning

⚙️ Setup Instructions
1️⃣ Clone the Repository
git clone https://github.com/vaishnavi21643/Intelliprep.git
cd Intelliprep

2️⃣ Create Virtual Environment
python -m venv env


Activate it:

Windows

env\Scripts\activate


Mac/Linux

source env/bin/activate

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Add API Keys

Create a .env file in the project root and add:

GEMINI_API_KEY=your_api_key_here


👉 Get Gemini API key from Google AI Studio.

Make sure your Django settings load environment variables.

5️⃣ Run Migrations
python manage.py migrate

6️⃣ Start Server
python manage.py runserver


Open browser:

http://127.0.0.1:8000/
