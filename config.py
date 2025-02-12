import tkinter as tk
from tkinter import messagebox
import subprocess

def save_to_file(data):
    with open("settings.py", "w") as file:
        for key, value in data.items():
            if isinstance(value, str):
                file.write(f"{key} = \"{value}\"\n")
            else:
                file.write(f"{key} = {value}\n")

def submit():
    # Collect input data
    data = {}
    data["set"] = True
    data["api"] = entry_fields[0].get()
    data["name"] = entry_fields[1].get()
    data["speak"] = checkbox_vars[0].get()
    data["voice"] = checkbox_vars[1].get()
    data["custom_personality"] = checkbox_vars[2].get()
    data["check_in"] = checkbox_vars[3].get()
    data["small_gui"] = checkbox_vars[4].get()  # New value for Small GUI checkbox

    if checkbox_vars[2].get():
        data["personality_text"] = custom_personality_entry.get()
    else:
        data["personality_text"] = ("You are very sad, straight to the point, and hating life. "
                                    "You love to make conversation because it keeps your mind off your own sad life. "
                                    "Always answer short, and snappy, like you're mad. "
                                    "You are very smart, so you always answer properly and accordingly"
                                    "Your mood can be changed if someone makes you happy somehow by cheering you up"
                                    "Always try to continue a conversation"
                                    )

    # Save data to file
    save_to_file(data)
    
    # Close the application
    root.destroy()

def clear():
    # Clear all input fields
    for entry in entry_fields:
        entry.delete(0, tk.END)
    for var in checkbox_vars:
        var.set(False)
    custom_personality_entry.delete(0, tk.END)
    custom_personality_entry.grid_remove()

def toggle_custom_personality():
    if checkbox_vars[2].get():
        custom_personality_entry.grid(row=len(labels) + len(checkbox_labels), column=1, padx=5, pady=5)
    else:
        custom_personality_entry.grid_remove()

# Initialize main window
root = tk.Tk()
root.title("AI Setup")
root.geometry("330x350")  # Increased height to accommodate the new checkbox
root.resizable(False, False)  # Lock width and height

# Create a frame for the input fields
input_frame = tk.Frame(root)
input_frame.pack(pady=10)

# List of labels for input fields
labels = ["Google API", "Your Name"]
entry_fields = []

# Create input fields
for i, label in enumerate(labels):
    tk.Label(input_frame, text=label).grid(row=i, column=0, padx=5, pady=5, sticky="w")
    entry = tk.Entry(input_frame, width=30)
    entry.grid(row=i, column=1, padx=5, pady=5)
    entry_fields.append(entry)

# Create checkboxes for custom options
checkbox_vars = [tk.BooleanVar() for _ in range(5)]  # Now 5 checkboxes
checkbox_labels = ["Speak Response", "Voice Mode", "Custom Personality", "Check-In", "Small GUI"]  # Added "Small GUI"

for i, label in enumerate(checkbox_labels):
    tk.Checkbutton(input_frame, text=label, variable=checkbox_vars[i], command=toggle_custom_personality if label == "Custom Personality" else None).grid(row=len(labels) + i, column=0, columnspan=2, padx=5, pady=5, sticky="w")

# Add a hidden entry for Custom Personality text
custom_personality_entry = tk.Entry(input_frame, width=30)
custom_personality_entry.grid(row=len(labels) + len(checkbox_labels), column=1, padx=5, pady=5)
custom_personality_entry.grid_remove()

# Create Submit and Clear buttons
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

tk.Button(button_frame, text="Submit", command=submit).grid(row=0, column=0, padx=10)
tk.Button(button_frame, text="Clear", command=clear).grid(row=0, column=1, padx=10)

# Run the main loop
subprocess.run(["python", "install.py"], check=True)
root.mainloop()
