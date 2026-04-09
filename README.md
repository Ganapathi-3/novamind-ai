 NovaMind AI - Secure Enterprise AI Assistant

A full-stack AI application that answers employee questions using company documents,
with Role-Based Access Control (RBAC) ensuring users only access authorized information.

## Features
- JWT Authentication with bcrypt password hashing
- 4-tier RBAC system (Admin, HR, Employee, Intern)
- RAG pipeline using LangChain and ChromaDB
- Semantic search with Sentence Transformers (all-MiniLM-L6-v2)
- Groq LLaMA 3 for context-grounded answers
- Professional frontend with HTML, Tailwind CSS, JavaScript
- Chat history stored in SQLite

## Tech Stack
- Backend: Python, FastAPI, SQLAlchemy
- AI/ML: LangChain, ChromaDB, Sentence Transformers, Groq API
- Frontend: HTML, Tailwind CSS, Vanilla JavaScript
- Database: SQLite
- Auth: JWT, bcrypt

## Setup

1. Clone the repository
   git clone https://github.com/YOUR_USERNAME/novamind-ai.git
   cd novamind-ai

2. Create virtual environment
   python -m venv venv
   venv\Scripts\activate

3. Install dependencies
   pip install -r requirements.txt

4. Create .env file
   GROQ_API_KEY=your_groq_api_key
   JWT_SECRET_KEY=your_secret_key

5. Seed demo data
   python seed_data.py

6. Run backend
   cd backend
   uvicorn main:app --reload

7. Open frontend
   Open frontend/index.html with Live Server

## Demo Accounts
| Username | Password | Role |
|----------|----------|------|
| alice_admin | admin123 | Admin |
| bob_hr | hr1234 | HR |
| carol_emp | emp123 | Employee |
| dave_intern | int123 | Intern |

## Project Structure
enterprise-ai/
  backend/        FastAPI backend
  frontend/       HTML/CSS/JS frontend
  data/documents/ Sample documents
  seed_data.py    Creates demo users and ingests documents

## Author
Ganapathi Gopal A
linkedin.com/in/ganapathigopal
github.com/ganapathi03"
