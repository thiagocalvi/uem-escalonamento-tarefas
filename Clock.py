import socket
import time
import threading

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
        self.server_socket = None
        
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
                
        except Exception as e:
            print(f"Erro ao enviar para Escalonador: {e}")
            
    def handle_message(self, message: str):
        """Processa mensagens recebidas pelo servidor"""
        message = message.strip().upper()
        
        if message == "FIM":
            print("Clock: Recebido sinal de FIM. Encerrando...")
            self.running = False
        else:
            print(f"Clock: Mensagem desconhecida recebida: {message}")
    
    def start_server(self):
        """Inicia o servidor do Clock para receber mensagens de controle"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port_clock))
            self.server_socket.listen(5)
            
            print(f"Clock: Servidor iniciado em {self.host}:{self.port_clock}")
            
            while self.running:
                try:
                    # Timeout para verificar se ainda está rodando
                    self.server_socket.settimeout(1.0)
                    
                    try:
                        client_socket, client_address = self.server_socket.accept()
                    except socket.timeout:
                        continue  # Continua o loop para verificar self.running
                    
                    # Processa a conexão
                    try:
                        data = client_socket.recv(1024)
                        if data:
                            message = data.decode().strip()
                            self.handle_message(message)
                    except Exception as e:
                        print(f"Erro ao processar mensagem: {e}")
                    finally:
                        client_socket.close()
                        
                except Exception as e:
                    if self.running:  # Só mostra erro se ainda está rodando
                        print(f"Erro no servidor Clock: {e}")
                    break
                    
        except Exception as e:
            print(f"Erro ao iniciar servidor Clock: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
                print("Clock: Servidor encerrado")
    
    def start_clock_loop(self):
        """Loop principal do clock - incrementa e envia para os outros"""
        print("Clock: Loop principal iniciado!")
        
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
            
        print("Clock: Loop principal encerrado.")
    
    def start_clock(self):
        """Inicia o Clock com servidor e loop principal em threads separadas"""
        print("Clock: Iniciando...")
        
        # Inicia servidor em thread separada
        server_thread = threading.Thread(target=self.start_server, daemon=True)
        server_thread.start()
        
        # Aguarda servidor subir
        time.sleep(1)
        
        # Inicia loop principal na thread atual
        self.start_clock_loop()
        
        # Aguarda thread do servidor terminar
        server_thread.join(timeout=1)
        
        print("Clock: Finalizado completamente.")