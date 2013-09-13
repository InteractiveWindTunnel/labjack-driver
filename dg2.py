from tunel.device import Tunel
from tunel.storage.FlatFileStorage import FlatFileStorage

from os import system
import curses
import threading
import time
import locale

locale.setlocale(locale.LC_ALL,"pl_PL.UTF-8")
def get_param(prompt_string):
     screen.clear()
     screen.border(0)
     screen.addstr(2, 2, prompt_string)
     screen.refresh()
     input = screen.getstr(10, 10, 60)
     return input

x = 0
screen = curses.initscr()
window = curses.newwin(1,20,0,0)
curses.start_color()
curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)
curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_GREEN)

class StatusThread(threading.Thread):
  _iter=0
  _window=None
  def setWindow(self,window):
    self._window = window
  def run(self):
   while True:
     self._iter+=1
     self._window.addstr(0,0,str(self._iter))
     time.sleep(1)
     self._window.refresh()
windrunning=True



t=Tunel()
fs = FlatFileStorage()
t.storage = fs

series=0
base_filename=''
fans_running=False
windpaused=False

def printWind():
    while windrunning:
        while not windpaused and windrunning:
            data = t.get_data()
            screen.addstr(14,2,"AIN0 : "+str(data[0]))
            screen.addstr(15,2,"AIN1 : "+str(data[1]))
            screen.addstr(16,2,"AIN2 : "+str(data[2]))
            screen.refresh()
            time.sleep(1)
wsthread=threading.Thread(target=printWind)
wsthread.start()
while x != ord('6'):
     screen.clear()
     screen.border(0)
     screen.addstr(6, 2, "ITA:Console v.01")
     screen.addstr(7, 4, "1 - Power on/off")
     screen.addstr(8, 4, "2 - Fans start/stop")
     screen.addstr(9, 4, "3 - Set output filename")
     screen.addstr(10, 4, "4 - Start/Stop measure")
     screen.addstr(11, 4, "5 - SetFanSpeed")
     screen.addstr(12, 4, "6 - The End")
     screen.addstr(1,20,'Aktywne watki : '+str(t.debug_threads()))
     if t.is_measuring()==True:
       screen.addstr(2,1,'Pomiary w toku ',curses.color_pair(2))
     if t.power_status()==False:
       screen.addstr(1,1,'System wylaczony',curses.color_pair(1))
       fans_running=False	
     else:
       screen.addstr(1,1,'System zalaczony',curses.color_pair(2))
       fans_running = t.fans_controller.is_running()
     if fans_running:
       screen.addstr(3,1,'Wiatraczki wlaczone',curses.color_pair(2))
     else:
       screen.addstr(3,1,'Wiatraczki wylaczone',curses.color_pair(1))
     screen.refresh()

     x = screen.getch()
     
     if x == ord('1'):
       if t.power_status()==False:
         t.power_on()
       else:
         t.power_off()
     if x == ord('2'):
       if t.fans_controller.is_running()==False:
         t.fans_controller.power_on()
       else:
         t.fans_controller.power_off()
     if x == ord('3'):
       windpaused=True
       base_filename = get_param("Podaj nazwe pliku (bez rozszerzenia)")
       windpaused=False
     if x == ord('4'):
       if t.is_measuring()==True:
         t.stop_measures()
         series+=1
       else:
         t.storage.filename='.'+base_filename+'_'+str(series)+'.csv'
         t.start_measures()
     if x==ord('5'):
       windpaused=True
       t.fans_controller.set_speed(int(get_param("Podaj predkosc")))
       windpaused=False
curses.endwin()
windrunning=False
wsthread.join()
