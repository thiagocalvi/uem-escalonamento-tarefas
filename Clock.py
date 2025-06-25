import socket
import time

class Clock:
    def __init__(self, host: str, port_clock: int, clock_delay: int, port_emissor: int, port_escalonador: int, emissor_escalonador_delay: int):
        self.host = host
        self.port_clock = port_clock
        self.clock_delay = clock_delay
        self.port_emissor = port_emissor
        self.port_escalonador = port_escalonador
        self.emissor_escalonador_delay = emissor_escalonador_delay
       
        self.current_clock = 0
        self.running = True
        
    def _send_to_emissor(self):
        """Envia clock para o Emissor"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.host, self.port_emissor))
                message = str(self.current_clock).encode()
                sock.send(message)
                print(f"Clock {self.current_clock} → Emissor")
        except Exception as e:
            print(f"Erro ao enviar para Emissor: {e}")
            
    def _send_to_escalonador(self):
        """Envia clock para o Escalonador"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.host, self.port_escalonador))
                message = str(self.current_clock).encode()
                sock.send(message)
                print(f"Clock {self.current_clock} → Escalonador")
                
                # Verifica se recebeu sinal de fim
                sock.settimeout(0.01)
                try:
                    response = sock.recv(1024)
                    if response and response.decode().strip() == "FIM":
                        print("Recebido sinal de FIM. Encerrando clock...")
                        self.running = False
                except socket.timeout:
                    pass  # Nenhuma resposta, continua normal
                    
        except Exception as e:
            print(f"Erro ao enviar para Escalonador: {e}")
            
    def start_clock(self):
        """Loop principal - incrementa e envia para os outros"""
        print("Clock iniciado!")
        
        # Aguarda um pouco para os outros servidores subirem
        time.sleep(1)
        
        while self.running:
            print(f"Clock: {self.current_clock}")
            
            # 1. Envia para EMISSOR primeiro
            self._send_to_emissor()
            
            # 2. Espera 5ms
            time.sleep(self.emissor_escalonador_delay / 1000.0)
            
            # 3. Envia para ESCALONADOR
            self._send_to_escalonador()
            
            # Se recebeu FIM, para o loop
            if not self.running:
                break
                
            # 4. Incrementa clock
            self.current_clock += 1
            
            # 5. Espera 100ms para próximo ciclo
            time.sleep(self.clock_delay / 1000.0)
            
        print("Clock encerrado.")
