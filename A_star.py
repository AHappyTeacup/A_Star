'''
Python and PyGame A* algorithm demonstration.
Path finding along a Hexagon tesselation.

Version 1.0.0

Python Version: 3.2.3
Pygame Version: 1.9

Click a Start point,
Click an End point.
Additional Hexagon clicks will create 'barriers' that the algorithm will have to work around.
'Enter' triggers the algorithm.
'Backspace' afterwards will reset the program.
'exit' or click the 'x' to terminate.

The distance function is straightforward: Euclidean 2-space distance. 
Might need to change this.

Possible future improvements:
    * Modifying the distance function?
    * Click-and-drag to create maze?
'''

import random, pygame, sys, math
from pygame.locals import *

#Window dimensions.
WINDOWWIDTH = 1080
WINDOWHEIGHT = 720

#Set the display
DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))

#RGB colour chart.
#                R,   G,   B.
WHITE       = (255, 255, 255)
BLACK       = (  0,   0,   0)
RED         = (255,   0,   0)
GREEN       = (  0, 255,   0)
BLUE        = (  0,   0, 255)
YELLOW      = (255, 255,   0)
DARKGREEN   = (  0, 155,   0)
DARKGRAY    = ( 40,  40,  40)

#Create a clock object and set the Frames Per Second.
FPS = 30
FPSCLOCK = pygame.time.Clock()

#This prevents the Optimisation function from entering an infinite recursion
OptList = []

#Booleans. And other things.
SetStart = True
startid = -1
SetEnd = True
endid = -1
RunAlg = False
currentNode = -1

def ReInitialise():
    global SetStart, startid, SetEnd, endid, RunAlg, currentNode, HexagonList
    SetStart = True
    startid = -1
    SetEnd = True
    endid = -1
    RunAlg = False
    currentNode = -1
    HexagonList = []
    SetHexagons()

def main():
    global HexagonList, SideLength, RunAlg
    #Create a list for 'Hexagon objects'. Dictionaries which hold the details for all the hexagons.
    HexagonList = []
    # initialise audio
    pygame.mixer.pre_init(22050, -16, 2, 512)
    #initialise pygame
    pygame.init()
    pygame.display.set_caption('A*.')
    #Hexagon sidelength.
    SideLength = 20

    #Fills the HexagonList
    SetHexagons()

    while True:
        #Set the background colour to black.
        DISPLAYSURF.fill(BLACK)

        #Tessellate the screen with Hexagons.
        PrintHexagons()

       #Runs computation.
        if RunAlg:
            Astar()

        #Allows user to continue tweaking their maze.
        else:
            checkInput()

        #Clear screen and delay if screen is refreshing too fast.
        pygame.display.update()
        FPSCLOCK.tick(FPS)

def SetHexagons():
    ident = 0
    #Every even row needs to be indented, rowNum will act as a tracker for this purpose.
    rowNum=1
    #y-coordinate, for loop to scroll down the y-axis.
    y=0
    while y <= WINDOWHEIGHT:
        #x-coordinate, for loop to scroll along the x-axis.
        if rowNum%2 == 0:
            x = 0
        else:
            x = SideLength*((math.sqrt(3))/2)

        while x <= WINDOWWIDTH:
            #A frustrating variable.
            derp = SideLength*((math.sqrt(3))/2)
            #Hexagon vertices in Euclidean 2-space
            a=(x, y-SideLength)
            b=(x+derp, y-SideLength/2)
            c=(x+derp, y+SideLength/2)
            d=(x, y+SideLength)
            e=(x-derp, y+SideLength/2)
            f=(x-derp, y-SideLength/2)
            #Make a list of the points
            plist = [a,b,c,d,e,f]
            #details necessary to print a hexagon.
            hexagon = {'colour':WHITE, 'PointList':plist, 'cx': x, 'cy': y, 't':1, 'IsBarrier': False, 'IsStart': False, 'IsEnd': False, 'IsVisited':False, 'Open': False, 'Closed':False, 'id': ident, 'neighbours': [], 'Parentid': -1, 'childid':-1, 'h':-1, 'g':-1, 'f':-1}
            #h = estimated distance to finish.
            #g = cost of getting to node.
            #f = g+h
            HexagonList.append(hexagon)
            ident+=1
            x+=2*derp
        rowNum+=1    
        y+=(3*SideLength)/2

def PrintHexagons():
    #I love how Python does this for lists and for loops.
    for hexagon in HexagonList:
        pygame.draw.polygon(DISPLAYSURF,hexagon['colour'],hexagon['PointList'], hexagon['t'])

def EuclideanDistance(x,y,a,b):
    #Two coordinates (x,y) and (a,b).
    #Junior Certificate Level mathematics.
    dist = math.sqrt((x-a)**2+(y-b)**2)
    return dist

def FindHex(p):
    global SetStart, SetEnd, startid, endid
    #Coordinates (a,b) for the recent mouseclick.
    #c is the shortest distance between the mouseclick and a hexagon centrepoint.
    #BestHex is the id for the closest hexagon to the mouseclick.
    a,b,c,BestHex=p[0],p[1],100,0
    for hexagon in HexagonList:
        #Distance between mousclick and current hexagon being examined.
        dist = EuclideanDistance(a,b, hexagon['cx'], hexagon['cy'])
        #Keeps BestHex up to date if a closer hexagon is found.
        if c>dist:
            c=dist
            BestHex = hexagon['id']
    #BestHex should now correspond to the clicked Hexagon. It must be found again.
    hexagon = HexagonList[BestHex]
    if not(RunAlg):
        #If the start has not been set, clicked hexagon is now the start hexagon.
        if SetStart and not hexagon['IsBarrier']:
            hexagon['IsStart'] = True
            hexagon['colour'] = GREEN
            hexagon['t']=0
            startid = hexagon['id']
            SetStart = False
            #If the end has not been set...
        elif SetEnd:
            #The hexagon is probably the start, and is being deselected.
            if hexagon['IsStart'] and not hexagon['IsBarrier']:
                hexagon['IsStart'] = False
                hexagon['colour'] = WHITE
                hexagon['t'] = 1
                SetStart = True
            #Or else probably the end is being set.
            elif not hexagon['IsBarrier']:
                hexagon['IsEnd'] = True
                hexagon['colour'] = RED
                hexagon['t']=0
                endid = hexagon['id']
                SetEnd = False
        #Every other case.
        else:
            #Clicking start or end a second time deselects them.
            if hexagon['IsStart']:
                hexagon['IsStart'] = False
                hexagon['colour'] = WHITE
                hexagon['t'] = 1
                SetStart = True
            elif hexagon['IsEnd']:
                hexagon['IsEnd'] = False
                hexagon['colour'] = WHITE
                hexagon['t'] = 1
                SetEnd = True
            #Otherwise they become a barrier hexagon, or are desellected as a barrier hexagon.
            elif hexagon['IsBarrier']:
                hexagon['IsBarrier'] = False
                hexagon['colour'] = WHITE
                hexagon['t'] = 1
            else:
                hexagon['IsBarrier'] = True
                hexagon['colour'] = DARKGRAY
                hexagon['t'] = 0

def SetupAlg():
    global HexagonList, SideLength, startid, endid, currentNode

    for hex1 in HexagonList:
        neighbourlist = []
        a,b = hex1['cx'], hex1['cy']
        hex1['h'] = EuclideanDistance(a,b, HexagonList[endid]['cx'], HexagonList[endid]['cy'])

        for hex2 in HexagonList:
            c,d = hex2['cx'], hex2['cy']
            dist = EuclideanDistance(a,b,c,d)

            if dist <= 2*SideLength and dist >0 and not(hex2['IsBarrier']) and not(hex2['IsStart']):
                neighbourlist.append(hex2['id'])

        hex1['neighbours'] = neighbourlist

    currentNode = startid
    HexagonList[endid]['h']=0
    HexagonList[startid]['g']=0

def checkInput():
    global RunAlg
    for event in pygame.event.get():
        #Exit if x is clicked.
        if event.type == QUIT:
            terminate()

        #Gets a mouseclick and coordinates.
        if event.type==pygame.MOUSEBUTTONDOWN:
            position = pygame.mouse.get_pos()
            FindHex(position)

        if event.type==KEYDOWN:
            #Enter triggers the pathfinding.
            if event.key == K_RETURN and not SetStart and not SetEnd:
                RunAlg = True
                SetupAlg()

            if event.key == K_BACKSPACE and not RunAlg:
                ReInitialise()

            #Sets escape to end game.
            if event.key == K_ESCAPE:
                terminate()

def terminate():
    pygame.quit()
    sys.exit()

def Astar():
    global HexagonList, currentNode, RunAlg, OptList
    #Stupidly large number.
    smallestf = 10000
    derp = 10000
    #Variable to hold the id for the next node.
    sfid=0
    #Current Node.
    cur = HexagonList[currentNode]
    #Cost of getting to current node.
    cost = cur['g']+1

    #Node is now no longer part of the open set.
    cur['Open'] = False
    cur['Closed'] = True
    #Redundant?
    cur['IsVisited'] = True
    if not cur['IsStart']:
        cur['colour'] = BLUE

    #Look at the surrounding nodes.
    for hexid in cur['neighbours']:

        #If the node under scrutiny is the end node, we have succeded. Mark path back to start and end.
        if hexid == endid:
            HexagonList[currentNode]['colour']=WHITE
            nextid = HexagonList[currentNode]['Parentid']
            while nextid != startid:
                HexagonList[nextid]['colour'] = WHITE
                cid = nextid
                nextid = HexagonList[cid]['Parentid']

            RunAlg = False
            return

        #Otherwise mark the nodes being examined.
        else:
            #Every newly inspected node is "Open". Has a h value, and is assigned an f value based on parent. Becomes child to closest parent.
            #Every examined node is "Closed". Has a g and a h value, with corresponding f.
            #An open node may re-evaluate a closed node, and re-evaluate the f's for its children.
            if not HexagonList[hexid]['IsVisited']:
                HexagonList[hexid]['Open'] = True
                HexagonList[hexid]['colour'] = YELLOW
                HexagonList[hexid]['t'] = 0
                HexagonList[hexid]['IsVisited'] = True
                HexagonList[hexid]['Parentid'] = currentNode
                HexagonList[hexid]['g'] = cost
                HexagonList[hexid]['f']= HexagonList[hexid]['h']+HexagonList[hexid]['g']

            #If the examined node has been previously visited, this gets more complex.
            if HexagonList[hexid]['IsVisited']:
                #Node has been visited and expanded past, so we need to check if the new path to this node is better.
                if HexagonList[hexid]['g'] > cost:
                    #It is better. Recalculate g and f.
                    HexagonList[hexid]['g'] = cost
                    HexagonList[hexid]['f'] = HexagonList[hexid]['g']+HexagonList[hexid]['h']
                    HexagonList[hexid]['Parentid'] = currentNode

                    #Now fix the g values around this node.
                    OptList = [-1]
                    Optimise(hexid)

            #Keep track of the hexagon with the lowest f value. This will be the child node our current.
            if HexagonList[hexid]['f'] < smallestf:
                smallestf = HexagonList[hexid]['f']
                sfid = hexid

    #After examining all the neighbours, assign the closest as the childnode.
    HexagonList[currentNode]['childid'] = sfid
    #Now choose the Open node with the lowest f value as the new current node.
    for hexagon in HexagonList:
        if hexagon['f'] < derp and hexagon['Open']:
            derp = hexagon['f']
            currentNode = hexagon['id']

#If a node's g value has been changed, all nodes who stem from this node must be re-evaluated.
def Optimise(ident):
    global HexagonList, OptList
    #Prevents this node being visited again during this cycle.
    OptList.append(ident)
    #Check all the surrounding hexagons
    for hexid in HexagonList[ident]['neighbours']:
        if HexagonList[hexid]['Parentid'] == ident and not hexid in OptList:
            HexagonList[hexid]['g'] = HexagonList[ident]['g']+1
            HexagonList[hexid]['f'] = HexagonList[hexid]['g']+HexagonList[hexid]['h']
            #Recursive step to fix the children of this node.
            Optimise(hexid)

if __name__ == '__main__':
    main()