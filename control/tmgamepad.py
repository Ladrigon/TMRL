import vgamepad as vg
import time


class TMGamePad:
    
    def __init__(self):
        # initialize gamepad
        self.gamepad = vg.VX360Gamepad()
        
    def steer(self, x):
        """
        x (float): [-1, 1] -1 full left, +1 full right
        """
        self.gamepad.left_joystick_float(x_value_float=x, y_value_float=0.0)


    def accelerate(self, y):
        """
        y (float): [-1, 1] -1 full brake, +1 full throttle
        """
        # self.gamepad.right_joystick_float(x_value_float=0.0, y_value_float=-y)
        self.gamepad.right_trigger_float(value_float=y)
    
    def decelerate(self, y):
        """
        y (float): [-1, 1] -1 full brake, +1 full throttle
        """
        # self.gamepad.right_joystick_float(x_value_float=0.0, y_value_float=-y)
        self.gamepad.left_trigger_float(value_float=y)

        
    def press(self, b):
        """
        respawn = y
        restart = b
        """
        
        if b == "y":
            self.gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)
            self.update()
            time.sleep(0.1)
            self.gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)
            self.update()
            
        elif b == "b":
            self.gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
            self.update()
            time.sleep(0.2)
            self.gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
            self.update()
        

    def update(self):
        """
        update state of gamepad with current values
        """
        self.gamepad.update()

    def reset(self):
        """
        reset to default state, needs update after
        """
        self.gamepad.reset() 

