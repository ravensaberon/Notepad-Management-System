import json
import os
from typing import Any
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
USERS_FILE = os.path.join(BASE_DIR, "users.json")
NOTES_FILE = os.path.join(BASE_DIR, "notes.json")

def ensure_data_files():
    os.makedirs(BASE_DIR, exist_ok=True)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({"users": []}, f, indent=2)
    if not os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "w") as f:
            json.dump({"notes": []}, f, indent=2)

def read_json(path: str) -> Any:
    ensure_data_files()
    with open(path, "r") as f:
        return json.load(f)

def write_json(path: str, data: Any):
    ensure_data_files()
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)

# User helpers
def find_user_by_username(username: str):
    users = read_json(USERS_FILE)["users"]
    for u in users:
        if u.get("username") == username:
            return u
    return None

def find_user_by_email(email: str):
    users = read_json(USERS_FILE)["users"]
    for u in users:
        if u.get("email", "").lower() == email.lower():
            return u
    return None

def add_user(user_dict: dict):
    data = read_json(USERS_FILE)
    data["users"].append(user_dict)
    write_json(USERS_FILE, data)

def update_user(username: str, update_fields: dict):
    data = read_json(USERS_FILE)
    for i, u in enumerate(data["users"]):
        if u["username"] == username:
            data["users"][i].update(update_fields)
            write_json(USERS_FILE, data)
            return True
    return False

# Password helpers
def hash_password(plain: str) -> str:
    return generate_password_hash(plain)

def verify_password(hashed: str, plain: str) -> bool:
    return check_password_hash(hashed, plain)

# Notes helpers
def get_all_notes():
    return read_json(NOTES_FILE)["notes"]

def save_all_notes(notes_list):
    write_json(NOTES_FILE, {"notes": notes_list})

def new_note_id():
    notes = get_all_notes()
    if not notes:
        return 1
    return max(n["id"] for n in notes) + 1

def add_note(note):
    notes = get_all_notes()
    notes.append(note)
    save_all_notes(notes)

def find_note_by_id(note_id):
    notes = get_all_notes()
    for n in notes:
        if n["id"] == note_id:
            return n
    return None

def update_note(note_id, fields):
    notes = get_all_notes()
    for i, n in enumerate(notes):
        if n["id"] == note_id:
            notes[i].update(fields)
            save_all_notes(notes)
            return True
    return False

def delete_note_permanent(note_id):
    notes = get_all_notes()
    notes = [n for n in notes if n["id"] != note_id]
    save_all_notes(notes)
