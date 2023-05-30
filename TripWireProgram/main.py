import tkinter as tk
import threading
import time
import configparser
import json
import sys

import character
import clipboardListener

config = configparser.ConfigParser()
config.read('config.ini')


def loadCharacters():
    characterList = []
    try:
        with open("data.json") as file:
            users = json.load(file)
            for user in users:
                char = character.Character()
                char.loadUser(user["character_id"])
                characterList.append(char)
    except:
        print("User database empty!")
        pass    
    return characterList

CHARACTERS = loadCharacters()

def authCharacter():
    newchar = character.Character()
    newchar.loadUser()
    CHARACTERS.append(newchar)
    charlist.insert(tk.END, newchar.get_char_name())

#create a new (main) window
mainWindow = tk.Tk()
mainWindow.title("Tripwire-Connector")
mainWindow.geometry("400x300")

#add file menu bar
menubar = tk.Menu(mainWindow)
mainWindow_menu = tk.Menu(menubar,tearoff=0)
mainWindow_menu.add_command(label="Authorize Char", command=authCharacter) # , command=CHARACTERS.append(authCharacter())
mainWindow_menu.add_command(label="Remove Char", command=None)#todo)
mainWindow_menu.add_command(label="Force ESI update")
mainWindow_menu.add_separator()
mainWindow_menu.add_command(label="Exit", command=mainWindow.quit)
menubar.add_cascade(label="File", menu=mainWindow_menu)

mainWindow.config(menu=mainWindow_menu)

label = tk.Label(mainWindow, text="Authorized Characters:")
label.grid(row=0, column=0, sticky="w")
#character list
charlist = tk.Listbox(mainWindow, height=5, width=63)
scrollbar = tk.Scrollbar(mainWindow, command=charlist.yview)
scrollbar.grid(row=1, column=1, sticky="ns")
charlist.config(yscrollcommand=scrollbar.set)

for char in CHARACTERS: 
    charlist.insert(tk.END, char.get_char_name())
    
charlist.grid(row=1, column=0, columnspan=1, sticky="nsew")

#create a console to display outputs
console = tk.Text(mainWindow, height=10, width=50)
console.grid(row=2, column=0, columnspan=2, sticky="nsew")

def write_console_output(msg):
    console.config(state="normal")
    console.insert(tk.END, msg + "\n")
    console.see(tk.END)
    console.config(state="disabled")
    
#override sys.stdout to write to console
sys.stdout.write = write_console_output

listener_thread = threading.Thread(target=clipboardListener.run_listener)
listener_thread.daemon = True
listener_thread.start()

mainWindow_menu.mainloop()