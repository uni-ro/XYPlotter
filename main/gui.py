"""
gui.py
GUI to handle user inputs and setup using Tkinter.
"""

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as mb
import tkinter.colorchooser as colour
import tkinter.scrolledtext as scrollT
import tkinter.simpledialog as dia
import os
import subprocess
import setup
import inputOutput as io
import datetime
import log
import constants as const
import numpy as np
import re
import importlib
from turtle import ScrolledCanvas, RawTurtle, TurtleScreen
import turtlePlot
import importlib

class GUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.variableCreation()
        self.notebookSetup()

    def variableCreation(self):
        #Finds all svg files in directory
        dirname = os.getcwd()

        self.filedir = dirname + '/sgvFiles' #yes svg is spelt wrong ;)
        self.file_list = os.listdir(self.filedir)
        self.DEFAULT_CONSTANTS_FILE_PATH = dirname + '/constants_defaults.py'

        # Create log for gui:
        log.createLog()

        # convert cm to pixels
        PIXELS_PER_CM = 267/2.54 #different resolution on 3D printer thingy
        height_in_cm = 2.5
        width_in_cm = 8.5

        self.height_in_pixels = int(height_in_cm * PIXELS_PER_CM)
        self.width_in_pixels = int(width_in_cm * PIXELS_PER_CM)

    def notebookSetup(self):
        # create the tkinter window
        self.geometry(f"{self.width_in_pixels}x{self.height_in_pixels}")

        label = tk.Label(self, text="XY-Plotter GUI")
        label.pack()

        # Create notebook
        self.notebook = ttk.Notebook(self, width=self.width_in_pixels, height=self.height_in_pixels)
        self.notebook.pack(fill = 'both', expand=True)

        self.frameCreation()
        self.frameSetup()

    def frameCreation(self):
        self.frameDict = {}

        mainFrame = MainFrame(self.notebook, self)
        self.frameDict[MainFrame] = mainFrame

        variablesFrame = VariablesFrame(self.notebook, self)
        self.frameDict[VariablesFrame] = variablesFrame

        logFrame = LogFrame(self.notebook, self)
        self.frameDict[LogFrame] = logFrame

        drawingFrame = DrawingFrame(self.notebook, self)
        self.frameDict[DrawingFrame] = drawingFrame

        # Add main notebook tab
        self.notebook.add(self.frameDict[MainFrame], text='Menu')

    def frameSetup(self):
        for frame in self.frameDict.values():
            frame.createPage()



    # Common Functions:

    # verify user action on file save
    def fileSaveCheck(self, fileDir : str, fileExtension : str, fileData : str, executeFunction = None, name : str = None):
        if name == None:
            name = dia.askstring("File Name", "What would you like to call the file (leave blank for timestamp)")

            if name == None: return

            if name.strip() == '': name = datetime.datetime.now().strftime('%d-%m-%y %H:%M:%S')

        #fileData = io.readFileData(tempLogFilePath)
        if fileData != False and io.writeFileData(f'{fileDir}/{name}.{fileExtension}', fileData):
            mb.showinfo("SUCCESS", "File successfully saved!")
            
            if executeFunction != None: executeFunction(name)

            #io.deleteFile(tempLogFilePath)
            #combobox.set(f'{name}.log')
        else: 
            print('fileData: ', fileData)
            print('fileDir: ', fileDir)
            print('name: ', name)
            print('fileExtension: ', fileExtension)
            mb.showerror("ERROR", "File could not be saved!")

class MainFrame(tk.Frame):
    def __init__(self, master, parent):
        super().__init__(master, name='main')
        self.parent = parent

    def createPage(self):
        # Create main frame
        self.configure(width=self.parent.width_in_pixels, height=self.parent.height_in_pixels - 20)
        #self.pack(fill='both', expand=True)

        # Create frames for sections of the screen (work around for using pack instead of grid)
        topFrame = tk.Frame(self)
        topFrame.pack(fill='x', expand=False, anchor='n')

        bottomFrame = tk.Frame(self)
        bottomFrame.pack(fill='x', expand=True, anchor='n')

        # create a listbox with items in file_list for svg files
        self.listboxHeight = tk.IntVar(self)
        self.listboxHeight.set(len(self.parent.file_list)) # Create dynamic tk variable # Doesn't work

        self.listbox = tk.Listbox(topFrame, selectmode=tk.SINGLE, width=80, height=self.listboxHeight.get())
        for filename in self.parent.file_list:
            self.listbox.insert(tk.END, filename)
        self.listbox.pack(side=tk.LEFT, fill='x', expand=True, anchor='n')

        # Create a frame to contain all the buttons
        mainButtonFrame = tk.Frame(topFrame)
        mainButtonFrame.pack(side=tk.RIGHT, fill='x', expand=True, anchor='n')

        self.canvasWidth = tk.IntVar(self)
        self.canvasHeight = tk.IntVar(self)

        self.canvasWidth.set(const.PLOTTER_WIDTH)
        self.canvasHeight.set(const.PLOTTER_HEIGHT)

        self.previewCanvas = ScrolledCanvas(bottomFrame, width=self.canvasWidth.get(), height=self.canvasHeight.get())
        self.previewCanvas.pack(anchor='center')

        self.screen = TurtleScreen(self.previewCanvas)
        self.turtle = RawTurtle(self.screen)

        self.master.bind('<<NotebookTabChanged>>', self.notebookTabChangedFunc, add='+')
        self.listbox.bind('<<ListboxSelect>>', self.save_selection)
        self.previewCanvas.bind('<Configure>', lambda e: e.widget.configure(width=self.canvasWidth.get(), height=self.canvasHeight.get()))

        self.createButtons(mainButtonFrame)


    def createButtons(self, mainButtonFrame):
        # Button to execute run_selection()
        previewButton = tk.Button(mainButtonFrame, text='Show Preview', command=self.run_selection)
        previewButton.pack()

        # Create button to create new change variable tab
        changeButton = tk.Button(mainButtonFrame, text='Change Variables', command=self.setupVariablesPage)
        changeButton.pack()

        # Create button to create new log tab
        logButton = tk.Button(mainButtonFrame, text='View Log', command=self.setupLogPage)
        logButton.pack()

        drawingButton = tk.Button(mainButtonFrame, text='Create Drawing', command=self.setupDrawingPage)
        drawingButton.pack()

        # Create button to quit
        quitButton = tk.Button(mainButtonFrame, text='Quit', command=self.exitGui)
        quitButton.pack()

    def updateListbox(self, e):
        self.listbox.delete(0, tk.END)
        for filename in os.listdir(self.parent.filedir):
            self.listbox.insert(tk.END, filename)
        self.listboxHeight.set(len(os.listdir(self.parent.filedir)))
        self.listbox.configure(height=self.listboxHeight.get())

    def updatePreviewCanvas(self, e):
        importlib.reload(const)
        self.canvasWidth.set(const.PLOTTER_WIDTH)
        self.canvasHeight.set(const.PLOTTER_HEIGHT)
        self.previewCanvas.configure(width=self.canvasWidth.get(), height=self.canvasHeight.get())
        
        if e.widget.tab(e.widget.select())['text'] == 'Menu':
            try:
                self.selected_file
                io.printd("Updating Selected Preview")
                self.run_selection()
            except AttributeError:
                ...

    def notebookTabChangedFunc(self, e):
        self.updateListbox(e)
        self.updatePreviewCanvas(e)

    def exitGui(self):
        """ Function to ask user about intention to quit """

        if mb.askyesno(title='Quit?', message='Are you sure you want to quit?'):
            self.parent.quit()

    # function to save the selected file in the list
    def save_selection(self, e):
        #selection = listbox.curselection()
        selection = e.widget.curselection()
        if selection:
            self.selected_file = self.listbox.get(selection)
            
            self.filePath = '\"sgvFiles/' + self.selected_file + '\"'

            # Save filePath in constants.py
            if setup.setVariable(setup.ConstantVariable('FILE', self.filePath, '   # Source file for plotting')):
                print('File successfully saved!')
                #mb.showinfo(title="SUCCESS", message='File successfully saved!')
            else:
                mb.showerror(title="FAILURE", message='File could not be saved!')
        else:
            if self.master.tab(self.master.select())['text'] != 'Log':
                mb.showwarning(title="WARNING", message='Ensure that you have first selected a file!')

    # Run main.py with the given selection
    def run_selection(self):
        """ Function to run the main.py file with the given gui parameter """

        # Check if a file has been saved
        try:
            # Define file path format to save in constants.py 
            self.filePath = '\"sgvFiles/' + self.selected_file + '\"'
            print(self.filePath)
        except AttributeError as e:
            mb.showwarning(title="WARNING", message='Ensure that you have first saved a selection!')
            return
        

        #turtle.clear()
        self.screen.reset()
        self.turtle.reset()
        #turtle.speed(10)
        #screen.clear()

        # Run main.py
        try:
            #subprocess.run(['python3', 'main.py', 'gui']
            #import main
            try:
                importlib.reload(self.main)
                io.printd('Main reloaded!')
            except AttributeError:
                self.main = importlib.import_module('main')

            #main = importlib.import_module('main')
            self.main.tp.turtlePlot(self.main.pointList, gui=True, turt=self.turtle, s=self.screen)
            #global logContents
            #logContents = log.log.dLog
        except Exception as e:
            print(e)

    def setupVariablesPage(self):
        self.master.add(self.parent.frameDict[VariablesFrame], text='Variables')

    def setupLogPage(self):
        self.master.add(self.parent.frameDict[LogFrame], text='Log')

    def setupDrawingPage(self):
        self.master.add(self.parent.frameDict[DrawingFrame], text='Draw')
        
class VariablesFrame(tk.Frame):
    def __init__(self, master, parent):
        super().__init__(master, name='variable')
        self.parent = parent

    def createPage(self):
        """ Function to create scrolling tab within notebook to contain variable changing objects """
        
        # Frame created for new tab
        self.configure(width=self.parent.width_in_pixels, height=self.parent.height_in_pixels)
        #tabFrame = tk.Frame(self, width=self.parent.width_in_pixels, height=self.parent.height_in_pixels, name='variables')
        #tabFrame.pack(fill='both', expand=True)

        # Canvas created to allow for scrolling
        scrollableCanvas = tk.Canvas(self)
        scrollableCanvas.pack(fill='both', expand=True)

        # Create scrollbar
        scrollBar = tk.Scrollbar(scrollableCanvas, orient='vertical', command=scrollableCanvas.yview)
        scrollBar.pack(fill=tk.Y, side=tk.RIGHT)

        # Configure scrollbar to the canvas
        scrollableCanvas.configure(yscrollcommand=scrollBar.set)
        scrollableCanvas.bind('<Configure>', lambda e: scrollableCanvas.configure(scrollregion=scrollableCanvas.bbox("all")))

        # Create frame that will be scrolled
        # This will contain all variable changing objects
        self.variableFrame = tk.Frame(scrollableCanvas)
        scrollableCanvas.create_window(0, 0, window=self.variableFrame, anchor='nw', width=self.parent.width_in_pixels) # Add frame to canvas

        # Add variable changer objects to given frame
        self.implement_Variables(self.variableFrame)

        # Create button to reset values
        defaultsButton = tk.Button(self.variableFrame, text="Reset to Default?", command=self.verify)
        defaultsButton.pack(side=tk.RIGHT)

    # Create variable changer tab
    def implement_Variables(self, frame):
        """ Function to add required variables to create a variable change interface in the given frame """
        # frame - tk.Frame object - the frame to add objects to.
        
        self.variableDict = dict()
        variableObjects = dict()
        varlist = setup.getVariables()

        # For each changeable variable in constants.py
        for var in varlist:
            self.variableDict[var.getName()] = var
            if var.debug != None: continue

            if var.getType() in [int, float]:
                """ If variable is of type int or float, create a scale object """
                # Note: floats with increments not implemented yet

                # Create Scale object
                variableObjects[var.getName()] = tk.Scale(frame, label=var.getName(), from_= var.getMin(), to= var.getMax(), orient='horizontal')
                variableObjects[var.getName()].set(var.getValue()) # Set current value as saved value
                variableObjects[var.getName()].bind("<ButtonRelease-1>", self.scaleFunc) # Add function
                variableObjects[var.getName()].pack(fill='x') # Fill scale along x axis

            if var.getType() in [bool]:
                """ If variable is of type bool, create a checkbutton object """

                #Create Checkbutton object
                variableObjects[var.getName()] = ttk.Checkbutton(frame, text=var.getName())
                variableObjects[var.getName()].invoke() # Used to update state when variables are reset
                variableObjects[var.getName()].bind("<ButtonRelease-1>", self.checkFunc) # Add function
                variableObjects[var.getName()].pack(fill='x') # Fill scale along x axis

                if var.getValue() == 'True': variableObjects[var.getName()].state(['selected']) # If saved value is True, set as checked
                else: variableObjects[var.getName()].state(['!selected']) # else set as unchecked

            if var.getType() in ['colour', 'color']:
                """ If variable is of type colour/color, create a colour chooser object """
                
                # Create variable label
                header = tk.Label(frame, text=var.getName())
                header.pack(expand=True, fill='x')

                # Create button to execute colourFunc()
                variableObjects[var.getName()] = tk.Button(frame, text='Choose Colour', name=var.getName().lower())
                variableObjects[var.getName()].bind("<ButtonRelease-1>", self.colourFunc) # Add function to button
                variableObjects[var.getName()].pack(fill='x') # Fill scale along x axis


    def scaleFunc(self, event):
        """ Function to call when a scale object is adjusted """
        
        widget = event.widget
        value = widget.get()
        var = self.variableDict[widget.cget('label')]

        setup.setVariable(setup.ConstantVariable(var.getName(), value, var.getComment()))

    def checkFunc(self, event):
        """ Function to call when checkbutton object is pressed """

        widget = event.widget
        value = widget.instate(['!selected'])
        var = self.variableDict[widget.cget('text')]

        setup.setVariable(setup.ConstantVariable(var.getName(), value, var.getComment()))

    def colourFunc(self, event):
        """ Function to call when button to create colour chooser is pressed """
        
        widget = event.widget
        var = self.variableDict[widget.winfo_name().upper()]
        colour.Chooser(self.variableFrame, label=var.getName()) # Create colour picker
        selected_colour = colour.askcolor()

        if selected_colour[0] != None: setup.setVariable(setup.ConstantVariable(var.getName(), selected_colour[0], var.getComment()))

    def verify(self):
        """ Function to check whether the user truly wishes to reset variables or not """
        # Note: reset also changes comment
        # Note: can be generalised, but no requirement as of creation

        # Create message box to inquire about user's true intention
        if mb.askyesno(title='Continue?', message='Are you sure you want to reset values to defaults?'):
            # Get default variable values 
            defaultObjects = setup.getVariables(filePath=self.parent.DEFAULT_CONSTANTS_FILE_PATH)

            for var in defaultObjects:
                setup.setVariable(var) # Save each variable as default

            self.parent[MainFrame].previewCanvas.configure(width=self.parent[MainFrame].canvasWidth.get(), height=self.parent[MainFrame].canvasHeight.get())
            self.createPage() # Re-create variable changer tab

class LogFrame(tk.Frame):
    
    def __init__(self, master, parent):
        super().__init__(master, name='logframe')
        self.parent = parent

    def createPage(self):
        self.logFilesPath = './logFiles'
        self.tempLogFilePath = const.TEMP_LOG_PATH
        self.logContents = tk.StringVar(self.parent)

        #------------------------------------------------------------------------------------
        
        # Elements
        self.configure(width=self.parent.width_in_pixels, height=self.parent.height_in_pixels)
        #logFrame = tk.Frame(notebook, width=width_in_pixels, height=height_in_pixels, name='logframe')
        
        self.scrolledText = scrollT.ScrolledText(self)
        self.combobox = ttk.Combobox(self, postcommand=lambda: self.combobox.configure(values=os.listdir(self.logFilesPath)))
        buttonFrame = tk.Frame(self)
        saveButton = tk.Button(buttonFrame, command=self.saveLogFile, text='Save Log File')
        deleteButton = tk.Button(buttonFrame, command=self.deleteFile, text='Delete File')
        filtersButton = tk.Button(buttonFrame, command=self.openFilterButtons, text='Open Filters')
        
        #------------------------------------------------------------------------------------

        #------------------------------------------------------------------------------------

        # Configurations

        #logContents = io.readFileData(tempLogFilePath)
        self.logContents.set(io.readFileData(self.tempLogFilePath))

        if self.logContents.get() != None and self.logContents.get(): self.scrolledText.insert(tk.INSERT, self.logContents.get())
        self.scrolledText.configure(state='disabled')


        self.combobox.set(const.TEMP_LOG_PATH.replace(self.logFilesPath + '/', ''))
        self.combobox['state'] = 'readonly'
        self.combobox.bind('<<ComboboxSelected>>', self.selectedLogFile)

        self.master.bind('<<NotebookTabChanged>>', self.updateLogContents, add="+")

        #------------------------------------------------------------------------------------
        

        # Packing order and grid placements

        self.combobox.pack()
        buttonFrame.pack(fill='x')
        saveButton.grid(row=0, column=0)
        deleteButton.grid(row=0, column=1)
        filtersButton.grid(row=0, column=2)
        self.scrolledText.pack(fill='both', expand=True)

        #------------------------------------------------------------------------------------

    #import log
    #def openLog():

        # General Functions

    def updateScrolledText(self, scrolledText, logContents):
        scrolledText.configure(state='normal')
        scrolledText.delete(0.0, tk.END)
        scrolledText.insert(tk.INSERT, logContents)
        scrolledText.configure(state='disabled')
        
        #------------------------------------------------------------------------------------

        # Button Functions
    def saveLogFile(self):
        def f(name):
            io.deleteFile(self.tempLogFilePath)
            self.combobox.set(f'{name}.log')

        self.parent.fileSaveCheck(self.logFilesPath, 'log', io.readFileData(self.tempLogFilePath), f)

    def deleteFile(self):
        selection = self.combobox.get()
        result = mb.askyesno("WARNING", f"Are you sure you want to delete the file {selection}?")
        if result == True:
            if io.deleteFile(self.logFilesPath + '/' + selection):
                mb.showinfo('SUCCESS', 'File successfully deleted!')
                defaultFile = os.listdir(self.logFilesPath)[0]
                
                self.combobox.set(defaultFile)
                self.updateScrolledText(self.scrolledText, io.readFileData(self.logFilesPath + '/' + defaultFile))
            else:
                mb.showerror('ERROR', f'File {selection} could not be deleted!')
        
    def openFilterButtons(self):
        filterRoot = tk.Toplevel(self.parent)
        filterRoot.lift(aboveThis=self.parent)

        frame = tk.Frame(filterRoot, width=self.parent.width_in_pixels, height=self.parent.height_in_pixels)

        variableObjects = dict()

        def filterFunc(e):
            widget = e.widget
            varName = widget.cget('text')
            value = widget.instate(['!selected'])

            print(value)

            outputType = re.search('([A-Z]+)_\w+', varName).groups()[0]
            
            textValue = self.scrolledText.get(0.0, tk.END)
            
            if value == False:
                filteredText = []

                lines = textValue.split('\n')
                for i in range(len(lines)):
                    line = lines[i]
                    if not line.startswith(outputType):
                        filteredText.append(line)

                textValue = '\n'.join(filteredText)
                self.updateScrolledText(scrolledText=self.scrolledText, logContents=textValue)

            elif value == True: # Requires work.
                filteredText = []
                savedLines = [line for line in self.logContents.get().split('\n') if line != '']
                textBoxLines = [line for line in textValue.split('\n') if line != '']
                
                b = 0

                for i in range(len(savedLines)):

                    if savedLines[i].startswith(textBoxLines[b]): 
                        filteredText.append(textBoxLines[b])
                        if b < len(textBoxLines) - 1: b += 1
                    
                    else: 
                        
                        if savedLines[i].startswith(outputType):
                            filteredText.append(savedLines[i])

                
                textValue = '\n'.join(filteredText)
                self.updateScrolledText(scrolledText=self.scrolledText, logContents=textValue)


        logVariables = setup.getVariables()
        for var in logVariables:
            if var.debug == None: continue

            if var.getType() in [bool]:
                """ If variable is of type bool, create a checkbutton object """

                #Create Checkbutton object
                variableObjects[var.getName()] = ttk.Checkbutton(frame, text=var.getName())
                variableObjects[var.getName()].invoke() # Used to update state when variables are reset
                variableObjects[var.getName()].bind("<ButtonRelease-1>", filterFunc) # Add function
                variableObjects[var.getName()].pack(fill='x') # Fill scale along x axis

                if var.getValue() == 'True': variableObjects[var.getName()].state(['selected']) # If saved value is True, set as checked
                else: variableObjects[var.getName()].state(['!selected']) # else set as unchecked

        frame.pack()

        filterRoot.mainloop()



        

    # Event Bound Functions

    def updateLogContents(self, e):
        #logContents = io.readFileData(tempLogFilePath)
        self.logContents.set(io.readFileData(self.tempLogFilePath))
        #updateScrolledText(scrolledText, logContents)
        self.updateScrolledText(self.scrolledText, self.logContents.get())
        self.combobox.set(self.tempLogFilePath.replace(self.logFilesPath + '/', ''))

    def selectedLogFile(self, e):
        widget = e.widget
        value = widget.get()

        #logContents = io.readFileData(logFilesPath + '/' + value)
        self.logContents.set(io.readFileData(self.logFilesPath + '/' + value))

        if self.logContents.get() != None and self.logContents.get():
            self.updateScrolledText(self.scrolledText, self.logContents.get())

        
        #notebook.add(logFrame, text='Log')

class DrawingFrame(tk.Frame):
    def __init__(self, master, parent):
        super().__init__(master, name='drawing')
        self.parent = parent

    def createPage(self):
        self.setupVariables()

        canvasClearButton = tk.Button(self, text='Clear Canvas', command=self.deleteElements)
        #canvasClearButton.grid(row=0, column=2)
        canvasClearButton.pack()

        self.radioFrame = tk.Frame(self)
        self.radioFrame.pack(fill='x')

        self.setupRadioFrame(self.radioFrame, self.radioVar)

        canvasFrame = tk.Frame(self)
        canvasFrame.pack(fill='both')

        self.canvas = tk.Canvas(canvasFrame, width=1000, height=1000, borderwidth=10, background='white')
        self.canvas.grid(row=0, column=0, padx=50)

        self.setupInfoBar(canvasFrame)

        self.canvas.bind('<ButtonPress>', self.press)
        self.canvas.bind('<ButtonRelease>', self.release)
        self.canvas.bind('<Motion>', self.mousePos)

    def setupVariables(self):
        self.drawingElementIDs = []
        self.elementTypes = {}
        self.elementData = {}

        self.radioVar = tk.IntVar(self)
        self.radioVar.set(0)

        self.chosenRadios = []

        self.isPressed = tk.BooleanVar(self)
        self.isPressed.set(False)

        self.isEditing = tk.BooleanVar(self)
        self.isEditing.set(False)

        self.arcPoints = []

        self.freeDrawPointIDs = []
        self.polylinePointIDs = []
        self.polylinePoints = []

        self.pathPointIDs = []
        self.pathPoints = []
        self.pathPointInfo = []

        self.editPointIDs = []
        self.editSelectedIDs = []
        self.edit_shapeID = []
        self.edit_key = ''
        self.edit_editingPoint = [0, 0]
        self.edit_info = {}
        self.edit_indexes = {}

        self.editPointSize = 2
        self.editPointColour = 'red'

        self.hasMoved = tk.BooleanVar(self)
        self.hasMoved.set(False)

        self.pointPurgatory = []

        self.coords = np.zeros(4)

        self.shapeID = None

        self.infoBarText = tk.StringVar(self)
        self.infoBarText.set('Currently Editing:')

    def setupRadioFrame(self, radioFrame, radioVar):
        lineRadio = tk.Radiobutton(radioFrame, text='Line', variable=radioVar, value=0)
        lineRadio.bind('<ButtonPress>', self.updateInfoBar)
        lineRadio.grid(row=0, column=0)

        arcRadio = tk.Radiobutton(radioFrame, text='Arc', variable=radioVar, value=1)
        arcRadio.bind('<ButtonPress>', self.updateInfoBar)
        arcRadio.grid(row=0, column=1)

        ellipseRadio = tk.Radiobutton(radioFrame, text='Ellipse', variable=radioVar, value=2)
        ellipseRadio.bind('<ButtonPress>', self.updateInfoBar)
        ellipseRadio.grid(row=0, column=2)

        rectangleRadio = tk.Radiobutton(radioFrame, text='Rectangle', variable=radioVar, value=3)
        rectangleRadio.bind('<ButtonPress>', self.updateInfoBar)
        rectangleRadio.grid(row=0, column=3)

        #freeDrawRadio = tk.Radiobutton(radioFrame, text='Free Draw', variable=radioVar, value=4)
        #freeDrawRadio.bind('<ButtonPress>', self.updateInfoBar)
        #freeDrawRadio.grid(row=0, column=4)

        polylineRadio = tk.Radiobutton(radioFrame, text='Polyline', variable=radioVar, value=5)
        polylineRadio.bind('<ButtonPress>', self.updateInfoBar)
        polylineRadio.grid(row=0, column=5)

        pathRadio = tk.Radiobutton(radioFrame, text='Path', variable=radioVar, value=6)
        pathRadio.bind('<ButtonPress>', self.updateInfoBar)
        pathRadio.grid(row=0, column=6)

        saveFile = tk.Button(radioFrame, text='Save', command=self.saveAsFile)
        saveFile.grid(row=0, column=8)

        eraserRadio = tk.Radiobutton(radioFrame, text='Eraser', variable=radioVar, value=9)
        eraserRadio.bind('<ButtonPress>', self.updateInfoBar)
        eraserRadio.grid(row=0, column=9)

    def setupInfoBar(self, canvasFrame):

        self.infoBar = tk.Frame(canvasFrame)
        self.infoBar.grid(row=0, column=1, sticky='nsew')

        currentSelection = tk.Label(self.infoBar, textvariable=self.infoBarText)
        currentSelection.pack()

        self.endDrawing = tk.Button(self.infoBar, text='End Drawing', command=self.closeDrawing, state='disabled')
        self.endDrawing.pack()

        undoRedoFrame = tk.Frame(self.infoBar)
        undoRedoFrame.pack()

        self.undoButton = tk.Button(undoRedoFrame, text='Undo', command=self.undo, state='active')
        self.undoButton.grid(row=0, column=0)

        self.redoButton = tk.Button(undoRedoFrame, text='Redo', command=self.redo, state='disabled')
        self.redoButton.grid(row=0, column=1)

        self.editPath = tk.Button(canvasFrame, text='Edit Path', command=self.edit)
        self.editPath.lower()
        self.editPath.pack(in_=self.infoBar)

        self.inf = self.info(self.infoBar, self.infoBarText)

    def openDrawing():
        """Testing concept of being able to draw own svgs"""
        #drawingFrame = tk.Frame(notebook)
        #drawingFrame.pack(fill='both', expand=True)

        #pixelSize = 100
        #pixelDimensions = '2x2'
        #pixels = np.zeros([int(pixelDimensions.split('x')[0]), int(pixelDimensions.split('x')[1])], dtype='object')

        #buttonFrame = tk.Frame(drawingFrame)
        #buttonFrame.pack(fill='x')

        #undoButton = tk.Button(buttonFrame, text='Undo', command=lambda: canvas.delete(drawingElementIDs[-1]))
        #undoButton.grid(row=0, column=0)

        #redoButton = tk.Button(buttonFrame, text='Redo')
        #redoButton.grid(row=0, column=1)

        
    def deleteElements(self):
        self.canvas.delete('all')
        self.drawingElementIDs = []
        self.elementTypes = {}
        self.coords[0:4] = 0
        self.closeDrawing()

    def updateInfoBar(self, e):
        widget = e.widget
        self.closeDrawing()
        
        if widget.cget('value') == 5:
            self.endDrawing.configure(state='active')
        elif widget.cget('value') == 6:
            self.editPath.tkraise()
            self.endDrawing.configure(state='active')
        else:
            self.editPath.lower()
            self.endDrawing.configure(state='disabled')

        self.inf.setSelected(widget.cget('text'))
        self.inf.updateInfoBar()

    def closeDrawing(self):
        if self.radioVar.get() == 5:
            self.coords[0:4] = 0
            self.drawingElementIDs.append(self.polylinePointIDs)
            self.elementTypes[', '.join([str(id) for id in self.polylinePointIDs])] = 'polyline'
            self.polylinePointIDs = []
            self.polylinePoints = []
            self.canvas.delete(self.shapeID)
            self.undoButton.configure(state='active')
        
        elif self.radioVar.get() == 6:
            self.coords[0:4] = 0
            self.drawingElementIDs.append(self.pathPointIDs)
            self.elementTypes[', '.join([str(id) for id in self.pathPointIDs])] = 'path'
            self.elementData[', '.join([str(id) for id in self.pathPointIDs])] = self.pathPointInfo
            self.pathPointIDs = []
            self.pathPoints = []
            self.pathPointInfo = []
            if type(self.shapeID) == list: [self.canvas.delete(id) for id in self.shapeID]
            else: self.canvas.delete(self.shapeID)
            self.undoButton.configure(state='active')
            print(self.shapeID)

    def undo(self):
        if len(self.drawingElementIDs) == 0: return
        if len(self.pointPurgatory) + 1 > 0: self.redoButton.configure(state='active')

        if self.radioVar.get() == 5 and len(self.polylinePointIDs) != 0:
            if len(self.polylinePointIDs) - 1 <= 0 and len(self.drawingElementIDs) - 1 <= 0: self.undoButton.configure(state='disabled')
            
            prevID = self.polylinePointIDs[-1]

            self.canvas.itemconfigure(prevID, state='hidden')
            self.canvas.addtag_withtag('undone', prevID)
            self.pointPurgatory.append(prevID)

            del self.polylinePointIDs[-1]
            
            """
            self.canvas.delete(self.polylinePointIDs[-1])
            self.pointPurgatory.append(self.polylinePointIDs[-1])

            del self.polylinePointIDs[-1]"""
            del self.polylinePoints[-2:]

            self.coords[0:2] = self.polylinePoints[-2:]

            if len(self.polylinePointIDs) - 1 <= 0: self.closeDrawing()

        else:
            if len(self.drawingElementIDs) - 1 <= 0: self.undoButton.configure(state='disabled')
            #print(self.drawingElementIDs)
            #print(self.elementTypes)
            #print(self.canvas.coords(self.drawingElementIDs[-1]))
            #print(self.shapeID)
            
            prevID = self.drawingElementIDs[-1]

            if self.shapeID in self.canvas.find_all(): self.canvas.delete(self.shapeID)

            self.canvas.itemconfigure(prevID, state='hidden')
            self.canvas.addtag_withtag('undone', prevID)
            self.pointPurgatory.append(prevID)

            del self.drawingElementIDs[-1]


            """
            print('Before')
            print(self.canvas.find_all())
            print(self.drawingElementIDs)
            print(self.shapeID)

            

            prevID = self.drawingElementIDs[-1]
            
            if type(prevID) == list: [self.canvas.itemconfigure(id, state='hidden') for id in prevID]#self.canvas.delete(id) for id in prevID]
            else: self.canvas.itemconfigure(prevID, state='hidden')#self.canvas.delete(prevID)
            
            
            if self.shapeID in self.canvas.find_all(): self.canvas.delete(self.shapeID)
            self.pointPurgatory.append(prevID)

            if type(prevID) == list: del self.elementTypes[', '.join([str(id) for id in prevID])]
            else: del self.elementTypes[prevID]
            
            del self.drawingElementIDs[-1]

            print('\nAfter')
            print(self.canvas.find_all())
            print(self.drawingElementIDs)
            print(self.shapeID)
            #self.shapeID = None
            
            """

            #print(self.drawingElementIDs)
            #print(self.elementTypes)
            #print(self.canvas.coords(self.drawingElementIDs[-1]))
            #print(self.shapeID)

    def redo(self):
        if len(self.pointPurgatory) - 1 <= 0: self.redoButton.configure(state='disabled')
        
        if self.radioVar.get() == 5 and len(self.pointPurgatory) != 0:
            if len(self.polylinePointIDs) + 1> 0 and len(self.drawingElementIDs) + 1 > 0: self.undoButton.configure(state='active')
            
            prevID = self.pointPurgatory[-1]

            self.canvas.itemconfigure(prevID, state='normal')
            self.canvas.dtag(prevID, 'undone')
            self.polylinePointIDs.append(prevID)

            coords = self.canvas.coords(prevID)

            [self.polylinePoints.append(coord) for coord in coords[-2:]]
            
            self.coords[0:2] = self.polylinePoints[-2:]

            del self.pointPurgatory[-1]

        else:
            if len(self.drawingElementIDs) + 1 > 0: self.undoButton.configure(state='active')

            prevID = self.pointPurgatory[-1]

            self.canvas.itemconfigure(prevID, state='normal')
            self.canvas.dtag(prevID, 'undone')
            self.drawingElementIDs.append(prevID)

            del self.pointPurgatory[-1]

            """"
            if len(self.pointPurgatory) != 0:
                print(self.pointPurgatory[0])
                self.canvas.itemconfigure(self.pointPurgatory[0], state='normal')
                print(self.canvas.coords(self.pointPurgatory[0]))

            """

    def edit(self):
        if self.isEditing.get(): 
            self.isEditing.set(False)
            self.inf.setEditing(self.isEditing.get())
        else: 
            self.isEditing.set(True)
            self.inf.setEditing(self.isEditing.get())
        self.inf.updateInfoBar()

        if self.radioVar.get() == 6 and self.isEditing.get():
            pathElements = {key: self.elementData[key] for key in self.elementTypes.keys() if self.elementTypes[key] == 'path'}
            if len([val for val in self.elementTypes.values() if val == 'path']) == 0: return

            point = [-10, -10]

            for path in pathElements.keys():
                data = pathElements[path]
                ids = path.split(', ')

                for cmd in data:
                    match cmd[0]:
                        case 'M': 
                            point = [cmd[1], cmd[2]]
                        case 'L': 
                            point = [cmd[1], cmd[2]]
                        case 'C': 
                            prevCurvePoint = [cmd[-4], cmd[-3]]

                            self.editPointIDs.append(self.canvas.create_line(point[0], point[1], cmd[1], cmd[2], fill=self.editPointColour, tags=['edit', 'line']))
                            self.editPointIDs.append(self.edit_create_point([cmd[1], cmd[2]]))

                            point = [cmd[-2], cmd[-1]]

                            self.editPointIDs.append(self.canvas.create_line(point[0], point[1], cmd[-4], cmd[-3], fill=self.editPointColour, tags=['edit', 'line']))
                            self.editPointIDs.append(self.edit_create_point([cmd[-4], cmd[-3]]))
                        case 'S': 
                            point = [cmd[-2], cmd[-1]]

                            self.editPointIDs.append(self.canvas.create_line(point[0], point[1], cmd[1], cmd[2], fill=self.editPointColour, tags=['edit', 'line']))
                            self.editPointIDs.append(self.edit_create_point([cmd[-4], cmd[-3]]))
                        case _: continue

                    id = self.edit_create_point(point)
                    self.editPointIDs.append(id)


            #print(pathElements)
        elif not self.isEditing.get() and len(self.editPointIDs) > 0:
            for id in self.editPointIDs:
                self.canvas.delete(id)
                self.editPointIDs = []

    def edit_create_point(self, point):
        return self.canvas.create_oval(point[0] - self.editPointSize, point[1] - self.editPointSize, point[0] + self.editPointSize, point[1] + self.editPointSize, fill=self.editPointColour, tags=['edit', 'point'])

    def calculateArc(self, coords):
        startX, startY = coords[0], coords[1]
        endX, endY = coords[2], coords[3]
        l = endX - startX
        h = startY - endY

        extent = 90

        if l >= 0 and h >= 0: return [0, extent]
        elif l < 0 and h >= 0: return [90, extent]
        elif l < 0 and h < 0: return [180, extent]
        elif l >= 0 and h < 0: return [270, extent]




    def press(self, e): 
        self.isPressed.set(True)
        self.hasMoved.set(False)
        if self.isEditing.get():
            self.edit_press(e)
            return
        self.coords[0], self.coords[1] = e.x, e.y
        self.pointPurgatory = []
        self.redoButton.configure(state='disabled')

        if self.radioVar.get() == 1:
            if len(self.arcPoints) == 4: self.arcPoints = []
            self.arcPoints.extend([e.x, e.y])

        elif self.radioVar.get() == 5:
            self.polylinePoints.extend(self.coords[0:2])
            
            if len(self.polylinePoints) >= 4:
                id = self.canvas.create_line(self.polylinePoints[-4:])
                #drawingElementIDs.append(id)
                self.polylinePointIDs.append(id)

        elif self.radioVar.get() == 6:
            self.pathPoints.extend(self.coords[0:2])
            if len(self.pathPoints) == 2: self.pathPointInfo.append(['M', self.pathPoints[0], self.pathPoints[1]])
            #if len(self.pathPointInfo) == 0: return
            if self.pathPointInfo[-1][0] == 'C' and len(self.pathPointInfo[-1]) < 5:
                self.pathPointInfo[-1].extend(self.coords[0:2])
            #elif self.pathPointInfo[-1][0] == 'C' and len(self.pathPointInfo[-1]) == 7:
            #    self.pathPointInfo.append(['S', self.pathPoints[-2], self.pathPoints[-1]])
    def edit_press(self, e):
        error = 3

        if self.radioVar.get() == 6: 
            overlapping = self.canvas.find_overlapping(e.x - error, e.y - error, e.x + error, e.y + error)
            structural = self.canvas.find_withtag('edit')

            self.editSelectedIDs = [id for id in overlapping if id in structural]
            
            possiblePathKeys = []
            pathKeys = [key for key in self.elementTypes.keys() if self.elementTypes[key] == 'path']
            print('pathKeys:', pathKeys)


            for key in pathKeys:
                data = []
                [data.extend(cmd) for cmd in self.elementData[key]]
                data = [d for d in data if type(d) != str]
                print('data:', data)
                points = [[data[i], data[i+1]] for i in range(0, len(data) - 1, 2)]
                print('points:', points)

                for id in self.editSelectedIDs:
                    selectedCoords = self.canvas.coords(id)
                    x = selectedCoords[0] + self.editPointSize
                    y = selectedCoords[1] + self.editPointSize

                    self.edit_editingPoint[0] = x
                    self.edit_editingPoint[1] = y

                    if self.edit_editingPoint in points: possiblePathKeys.append(key)
                
            print('possible path keys:', possiblePathKeys)

            count = {key: 0 for key in possiblePathKeys}
            for key in possiblePathKeys: count[key] += 1
            
            self.edit_key = max(count)

            canvasIDs = self.keyToList(self.edit_key)
            cmdType, prevCmdData, cmdData, nextCmdData = self.cmdFinder(self.edit_key, self.edit_editingPoint)
            cmdIndex = self.elementData[self.edit_key].index(cmdData) - 1 # To account for difference regarding the move command that isn't shown in the ids
            if nextCmdData != []: nextCmdIndex = self.elementData[self.edit_key].index(nextCmdData) - 1


            [self.edit_shapeID.append(canvasIDs[i]) for i in range(len(canvasIDs)) if i in [cmdIndex, nextCmdIndex]]

            #for l in canvasIDs:
            #    self.edit_shapeID.append(l)
                #[self.canvas.delete(id) for id in l if l in canvasIDs[0:2]]


    def release(self, e): 
        self.isPressed.set(False)
        if self.isEditing.get():
            self.edit_release(e)
            return
        self.coords[2], self.coords[3] = e.x, e.y

        if self.radioVar.get() == 0: 
            id = self.canvas.create_line(list(self.coords))
            print('LINE ID:', id)
            self.drawingElementIDs.append(id)
            self.elementTypes[id] = 'line'
        elif self.radioVar.get() == 1: self.drawingElementIDs.append(self.canvas.create_arc(list(self.coords), start=self.calculateArc(self.coords)[0], extent=self.calculateArc(self.coords)[1], style='arc'))
        elif self.radioVar.get() == 2: 
            id = self.canvas.create_oval(list(self.coords))
            self.drawingElementIDs.append(id)
            self.elementTypes[id] = 'ellipse'
        elif self.radioVar.get() == 3: 
            id = self.canvas.create_rectangle(list(self.coords))
            self.drawingElementIDs.append(id)
            self.elementTypes[id] = 'rectangle'
        elif self.radioVar.get() == 4: self.drawingElementIDs.append(self.freeDrawPointIDs)
        
        elif self.radioVar.get() == 6:

            if not self.hasMoved.get():

                if len(self.pathPoints) >= 4:
                    id = self.canvas.create_line(self.pathPoints[-4:])
                    self.pathPointInfo.append(['L', self.pathPoints[-2], self.pathPoints[-1]])
                    self.pathPointIDs.append(id)

            else:
                if self.pathPointInfo[-1][0] not in ['C', 'S']:
                    if self.pathPointInfo[-1][0] in ['L', 'M']: 
                        self.canvas.delete(self.shapeID)
                        xStart, yStart = self.pathPoints[-4], self.pathPoints[-3]
                        x1, y1 = self.pathPoints[-4], self.pathPoints[-3]
                        x2, y2 = self.coords[-2:]
                        xEnd, yEnd = self.pathPoints[-2:]

                        self.pathPointInfo.append(['C', x1, y1, x2, y2, xEnd, yEnd])

                        xPoints, yPoints = self.cubicBezierCurvePoints(xStart, yStart, x1, y1, x2, y2, xEnd, yEnd)
                        ids = self.canvasPointSmoother(xPoints, yPoints)
                        self.pathPointIDs.append(ids)

                        #id = self.canvas.create_line(self.pathPoints[-4], self.pathPoints[-3], self.pathPoints[-2], self.pathPoints[-1])
                        #self.pathPointIDs.append(id)
                        #self.pathPointInfo.append(['L', self.pathPoints[-2], self.pathPoints[-1]])
                    #else: self.pathPointInfo.append(['C', self.coords[-2], self.coords[-1]])
                
                elif ( len(self.pathPointInfo[-1]) == 7 and self.pathPointInfo[-1][0] == 'C' ) or ( len(self.pathPointInfo[-1]) == 5 and self.pathPointInfo[-1][0] == 'S' ):
                    self.pathPointInfo.append(['S', self.coords[-2], self.coords[-1], self.pathPoints[-2], self.pathPoints[-1]])

                    from pointList import Vec2D
                    vecStart = Vec2D(self.pathPoints[-4], self.pathPoints[-3], 'rec')
                    vecPrevX1 = Vec2D(self.pathPointInfo[-2][-4], self.pathPointInfo[-2][-3], 'rec')

                    relVec = -1*vecStart + vecPrevX1
                    oppVec = -1*relVec
                    posVec = vecStart + oppVec

                    xStart, yStart = vecStart.vec.x, vecStart.vec.y
                    x1, y1 = posVec.vec.x, posVec.vec.y
                    x2, y2 = self.coords[-2:]
                    xEnd, yEnd = self.pathPoints[-2:]

                    xPoints, yPoints = self.cubicBezierCurvePoints(xStart, yStart, x1, y1, x2, y2, xEnd, yEnd)
                    ids = self.canvasPointSmoother(xPoints, yPoints)
                    self.pathPointIDs.append(ids)

                    
                elif len(self.pathPointInfo[-1]) == 5 and self.pathPointInfo[-1][0] == 'C':
                    self.pathPointInfo[-1].insert(-2, self.coords[-2])
                    self.pathPointInfo[-1].insert(-2, self.coords[-1])

                    xStart, yStart = self.pathPointInfo[-2][-2:]
                    x1, y1 = self.pathPointInfo[-1][1:3]
                    x2, y2 = self.coords[-2:]
                    xEnd, yEnd = self.pathPointInfo[-1][-2:]
                    
                    xPoints, yPoints = self.cubicBezierCurvePoints(xStart, yStart, x1, y1, x2, y2, xEnd, yEnd)
                    ids = self.canvasPointSmoother(xPoints, yPoints)
                    self.pathPointIDs.append(ids)


                """
                if len(self.pathPointInfo) == 0 or self.pathPointInfo[-1][0] not in ['C', 'S']: self.pathPointInfo.append(['C', self.coords[-2], self.coords[-1]])
                elif len(self.pathPointInfo[-1]) >= 7 or len(self.pathPointInfo[-2]) >= 7: # <-------------------------
                    if self.pathPointInfo[-2][0] == 'C': # <--------------------------
                        from pointList import Vec2D
                        vecStart = Vec2D(self.pathPointInfo[-2][-2], self.pathPointInfo[-2][-1], 'rec')
                        vecPrevX1 = Vec2D(self.pathPointInfo[-2][-4], self.pathPointInfo[-2][-3], 'rec')

                        relVec = -1*vecStart + vecPrevX1
                        oppVec = -1*relVec
                        posVec = vecStart + oppVec
                        
                        self.pathPointInfo[-1].insert(-2, posVec.vec.x)
                        self.pathPointInfo[-1].insert(-2, posVec.vec.y)

                        print('Inserted')
                        print(self.pathPointInfo)

                        xStart, yStart = self.pathPointInfo[-2][-2:]
                        x1, y1 = posVec.vec.x, posVec.vec.y
                        x2, y2 = self.coords[-2:]
                        xEnd, yEnd = self.pathPointInfo[-1][-2:]

                        xPoints, yPoints = self.cubicBezierCurvePoints(xStart, yStart, x1, y1, x2, y2, xEnd, yEnd)
                        self.shapeID = self.canvasPointSmoother(xPoints, yPoints)


                        self.pathPointInfo.append([])
                    else: self.pathPointInfo.append(['C', self.coords[-2], self.coords[-1]])
                else: 
                    self.pathPointInfo[-1].insert(-2, self.coords[-2])
                    self.pathPointInfo[-1].insert(-2, self.coords[-1])

                    xStart, yStart = self.pathPointInfo[-2][-2:]
                    x1, y1 = self.pathPointInfo[-1][1:3]
                    x2, y2 = self.coords[-2:]
                    xEnd, yEnd = self.pathPointInfo[-1][-2:]
                    
                    xPoints, yPoints = self.cubicBezierCurvePoints(xStart, yStart, x1, y1, x2, y2, xEnd, yEnd)
                    ids = self.canvasPointSmoother(xPoints, yPoints)
                    self.pathPointIDs.append(ids)"""

                """elif len(self.pathPointInfo[-1]) >= 7: 
                    if self.pathPointInfo[-1][0] == 'C':
                        xStart, yStart = self.pathPointInfo[-2][-2:]
                        x1, y1 = self.pathPointInfo[-1][1:3]
                        x2, y2 = self.coords[-2:]
                        xEnd, yEnd = self.pathPointInfo[-1][-2:]
                        
                        xPoints, yPoints = self.cubicBezierCurvePoints(xStart, yStart, x1, y1, x2, y2, xEnd, yEnd)
                        ids = self.canvasPointSmoother(xPoints, yPoints)
                        self.pathPointIDs.append(ids)

                        print('self.shapeID:', self.shapeID)

                    self.pathPointInfo.append(['C', self.coords[-2], self.coords[-1]])"""

            print('pathPointInfo:', self.pathPointInfo)
            

        self.hasMoved.set(False)
    def edit_release(self, e):
        if self.radioVar.get() == 6:
            pathData = self.elementData[self.edit_key]
            
            pathIDs = self.keyToList(self.edit_key)


            self.edit_create_point([e.x, e.y])

            #print('\nDrawingElementIDs:\n', self.drawingElementIDs[0])
            pathIndex = -1
            cmdIndexes = []
            newData = []

            if pathIDs in self.drawingElementIDs: pathIndex = self.drawingElementIDs.index(pathIDs)
            for cmd in self.edit_info.keys():
                data = cmd.split(', ')
                convertedCmd = []
                convertedCmd.append(data[0])
                [convertedCmd.append(float(point)) for point in data[1:]]

                if convertedCmd in pathData: 
                    cmdIndexes.append(pathData.index(convertedCmd))
                    newData.append(self.edit_info[cmd])

            #[cmdIndexes.append(pathData.index([float(point) for point in cmd.split(', ')[1:]].insert(0, cmd.split(', ')[0]))) for cmd in self.edit_info.keys() if [float(cmd.split(', ')[i]) for i in range(len(cmd.split(', ')))] in pathData]
            
            print(cmdIndexes)
            for i in range(len(cmdIndexes)):
                #self.elementData[self.edit_key]
                #self.elementData[self.edit_key][cmdIndexes[i]] = newData[i]
                
                print(pathData[cmdIndexes[i]])
                print(newData[i])
                print(pathIDs[cmdIndexes[i]])

                cmdType = pathData[cmdIndexes[i]][0]
                prevCmdData = []
                if cmdIndexes[i] - 1 >= 0: prevCmdData = pathData[cmdIndexes[i] - 1]

                cmdData = pathData[cmdIndexes[i]]
                nextCmdData = []
                if cmdIndexes[i] + 1 <= len(pathData): nextCmdData = pathData[cmdIndexes[i] + 1]


                newCmdIDs = []

                from pointList import Vec2D

                if cmdType == 'C':
                    xPoints, yPoints = self.cubicBezierCurvePoints(prevCmdData[-2], prevCmdData[-1], cmdData[1], cmdData[2], cmdData[3], cmdData[4], e.x, e.y)
                    newCmdIDs.append(self.canvasPointSmoother(xPoints, yPoints))
                    
                elif cmdType == 'S':
                    vecStart = Vec2D(prevCmdData[-2], prevCmdData[-1], 'rec')
                    vecPrevX1 = Vec2D(prevCmdData[-4], prevCmdData[-3], 'rec')

                    relVec = -1*vecStart + vecPrevX1
                    oppVec = -1*relVec
                    posVec = vecStart + oppVec

                    xPoints, yPoints = self.cubicBezierCurvePoints(vecStart.vec.x, vecStart.vec.y, posVec.vec.x, posVec.vec.y, cmdData[-4], cmdData[-3], e.x, e.y)
                    newCmdIDs.append(self.canvasPointSmoother(xPoints, yPoints))

                if nextCmdData[0] == 'S':
                    vecStart = Vec2D(e.x, e.y, 'rec')
                    vecPrevX1 = Vec2D(cmdData[-4], cmdData[-3], 'rec')

                    relVec = -1*vecStart + vecPrevX1
                    oppVec = -1*relVec
                    posVec = vecStart + oppVec

                    xPoints, yPoints = self.cubicBezierCurvePoints(e.x, e.y, posVec.vec.x, posVec.vec.y, nextCmdData[-4], nextCmdData[-3], nextCmdData[-2], nextCmdData[-1])
                    newCmdIDs.append(self.canvasPointSmoother(xPoints, yPoints))

                pathIDs[cmdIndexes[i]] = newCmdIDs[0]
                pathIDs[cmdIndexes[i] + 1] = newCmdIDs[1]

                pathData[cmdIndexes[i]] = newData[i]

                self.drawingElementIDs[pathIndex] = pathIDs

                self.elementTypes[', '.join([str(id) for id in pathIDs])] = self.elementTypes[self.edit_key]
                del self.elementTypes[self.edit_key]

                self.elementData[', '.join([str(id) for id in pathIDs])] = pathData
                del self.elementData[self.edit_key]

    def mousePos(self, e):
        widget = e.widget
        self.hasMoved.set(True)


        self.inf.setMousePos((e.x, e.y))
        self.inf.setID(widget.find_overlapping(x1=e.x-2, y1=e.y-2, x2=e.x+2, y2=e.y+2))
        self.inf.updateInfoBar()
        
        if self.isEditing.get():
            self.edit_mousePos(e)
            return

        if self.isPressed.get():
            self.coords[2], self.coords[3] = e.x, e.y
            
            if self.radioVar.get() == 0: 
                if self.shapeID != None: widget.delete(self.shapeID)
                self.shapeID = widget.create_line(list(self.coords))
            elif self.radioVar.get() == 1:
                if self.shapeID != None: widget.delete(self.shapeID)
                self.shapeID = widget.create_arc(list(self.coords), start=self.calculateArc(self.coords)[0], extent=self.calculateArc(self.coords)[1], style='arc')
            elif self.radioVar.get() == 2:
                if self.shapeID != None: widget.delete(self.shapeID)
                self.shapeID = widget.create_oval(list(self.coords))
            elif self.radioVar.get() == 3:
                if self.shapeID != None: widget.delete(self.shapeID)
                self.shapeID = widget.create_rectangle(list(self.coords))
            elif self.radioVar.get() == 4:
                self.freeDrawPointIDs.append(self.canvas.create_oval(e.x, e.y, e.x, e.y, width=3))
                if len(self.freeDrawPointIDs) > 1: 
                    prevCoords = self.canvas.coords(self.freeDrawPointIDs[-2])[0:2]    
                    widget.create_line(list(prevCoords + list(self.coords[2:])), width=3)


            elif self.radioVar.get() == 6:
                if self.shapeID != None and type(self.shapeID) == list: [widget.delete(id) for id in self.shapeID]
                elif self.shapeID != None: widget.delete(id)
                #self.shapeID = widget.create_line(self.pathPoints[-2:] + list(self.coords[-2:]))

                
                if self.pathPointInfo[-1][0] in ['L', 'M']: 
                    
                    xStart, yStart = self.pathPoints[-4], self.pathPoints[-3]
                    x1, y1 = self.pathPoints[-4], self.pathPoints[-3]
                    x2, y2 = e.x, e.y
                    xEnd, yEnd = self.pathPoints[-2:]

                    xPoints, yPoints = self.cubicBezierCurvePoints(xStart, yStart, x1, y1, x2, y2, xEnd, yEnd)
                    self.shapeID = self.canvasPointSmoother(xPoints, yPoints)

                elif ( len(self.pathPointInfo[-1]) == 7 and self.pathPointInfo[-1][0] == 'C' ) or ( len(self.pathPointInfo[-1]) == 5 and self.pathPointInfo[-1][0] == 'S' ):

                    from pointList import Vec2D
                    vecStart = Vec2D(self.pathPoints[-4], self.pathPoints[-3], 'rec')
                    vecPrevX1 = Vec2D(self.pathPointInfo[-1][-4], self.pathPointInfo[-1][-3], 'rec')

                    relVec = -1*vecStart + vecPrevX1
                    oppVec = -1*relVec
                    posVec = vecStart + oppVec

                    xStart, yStart = vecStart.vec.x, vecStart.vec.y
                    x1, y1 = posVec.vec.x, posVec.vec.y
                    x2, y2 = self.coords[-2:]
                    xEnd, yEnd = self.pathPoints[-2:]

                    xPoints, yPoints = self.cubicBezierCurvePoints(xStart, yStart, x1, y1, x2, y2, xEnd, yEnd)
                    self.shapeID = self.canvasPointSmoother(xPoints, yPoints)

                    
                elif len(self.pathPointInfo[-1]) == 5 and self.pathPointInfo[-1][0] == 'C':

                    xStart, yStart = self.pathPointInfo[-2][-2:]
                    x1, y1 = self.pathPointInfo[-1][1:3]
                    x2, y2 = self.coords[-2:]
                    xEnd, yEnd = self.pathPointInfo[-1][-2:]
                    
                    xPoints, yPoints = self.cubicBezierCurvePoints(xStart, yStart, x1, y1, x2, y2, xEnd, yEnd)
                    self.shapeID = self.canvasPointSmoother(xPoints, yPoints)


                """from shapePath import CubicCurve
                if len(self.pathPointInfo) < 2: return
                if len(self.pathPointInfo[-1]) < 7:

                    xStart, yStart = self.pathPointInfo[-2][-2:]
                    x1, y1 = self.pathPointInfo[-1][1:3]
                    x2, y2 = self.coords[-2:]#self.pathPointInfo[-1][3:5]
                    xEnd, yEnd = self.pathPointInfo[-1][-2:]

                    #testCurve.xStart = [testCurve.xStart]
                    #testCurve.yStart = [testCurve.yStart]
                    #testCurve.x1 = [testCurve.x1]
                    #testCurve.y1 = [testCurve.y1]
                    #testCurve.x2 = [testCurve.x2]
                    #testCurve.y2 = [testCurve.y2]
                    #testCurve.xEnd = [testCurve.xEnd]
                    #testCurve.yEnd = [testCurve.yEnd]

                    xPoints, yPoints = self.cubicBezierCurvePoints(xStart, yStart, x1, y1, x2, y2, xEnd, yEnd)
                    self.shapeID = self.canvasPointSmoother(xPoints, yPoints)

                elif len(self.pathPointInfo[-1]) == 7 and self.pathPointInfo[-1][0] == 'C':
                    from pointList import Vec2D
                    vecStart = Vec2D(self.pathPointInfo[-2][-2], self.pathPointInfo[-2][-1], 'rec')
                    vecPrevX1 = Vec2D(self.pathPointInfo[-2][-4], self.pathPointInfo[-2][-3], 'rec')

                    relVec = -1*vecStart + vecPrevX1
                    oppVec = -1*relVec
                    posVec = vecStart + oppVec
                    
                    xStart, yStart = self.pathPointInfo[-2][-2:]
                    x1, y1 = posVec.vec.x, posVec.vec.y
                    x2, y2 = self.coords[-2:]
                    xEnd, yEnd = self.pathPointInfo[-1][-2:]

                    xPoints, yPoints = self.cubicBezierCurvePoints(xStart, yStart, x1, y1, x2, y2, xEnd, yEnd)
                    self.shapeID = self.canvasPointSmoother(xPoints, yPoints)"""


            elif self.radioVar.get() == 9:
                xpad = 2
                ypad = 2
                
                closestElements = widget.find_overlapping(x1=e.x-xpad, y1=e.y-ypad, x2=e.x+xpad, y2=e.y+ypad)
                if len(closestElements) > 0:
                    widget.delete(closestElements[0])
                    if closestElements[0] in self.drawingElementIDs: 
                        del self.drawingElementIDs[self.drawingElementIDs.index(closestElements[0])]
                    del self.elementTypes[closestElements[0]]
        
        else:
            if self.radioVar.get() == 5: 
                if self.coords[0] != 0 and self.coords[1] != 0: self.coords[2], self.coords[3] = e.x, e.y

                if self.shapeID != None: widget.delete(self.shapeID)
                self.shapeID = widget.create_line(list(self.coords))

            elif self.radioVar.get() == 6:
                if self.shapeID != None and type(self.shapeID) == list: [widget.delete(id) for id in self.shapeID]
                elif self.shapeID != None: widget.delete(self.shapeID)


                if len(self.pathPointInfo) == 0: return
                if self.pathPointInfo[-1][0] not in ['C', 'S']:
                    if self.pathPointInfo[-1][0] in ['L', 'M']: 

                        xStart, yStart = self.pathPoints[-2], self.pathPoints[-1]
                        x1, y1 = self.pathPoints[-2], self.pathPoints[-1]
                        x2, y2 = e.x, e.y
                        xEnd, yEnd = e.x, e.y

                        xPoints, yPoints = self.cubicBezierCurvePoints(xStart, yStart, x1, y1, x2, y2, xEnd, yEnd)
                        self.shapeID = self.canvasPointSmoother(xPoints, yPoints)
                    
                    #else: self.shapeID = widget.create_line(self.pathPoints[-2], self.pathPoints[-1], e.x, e.y)
                
                elif ( len(self.pathPointInfo[-1]) == 7 and self.pathPointInfo[-1][0] == 'C' ) or ( len(self.pathPointInfo[-1]) == 5 and self.pathPointInfo[-1][0] == 'S' ):

                    from pointList import Vec2D
                    vecStart = Vec2D(self.pathPoints[-2], self.pathPoints[-1], 'rec')
                    vecPrevX1 = Vec2D(self.pathPointInfo[-1][-4], self.pathPointInfo[-1][-3], 'rec')

                    relVec = -1*vecStart + vecPrevX1
                    oppVec = -1*relVec
                    posVec = vecStart + oppVec

                    xStart, yStart = vecStart.vec.x, vecStart.vec.y
                    x1, y1 = posVec.vec.x, posVec.vec.y
                    x2, y2 = e.x, e.y
                    xEnd, yEnd = e.x, e.y

                    xPoints, yPoints = self.cubicBezierCurvePoints(xStart, yStart, x1, y1, x2, y2, xEnd, yEnd)
                    self.shapeID = self.canvasPointSmoother(xPoints, yPoints)

                elif len(self.pathPointInfo[-1]) == 3 and self.pathPointInfo[-1][0] == 'C':
                    xStart, yStart = self.pathPoints[-2:]
                    x1, y1 = self.pathPointInfo[-1][1:3]
                    x2, y2 = e.x, e.y
                    xEnd, yEnd = e.x, e.y
                    
                    xPoints, yPoints = self.cubicBezierCurvePoints(xStart, yStart, x1, y1, x2, y2, xEnd, yEnd)
                    self.shapeID = self.canvasPointSmoother(xPoints, yPoints)


        #removeColour = tk.Button(drawingFrame, text='Clear Canvas', command=lambda: [[p.configure(background='blue') for p in r] for r in pixels])
        #removeColour.pack()
    def edit_mousePos(self, e):
        if self.isPressed.get():
            if self.radioVar.get() == 6:
                [self.canvas.delete(id) for id in self.editSelectedIDs]

                if len(self.edit_shapeID) > 0: 
                    for id in self.edit_shapeID:
                        if type(id) != list: 
                            self.canvas.delete(id)
                        else: [self.canvas.delete(d) for d in id]



                self.edit_shapeID.append(self.edit_create_point([e.x, e.y]))

                cmdType, prevCmdData, cmdData, nextCmdData = self.cmdFinder(self.edit_key, self.edit_editingPoint)

                #print('cmdData:', cmdData)
                #print('prevCmdData:', prevCmdData)
                from pointList import Vec2D

                if cmdType == 'C':
                    xPoints, yPoints = self.cubicBezierCurvePoints(prevCmdData[-2], prevCmdData[-1], cmdData[1], cmdData[2], cmdData[3], cmdData[4], e.x, e.y)
                    self.edit_shapeID.append(self.canvasPointSmoother(xPoints, yPoints))
                    
                    self.edit_info[', '.join([str(d) for d in cmdData])] = [cmdType, cmdData[1], cmdData[2], cmdData[3], cmdData[4], e.x, e.y]
                elif cmdType == 'S':
                    vecStart = Vec2D(prevCmdData[-2], prevCmdData[-1], 'rec')
                    vecPrevX1 = Vec2D(prevCmdData[-4], prevCmdData[-3], 'rec')

                    relVec = -1*vecStart + vecPrevX1
                    oppVec = -1*relVec
                    posVec = vecStart + oppVec

                    xPoints, yPoints = self.cubicBezierCurvePoints(vecStart.vec.x, vecStart.vec.y, posVec.vec.x, posVec.vec.y, cmdData[-4], cmdData[-3], e.x, e.y)
                    self.edit_shapeID.append(self.canvasPointSmoother(xPoints, yPoints))

                    self.edit_info[', '.join([str(d) for d in cmdData])] = [cmdType, cmdData[-4], cmdData[-3], e.x, e.y]

                if nextCmdData[0] == 'S':
                    vecStart = Vec2D(e.x, e.y, 'rec')
                    vecPrevX1 = Vec2D(cmdData[-4], cmdData[-3], 'rec')

                    relVec = -1*vecStart + vecPrevX1
                    oppVec = -1*relVec
                    posVec = vecStart + oppVec

                    xPoints, yPoints = self.cubicBezierCurvePoints(e.x, e.y, posVec.vec.x, posVec.vec.y, nextCmdData[-4], nextCmdData[-3], nextCmdData[-2], nextCmdData[-1])
                    self.edit_shapeID.append(self.canvasPointSmoother(xPoints, yPoints))

                    #self.edit_info[', '.join([str(d) for d in cmdData])] = [cmdType, nextCmdData[-4], nextCmdData[-3], nextCmdData[-2], nextCmdData[-1]]


    def cubicBezierCurvePoints(self, xStart, yStart, x1, y1, x2, y2, xEnd, yEnd):
        xPoints = []
        yPoints = []

        for t in range(0, const.CURVE_SAMPLE_POINTS + 1, 1):
            t /= const.CURVE_SAMPLE_POINTS
            xPoint = (((1 - t) ** 3) * xStart) + (3 * t * ((1 - t) ** 2) * (x1)) + (
                    3 * (t ** 2) * (1 - t) * (x2)) + (t ** 3 * (xEnd))
            yPoint = (((1 - t) ** 3) * yStart) + (3 * t * ((1 - t) ** 2) * (y1)) + (
                    3 * (t ** 2) * (1 - t) * (y2)) + (t ** 3 * (yEnd))
            xPoints.append(xPoint)
            yPoints.append(yPoint)

        return xPoints, yPoints

    def canvasPointSmoother(self, xArray, yArray):
        idList = []
        for i in range(int(len(xArray) - 1)):
            idList.append(self.canvas.create_line(xArray[i], yArray[i], xArray[i+1], yArray[i+1]))

        return idList

    def keyToList(self, key):
        pathIDs = key
        insides = re.compile(r'''\[
                    ([ ,0-9]+)
                    \]''', re.VERBOSE)
        search = re.findall(insides, pathIDs)
        
        IDs = []
        [IDs.append([int(id) for id in found.split(', ')]) for found in search]

        return IDs

    def cmdFinder(self, key, point):
        cmdType = ''
        prevCmdData = []
        cmdData = []
        nextCmdData = []

        if key != '':
            data = self.elementData[key]
            
            for i in range(len(data)):
                cmd = data[i]
                if i != 0: prevCmdData = data[i-1]
                if i != len(data): nextCmdData = data[i+1]

                points = []
                for i in range(len(cmd[1:]) - 1):
                    points.append([cmd[i + 1], cmd[i + 2]])

                if point in points:
                    cmdData = cmd
                    cmdType = cmd[0]
                    break

        return cmdType, prevCmdData, cmdData, nextCmdData

    def get_header(self, svgHeight, svgWidth):
        return f'<svg height=\"{svgHeight}\" width=\"{svgWidth}\">'
        
    def get_footer(self):
        return '</svg>'


    def saveAsFile(self):
        svgElements = []
        svgElements.append(self.get_header(self.canvas.cget('width'), self.canvas.cget('height')))

        print(self.drawingElementIDs)
        for id in self.drawingElementIDs:
            if 'undone' in self.canvas.gettags(id): continue
            if type(id) != list:
                x1, y1, x2, y2 = self.canvas.coords(id)
                width = x2-x1
                height = y2-y1
                centre = [x1 + width/2, y1 + height/2]
                
                if self.elementTypes[id] == 'rectangle':
                    if x1 > x2: top_left_x = x2
                    else: top_left_x = x1

                    if y1 < y2: top_left_y = y2
                    else: top_left_y = y1

                    svgElements.append(str(self.svg(self.elementTypes[id], x=top_left_x, y=top_left_y, width=width, height=height)))

                elif self.elementTypes[id] == 'line':
                    svgElements.append(str(self.svg(self.elementTypes[id], x=x1, y=y1, x2=x2, y2=y2)))

                elif self.elementTypes[id] == 'ellipse':
                    svgElements.append(str(self.svg(self.elementTypes[id], x=centre[0], y=centre[1], width=width, height=height)))

                #elif elementTypes[id] == 'arc':
                    #svgElements.append(str(svg(elementTypes[id], x)))
            else:
                key = ', '.join([str(i) for i in id])

                if self.elementTypes[key] == 'polyline':
                    pointData = []
                    [pointData.extend(self.canvas.coords(i)[0:2]) for i in id]
                    pointData.extend(self.canvas.coords(id[-1])[2:4])
                    svgElements.append(str(self.svg(self.elementTypes[key], pointData=pointData)))

                elif self.elementTypes[key] == 'path':
                    svgElements.append(str(self.svg(self.elementTypes[key], pointData=self.elementData[key])))

        svgElements.append(self.get_footer())

        data = '\n'.join(svgElements)

        self.parent.fileSaveCheck('./sgvFiles', 'svg', data)
        # io.writeFileData('./sgvFiles/savedFile.svg', data)
            

    class svg():
        def __init__(self, shape, x=None, y=None, x2=None, y2=None, width=0, height=0, pointData: list =[]):
            self.shape = shape
            self.x = x
            self.y = y
            self.x2 = x2
            self.y2 = y2
            self.width = width
            self.height = height
            self.pointData = pointData

        def __str__(self):
            if self.shape == 'rectangle':
                return f'<rect x=\"{self.x}\" y=\"{self.y}\" width=\"{self.width}\" height=\"{self.height}\"/>'
            elif self.shape == 'line':
                return f'<line x1=\"{self.x}\" x2=\"{self.x2}\" y1=\"{self.y}\" y2=\"{self.y2}\"/>'
            elif self.shape == 'ellipse':
                return f'<ellipse cx=\"{self.x}\" cy=\"{self.y}\" rx=\"{self.width/2}\" ry=\"{self.height/2}\"/>'
            
            
            elif self.shape == 'polyline':
                return f'<polyline points=\"{" ".join([ str(point) for point in self.pointData])}\"/>'
            elif self.shape == 'path':
                return f'<path d=\"{" ".join( [ " ".join([ str(arg) for arg in cmd]) for cmd in self.pointData] )}\"/>'

    class info():
        def __init__(self, infoBar, infoBarText, selected=''):
            self.infoBar = infoBar
            self.infoBarText = infoBarText
            self.selected = selected
            self.mousePos = (0, 0)
            self.ID = 0
            self.editing = False
            self.textCreator()
        
        def textCreator(self):
            self.text = {

                'Currently Selected: ': self.selected,
                'Mouse Pos: ': self.mousePos,
                'Id: ': self.ID,
                'Currently Editing: ': self.editing

            }
            
            
        def setMousePos(self, mousePos):
            self.mousePos = mousePos
            self.text['Mouse Pos: '] = self.mousePos

        def setSelected(self, selected):
            self.selected = selected
            self.text['Currently Selected: '] = self.selected

        def setID(self, ID):
            self.ID = ID
            self.text['Id: '] =self.ID

        def setEditing(self, editing):
            self.editing = editing
            self.text['Currently Editing: '] = self.editing

        def updateInfoBar(self):
            combinedText = []
            for key in self.text:
                combinedText.append(key + str(self.text[key]))

            self.infoBarText.set('\n'.join(combinedText))


if __name__ == '__main__':
    gui = GUI()
    gui.mainloop()