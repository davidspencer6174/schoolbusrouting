import constants
import tkinter
from tkinter.filedialog import askopenfilename
from main import full_run

files_needed = ["Student data", "School data", "Bus data", "Map data",
                "Geocodes for map data", "Bus capacities for different ages",
                "Parameters", "Explicitly allowed school pairs (optional)",
                "Explicitly forbidden school pairs (optional)"]

filenames = ["" for i in range(9)]

textboxes = [None for i in range(9)]

buttons = [None for i in range(9)]

def set_file(index):
    filenames[index] = askopenfilename()
    textboxes[index].delete(1.0, tkinter.END)
    textboxes[index].insert(tkinter.END, filenames[index])
  
def create_routes():
    constants.FILENAMES = filenames
    full_run()

def run_gui():
    top = tkinter.Tk()
    
    for i in range(9):
        buttons[i] = tkinter.Button(top, text=files_needed[i], command = lambda: set_file(i))
        textboxes[i] = tkinter.Text(top, height = 1)
        buttons[i].pack()
        textboxes[i].pack()
        
    start_button = tkinter.Button(top, text="Create Routes", command = create_routes)
    start_button.pack()
    
    top.mainloop()