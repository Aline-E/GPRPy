# import sys
# if sys.version_info[0] < 3:
#     import Tkinter as tk
#     from Tkinter import filedialog as fd
# else:
#     import tkinter as tk
#     from tkinter import filedialog as fd

import tkinter as tk
from tkinter import filedialog as fd
from tkinter import simpledialog as sd

import matplotlib as mpl
mpl.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
#import matplotlib.pyplot as plt

import gprpy as gp

from scipy import signal
import numpy as np

class GPRPyApp:

    def __init__(self,master):
        self.window = master

        
        # Initialize the gprpy
        proj = gp.gprpy2d()

        # Show splash screen
        fig=Figure(figsize=(8,5))
        a=fig.add_subplot(111)
        splash=signal.ricker(50,4)
        a.plot(splash)
        a.get_xaxis().set_visible(False)
        a.get_yaxis().set_visible(False)
        canvas = FigureCanvasTkAgg(fig, master=self.window)
        canvas.get_tk_widget().grid(row=1,column=0,columnspan=7,rowspan=15,sticky='nsew')
        canvas.draw()
 


        # Load data
        LoadButton = tk.Button(
            text="Import Data", fg="black",
            command=lambda : [self.loadData(proj),
                              self.plotTWTTData(proj,fig=fig,a=a,canvas=canvas,
                                                maxyval=float(myv.get()),
                                                contrast=float(contr.get()),
                                                color=colvar.get())])
        LoadButton.config(height = 1, width = 10)         
        LoadButton.grid(row=0, column=7, sticky='nsew')

        # TimeZero Adjust
        TZAButton = tk.Button(
            text="Time Zero Adj", fg="black",
            command=lambda : [proj.timeZeroAdjust(),
                              self.plotTWTTData(proj,fig=fig,a=a,canvas=canvas,
                                                maxyval=float(myv.get()),
                                                contrast=float(contr.get()),
                                                color=colvar.get())])
        TZAButton.config(height = 1, width = 10)         
        TZAButton.grid(row=1, column=7, sticky='nsew')

        # Dewow
        DewowButton = tk.Button(
            text="Dewow", fg="black",
            command=lambda : [self.dewow(proj),
                              self.plotTWTTData(proj,fig=fig,a=a,canvas=canvas,
                                                maxyval=float(myv.get()),
                                                contrast=float(contr.get()),
                                                color=colvar.get())])
        DewowButton.config(height = 1, width = 10)         
        DewowButton.grid(row=2, column=7, sticky='nsew')
        

        # Save data
        SaveButton = tk.Button(
            text="Save Data", fg="black",
            command=lambda : self.saveData(proj))
        SaveButton.config(height = 1, width = 10)         
        SaveButton.grid(row=13, column=7, sticky='nsew')

        # Print Figure
        PrintButton = tk.Button(
            text="Print Figure", fg="black",
            command=lambda : self.printTWTTFig(proj=proj,fig=fig))
        PrintButton.config(height = 1, width = 10)         
        PrintButton.grid(row=14, column=7, sticky='nsew')

        # Write history
        HistButton = tk.Button(
            text="Write history", fg="black",
            command=lambda : self.writeHistory(proj))
        HistButton.config(height = 1, width = 10)         
        HistButton.grid(row=15, column=7, sticky='nsew')
        
        
        ## Plotting
        
        # Refreshing plot
        plotButton = tk.Button(
            text="Refresh Plot",
            command=lambda : self.plotTWTTData(proj,fig=fig,a=a,canvas=canvas,
                                               maxyval=float(myv.get()),
                                               contrast=float(contr.get()),
                                               color=colvar.get()))
        plotButton.config(height = 1, width = 10)
        plotButton.grid(row=0, column=6, sticky='nsew')

        # Undo Button
        undoButton = tk.Button(
            text="Undo",
            command=lambda : [proj.undo(),
                              self.plotTWTTData(proj,fig=fig,a=a,canvas=canvas,
                                                maxyval=float(myv.get()),
                                                contrast=float(contr.get()),
                                                color=colvar.get())])
        undoButton.config(height = 1, width = 10)
        undoButton.grid(row=0, column=0, sticky='nsew')
        
                     
             
        # y limit
        myvtext = tk.StringVar()
        myvtext.set("Max y value")
        myvlabel = tk.Label(master, textvariable=myvtext,height = 1,width = 10)
        myvlabel.grid(row=0, column=1, sticky='nsew')
        myv = tk.StringVar()
        maxybox = tk.Entry(master, textvariable=myv)
        maxybox.grid(row=0, column=2, sticky='nsew')
        maxybox.config(width=8)
        myv.set("1000000")

        # Contrast
        contrtext = tk.StringVar()
        contrtext.set("Contrast")
        contrlabel = tk.Label(master, textvariable=contrtext,height = 1,width = 8)
        contrlabel.grid(row=0, column=3, sticky='nsew')
        contr = tk.StringVar()
        contrbox = tk.Entry(master, textvariable=contr, width=8)
        contrbox.grid(row=0, column=4, sticky='nsew')
        contr.set("1")

        # Mode switch for figure color
        colvar=tk.StringVar()
        colvar.set("gray")
        colswitch = tk.OptionMenu(master,colvar,"gray","bwr")
        colswitch.grid(row=0, column=5, sticky='nsew')




    def dewow(self,proj):
        window = sd.askinteger("Input","Dewow window width (number of samples)")
        proj.dewow(window=window)
        

        

        
    def loadData(self,proj):
        filename = fd.askopenfilename( filetypes= (("GPRPy", ".gpr"),
                                                   ("Sensors and Software", "*.DT1"),
                                                   ("GSSI", ".DZT")))
        proj.importdata(filename=filename)
        print("Loaded " + filename)

        
    def saveData(self,proj):        
        filename = fd.asksaveasfilename(defaultextension=".gpr")
        proj.save(filename)
       

        
    def writeHistory(self,proj):        
        filename = fd.asksaveasfilename(defaultextension=".py")
        proj.writeHistory(filename)
        print("Wrote history to " + filename)


    def plotTWTTData(self,proj,fig,a,canvas,maxyval,contrast,color):
        print("plotting, y-max " + str(maxyval))
        #color="gray"

        stdcont = np.argmax(abs(proj.data))        
        a.imshow(proj.data,cmap=color,extent=[min(proj.profilePos),
                                              max(proj.profilePos),
                                              max(proj.twtt),
                                              min(proj.twtt)],
                 aspect="auto",
                 vmin=-stdcont/contrast, vmax=stdcont/contrast)
        
        a.set_ylim([0,min(maxyval,max(proj.twtt))])
        a.invert_yaxis()
        a.get_xaxis().set_visible(True)
        a.get_yaxis().set_visible(True)
        a.set_ylabel("two-way travel time [ns]")
        a.set_xlabel("profile position")
        a.xaxis.tick_top()
        a.xaxis.set_label_position('top')
        
        canvas.get_tk_widget().grid(row=1,column=0,columnspan=7, rowspan=15, sticky='nsew')
        canvas.draw()
        

    def printTWTTFig(self,proj,fig):
        figname = fd.asksaveasfilename(defaultextension=".pdf")        
        fig.savefig(figname, format='pdf')        
        # Put what you did in history        
        histstr = "mygpr.printTWTT('%s')" %(figname)
        proj.history.append(histstr)
        print("Saved figure as %s" %(figname+'.pdf'))
        
root = tk.Tk()

app = GPRPyApp(root)

root.mainloop()



