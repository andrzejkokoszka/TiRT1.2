#!/usr/bin/env python
# -*- coding: utf-8 -*-

import Tkinter as tk #import modułu biblioteki Tkinter -- okienka

class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.grid(sticky=tk.N+tk.S+tk.E+tk.W)

        # Widgety interfejsu graficznego
        self.label_videoModified = None
        self.label_videoOrigin = None
        self.snapshotButton = None

        self.createWidgets()

    def createWidgets(self):

        top=self.winfo_toplevel()
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)

        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=1)
        self.columnconfigure(2,weight=1)
        self.columnconfigure(3,weight=1)

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.snapshotButton = tk.Button(self, text="Snapshot",command=self.snapshot)
        #self.snapshotButton.grid(column=0,row=0,columnspan=1,sticky=tk.NW+tk.SW)

        self.label_videoModified = tk.Label(self)
        self.label_videoModified.grid(row=1,column=0,sticky=tk.N+tk.S+tk.S+tk.E)

        self.label_videoOrigin = tk.Label(self)
        self.label_videoOrigin.grid(row=1,column=1)

    def snapshot(self):
        pass

if __name__=="__main__":
    app = Application()
    app.master.title('Sample application')
    app.mainloop()
