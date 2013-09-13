import u3
import threading
import serial
import redis
import time

class TunnelState:
    NONE = 0
    POWER = 1
    FANS = 2
    STREAM = 4
    MEASURES = 8
    

class Tunel:
    _device  = None
    storage  = None
    _freq    = 50
    _stream  = False
    _finish  = False
    fans_controller  = None
    _fan_status = False
    _mthread = None
    _MAX_FREQ = 50
    angle = 0

    def __init__(self):
        self._device = u3.U3()
        self._device.writeRegister(6750, 65535)
        self.fans_controller = FansController()
    def power_status(self):
        if self._device.readRegister(6701) == 255:
            return False
        else:
            return True

    def power_on(self):
        self._device.writeRegister(6701, 256)
        self._device.writeRegister(50501, 1)
        self._device.writeRegister(7000, 6)
        self._device.writeRegister(7002, 14)
        self._device.writeRegister(7100, 60150)
        self._device.writeRegister(5000, 5)
        self.angle = 0
    def power_off(self):
        self._device.writeRegister(6701, 65535)
        self._device.writeRegister(50501, 0)
        self._device.writeRegister(5000, 0)
    def get_data(self):
        return [
            self._device.readRegister(0),
            self._device.readRegister(2),
            self._device.readRegister(4),
            self._device.readRegister(6),
            self._device.readRegister(14)
        ]
    def set_frequency(self, freq):
        if freq>self.MAX_FREQ:
            raise RuntimeWarning('freq over limit')
        self.freq = freq

    def start_measures(self):
        if not self.storage:
            raise RuntimeWarning('storage not set') 
        self.storage.open_series()
        self._finish = False
        self._mthread = threading.Thread(name="measures", target=self._measuring)
        self._mthread.start()

    def stop_measures(self):
        self._finish = True
        self._mthread.join(5)
        self.storage.close_series()

    def is_measuring(self):
        if self._mthread==None:
            return False
        return self._mthread.is_alive()

    def _measuring(self):
        while not self._finish:
            self.storage.put_data(self.get_data())

    def debug_threads(self):
        return threading.active_count()

    def set_angle(self, angle):
        current = int((self._device.readRegister(7100)-60150)/35)
        target = 60150 + (angle*35)
        step = 1
        if angle<current:
            step = -1
        for i in range(current,angle,step):
            self._device.writeRegister(7100,60150+(i*35))
            time.sleep(0.1)
        self.angle = angle

class FansController:
    _serial=None
    port = '/dev/ttyUSB0'
    timeout = 0.2
    _reddb = None
    def __init__(self):
        self._serial = serial.Serial(self.port, timeout = self.timeout)
        self._serial.read(255)
        self._reddb = redis.Redis()
        self._reddb.delete('fans:lock')
    def __del__(self):
        if not self._serial == None:
            self._serial.close()
    def send_command(self, comm, expected = 255):
        while not self._reddb.setnx('fans:lock', True):
            time.sleep(self.timeout)
        self._serial.write(comm)
        ret = self._serial.read(expected)
        self._reddb.delete('fans:lock')
        return ret

    def set_speed(self, speed):
        str_comm = "SAS="
        str_comm += (str(speed)+',')*9
        str_comm +='0,0,0\r'
        ret = self.send_command(str_comm)
        return ret == str_comm

    def get_speed(self):
#       values = self._reddb.get('fans:speed')
        values=[]
        i = self._reddb.llen('fans:speed')
        while i!=0:
            values.append(float(self._reddb.lindex('fans:speed', i - 1)))
            i-=1
        if values:
            return values
        str_comm = "GAF\r"
        ret=self.send_command(str_comm)
        back_comm = ret.split('=')
        param = back_comm[0]
        if param == 'GAF':
            back_comm[1].rstrip('\r')
            val_str=back_comm[1].split(',')
            val = [self.to_rpm(float(x)) for x in val_str]
            ret = val[0:9]
            i=0
            while i<len(ret): 
                self._reddb.lpush('fans:speed',ret[i])
                i+=1
            self._reddb.expire('fans:speed',1)
            return ret
        return None

    def power_on(self):
        str_comm="PWR=1\r"
        ret = self.send_command(str_comm,len(str_comm))
        return ret==str_comm

    def power_off(self):
        str_comm="PWR=0\r"
        ret = self.send_command(str_comm,len(str_comm))
        self._reddb.delete('fans:speed')
        return ret == str_comm

    def is_running(self):
        speeds=self.get_speed()
        if speeds == None:
            return False
        for t in speeds:
            if t < 100: 
                return False
        return True

    def to_rpm(self,x):
                if x==0.0 : return 0
        return float((1/((x/10000)*2))*60)

class MeasuresStorage:
    def put_data(self,data):
        pass
    def set_param(self,param,value):
        self._param[param]=value
    def open_series(self, name):
        pass
    def close_series(self, name):
        pass
