
import sys
import os

# Tell Python where to find our backend files
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from database import engine, SessionLocal, Base
from models import User
from auth import hash_password
from rag import ingest_document
from pathlib import Path


def create_users():
    """Create 4 demo users with different roles."""
    print("\n--- Creating demo users ---")

    # Create the database tables if they don't exist yet
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # List of users to create: (username, email, password, role)
    users = [
        ("alice_admin", "alice@technova.com", "admin123", "admin"),
        ("bob_hr",      "bob@technova.com",   "hr1234",   "hr"),
        ("carol_emp",   "carol@technova.com", "emp123",   "employee"),
        ("dave_intern", "dave@technova.com",  "int123",   "intern"),
    ]

    for username, email, password, role in users:
        # Check if user already exists (so we can run this script multiple times safely)
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"  Skipping {username} - already exists")
            continue

        # Create new user with hashed password
        new_user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role=role
        )
        db.add(new_user)
        print(f"  Created: {username} (role={role})")

    db.commit()
    db.close()
    print("  Users done!")


def ingest_all_documents():
    """Load all sample documents into the Chroma vector store."""
    print("\n--- Ingesting documents into vector store ---")
    print("  (First run downloads the AI model, takes 2-3 minutes)")

    # Path to the documents folder
    docs_root = Path(__file__).parent / "data" / "documents"

    if not docs_root.exists():
        print(f"  ERROR: Folder not found: {docs_root}")
        return

    total_chunks = 0
    total_docs = 0

    # Loop through each department folder (public, hr, engineering, finance)
    for dept_folder in sorted(docs_root.iterdir()):
        if not dept_folder.is_dir():
            continue

        department_name = dept_folder.name
        print(f"\n  Department: {department_name.upper()}")

        # Loop through each .txt file in this folder
        for doc_file in sorted(dept_folder.glob("*.txt")):
            try:
                # Ingest the document - this creates embeddings and stores in Chroma
                chunk_count = ingest_document(
                    file_path=str(doc_file),
                    department=department_name,
                    access_level="public" if department_name == "public" else "internal"
                )
                print(f"    OK: {doc_file.name} -> {chunk_count} chunks created")
                total_chunks += chunk_count
                total_docs += 1

            except Exception as e:
                print(f"    FAILED: {doc_file.name} -> Error: {e}")

    print(f"\n  Total: {total_docs} documents, {total_chunks} chunks stored")


def print_summary():
    """Print final instructions."""
    print("\n" + "="*50)
    print("SETUP COMPLETE!")
    print("="*50)
    print("\nDemo login accounts:")
    print("  alice_admin / admin123  (sees everything)")
    print("  bob_hr      / hr1234   (sees HR + public)")
    print("  carol_emp   / emp123   (sees engineering + public)")
    print("  dave_intern / int123   (sees public only)")
    print("\nNext steps:")
    print("  Terminal 1: cd backend")
    print("              uvicorn main:app --reload")
    print("")
    print("  Terminal 2: cd frontend")
    print("              streamlit run app.py")
    print("")
    print("  Then open: http://localhost:8501")
    print("="*50)


if __name__ == "__main__":
    create_users()
    ingest_all_documents()
    print_summary()