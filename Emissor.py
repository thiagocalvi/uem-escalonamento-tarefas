import socket
import json

class Emissor:
    def __init__(self, host: str, port_emissor: int, port_escalonador: int, port_clock: int, tasks: list):
        """
        Inicializa o Emissor.
        Args:
            host (str): Endereço do host
            port_emissor (int): Porta do Emissor
            port_escalonador (int): Porta do Escalonador
            port_clock (int): Porta do Clock
            tasks (list): Lista de tarefas
        """
        self.host = host
        self.port_emissor = port_emissor
        self.port_escalonador = port_escalonador
        self.port_clock = port_clock
        
        self.tasks = tasks  # Lista de todas as tarefas
        self.emitted_tasks = []  # Tarefas já emitidas
        self.current_clock = 0
        self.all_tasks_emitted = False
        self.server_socket = None
            
    def send_to_clock(self, message):
        """Envia mensagem para o Clock"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.host, self.port_clock))
                sock.send(message.encode())
                print(f"Emissor: Mensagem enviada ao Clock: {message}")
        except Exception as e:
            print(f"Erro ao enviar mensagem ao Clock: {e}")
            
    def send_task_to_escalonador(self, task):
        """Envia uma tarefa para o Escalonador"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.host, self.port_escalonador))
                
                # Converte a tarefa para formato JSON para envio
                task_data = {
                    'type': 'TASK',
                    'id': task.task_id,
                    'arrival_time': task.arrival_time,
                    'burst_time': task.burst_time,
                    'priority': task.priority
                }
                
                message = json.dumps(task_data).encode()
                sock.send(message)
                print(f"Emissor: Tarefa {task.task_id} enviada ao Escalonador (clock={self.current_clock})")
                
        except Exception as e:
            print(f"Erro ao enviar tarefa {task.task_id}: {e}")
            
    def send_all_tasks_emitted_signal(self):
        """Informa ao Escalonador que todas as tarefas foram emitidas"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.host, self.port_escalonador))
                
                message_data = {
                    'type': 'ALL_TASKS_EMITTED'
                }
                
                message = json.dumps(message_data).encode()
                sock.send(message)
                print("Emissor: Sinal 'TODAS AS TAREFAS EMITIDAS' enviado ao Escalonador")
                
        except Exception as e:
            print(f"Erro ao enviar sinal de fim: {e}")
            
    def check_and_emit_tasks(self):
        """Verifica quais tarefas devem ser emitidas no clock atual"""
        tasks_to_emit = []
        
        # Encontra tarefas que devem ser emitidas agora
        for task in self.tasks:
            if (task.arrival_time == self.current_clock and 
                task not in self.emitted_tasks):
                tasks_to_emit.append(task)
                
        # Emite as tarefas encontradas
        for task in tasks_to_emit:
            self.send_task_to_escalonador(task)
            self.emitted_tasks.append(task)
            
        # Verifica se todas as tarefas foram emitidas
        if (len(self.emitted_tasks) == len(self.tasks) and 
            not self.all_tasks_emitted):
            self.send_all_tasks_emitted_signal()
            self.all_tasks_emitted = True
            
    def handle_clock_message(self, clock_value):
        """Processa mensagem recebida do Clock"""
        self.current_clock = clock_value
        print(f"Emissor: Recebido clock {self.current_clock}")
        
        # Verifica e emite tarefas para este clock
        self.check_and_emit_tasks()
        
    def start_server(self):
        """Inicia o servidor do Emissor para receber mensagens do Clock"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port_emissor))
            self.server_socket.listen(5)
            
            print(f"Emissor: Servidor iniciado em {self.host}:{self.port_emissor}")
            
            while True:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    
                    # Recebe dados do cliente (Clock)
                    data = client_socket.recv(1024)
                    if data:
                        clock_value = int(data.decode().strip())
                        self.handle_clock_message(clock_value)
                    
                    client_socket.close()
                    
                except Exception as e:
                    print(f"Erro ao processar conexão: {e}")
                    break
                    
        except Exception as e:
            print(f"Erro no servidor Emissor: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
                print("Emissor: Servidor encerrado")


