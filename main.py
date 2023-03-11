import json
import os
from typing import List
from psapi import EnumProcessModulesEx, GetModuleFileNameEx
from ReadWriteMemory import ReadWriteMemory, ReadWriteMemoryError
from time import sleep
import threading
import tkinter as tk
from tkinter import Button, Label
from tkinter import ttk
from ctypes import *
from uwp import get_minecraft_version


# Based on https://github.com/randomdavis/process_interface.py/blob/main/process_interface.py
class Memory:
    def __init__(self, process):
        self.process = process

    def write(self, address, data, buffer_size=4):
        try:
            count = c_ulong(0)
            c_int(0)
            if not windll.kernel32.WriteProcessMemory(self.process.handle, address, byref(data), buffer_size,
                                                      byref(count)):
                print("Failed: Write Memory - Error Code: ", FormatError(windll.kernel32.GetLastError()))
                windll.kernel32.SetLastError(10000)
            else:
                return False
        except (BufferError, ValueError, TypeError) as error:
            print("Failed: Read Memory #2 - Error Code: ", windll.kernel32.GetLastError())
            return False

    def read(self, address, buffer_size=4):
        try:
            buf = create_string_buffer(buffer_size)
            bytes_read = c_ulong(0)
            if windll.kernel32.ReadProcessMemory(self.process.handle, address, buf, buffer_size, byref(bytes_read)):
                return buf
            else:
                print("Failed: Read Memory - Error Code: ", windll.kernel32.GetLastError())
                return False
        except (BufferError, ValueError, TypeError) as error:
            print("Failed: Read Memory #2 - Error Code: ", windll.kernel32.GetLastError())
            return False

    def get_pointer(self, base_address: int, offsets: List[hex] = ()):
        temp_address = c_uint64.from_buffer(self.read(c_uint64(base_address), 8)).value
        pointer = 0x0
        if not offsets:
            return base_address
        else:
            for offset in offsets:
                pointer = c_uint64(int(temp_address) + offset)
                temp_address = c_uint64.from_buffer(self.read(pointer, 8)).value
            return pointer


class KeybindsChanger:
    def __init__(self, use_gui=True):
        self.prepare_dirs()
        self.module_name = None
        self.module_base = None
        self.pointers_offset = None

        self.searching_for_process = False
        self.pointer_map = {}

        self.process = None
        self.use_gui = use_gui
        self.selected_profile = None

        self.profiles_list = {'values': []}
        self.status_label = {'text': ''}

        self.memory = None

        self.start_process_search()

        self.buttons = []

        self.profiles = {}

        if use_gui:
            self.init_gui()

    def init_gui(self):
        window = tk.Tk()
        window.title('Minecraft Keybinds Switcher')
        window.geometry('330x520')
        window.resizable(width=False, height=False)

        self.status_label = Label(window, text='Searching for Minecraft', width=16)
        self.status_label.grid(row=1, column=1, columnspan=2, ipadx=105, ipady=20, sticky='n')

        Label(window, text='Profile:').grid(row=2, column=1, pady=5, sticky='e')

        self.selected_profile = tk.StringVar()
        self.profiles_list = ttk.Combobox(window, width=27, textvariable=self.selected_profile)
        self.load_profiles()
        self.profiles_list.grid(row=2, column=2, pady=5)

        Button(window, text='SAVE CURRENT', width=38, command=self.save_current_as_profile).grid(row=4, column=1,
                                                                                                 columnspan=2, pady=5)
        Button(window, text='APPLY', width=38, command=self.apply_profile).grid(row=5, column=1,
                                                                                columnspan=2)
        delete_btn_id = 0
        for slot_id in range(9):
            slot = Label(window, text=f'SLOT {slot_id + 1}: X', font=1)
            slot.grid(row=6 + slot_id, column=1, columnspan=2, pady=5)
            self.buttons.append(slot)
            delete_btn_id = slot_id + 7

        Button(window, text='DELETE SELECTED', width=38, command=self.delete_current_profile).grid(row=delete_btn_id,
                                                                                                   column=1,
                                                                                                   columnspan=2,
                                                                                                   pady=14)
        window.mainloop()

    def start_process_search(self):
        if self.searching_for_process:
            return
        self.searching_for_process = True
        threading.Thread(target=self.load_pointer_map, daemon=True).start()

    def prepare_dirs(self):
        if not os.path.exists(f'./memory_maps'):
            os.mkdir('./memory_maps')
        if not os.path.exists('./profiles'):
            os.mkdir('./profiles')

    def load_profiles(self):
        self.profiles = {}

        for file in os.listdir('./profiles'):
            filename = os.fsdecode(file)
            if filename.endswith(".json"):
                with open(f'./profiles/{filename}') as profile_file:
                    data = json.load(profile_file)
                    self.profiles.update({filename: data})
                    self.profiles_list['values'] = [x['Name'] for x in self.profiles.values()]
                continue
            else:
                continue

    def save_current_as_profile(self):
        name = self.selected_profile.get()
        if not name:
            return
        profile = {'Name': name}
        filename = name.lower()
        for slot_id in range(9):
            slot = int(c_int32.from_buffer(self.memory.read(self.pointer_map[slot_id], 4)).value)
            profile.update({f'Slot{slot_id + 1}': slot})
        with open(f'./profiles/{filename}.json', 'w', encoding='utf-8') as f:
            json.dump(profile, f, ensure_ascii=False, indent=4)
        self.load_profiles()

    def get_current_profile(self):
        try:
            return [(x, y) for x, y in zip(self.profiles.values(),
                                           self.profiles.items()) if x['Name'] == self.selected_profile.get()][0]
        except (IndexError, KeyError):
            return False

    def delete_current_profile(self):
        try:
            profile = self.get_current_profile()
            if not profile:
                print('NO PROFILE SELECTED')
                return
            file_to_delete = self.get_current_profile()[1][0]
            path = f'./profiles/{file_to_delete}'
            os.remove(path)
            self.selected_profile.set('')
            self.load_profiles()
        except (IndexError, KeyError, FileNotFoundError):
            print('DELETE ERROR')

    def apply_profile(self):
        try:
            current_profile = self.get_current_profile()[0]
            current_profile = list(current_profile.values())[1:]
            for slot_id in range(9):
                self.memory.write(self.pointer_map[slot_id], c_int32(current_profile[slot_id]), 4)
            self.update_values()
        except (IndexError, KeyError):
            print('APPLY ERROR')

    def update_values(self):
        if not self.use_gui:
            return
        profile = self.get_current_profile()
        current_profile = None
        if profile:
            current_profile = self.get_current_profile()[0]
            current_profile = list(current_profile.values())[1:]
        for slot_id in range(9):
            slot = int(c_int32.from_buffer(self.memory.read(self.pointer_map[slot_id], 4)).value)
            btn = f'MB{slot + 100}' if slot < 0 else chr(slot)
            to_btn = ''
            if current_profile:
                to_slot = current_profile[slot_id]
                if to_slot != slot:
                    to_btn = ' => ' + (f'MB{to_slot + 100}' if to_slot < 0 else chr(to_slot))

            self.buttons[slot_id]['text'] = f'SLOT {slot_id + 1}: {btn}{to_btn}'

    def realtime_values_update(self):
        while True:
            try:
                self.update_values()
                sleep(1)
            except:
                self.status_label['text'] = "Searching for Minecraft"
                self.start_process_search()
                break

    def load_pointer_map(self):
        filename = f'memory_map_{get_minecraft_version()}.json'
        try:
            with open(f'./memory_maps/{filename}') as file:
                data = json.load(file)
                base_struct = data['BaseAddress'].split('+')
                self.module_name = base_struct[0]
                # Find process
                rwm = ReadWriteMemory()
                while True:
                    try:
                        process = rwm.get_process_by_name(self.module_name)
                        process.open()
                        break
                    except ReadWriteMemoryError:
                        sleep(3)
                        pass
                self.status_label['text'] = "Attached to Minecraft"
                self.searching_for_process = False
                self.process = process
                self.memory = Memory(process)
                # Load modules
                for handle in EnumProcessModulesEx(self.process.handle):
                    module_base = int(handle.value)  # base addr
                    module_name = os.path.basename(
                        GetModuleFileNameEx(self.process.handle, handle))  # name
                    # print({module_name: module_base})
                    if module_name == self.module_name:
                        self.module_base = module_base
                        break
                if not self.module_base:
                    print('FAILED TO FIND MODULE')
                    return
                # Calculate base
                self.pointers_offset = int(base_struct[1], 16)
                self.pointer_map = []
                start_pointer_address = self.module_base + self.pointers_offset
                # read pointers
                data = list(data.values())[1:]
                for slot_id in range(9):
                    offsets_obj = []
                    offsets = data[slot_id].split(',')
                    for offset in offsets:
                        offsets_obj.append(int(offset, 16))
                        errors = 0
                        error_limit = 4
                        while True:
                            try:
                                errors += 1
                                pointer = self.memory.get_pointer(start_pointer_address, offsets=offsets_obj)
                                break
                            except:
                                if errors == error_limit:
                                    print('Failed to load pointers, restart required.')
                                    return
                                sleep(5)
                    self.pointer_map.append(pointer)
                threading.Thread(target=self.realtime_values_update, daemon=True).start()
        except FileNotFoundError:
            print('Version not supported!')
            self.status_label['text'] = "Unsupported version!"


if __name__ == '__main__':
    mkc = KeybindsChanger()
