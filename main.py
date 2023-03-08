from ReadWriteMemory import ReadWriteMemory
from time import sleep
import threading
import tkinter as tk
from tkinter import Button, Label, Entry
from tkinter import ttk


class KeybindsChanger:
    def __init__(self, use_gui=True):

        base = 0x04000000
        static_address_offset = 0x0491CA88
        self.pointer_static_address = base + static_address_offset
        self.searching_for_process = False
        self.pointer_map = {}

        self.process = None
        self.use_gui = use_gui
        if use_gui:
            self.init_gui()

        self.profiles_list = {'values': []}
        self.status_label = {'text': ''}

        self.start_process_search()

    def init_gui(self):
        window = tk.Tk()
        window.title('Minecraft Keybinds Switcher')
        window.geometry('330x500')
        window.resizable(width=False, height=False)

        self.status_label = Label(window, text='Searching for Minecraft')
        self.status_label.grid(row=1, column=1, columnspan=2, ipadx=100, ipady=20, sticky='n')

        Label(window, text='Profile:').grid(row=2, column=1, pady=5, sticky='e')

        selected_profile = tk.StringVar()
        self.profiles_list = ttk.Combobox(window, width=27, textvariable=selected_profile)
        self.profiles_list['values'] = ['Bridge', 'CTF', 'EggWars']
        self.profiles_list.grid(row=2, column=2, pady=5)

        # Label(window, text='Name:').grid(row=3, column=1, sticky='e', pady=5)
        # Entry(window, width=30).grid(row=3, column=2, pady=5)

        Button(window, text='SAVE CURRENT', width=38).grid(row=4, column=1, columnspan=2, pady=5)
        Button(window, text='DELETE SELECTED', width=38).grid(row=5, column=1, columnspan=2)

        Label(window, text='SLOT 1: X', font=1).grid(row=6, column=1, columnspan=2, pady=5)
        Label(window, text='SLOT 2: X', font=1).grid(row=7, column=1, columnspan=2, pady=5)
        Label(window, text='SLOT 3: X', font=1).grid(row=8, column=1, columnspan=2, pady=5)
        Label(window, text='SLOT 4: X', font=1).grid(row=9, column=1, columnspan=2, pady=5)
        Label(window, text='SLOT 5: X', font=1).grid(row=10, column=1, columnspan=2, pady=5)
        Label(window, text='SLOT 6: X', font=1).grid(row=11, column=1, columnspan=2, pady=5)
        Label(window, text='SLOT 7: X', font=1).grid(row=12, column=1, columnspan=2, pady=5)
        Label(window, text='SLOT 8: X', font=1).grid(row=12, column=1, columnspan=2, pady=5)
        Label(window, text='SLOT 9: X', font=1).grid(row=13, column=1, columnspan=2, pady=5)

        Button(window, text='APPLY', width=38).grid(row=14, column=1, columnspan=2, pady=14)
        # frame = Frame(root, bg='#fafafa')
        # frame.place(rely=0.10, relx=0.10, relheight=0.8, relwidth=0.8)
        # button = Button(root, text='APPLY')
        # button.pack(pady=10)
        window.mainloop()

    def start_process_search(self):
        if self.searching_for_process:
            return
        self.searching_for_process = True
        threading.Thread(target=self.find_process, args=self.status_label).start()

    def find_process(self, status_label):
        rwm = ReadWriteMemory()
        while True:
            try:
                process = rwm.get_process_by_name("Minecraft.Windows.exe")
                process.open()
                break
            except:
                sleep(3)
                pass
        self.searching_for_process = False
        self.process = process

    def attach_and_load(self):
        pass

    def update_values(self):
        pass

    def load_pointer_map(self, filename):
        self.pointer_map = {}


if __name__ == '__main__':
    mkc = KeybindsChanger()
