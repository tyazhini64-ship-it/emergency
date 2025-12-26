import tkinter as tk
from tkinter import messagebox
import platform
import sqlite3
import os

class PomodoroApp:
    def __init__(self, master):
        self.master = master
        master.title("Pomodoro Timer")
        master.geometry("600x700")
        master.configure(bg="#F5E1FF")

        # Timer settings
        self.pomodoro_duration = 25 * 60
        self.break_duration = 5 * 60
        self.remaining_time = self.pomodoro_duration
        self.is_running = False
        
        # Track blocked sites dynamically
        self.blocked_sites = [] 
        self.hosts_path = self.get_hosts_path()

        # Database connection
        self.conn = sqlite3.connect('tasks.db')
        self.create_tasks_table()

        # UI Elements
        self.website_label = tk.Label(master, text="Enter website to Block (e.g. facebook.com):",
                                      font=("Impact", 14), bg="#F5E1FF", fg="#6A5ACD")
        self.website_label.pack(pady=5)
        self.website_entry = tk.Entry(master, width=30, font=("Impact", 14), bg="#E6D1F7", fg="black")
        self.website_entry.pack(pady=5)

        # Timer display
        self.timer_label = tk.Label(master, text=self.format_time(self.remaining_time),
                                     font=("Impact", 120), bg="#F5E1FF", fg="#6A5ACD")
        self.timer_label.pack(pady=1)

        # Control buttons
        self.controls_frame = tk.Frame(master, bg="#F5E1FF")
        self.controls_frame.pack(pady=3)
        self.create_button(self.controls_frame, "Start Timer & Block", self.start_timer).pack(side=tk.LEFT, padx=5)
        self.create_button(self.controls_frame, "Reset Timer", self.reset_timer).pack(side=tk.LEFT, padx=5)

        # To-do list section
        self.todo_entry = self.create_entry(master, "To-Do List:")
        self.create_button(master, "Add Task", self.add_task).pack(pady=5)
        self.task_listbox = tk.Listbox(master, width=50, height=8, font=("Garamond", 14), bg="#E6D1F7", fg="#6A5ACD")
        self.task_listbox.pack(pady=5)
        self.create_button(master, "Complete Task", self.complete_task).pack(pady=5)
        self.load_tasks()

    def create_button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, font=("Impact", 14), bg="#D3C0E8", fg="black")

    def create_entry(self, parent, label_text):
        tk.Label(parent, text=label_text, font=("Impact", 14), bg="#F5E1FF", fg="#6A5ACD").pack()
        entry = tk.Entry(parent, width=50, font=("Impact", 14), bg="#E6D1F7", fg="black")
        entry.pack(pady=5)
        return entry

    def format_time(self, seconds):
        return f"{seconds // 60:02}:{seconds % 60:02}"

    def get_hosts_path(self):
        if platform.system() == "Windows":
            return r"C:\Windows\System32\drivers\etc\hosts"
        return "/etc/hosts"

    # --- Core Logic ---

    def start_timer(self):
        if not self.is_running:
            site_to_block = self.website_entry.get().strip()
            if site_to_block:
                if self.block_website(site_to_block):
                    self.is_running = True
                    self.update_timer()
            else:
                messagebox.showwarning("Warning", "Please enter a website URL first!")

    def update_timer(self):
        if self.is_running and self.remaining_time > 0:
            self.remaining_time -= 1
            self.timer_label.config(text=self.format_time(self.remaining_time))
            self.master.after(1000, self.update_timer)
        elif self.remaining_time == 0:
            self.is_running = False
            self.unblock_websites()
            messagebox.showinfo("Time's up!", "Session complete! Websites unblocked.")

    def reset_timer(self):
        self.is_running = False
        self.unblock_websites()
        self.remaining_time = self.pomodoro_duration
        self.timer_label.config(text=self.format_time(self.remaining_time), fg="#6A5ACD")

    def block_website(self, website):
        redirect = "127.0.0.1"
        try:
            with open(self.hosts_path, "r+") as file:
                content = file.read()
                if website not in content:
                    file.write(f"{redirect} {website}\n")
                    file.write(f"{redirect} www.{website}\n") # Block www version too
                if website not in self.blocked_sites:
                    self.blocked_sites.append(website)
            return True
        except PermissionError:
            messagebox.showerror("Permission Error", "Run as Administrator/Sudo to block websites!")
            return False

    def unblock_websites(self):
        if not self.blocked_sites:
            return
        try:
            with open(self.hosts_path, "r") as file:
                lines = file.readlines()
            with open(self.hosts_path, "w") as file:
                for line in lines:
                    # If the line doesn't contain any of our blocked sites, keep it
                    if not any(site in line for site in self.blocked_sites):
                        file.write(line)
            self.blocked_sites = []
        except Exception as e:
            print(f"Error unblocking: {e}")

    # --- Database & Tasks ---
    def create_tasks_table(self):
        with self.conn:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, task TEXT NOT NULL)''')

    def load_tasks(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT task FROM tasks")
        for row in cursor.fetchall():
            self.task_listbox.insert(tk.END, row[0])

    def add_task(self):
        task = self.todo_entry.get().strip()
        if task:
            self.task_listbox.insert(tk.END, task)
            with self.conn:
                self.conn.execute("INSERT INTO tasks (task) VALUES (?)", (task,))
            self.todo_entry.delete(0, tk.END)

    def complete_task(self):
        selection = self.task_listbox.curselection()
        if selection:
            task_text = self.task_listbox.get(selection)
            self.task_listbox.delete(selection)
            with self.conn:
                self.conn.execute("DELETE FROM tasks WHERE task=?", (task_text,))

if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroApp(root)
    root.mainloop()
