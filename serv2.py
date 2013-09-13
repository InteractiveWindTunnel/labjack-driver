from twisted.internet import reactor
from websocket import WebSocketHandler, WebSocketSite
from twisted.web.static import File
import time
import json
import threading
from tunel.device import Tunel
import redis
#from tunel.experiment.exp03 import Experiment03

tunel=Tunel()

class Tunelhandler(WebSocketHandler):
    n=0
    errors=[]
    _saving = False
    _freq=1
    _db = redis.Redis()
    def connectionMade(self):
          self.senddata()
    def connectionLost(self, reason):
          print 'Utracono polaczenie '+reason.__str__()
    def frameReceived(self, frame):
          print str(frame)
          try:
             command = json.loads(frame)
             if 'command' in command and 'params' in command:
               if command['command']=='power':
                 if command['params']['state']==0:
                   self.power_off()
                 else: 
                   self.power_on()
               if command['command']=='fans_power':
                 if command['params']['state']==0:
                   self.fans_stop()
                 else:
                   self.fans_start()
               if command['command']=='servo':
                 if command['params']['angle']>=-90 and command['params']['angle']<=90:
                   self.set_servo_angle(command['params']['angle'])
                 else:
                   errors.append('Kat poza zakresem')
               if command['command']=='fans_speed':
                 if command['params']['pwm']>=0 and command['params']['pwm']<=1000:
                   self.fans_speed(command['params']['pwm'])
                 else:
                   errors.append('PWM poza zakresem')
             print str(command)
          except ValueError:
             self.errors.append('Command is not json')
             print 'Bledny json'

#          if 'command' in command:
#          self.senddata()
          
    def senddata(self):
          d=tunel.get_data()
          speeds=tunel.fans_controller.get_speed()
          ret = {
			'ain':{'ain0':d[0],'ain1':d[1],'ain2':d[2],'ain3':d[3],'ain7':d[4]},
			'wind':speeds,
			'states':{'device':tunel.power_status(),'fans':tunel.fans_controller.is_running()}
#			'last_message':,
		}
          self.transport.write(json.dumps(ret))
          reactor.callLater(1/self._freq,self.senddata)
    def power_on(self):
          tunel.power_on()
    def power_off(self):
          tunel.power_off()
    def fans_start(self):
          tunel.fans_controller.power_on()
    def fans_stop(self):
          tunel.fans_controller.power_off()
    def fans_speed(self,speed):
          tunel.fans_controller.set_speed(speed)
    def set_freq(self,freq):
          self._freq = freq
    def start_measuring(self):
          _saving=True
    def stop_measuring(self):
          _saving=False
    def set_servo_angle(self,angle):
          if angle>=-90 and angle <=90:
              tunel.set_angle(angle)
if __name__ == "__main__":
    root = File(".")
    site = WebSocketSite(root)
    site.addHandler("/echo", Tunelhandler)
    reactor.listenTCP(5563, site)
    reactor.run()
      

