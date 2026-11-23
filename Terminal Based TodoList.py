"""
Terminal-based TodoList

What to type in terminal:
    python "Terminal Based TodoList.py" add Buy milk
    python "Terminal Based TodoList.py" list
    python "Terminal Based TodoList.py" done 1
    python "Terminal Based TodoList.py" undone 1
    python "Terminal Based TodoList.py" delete 1

Format of todo.txt:
    NEXT_ID=4          <- next ID to hand out (so IDs are never reused)
    1|0|Buy milk       <- id|status(0=pending, 1=done)|activity

Rules this program follows:
    - The list is saved when the program ends.
    - Every task has a unique ID that is never reused, even after a restart or after deleting the highest-numbered task.
    - Tampering with todo.txt from outside is detected by format and reported with a [WARNING]. Malformed lines are ignored but preserved (written back unchanged when saving).

Exit codes: 0 = success, 1 = user error, 2 = file problem
"""

import os
import sys

FILE = "todo.txt"


class TodoList:
    """
    Holds all tasks in memory and handles loading from / saving to the file.

        filename:  Path of the storage file.
        tasks:     List of valid tasks, each task is [id, status, text].
        bad_lines: Malformed lines found in the file (kept so they are not lost).
        next_id:   The ID that the next added task will receive.
    """

    def __init__(self, filename):
        """Set up an empty list, then immediately load the file."""
        self.filename = filename
        self.tasks = []
        self.bad_lines = []
        self.next_id = 1
        self.load()

    def load(self):
        """
        Read the storage file into memory and check it for tampering.

        - Missing file: Start with an empty list (not an error).
        - Unreadable file: Print an error and exit with code 2.
        - Each line must be either NEXT_ID=<number> or <id>|<0 or 1>|<text>. Any other line or a duplicate ID is reported, ignored, and kept in bad_lines so it's written back on save.
        - If NEXT_ID is missing or not bigger than the highest ID, it's repaired and reported.
        """
        if not os.path.exists(self.filename):
            return

        try:
            with open(self.filename, encoding="utf-8") as f:
                lines = f.read().splitlines()
        except (OSError, UnicodeDecodeError):
            print("Error: can't read file")
            sys.exit(2)

        saved_next_id = None
        used_ids = []

        for number, line in enumerate(lines, 1):
            if line.strip() == "":
                continue

            if line.startswith("NEXT_ID=") and line[8:].isdigit() and saved_next_id is None:
                saved_next_id = int(line[8:])
                continue

            parts = line.split("|", 2)
            valid = (
                len(parts) == 3
                and parts[0].isdigit()
                and parts[1] in ("0", "1")
                and parts[2].strip() != ""
                and int(parts[0]) not in used_ids
            )
            if valid:
                self.tasks.append([int(parts[0]), parts[1], parts[2]])
                used_ids.append(int(parts[0]))
            else:
                print(f"[WARNING] Line {number} is malformed, ignored: {line}")
                self.bad_lines.append(line)

        biggest = max(used_ids, default=0)
        if saved_next_id is None or saved_next_id <= biggest:
            if self.tasks or self.bad_lines:
                print("[WARNING] NEXT_ID missing or inconsistent, fixed")
            self.next_id = biggest + 1
        else:
            self.next_id = saved_next_id

    def save(self):
        """
        Write everything back to the file.
        Order: The NEXT_ID line, then all valid tasks, then the malformed lines exactly as they were found (preserved). If writing fails, print an error and exit with code 2.
        """
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                f.write(f"NEXT_ID={self.next_id}\n")
                for t in self.tasks:
                    f.write(f"{t[0]}|{t[1]}|{t[2]}\n")
                for line in self.bad_lines:
                    f.write(line + "\n")
        except OSError:
            print("Error: can't write file")
            sys.exit(2)

    def find(self, id_text):
        """
        Return the task with the given ID. Exits with code 1 if the ID is not a number or does not exist.
        """
        if not id_text.isdigit():
            print("Error: ID must be a number")
            sys.exit(1)
        for t in self.tasks:
            if t[0] == int(id_text):
                return t
        print(f"Error: ID {id_text} not found")
        sys.exit(1)

    def add(self, text):
        """
        Add a new pending task using the next free ID. next_id only ever goes up, so an ID is never reused. Exits with code 1 if the text is empty.
        """
        if text.strip() == "":
            print("Error: text must not be empty")
            sys.exit(1)
        self.tasks.append([self.next_id, "0", text.strip()])
        print(f"Added #{self.next_id}: {text.strip()}")
        self.next_id += 1

    def show(self):
        """Print all tasks, with [x] for done and [ ] for pending."""
        if len(self.tasks) == 0:
            print("(empty)")
        for t in self.tasks:
            mark = "x" if t[1] == "1" else " "
            print(f"[{mark}] #{t[0]} {t[2]}")

    def set_status(self, id_text, status):
        """Mark a task as done ("1") or pending ("0")."""
        t = self.find(id_text)
        t[1] = status
        print(f"OK: #{t[0]} updated")

    def delete(self, id_text):
        """
        Remove a task. Other tasks keep their IDs (no renumbering) and next_id is untouched, so the freed ID is never given to a new task.
        """
        t = self.find(id_text)
        self.tasks.remove(t)
        print(f"OK: #{t[0]} deleted")


def main():
    """
    Read the command typed in the terminal and run it. Only commands that change the list (add, done, undone, delete) save the
    file at the end; list does not.
    """
    args = sys.argv[1:]
    if len(args) == 0:
        print("Usage: add <text> | list | done <id> | undone <id> | delete <id>")
        sys.exit(1)

    todo = TodoList(FILE)
    cmd = args[0]

    if cmd == "add":
        todo.add(" ".join(args[1:]))
    elif cmd == "list":
        todo.show()
        return
    elif cmd == "done" and len(args) == 2:
        todo.set_status(args[1], "1")
    elif cmd == "undone" and len(args) == 2:
        todo.set_status(args[1], "0")
    elif cmd == "delete" and len(args) == 2:
        todo.delete(args[1])
    else:
        print("Error: unknown command or missing argument")
        sys.exit(1)

    todo.save()


main()