import os
import sys
import winreg as reg
from tkinter import messagebox
import tkinter as tk


def show_message(title, message):
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    messagebox.showinfo(title, message)
    root.destroy()


def add_to_startup(file_path=None):
    if file_path is None:
        file_path = os.path.abspath(sys.argv[0])  # Get the path of the current script

    # Define the registry key and value
    key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    value_name = "Meetn Bonus App"  # Name for your app in the registry

    try:
        open_key = reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_SET_VALUE)
        reg.SetValueEx(open_key, value_name, 0, reg.REG_SZ, file_path + ' --auto-run')
        reg.CloseKey(open_key)
        # show_message("Success", f"Successfully added {file_path} to startup.")
    except WindowsError as e:
        show_message("Error", f"Error adding to startup: {e}")


def remove_from_startup():
    # Define the registry key and value name used for adding the app to startup
    key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    value_name = "Meetn Bonus App"  # The same name used to add to startup

    try:
        open_key = reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_SET_VALUE)
        reg.DeleteValue(open_key, value_name)
        reg.CloseKey(open_key)
        # show_message("Success", f"Successfully removed {value_name} from startup.")
    except FileNotFoundError:
        show_message("Info", f"{value_name} not found in startup.")
    except WindowsError as e:
        show_message("Error", f"Error removing from startup: {e}")


import winreg


def check_startup_registry(app_name):
    paths = [
        r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run',
        r'SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce',
    ]

    try:
        for path in paths:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_READ) as key:
                num_values = winreg.QueryInfoKey(key)[1]
                for i in range(num_values):
                    value_name, value_data, _ = winreg.EnumValue(key, i)
                    if app_name.lower() in value_name.lower() or app_name.lower() in value_data.lower():
                        return True

    except WindowsError:
        pass

    return False



if __name__ =='__main__':
    app_name_to_check = "Meetn Bonus App"
    if check_startup_registry(app_name_to_check):
        print(f"{app_name_to_check} is set to start on boot.")
    else:
        print(f"{app_name_to_check} is not set to start on boot.")