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

    def start(self) -> None:
       while True:
            self.current_clock += 1
            print(f"Clock: {self.current_clock}")
            
            # Envia o tempo atual para o Emissor de Tarefas
            self.send_to_emissor()
            
            # Envia o tempo atual para o Escalonador de Tarefas
            self.send_to_escalonador()
            
            # Aguarda o delay do clock
            time.sleep(self.clock_delay / 1000.0)

