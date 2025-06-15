import socket

class Clock:
    def __init__(self, host:str, port_clock:int, clock_delay:int, port_emissor:int, port_escalonador:int, emissor_escalonador_delay:int):
        self.host = host
        self.port_clock = port_clock
        self.clock_delay = clock_delay
        self.port_emissor = port_emissor
        self.port_escalonador = port_escalonador
        self.emissor_escalonador_delay = emissor_escalonador_delay
        
        self.current_clock = 0
        self.clock_socket = None
        self.emissor_socket = None
        self.escalonador_socket = None

