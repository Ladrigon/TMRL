from pygbx import Gbx, GbxType
from shapely.geometry import LineString, MultiLineString
from shapely.affinity import rotate, translate
from shapely.ops import polygonize
import numpy as np

def StadiumRoadMainGTCurve(position, rotation, radius): 
    """Generation of curved paths"""
    theta = np.radians(np.linspace(-90, 0, 100))
    x_out = position[0]*32+radius*32* np.cos(theta)
    y_out = position[1]*32 + radius*32 *(1+ np.sin(theta))
    
    arc_out = LineString(np.column_stack([x_out, y_out]))
    arc_out = rotate(arc_out, rotation*90)
    5
    x_in = position[0]*32+(radius-1)*32* np.cos(theta)
    y_in = position[1]*32 +radius*32+ (radius-1)*32 *np.sin(theta)
    
    arc_in = LineString(np.column_stack([x_in, y_in]))
    arc_in = rotate(arc_in, rotation*90)
    if rotation == 1:
        arc_in = translate(arc_in, 0, -32)
    elif rotation == 2:
        arc_in = translate(arc_in, 32, -32)
    elif rotation == 3:
        arc_in = translate(arc_in, 32, 0)    
    return arc_out, arc_in

def StadiumRoadMain(position, rotation, flag):
    """Generation of straight paths"""
    state = 1
    if flag == "0x21002":
        state = 0
        line = StadiumRoadMainGTCurve(position, rotation, 1)
        return line

    l1 = LineString([(0+position[0]*32, 0+position[1]*32), ((1-state)*32+position[0]*32, state*32+position[1]*32)])
    l2 = LineString([(32+position[0]*32, 0+position[1]*32), (32+position[0]*32, 32+position[1]*32)])
    line = MultiLineString([l1, l2])
    line = rotate(line, rotation*90)
    
    return line.geoms[0], line.geoms[1]

    
def map_track(path):
    """Reads the contents of the map file and returns a 2D discretized track"""
    g = Gbx(path)
    challenges = g.get_classes_by_ids([GbxType.CHALLENGE, GbxType.CHALLENGE_OLD])
    if not challenges:
        quit()
    
    challenge = challenges[0]
    
    line_lst = []
    
    for block in challenge.blocks:
        if block.name in ["StadiumRoadMain", "StadiumRoadMainCheckpoint", "StadiumRoadMainStartFinishLine"]:
            line = StadiumRoadMain((block.position[0], block.position[2]),block.rotation, hex(block.flags))
            line_lst.append(line[0])
            line_lst.append(line[1])

        elif block.name in ["StadiumRoadMainGTCurve2","StadiumRoadMainGTCurve3", "StadiumRoadMainGTCurve4","StadiumRoadMainGTCurve5"]:
            line = StadiumRoadMainGTCurve((block.position[0], block.position[2]),block.rotation, int(block.name[-1]))
            line_lst.append(line[0])
            line_lst.append(line[1])
            
    track = polygonize(line_lst)
    return track[0]