import win32api, win32gui, win32con
import win32clipboard
import threading
import ctypes
import json
import time

from dataclasses import dataclass
from pathlib import Path
from typing import Union, List, Optional

ACCEPTABLE_PROGRAMMS = ["EVE - Sylwanin Mo'at'ite", "EVE - Seze Mo'at'ite", "EVE - Neytiri Mo'at'ite"]

@dataclass
class Clip:
    type: str
    value: Union[str, List[Path]]
    
def read_clipboard() -> Optional[Clip]:
    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
            data: tuple = win32clipboard.GetClipboardData(win32con.CF_HDROP)
            return None
        elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
            data: str = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            return {"type": "text", "data": data}
        elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
            data: bytes = win32clipboard.GetClipboardData(win32con.CF_TEXT)
            return {"type": "text", "data": data.decode()}
        elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_BITMAP):
            # TODO: handle screenshots
            pass
        return None
    finally:
        win32clipboard.CloseClipboard()
        
        
class Clipboard:
    def _create_window(self) -> int:
        """
        Create a window for listening to messages
        :return: window hwnd
        """
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self._process_message
        wc.lpszClassName = self.__class__.__name__
        wc.hInstance = win32api.GetModuleHandle(None)
        class_atom = win32gui.RegisterClass(wc)
        return win32gui.CreateWindow(class_atom, self.__class__.__name__, 0, 0, 0, 0, 0, 0, 0, wc.hInstance, None)
      
    def _process_message(self, hwnd: int, msg: int, wparam: int, lparam: int):
        WM_CLIPBOARDUPDATE = 0x031D
        if msg == WM_CLIPBOARDUPDATE:
            #what happens if the clipboard changed
            print('clipboard updated!')
            originProg = win32gui.GetWindowText(win32gui.GetForegroundWindow())
            print("The Copy took place in the Window: " + originProg)
            if originProg in ACCEPTABLE_PROGRAMMS: 
                clipboard = read_clipboard()
                data = {
                    "character": originProg[6:],
                    "time": str(time.time()),
                    "type": clipboard["type"], 
                    "data": clipboard["data"]
                }
                json_data = json.dumps(data, indent=4)
                with open("clipboard.txt", "w") as outfile:
                    outfile.write(json_data)
                    outfile.close()
                print("Write to File")   
        return 0
    

    def listen(self):
        def runner():
            hwnd = self._create_window()
            ctypes.windll.user32.AddClipboardFormatListener(hwnd)
            win32gui.PumpMessages()

        th = threading.Thread(target=runner, daemon=True)
        th.start()
        while th.is_alive():
            th.join(0.25)
            
if __name__ == '__main__':
   clipboard = Clipboard()
   clipboard.listen()
   
def run_listener():
    clipboard = Clipboard()
    clipboard.listen()