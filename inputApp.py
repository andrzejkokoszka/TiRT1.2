#!/usr/bin/env python
# -*- coding: utf-8 -*-

import Tkinter as tk #import modułu biblioteki Tkinter -- okienka

class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.grid(sticky=tk.N+tk.S+tk.E+tk.W)

        # Widgety interfejsu graficznego
        self.checkbox_filterGray = None # checkbox filtra szarosci
        self.checkbox_resize = None # checbox do zmiany rozmiaru obrazu
        self.scale_resize = None # slider do zmiany wspolczynnika skalowania obrazu
        self.checkbox_contrast = None # checbox do zmiany kontrastu obrazu
        self.scale_contrast = None # slider do zmiany kontrastu
        self.checkbox_brightness = None # checbox do zmiany jasności obrazu
        self.scale_brightness = None # slider do zmiany jasności obrazu

        # Zmienne do obsługi widgetow
        self.var_checkbox_filterGray = tk.IntVar() # wartość checboxa od filtra szarosci
        self.var_checkbox_resize = tk.IntVar() # wartosć checkboxa do zmiany rozmiaru obrazu
        self.var_scale_resize = tk.DoubleVar() # wartosć slidera do wyboru współczynnika skalowania obrazu
        self.var_checkbox_contrast = tk.IntVar() # wartosć checkboxa do zmiany kontrastu obrazu
        self.var_scale_contrast = tk.DoubleVar() # wartosć slidera do wyboru współczynnika kontrastu obrazu
        self.var_checkbox_brightness = tk.IntVar() # wartosć checkboxa do zmiany jasności obrazu
        self.var_scale_brightness = tk.DoubleVar() # wartosć slidera do wyboru współczynnika jasności obrazu

        self.createWidgets()

    def createWidgets(self):

        top = self.winfo_toplevel()
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)

        self.columnconfigure(0,weight=1)
        self.rowconfigure(0, weight=1)

        self.checkbox_resize = tk.Checkbutton(self, text="Image scalling", variable=self.var_checkbox_resize, command=self.cmd_checkbox_resize)
        self.checkbox_resize.grid(column=0,row=0,sticky=tk.W)

        # slider do zmiany wspolczynnika skalowania obrazu
        self.scale_resize = tk.Scale(self, from_=0.5, to=1, resolution=0.01, orient=tk.HORIZONTAL, tickinterval=0.1,
                                     length = 200, state=tk.DISABLED, variable=self.var_scale_resize)
        self.scale_resize.grid(row=0,column=1)
        self.var_scale_resize.set(1)

        self.checkbox_brightness = tk.Checkbutton(self, text="Brightness enhancement", variable=self.var_checkbox_brightness, command=self.cmd_checkbox_brightness)
        self.checkbox_brightness.grid(row=1,column=0,sticky=tk.W)

        # slider do zmiany jasności obrazu
        self.scale_brightness = tk.Scale(self, from_=-100, to=100, resolution=1, orient=tk.HORIZONTAL, tickinterval=50,
                                       length=200, state=tk.DISABLED, variable=self.var_scale_brightness)
        self.scale_brightness.grid(row=1,column=1)

        self.checkbox_contrast = tk.Checkbutton(self, text="Contrast enhancement", variable=self.var_checkbox_contrast, command=self.cmd_checkbox_contrast)
        self.checkbox_contrast.grid(row=2,column=0,sticky=tk.W)

        # slider do zmiany kontrastu obrazu
        self.scale_contrast = tk.Scale(self, from_=-100, to=100, resolution=1, orient=tk.HORIZONTAL, tickinterval=50,
                                     length=200, state=tk.DISABLED, variable=self.var_scale_contrast)
        self.scale_contrast.grid(row=2,column=1)

        self.checkbox_filterGray = tk.Checkbutton(self, text="Gray filter", variable=self.var_checkbox_filterGray)
        self.checkbox_filterGray.grid(column=0,row=3,columnspan=2,pady=10)


    def cmd_checkbox_resize(self):
        """ Metoda obsługująca checkbox do zmiany rozmiaru obrazu """
        if self.var_checkbox_resize.get():
            self.scale_resize.config(state=tk.NORMAL)
        else:
            self.scale_resize.config(state=tk.DISABLED)
            end_val = self.scale_resize.cget("to") # wartość końca przedziału slidera
            self.var_scale_resize.set(end_val)

    def cmd_checkbox_contrast(self):
        """ Metoda obsługująca checkbox do zmiany kontrastu obrazu """
        if self.var_checkbox_contrast.get():
            self.scale_contrast.config(state=tk.NORMAL)
        else:
            self.scale_contrast.config(state=tk.DISABLED)
            self.var_scale_contrast.set(0)

    def cmd_checkbox_brightness(self):
        """ Metoda obsługująca checkbox do zmiany jasności obrazu """
        if self.var_checkbox_brightness.get():
            self.scale_brightness.config(state=tk.NORMAL)
        else:
            self.scale_brightness.config(state=tk.DISABLED)
            self.var_scale_brightness.set(0)

if __name__=="__main__":
    app = Application()
    app.master.title('Input settings')
    app.mainloop()
