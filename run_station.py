from station import Station

ss = Station()
ss.bind_clients_listener('127.0.0.1', 27015)
ss.power_on()
