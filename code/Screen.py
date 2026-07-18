# -*- coding: utf-8 -*-
import time
import tkinter as tk
from PIL import Image, ImageTk
import Settings as s
import random


class Screen(tk.Tk):
    def __init__(self):
        print("screen start")
        tk.Tk.__init__(self, className='Poppy')
        self._frame = None
        self.switch_frame(EyesPage)
        self["bg"] = "#F3FCFB"

    def switch_frame(self, frame_class):
        """Destroys current frame and replaces it with a new one."""
        new_frame = frame_class(self)
        if self._frame is not None:
            if hasattr(self._frame, 'background_label'):
                self._frame.background_label.destroy()
            self._frame.destroy()
        self._frame = new_frame
        self._frame.pack()


class EyesPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        image = Image.open('pictures//eyes.png')
        self.photo_image = ImageTk.PhotoImage(image)  # self. - for keeping the photo in memory so it will be shown
        tk.Label(self, image=self.photo_image).pack()


class FullScreenApp(object):
    def __init__(self, master, **kwargs):
        self.master = master
        pad = 3
        self._geom = '200x200+0+0'
        master.geometry("{0}x{1}+0+0".format(
            master.winfo_screenwidth()-pad, master.winfo_screenheight()-pad))
        master.bind('<Escape>', self.toggle_geom)

        # Camera preview thumbnail — bottom-right corner, updated from main thread.
        self._cam_label = tk.Label(master, bg='black', bd=2, relief='solid')
        self._cam_label.place(relx=1.0, rely=1.0, anchor='se', x=-10, y=-10)
        self._update_camera()

    def _update_camera(self):
        try:
            cap = getattr(s, 'cap', None)
            if cap and cap.isOpened():
                ok, frame = cap.read()
                if ok:
                    import cv2
                    frame = cv2.flip(frame, 1)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w = frame.shape[:2]
                    thumb_w = 320
                    thumb_h = int(h * thumb_w / w)
                    img = Image.fromarray(frame).resize((thumb_w, thumb_h), Image.BILINEAR)
                    photo = ImageTk.PhotoImage(img)
                    self._cam_label.configure(image=photo)
                    self._cam_label._photo = photo  # prevent GC
        except Exception:
            pass
        self.master.after(66, self._update_camera)  # ~15 fps — light enough for main thread

    def toggle_geom(self, event):
        geom=self.master.winfo_geometry()
        print(geom, self._geom)
        self.master.geometry(self._geom)
        self._geom = geom


if __name__ == "__main__":
    s.screen = Screen()
    app = FullScreenApp(s.screen)
    s.screen.mainloop()
