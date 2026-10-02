"""
Contact Management System
=========================
A menu-driven application to add, search, update, display and delete contacts.
Contacts are stored persistently in a JSON file, so data survives between runs.

Run with:  python contact_manager.py
"""

import json
import os
import re
from datetime import datetime

DATA_FILE = "contacts.json"


# ----------------------------------------------------------------------
#  Storage layer  -  handles reading and writing the JSON file
# ----------------------------------------------------------------------
class ContactBook:
    def __init__(self, filename=DATA_FILE):
        self.filename = filename
        self.contacts = self.load()

    def load(self):
        """Read contacts from disk. Returns an empty list if no file exists."""
        if not os.path.exists(self.filename):
            return []
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            print("! Warning: contacts file is unreadable. Starting with an empty book.")
            return []

    def save(self):
        """Write the current contact list back to disk."""
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.contacts, f, indent=4)
            return True
        except OSError as e:
            print(f"! Could not save file: {e}")
            return False

    # ------------------------------------------------------------------
    #  Core operations
    # ------------------------------------------------------------------
    def add(self, name, phone, email=""):
        self.contacts.append({
            "name": name,
            "phone": phone,
            "email": email,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        self.save()

    def find_by_phone(self, phone):
        """Exact phone match - used to block duplicates."""
        for c in self.contacts:
            if c["phone"] == phone:
                return c
        return None

    def search(self, term):
        """Case-insensitive partial match on name or phone."""
        term = term.lower().strip()
        return [c for c in self.contacts
                if term in c["name"].lower() or term in c["phone"]]

    def update(self, index, name=None, phone=None, email=None):
        contact = self.contacts[index]
        if name:
            contact["name"] = name
        if phone:
            contact["phone"] = phone
        if email is not None and email != "":
            contact["email"] = email
        self.save()

    def delete(self, index):
        removed = self.contacts.pop(index)
        self.save()
        return removed

    def all_sorted(self):
        return sorted(self.contacts, key=lambda c: c["name"].lower())

    def __len__(self):
        return len(self.contacts)


# ----------------------------------------------------------------------
#  Validation helpers
# ----------------------------------------------------------------------
def valid_name(name):
    """Letters, spaces, dots and apostrophes only; at least 2 characters."""
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z .']{1,49}", name.strip()))


def valid_phone(phone):
    """Accepts 10-15 digits, optionally prefixed with +. Spaces/dashes ignored."""
    cleaned = re.sub(r"[\s\-()]", "", phone)
    return bool(re.fullmatch(r"\+?\d{10,15}", cleaned)), cleaned


def valid_email(email):
    """Empty is allowed (email is optional)."""
    if email.strip() == "":
        return True
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}", email.strip()))


def ask_name(prompt="Name: ", allow_blank=False):
    while True:
        value = input(prompt).strip()
        if allow_blank and value == "":
            return ""
        if valid_name(value):
            return value.title()
        print("  -> Invalid name. Use letters only (2-50 characters).")


def ask_phone(book, prompt="Phone: ", allow_blank=False, skip_duplicate_check=False):
    while True:
        value = input(prompt).strip()
        if allow_blank and value == "":
            return ""
        ok, cleaned = valid_phone(value)
        if not ok:
            print("  -> Invalid number. Enter 10-15 digits, e.g. 9876543210 or +919876543210.")
            continue
        if not skip_duplicate_check and book.find_by_phone(cleaned):
            print("  -> A contact with this number already exists.")
            continue
        return cleaned


def ask_email(prompt="Email (optional): "):
    while True:
        value = input(prompt).strip()
        if valid_email(value):
            return value
        print("  -> Invalid email format.")


# ----------------------------------------------------------------------
#  Display helpers
# ----------------------------------------------------------------------
def print_table(contacts, title="CONTACTS"):
    if not contacts:
        print("\n  No contacts to show.")
        return
    print(f"\n{title}")
    print("-" * 74)
    print(f"{'No.':<5}{'NAME':<24}{'PHONE':<18}{'EMAIL':<27}")
    print("-" * 74)
    for i, c in enumerate(contacts, start=1):
        email = c.get("email", "") or "-"
        print(f"{i:<5}{c['name'][:23]:<24}{c['phone']:<18}{email[:26]:<27}")
    print("-" * 74)
    print(f"Total: {len(contacts)} contact(s)")


def choose_from(results):
    """Let the user pick one contact out of a result list. Returns the dict or None."""
    print_table(results, "SEARCH RESULTS")
    while True:
        choice = input("\nEnter the No. to select (or 0 to cancel): ").strip()
        if choice == "0":
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(results):
            return results[int(choice) - 1]
        print("  -> Invalid selection.")


# ----------------------------------------------------------------------
#  Menu actions
# ----------------------------------------------------------------------
def add_contact(book):
    print("\n--- ADD CONTACT ---")
    name = ask_name()
    phone = ask_phone(book)
    email = ask_email()
    book.add(name, phone, email)
    print(f"\n[OK] '{name}' saved successfully.")


def search_contact(book):
    print("\n--- SEARCH CONTACT ---")
    if len(book) == 0:
        print("  Contact book is empty.")
        return
    term = input("Enter name or number to search: ").strip()
    if not term:
        print("  -> Search term cannot be empty.")
        return
    results = book.search(term)
    if results:
        print_table(results, f"RESULTS FOR '{term}'")
    else:
        print(f"\n  No contact found matching '{term}'.")


def update_contact(book):
    print("\n--- UPDATE CONTACT ---")
    if len(book) == 0:
        print("  Contact book is empty.")
        return
    term = input("Search the contact to update: ").strip()
    results = book.search(term)
    if not results:
        print(f"\n  No contact found matching '{term}'.")
        return

    target = results[0] if len(results) == 1 else choose_from(results)
    if target is None:
        print("  Cancelled.")
        return

    index = book.contacts.index(target)
    print(f"\nEditing: {target['name']} | {target['phone']} | {target.get('email') or '-'}")
    print("Press ENTER to keep the current value.\n")

    new_name = ask_name("New name: ", allow_blank=True)
    new_phone = ask_phone(book, "New phone: ", allow_blank=True)
    new_email = ask_email("New email: ")

    if not (new_name or new_phone or new_email):
        print("\n  Nothing changed.")
        return

    book.update(index, new_name, new_phone, new_email)
    print("\n[OK] Contact updated.")


def display_contacts(book):
    print_table(book.all_sorted(), "ALL CONTACTS (A-Z)")


def delete_contact(book):
    print("\n--- DELETE CONTACT ---")
    if len(book) == 0:
        print("  Contact book is empty.")
        return
    term = input("Search the contact to delete: ").strip()
    results = book.search(term)
    if not results:
        print(f"\n  No contact found matching '{term}'.")
        return

    target = results[0] if len(results) == 1 else choose_from(results)
    if target is None:
        print("  Cancelled.")
        return

    confirm = input(f"\nDelete '{target['name']}' ({target['phone']})? (y/n): ").strip().lower()
    if confirm == "y":
        book.delete(book.contacts.index(target))
        print(f"\n[OK] '{target['name']}' deleted.")
    else:
        print("  Cancelled.")


# ----------------------------------------------------------------------
#  Main program loop
# ----------------------------------------------------------------------
MENU = """
==================================================
        CONTACT MANAGEMENT SYSTEM
==================================================
  1. Add Contact
  2. Search Contact
  3. Update Contact
  4. Display All Contacts
  5. Delete Contact
  6. Exit
==================================================
"""


def main():
    book = ContactBook()
    print("\nWelcome! Loaded", len(book), "contact(s) from storage.")

    actions = {
        "1": add_contact,
        "2": search_contact,
        "3": update_contact,
        "4": display_contacts,
        "5": delete_contact,
    }

    while True:
        print(MENU)
        choice = input("Enter your choice (1-6): ").strip()

        if choice == "6":
            print("\nAll changes saved. Goodbye!\n")
            break
        elif choice in actions:
            actions[choice](book)
        else:
            print("\n  -> Invalid choice. Please enter a number from 1 to 6.")

        input("\nPress ENTER to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Data already saved. Goodbye!\n")