"""
parseData.py - parse file string into objects

"""
# Libraries
from gCodeConverterObjects import Shape

#Constants
SHAPE_LIST = ["path", "rect", "circle", "ellipse", "line", "polyline", "polygon"]  # not  implemented: , "line", "polyline", "polygon"]
FORMAT_SYSTAX = ["svg"]

"""Gets data from file string and retruns dict"""
def getObjData(objData):
    # Make object data into list
    objData = objData.split("\"")
    objDataClean = []
    for item in objData:
        item = item.strip()
        item = item.strip("=")
        item = item.strip()
        if len(objDataClean) == 0:
            item = item.split()
            item = item[1].strip()
        objDataClean.append(item)
    objDataClean = objDataClean[:-1]
    # Make list into dict
    objDataDict = {}
    for index, item in enumerate(objDataClean):
        if index%2 == 0:
            objDataDict[item] = objDataClean[index+1]
    # Removes ID tag from data
    try:
        del objDataDict["id"]
    except KeyError as err:
        if str(err) != "'id'":
            raise KeyError(str(err))
    return objDataDict

"""Creates shape objects from dict"""
def createShape(shapeName, shapeDataDict, gData):
    # Note: some objects may not exist
    newShape = Shape(shapeName)
    for item in gData:
        itemAdded = newShape.add(item, gData[item])
        if itemAdded:
            print("Successfully added\t" + str(item) + "\tto " + str(shapeName))
        else:
            print("Could not find\t\t" + str(item) + "\tin " + str(shapeName))
    for item in shapeDataDict:
        itemAdded = newShape.add(item, shapeDataDict[item])
        if itemAdded:
            print("Successfully added\t" + str(item) + "\tto " + str(shapeName))
        else:
            print("Could not find\t\t" + str(item) + "\tin " + str(shapeName))
    return newShape

"""Split file string into shape list"""
def splitStrip(fileText):
    fileList = fileText.split("<")
    fileListStrip = []
    for item in fileList:
        item = item.strip()
        fileListStrip.append(item)
    return fileListStrip

"""Create objects from shape list"""
def objCreate(shapeStrList):
    shapeObjList = []
    gData = {}
    for item in shapeStrList:
        if item != "":
            objName = item.split()[0]
            if objName in SHAPE_LIST:
                # Create shape object
                print("Creating object: " + objName)
                objDict = getObjData(item)
                shapeObj = createShape(objName, objDict, gData)
                shapeObjList.append(shapeObj)
            elif objName in FORMAT_SYSTAX:
                print(objName + " format")
            elif objName == "g":
                # Creates g container
                print("Open g container")
                gData = getObjData(item)
            elif objName == "/g>":
                # Close g container
                print("Close g container")
                gData = {}
            elif "/" in objName:
                print("Closing: " + str(objName[1:-1]))
            else:
                print("What dis: " + str(objName))
    
    return shapeObjList

