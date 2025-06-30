import socket
import json
import threading
import time
import math
from collections import deque
from Task import Task

class Escalonador:
    def __init__(self, host: str, port_escalonador: int, port_clock: int, port_emissor: int, algorithm: str):
        """
        Inicializa o Escalonador.
        Args:
            host (str): Endereço do host
            port_escalonador (int): Porta do Escalonador
            port_clock (int): Porta do Clock
            port_emissor (int): Porta do Emissor
            algorithm (str): Algoritmo de escalonamento (fcfs, rr, sjf, srtf, prioc, priop, priod)
        """
        self.host = host
        self.port_escalonador = port_escalonador
        self.port_clock = port_clock
        self.port_emissor = port_emissor
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
        task.first_execution = True
        task.original_priority = task.priority
        
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
        
        # 2. FCFS não tem preempção, então pula essa parte
        
        # 3. Seleciona próxima tarefa (primeira da fila)
        if not self.current_task and self.ready_queue:
            self.current_task = self.ready_queue.pop(0)  # FIFO
            if self.current_task.start_time is None:
                self.current_task.start_time = self.current_clock
        
        # 4. Executa tarefa atual
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
            self.current_task = self.ready_queue.pop(0)  # FIFO
            if self.current_task.start_time is None:
                self.current_task.start_time = self.current_clock
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
        
        # 2. SJF não preemptivo, então pula essa parte
        
        # 3. Seleciona próxima tarefa (menor burst time)
        if not self.current_task and self.ready_queue:
            self.current_task = min(self.ready_queue, key=lambda t: t.burst_time)
            self.ready_queue.remove(self.current_task)
            if self.current_task.start_time is None:
                self.current_task.start_time = self.current_clock
        
        # 4. Executa tarefa atual
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
                if self.current_task.start_time is None:
                    self.current_task.start_time = self.current_clock
        
        # 3. Seleciona próxima tarefa (menor tempo restante)
        if not self.current_task and self.ready_queue:
            self.current_task = min(self.ready_queue, key=lambda t: t.remaining_time)
            self.ready_queue.remove(self.current_task)
            if self.current_task.start_time is None:
                self.current_task.start_time = self.current_clock
        
        # 4. Executa tarefa atual
        self.execute_current_task()
        
    def execute_prioc(self):
        """Executa algoritmo de Prioridades Fixas Cooperativo"""
        # 1. Verifica se tarefa atual terminou
        if self.current_task and self.current_task.remaining_time <= 0:
            self.finish_current_task()
        
        # 2. Cooperativo não tem preempção, então pula essa parte
        
        # 3. Seleciona próxima tarefa (maior prioridade = menor número)
        if not self.current_task and self.ready_queue:
            self.current_task = min(self.ready_queue, key=lambda t: t.priority)
            self.ready_queue.remove(self.current_task)
            if self.current_task.start_time is None:
                self.current_task.start_time = self.current_clock
        
        # 4. Executa tarefa atual
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
                if self.current_task.start_time is None:
                    self.current_task.start_time = self.current_clock
        
        # 3. Seleciona próxima tarefa (maior prioridade = menor número)
        if not self.current_task and self.ready_queue:
            self.current_task = min(self.ready_queue, key=lambda t: t.priority)
            self.ready_queue.remove(self.current_task)
            if self.current_task.start_time is None:
                self.current_task.start_time = self.current_clock
        
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
                if self.current_task.start_time is None:
                    self.current_task.start_time = self.current_clock
        
        # 4. Seleciona próxima tarefa (maior prioridade = menor número)
        if not self.current_task and self.ready_queue:
            self.current_task = min(self.ready_queue, key=lambda t: t.priority)
            self.ready_queue.remove(self.current_task)
            if self.current_task.start_time is None:
                self.current_task.start_time = self.current_clock
        
        # 5. Executa tarefa atual
        self.execute_current_task()
        
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
        
        # Gera arquivo de saída -> Pode ser colocado aqui ou na main(ainda tem que ver) -> se for aqui, falta a função generate_output_file
        self.generate_output_file()
        
        # Fecha servidor -> O servidor deve ser iniciado na main. Deve-se analisar se fecha aqui ou lá. Dependendo da escolha, mudar os outros arquivos.
        if self.server_socket:
            self.server_socket.close()
            
        print("Simulação finalizada!")