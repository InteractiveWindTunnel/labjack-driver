from device import tunel
class TunnelService(object):
    """Tunnel Serivce controller"""
    
    def __init__(self):
        self.tunel = Tunel()
        self.state = self.tunel.getState()

    def commandPowerOn(self):
        self.tunel.powerOn()
        
    def commandPowerStop(self):
        self.tunel.powerOff()
    
    def commandFansStop(self):
        self.tunel.fansController.powerOn()

    def commandFansStart(self):
        self.tunel.fansController.powerOff()

    def commandFansSpeed(self,speed):
        self.tunel.fansController.setSpeed(speed)

    def commandStartMeasure(self):
        self.tunel.startMeasure()
