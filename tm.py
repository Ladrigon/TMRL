import time
import numpy as np
from mapper import map_track
import game_state

from control.tmgamepad import TMGamePad

from shapely.geometry import Point, LineString, MultiPoint
from shapely.ops import split, nearest_points

class TM():

    def __init__(self):
        self.track = map_track("C:/Users/Tilen/Documents/ManiaPlanet/Maps/My Maps/ai.Map.Gbx")
        self.centerline = self.track.exterior.buffer(16).interiors[0]
        self.gamestate = 0
        # get current time on creation for tracking lap
        self.thetime = time.time()
        # initialize laps
        self.current_lap = 1

        # telemetry
        self.telemetry = None

        self.first_time = True
        
        self.slip = 0
            
        self.pad = TMGamePad()
        self.telemetry = self.update_telemetry()
        
        self.gate = self.generate_gates()
        self.gate_state = np.zeros(len(self.gate.geoms)+1)
        self.point = 0
        
        self.p1 = [[0],[0]]
        self.p2 = [[0],[0]]
        self.current_pos = 0
        
        self.lap_prev = 0
        
    def generate_gates(self):
        """Generation of track checkpoints used for progression tracking"""
        centerline = self.centerline
        self.distance_delta = 0.25
        distances = np.arange(0, centerline.length, self.distance_delta)
        points = MultiPoint([centerline.interpolate(distance) for distance in distances])

        return points

    def check_gate(self):        
        """Check track progression"""        
        car = Point(round(self.telemetry[0]),round(self.telemetry[1]))#.buffer(4)
        check_point = nearest_points(car, self.gate)[1]
        for i in range(len(self.gate.geoms)):
            if self.gate.geoms[i] == check_point:
                self.p1 = self.gate.geoms[i].xy
                self.p2 = self.gate.geoms[i+int(1/self.distance_delta)].xy
                self.current_pos = i
                if self.gate_state[i] !=1:
                    if self.first_time:
                        self.first_time = False
                        self.p0 = i
                    
                    
                    self.gate_state[i] = 1
                    self.gate_collision = True
                    if self.lap_prev != self.lap():
                        self.lap_prev = self.lap()
                        self.gate_state = np.zeros(len(self.gate.geoms)+1)
    
                    self.point = self.p0- i
                    if self.point < 0:
                        self.point = len(self.gate.geoms)+1 + self.point
                    return self.point
        return 0

        
    def state(self):
        # gamesate
        self.gamestate = game_state.game_state()
        return(self.gamestate)
    
    def update_telemetry(self):
        """update all relevant telemetry data"""
        # coordinates and speed
        x, y, speed = game_state.vehicle()
        self.slip = game_state.slip()
        self.time = game_state.time()
        direction = game_state.angle()
        # create telemetry
        self.telemetry = np.array([x, y, speed, direction])

    def vehicle_telemetry(self):
        return(self.telemetry)

    def vehicle_lidar(self, resolution_degree=1):
        lidar = self._lidar(resolution_degree)
        return(lidar)

    def vehicle_collision(self):
        """Check for collision with wall""" #UNUSED
        # collison = int(np.min(self.vehicle_border_detector()) < 0.1)
        collison = int(np.min(self._lidar(15)) < 6)
        return(collison)

    def vehicle_angle(self):
        """Calculate angle of car compared to ecnterline"""
        a = self.p1
        b = self.p2
        
        x = b[0][0] - a[0][0]
        y = b[1][0] - a[1][0]
        track_angle = np.arctan2(y,x)
        return self.telemetry[3] - track_angle


    def lap_radius(self, distance_ahead = 0.1, range_ahead = 2, n_radii = 10, sample_step = 1):
        """Generate track curvature"""
        radius = []
        
        step = np.linspace(int(distance_ahead*self.telemetry[2]/self.distance_delta), int(distance_ahead+range_ahead*self.telemetry[2]/self.distance_delta), n_radii, dtype= int)
        for i in range(len(step)):
            idx = self.current_pos+step[i]
            if idx >= len(self.gate.geoms):
                idx = idx - len(self.gate.geoms)-1
            a = np.array([self.gate.geoms[idx].xy[0],self.gate.geoms[idx].xy[1]])
            idx = self.current_pos+step[i]+1*sample_step
            if idx+1*sample_step >= len(self.gate.geoms):
                idx = idx - len(self.gate.geoms)-1
            b = np.array([self.gate.geoms[idx].xy[0],self.gate.geoms[idx].xy[1]])
            idx = self.current_pos+step[i]+2*sample_step
            if idx+2*sample_step >= len(self.gate.geoms):
                idx = idx - len(self.gate.geoms)-1
            c = np.array([self.gate.geoms[idx].xy[0],self.gate.geoms[idx].xy[1]])
            
            d = (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1])) * 2.0 / sample_step
        
            radius.append(d)
            
        radius = np.array(radius)
        radius[radius == 0.0] = 100
       
        return radius
    
    def lap(self):
        """Return current lap"""
        self.current_lap = game_state.lap()
        return(self.current_lap)

    def laptime(self):
        """Return laptime"""
        nowtime = time.time()
        laptime = nowtime - self.thetime
        return(laptime)

    def delta_distance(self):
        car = Point(self.telemetry[0], self.telemetry[1])
        point_1 = nearest_points(car, self.centerline)[1]
        delta = self.point_0.distance(point_1)
        self.point_0 = point_1
        return delta
        

    def reset_laptime(self):
        self.thetime = time.time()
        

    def restart_race(self):
        """reset the whole race and start at lap 1 again"""
        self.pad.press("b")
        self.gate_state = np.zeros(len(self.gate.geoms)+1)
        self.point = 0
        time.sleep(3) # wait for race to start
        self.reset_laptime()
   
    def  _lidar(self, resolution_degree=1):
        """Generation of the LIDAR environment"""
        telemetry = self.telemetry
         
        car = Point(telemetry[0], telemetry[1])
        ang = telemetry[3]

        telemetry = self.telemetry
        beam_angles = np.radians(np.arange(0,181, resolution_degree))
        lidar = []
        
        for beam in beam_angles:
            lidar_line = LineString([car, Point(car.x + 300 * np.cos(ang+beam), car.y + 300 * np.sin(ang+beam))])
            lidar_line = split(lidar_line, self.track).geoms[0]
            lidar.append(lidar_line.length)
            
            # if beam == beam_angles[self.lidar_beams//2]:
            #     center = lidar_line
        
        return np.array(lidar)#np.flip()
