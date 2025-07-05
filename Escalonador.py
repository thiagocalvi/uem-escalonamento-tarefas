import socket
import json
import threading
import time
import math
from collections import deque
from Task import Task

class Escalonador:
    def __init__(self, host: str, port_escalonador: int, port_clock: int, algorithm: str):
        """
        Inicializa o Escalonador.
        Args:
            host (str): Endereço do host
            port_escalonador (int): Porta do Escalonador
            port_clock (int): Porta do Clock
            algorithm (str): Algoritmo de escalonamento
        """
        self.host = host
        self.port_escalonador = port_escalonador
        self.port_clock = port_clock
        self.algorithm = algorithm
        
        self.ready_queue = []  # Fila de tarefas prontas
        self.finished_tasks = []  # Tarefas finalizadas
        self.current_task = None  # Tarefa atualmente em execução
        self.current_clock = 0
        self.all_tasks_emitted = False
        self.simulation_finished = False
        self.server_socket = None
        
        # Para controle de execução
        self.execution_timeline = []  # Timeline de execução
        self.quantum = 3  # Quantum para Round Robin
        self.current_quantum = 0  # Quantum atual da tarefa em execução
        
        # Para algoritmos de prioridade dinâmica
        self.aging_counter = 0
        
        # Mapeamento de algoritmos para funções
        self.algorithm_map = {
            'fcfs': self.execute_fcfs,
            'rr': self.execute_rr,
            'sjf': self.execute_sjf,
            'srtf': self.execute_srtf,
            'prioc': self.execute_prioc,
            'priop': self.execute_priop,
            'priod': self.execute_priod
        }

    def execute_scheduling(self):
        """Executa o algoritmo de escalonamento selecionado"""
        if self.algorithm in self.algorithm_map:
            self.algorithm_map[self.algorithm]()
        else:
            print(f"Algoritmo {self.algorithm} não implementado")

    def handle_client(self, client_socket):
        """Processa mensagens recebidas"""
        try:
            data = client_socket.recv(1024)
            if data:
                message = data.decode()
                
                # Verifica se é mensagem do Clock (número simples)
                if message.isdigit():
                    self.handle_clock_message(int(message))
                else:
                    # Mensagem JSON do Emissor
                    try:
                        json_data = json.loads(message)
                        if json_data.get('type') == 'TASK':
                            self.handle_new_task(json_data)
                        elif json_data.get('type') == 'ALL_TASKS_EMITTED':
                            self.handle_all_tasks_emitted()
                    except json.JSONDecodeError:
                        print(f"Erro ao decodificar JSON: {message}")
                        
        except Exception as e:
            print(f"Erro ao processar mensagem: {e}")
        finally:
            client_socket.close()

    def handle_new_task(self, task_data):
        """Processa nova tarefa recebida do Emissor"""
        task = Task(
            task_data['id'],
            task_data['arrival_time'],
            task_data['burst_time'],
            task_data['priority']
        )
        
        # Adiciona informações para controle
        task.start_time = None
        task.finish_time = None
        task.remaining_time = task.burst_time  # IMPORTANTE: Inicializar remaining_time
        task.response_time = None
        task.original_priority = task.priority
        task.has_started = False
        
        self.ready_queue.append(task)
        print(f"Escalonador: Tarefa {task.task_id} adicionada à fila (clock={self.current_clock})")
        
    def handle_all_tasks_emitted(self):
        """Processa sinal de que todas as tarefas foram emitidas"""
        self.all_tasks_emitted = True
        print("Escalonador: Todas as tarefas foram emitidas")
        
    def handle_clock_message(self, clock_value):
        """Processa mensagem de clock"""
        self.current_clock = clock_value
        print(f"Escalonador: Recebido clock {self.current_clock}")
        
        # Executa o algoritmo de escalonamento
        self.execute_scheduling()
        
        # Verifica se a simulação terminou
        if self.check_simulation_end():
            self.finish_simulation()
    
    def execute_fcfs(self):
        """Executa algoritmo First-Come, First-Served"""
        # 1. Verifica se tarefa atual terminou
        if self.current_task and self.current_task.remaining_time <= 0:
            self.finish_current_task()
        
        # 2. Seleciona próxima tarefa (primeira da fila por arrival_time)
        if not self.current_task and self.ready_queue:
            # Ordena por arrival_time para garantir FCFS
            self.ready_queue.sort(key=lambda t: t.arrival_time)
            self.current_task = self.ready_queue.pop(0)
            self.start_task_execution()
        
        # 3. Executa tarefa atual
        self.execute_current_task()
        
    def execute_rr(self):
        """Executa algoritmo Round Robin"""
        # 1. Verifica se tarefa atual terminou
        if self.current_task and self.current_task.remaining_time <= 0:
            self.finish_current_task()
        
        # 2. Verifica preempção por quantum
        if self.current_task and self.current_quantum >= self.quantum:
            # Volta para o final da fila
            self.ready_queue.append(self.current_task)
            self.current_task = None
            self.current_quantum = 0
        
        # 3. Seleciona próxima tarefa (FIFO para RR)
        if not self.current_task and self.ready_queue:
            # Ordena por arrival_time para manter ordem FIFO
            self.ready_queue.sort(key=lambda t: t.arrival_time)
            self.current_task = self.ready_queue.pop(0)
            self.start_task_execution()
            self.current_quantum = 0
        
        # 4. Executa tarefa atual
        self.execute_current_task()
        if self.current_task:
            self.current_quantum += 1
            
    def execute_sjf(self):
        """Executa algoritmo Shortest Job First"""
        # 1. Verifica se tarefa atual terminou
        if self.current_task and self.current_task.remaining_time <= 0:
            self.finish_current_task()
        
        # 2. Seleciona próxima tarefa (menor burst time)
        if not self.current_task and self.ready_queue:
            self.current_task = min(self.ready_queue, key=lambda t: t.burst_time)
            self.ready_queue.remove(self.current_task)
            self.start_task_execution()
        
        # 3. Executa tarefa atual
        self.execute_current_task()
        
    def execute_srtf(self):
        """Executa algoritmo Shortest Remaining Time First"""
        # 1. Verifica se tarefa atual terminou
        if self.current_task and self.current_task.remaining_time <= 0:
            self.finish_current_task()
        
        # 2. Verifica preempção por menor tempo restante
        if self.current_task and self.ready_queue:
            shortest_ready = min(self.ready_queue, key=lambda t: t.remaining_time)
            if shortest_ready.remaining_time < self.current_task.remaining_time:
                self.ready_queue.append(self.current_task)
                self.ready_queue.remove(shortest_ready)
                self.current_task = shortest_ready
                self.start_task_execution()
        
        # 3. Seleciona próxima tarefa (menor tempo restante)
        if not self.current_task and self.ready_queue:
            self.current_task = min(self.ready_queue, key=lambda t: t.remaining_time)
            self.ready_queue.remove(self.current_task)
            self.start_task_execution()
        
        # 4. Executa tarefa atual
        self.execute_current_task()
        
    def execute_prioc(self):
        """Executa algoritmo de Prioridades Fixas Cooperativo"""
        # 1. Verifica se tarefa atual terminou
        if self.current_task and self.current_task.remaining_time <= 0:
            self.finish_current_task()
        
        # 2. Seleciona próxima tarefa (maior prioridade = menor número)
        if not self.current_task and self.ready_queue:
            self.current_task = min(self.ready_queue, key=lambda t: t.priority)
            self.ready_queue.remove(self.current_task)
            self.start_task_execution()
        
        # 3. Executa tarefa atual
        self.execute_current_task()
        
    def execute_priop(self):
        """Executa algoritmo de Prioridades Fixas Preemptivo"""
        # 1. Verifica se tarefa atual terminou
        if self.current_task and self.current_task.remaining_time <= 0:
            self.finish_current_task()
        
        # 2. Verifica preempção por prioridade
        if self.current_task and self.ready_queue:
            highest_priority = min(self.ready_queue, key=lambda t: t.priority)
            if highest_priority.priority < self.current_task.priority:
                self.ready_queue.append(self.current_task)
                self.ready_queue.remove(highest_priority)
                self.current_task = highest_priority
                self.start_task_execution()
        
        # 3. Seleciona próxima tarefa (maior prioridade = menor número)
        if not self.current_task and self.ready_queue:
            self.current_task = min(self.ready_queue, key=lambda t: t.priority)
            self.ready_queue.remove(self.current_task)
            self.start_task_execution()
        
        # 4. Executa tarefa atual
        self.execute_current_task()
        
    def execute_priod(self):
        """Executa algoritmo de Prioridades Dinâmicas"""
        # 1. Aplica aging (a cada 5 unidades de clock)
        self.apply_aging()
        
        # 2. Verifica se tarefa atual terminou
        if self.current_task and self.current_task.remaining_time <= 0:
            self.finish_current_task()
        
        # 3. Verifica preempção por prioridade (dinâmica)
        if self.current_task and self.ready_queue:
            highest_priority = min(self.ready_queue, key=lambda t: t.priority)
            if highest_priority.priority < self.current_task.priority:
                self.ready_queue.append(self.current_task)
                self.ready_queue.remove(highest_priority)
                self.current_task = highest_priority
                self.start_task_execution()
        
        # 4. Seleciona próxima tarefa (maior prioridade = menor número)
        if not self.current_task and self.ready_queue:
            self.current_task = min(self.ready_queue, key=lambda t: t.priority)
            self.ready_queue.remove(self.current_task)
            self.start_task_execution()
        
        # 5. Executa tarefa atual
        self.execute_current_task()
    
    def start_task_execution(self):
        """Inicia a execução de uma tarefa"""
        if self.current_task and not self.current_task.has_started:
            self.current_task.start_time = self.current_clock
            self.current_task.response_time = self.current_clock - self.current_task.arrival_time
            self.current_task.has_started = True
            
    def execute_current_task(self):
        """Executa a tarefa atual por uma unidade de tempo"""
        if self.current_task:
            self.execution_timeline.append(self.current_task.task_id)
            self.current_task.remaining_time -= 1
            print(f"Escalonador: Executando {self.current_task.task_id} (restante: {self.current_task.remaining_time})")
        else:
            self.execution_timeline.append("idle")
            print("Escalonador: CPU idle")
            
    def finish_current_task(self):
        """Finaliza a tarefa atual"""
        if self.current_task:
            self.current_task.finish_time = self.current_clock
            self.finished_tasks.append(self.current_task)
            print(f"Escalonador: Tarefa {self.current_task.task_id} finalizada no clock {self.current_clock}")
            self.current_task = None
            self.current_quantum = 0
    
    def apply_aging(self):
        """Aplica aging para prioridade dinâmica"""
        self.aging_counter += 1
        if self.aging_counter >= 5:  # A cada 5 unidades de clock
            for task in self.ready_queue:
                if task.priority > 1:  # Não reduz abaixo de 1
                    task.priority -= 1
            # Aplica aging na tarefa atual também
            if self.current_task and self.current_task.priority > 1:
                self.current_task.priority -= 1
            self.aging_counter = 0
            print("Escalonador: Aging aplicado às tarefas")
    
    def send_end_signal_to_clock(self):
        """Envia sinal de FIM para o Clock"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.host, self.port_clock))
                message = "FIM".encode()
                sock.send(message)
                print("Escalonador: Sinal de FIM enviado ao Clock")
        except Exception as e:
            print(f"Erro ao enviar sinal de FIM ao Clock: {e}")
            
    def check_simulation_end(self):
        """Verifica se a simulação deve terminar"""
        return (self.all_tasks_emitted and 
                not self.current_task and 
                not self.ready_queue and 
                len(self.finished_tasks) > 0)
                
    def finish_simulation(self):
        """Finaliza a simulação"""
        self.simulation_finished = True
        
        # Envia sinal de fim para Clock
        self.send_end_signal_to_clock()
        
        # Gera arquivo de saída
        self.generate_output_file()
        
        print("Simulação finalizada!")

    def generate_output_file(self):
        """Gera arquivo de saída com resultados da simulação"""
        try:
            # Calcula estatísticas
            total_wait_time = 0
            total_turnaround_time = 0
            total_response_time = 0
            
            for task in self.finished_tasks:
                wait_time = task.start_time - task.arrival_time
                turnaround_time = task.finish_time - task.arrival_time
                response_time = task.response_time if task.response_time else 0
                
                total_wait_time += wait_time
                total_turnaround_time += turnaround_time
                total_response_time += response_time
            
            num_tasks = len(self.finished_tasks)
            avg_wait_time = total_wait_time / num_tasks if num_tasks > 0 else 0
            avg_turnaround_time = total_turnaround_time / num_tasks if num_tasks > 0 else 0
            avg_response_time = total_response_time / num_tasks if num_tasks > 0 else 0
            
            # Cria conteúdo do arquivo
            output_lines = []
            output_lines.append(f"=== RESULTADOS DA SIMULAÇÃO ===")
            output_lines.append(f"Algoritmo: {self.algorithm.upper()}")
            output_lines.append(f"Número de tarefas: {num_tasks}")
            output_lines.append(f"Tempo total de simulação: {self.current_clock}")
            output_lines.append("")
            
            # Timeline de execução
            output_lines.append("Timeline de execução:")
            timeline_str = " | ".join(self.execution_timeline)
            output_lines.append(timeline_str)
            output_lines.append("")
            
            # Estatísticas das tarefas
            output_lines.append("Estatísticas das tarefas:")
            output_lines.append("ID | Chegada | Burst | Início | Fim | Wait | Turnaround | Response")
            for task in self.finished_tasks:
                wait_time = task.start_time - task.arrival_time
                turnaround_time = task.finish_time - task.arrival_time
                response_time = task.response_time if task.response_time else 0
                output_lines.append(f"{task.task_id} | {task.arrival_time} | {task.burst_time} | {task.start_time} | {task.finish_time} | {wait_time} | {turnaround_time} | {response_time}")
            
            output_lines.append("")
            output_lines.append("Médias:")
            output_lines.append(f"Tempo médio de espera: {avg_wait_time:.2f}")
            output_lines.append(f"Tempo médio de turnaround: {avg_turnaround_time:.2f}")
            output_lines.append(f"Tempo médio de resposta: {avg_response_time:.2f}")
            
            # Salva arquivo
            filename = f"resultado_{self.algorithm}.txt"
            with open(filename, 'w') as f:
                f.write('\n'.join(output_lines))
            
            print(f"Escalonador: Arquivo de saída gerado: {filename}")
            
        except Exception as e:
            print(f"Erro ao gerar arquivo de saída: {e}")

    def start_server(self):
        """Inicia o servidor do Escalonador para receber mensagens"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port_escalonador))
            self.server_socket.listen(5)
            
            print(f"Escalonador: Servidor iniciado em {self.host}:{self.port_escalonador}")
            
            while not self.simulation_finished:
                try:
                    # Timeout para verificar se ainda está rodando
                    self.server_socket.settimeout(1.0)
                    
                    try:
                        client_socket, client_address = self.server_socket.accept()
                    except socket.timeout:
                        continue  # Continua o loop para verificar simulation_finished
                    
                    # Processa a conexão usando a função existente
                    self.handle_client(client_socket)
                    
                except Exception as e:
                    if not self.simulation_finished:
                        print(f"Erro no servidor Escalonador: {e}")
                    break
                    
        except Exception as e:
            print(f"Erro ao iniciar servidor Escalonador: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
                print("Escalonador: Servidor encerrado")