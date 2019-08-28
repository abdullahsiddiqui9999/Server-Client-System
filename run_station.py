from station import Station
import sys

ss = Station(sys.argv[1], int(sys.argv[2]))
ss.power_on()
