import socket
import json
from Task import Task

class Escalonador:
    def __init__(self, host: str, port_escalonador: int, port_clock: int, port_emissor: int, algorithm: str):
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
        
        # Para controle de sincronização com clock
        self.pending_tasks = []  # Tarefas recebidas aguardando próximo clock
        self.pending_all_tasks_emitted = False  # Flag para ALL_TASKS_EMITTED pendente
        
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
        """
            Executa o algoritmo de escalonamento selecionado
        """
        self.algorithm_map[self.algorithm]()

    def handle_client(self, client_socket):
        """
            Processa mensagens recebidas - apenas armazena, execução acontece no clock
        """
        try:
            data = client_socket.recv(1024)
            if data:
                message = data.decode()
                
                # Verifica se é mensagem do Clock (número simples)
                if message.isdigit():
                    self.handle_clock_message(int(message))

                elif message.startswith("{") and message.endswith("}"):
                    # Mensagem JSON do Emissor - apenas armazena para processar no próximo clock
                    try:
                        json_data = json.loads(message)
                        if json_data.get('type') == 'TASK':
                            # Armazena tarefa para processar no próximo clock
                            self.pending_tasks.append(json_data)
                        elif json_data.get('type') == 'ALL_TASKS_EMITTED':
                            # Armazena flag para processar no próximo clock
                            self.pending_all_tasks_emitted = True
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
        task.dynamic_priority = task.priority
        # CORRIGIDO: usa arrival_time como entrada na fila, não current_clock
        task.ready_queue_entry_time = task.arrival_time
        
        self.ready_queue.append(task)
        print(f"Escalonador: Tarefa {task.task_id} adicionada à fila (clock={self.current_clock})")
        
    def handle_all_tasks_emitted(self):
        """Processa sinal de que todas as tarefas foram emitidas"""
        self.all_tasks_emitted = True
        print("Escalonador: Todas as tarefas foram emitidas")
        
    def handle_clock_message(self, clock_value):
        """Processa mensagem de clock e executa operações pendentes"""
        self.current_clock = clock_value
        print(f"Escalonador: Recebido clock {self.current_clock}")
        
        # 1. Primeiro processa tarefas pendentes
        while self.pending_tasks:
            task_data = self.pending_tasks.pop(0)
            self.handle_new_task(task_data)
        
        # 2. Processa flag de todas as tarefas emitidas
        if self.pending_all_tasks_emitted:
            self.handle_all_tasks_emitted()
            self.pending_all_tasks_emitted = False
        
        # 3. Executa o algoritmo de escalonamento
        self.execute_scheduling()
        
        # 4. Verifica se a simulação terminou
        if self.check_simulation_end():
            self.finish_simulation()
    
    def execute_fcfs(self):
        """Executa algoritmo First-Come, First-Served"""
        # 1. Verifica se tarefa atual terminou
        if self.current_task and self.current_task.remaining_time == 0:
            self.finish_current_task()
        
        # 2. Seleciona próxima tarefa (primeira da fila por arrival_time)
        if not self.current_task and self.ready_queue:
            # Ordena por arrival_time para garantir FCFS
            #self.ready_queue.sort(key=lambda t: t.arrival_time)
            self.current_task = self.ready_queue.pop(0)
            self.start_task_execution()
        
        # 3. Executa tarefa atual
        if self.current_task:
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
            #self.ready_queue.sort(key=lambda t: t.arrival_time)
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
        if self.current_task:
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
        print(f'Tarefas na fila de prontas (id , prioridade dinamica): {[(t.task_id, t.dynamic_priority) for t in self.ready_queue]}')
        
        # Verifica se tarefa terminou
        if self.current_task and self.current_task.remaining_time <= 0:
            self.finish_current_task()
            if not self.ready_queue:
                return
            self.apply_aging()
            
            self.current_task = min(self.ready_queue, key=lambda t: (t.dynamic_priority, t.arrival_time)) # Seleciona a tarefa com maior prioridade dinâmica
            self.ready_queue.remove(self.current_task) # Remove da fila de prontas
            self.current_task.dynamic_priority = self.current_task.original_priority # Restaura prioridade original
            
            if not self.current_task.has_started:
                self.start_task_execution()
                self.apply_aging()
        
        # Seleciona próxima tarefa se não há tarefa executando
        elif not self.current_task and self.ready_queue:
        
            self.current_task = min(self.ready_queue, key=lambda t: (t.dynamic_priority, t.arrival_time)) # Seleciona a tarefa com maior prioridade dinâmica
            
            print(f'Tarefa selecionada para execução: id:{self.current_task.task_id} , Pd: {self.current_task.dynamic_priority}')
            
            self.ready_queue.remove(self.current_task) # Remove da fila de prontas

            self.current_task.dynamic_priority = self.current_task.original_priority # Restaura prioridade original

            print(f'Tarefas na fila de prontas (id , prioridade dinamica): {[(t.task_id, t.dynamic_priority) for t in self.ready_queue]}')

            if not self.current_task.has_started:
                self.start_task_execution()

                self.apply_aging()
            
    

            # Verifica preempção por prioridade (dinâmica)
        elif self.current_task and self.ready_queue:
            # Encontra a tarefa com maior prioridade na fila (menor valor = maior prioridade)
            # Em caso de empate, usa arrival_time como critério de desempate
            highest_priority = min(self.ready_queue, key=lambda t: (t.dynamic_priority, t.arrival_time))
            print(f'Tarefa selecionada (id , prioridade dinamica): {self.current_task.task_id}, {self.current_task.dynamic_priority}')
            
            if highest_priority.dynamic_priority < self.current_task.dynamic_priority:
                print(f"Escalonador: Preempção dinâmica: t{highest_priority.task_id}(prio={highest_priority.dynamic_priority}) preempta t{self.current_task.task_id}(prio={self.current_task.dynamic_priority})")
                print(f'tarefas na fila: {[(t.task_id, t.dynamic_priority) for t in self.ready_queue]}')
                self.ready_queue.remove(highest_priority)
                self.current_task.dynamic_priority = self.current_task.original_priority
                self.ready_queue.append(self.current_task)
                self.current_task = highest_priority
                self.current_task.dynamic_priority = highest_priority.original_priority
                print(f'Tarefas na fila de prontas (id , prioridade dinamica): {[(t.task_id, t.dynamic_priority) for t in self.ready_queue]}')
                if not self.current_task.has_started:
                    self.start_task_execution()

        if self.current_task:
            self.execute_current_task()

        
    



    def start_task_execution(self):
        """Inicia a execução de uma tarefa"""
        if self.current_task and not self.current_task.has_started:
            self.current_task.start_time = self.current_clock
            self.current_task.response_time = self.current_clock - self.current_task.arrival_time
            self.current_task.has_started = True
            print(f"Escalonador: Iniciando execução da tarefa t{self.current_task.task_id} no clock {self.current_clock}")
            
    def execute_current_task(self):
        """Executa a tarefa atual por uma unidade de tempo"""
        if self.current_task:
            # Registra no timeline com formato correto (t0, t1, etc.)
            self.execution_timeline.append(f"t{self.current_task.task_id}")
            self.current_task.remaining_time -= 1
            print(f"Escalonador: Executando t{self.current_task.task_id} (restante: {self.current_task.remaining_time})")
            
    def finish_current_task(self):
        """Finaliza a tarefa atual"""
        if self.current_task:
            # finish_time é o clock atual (momento exato da finalização)
            self.current_task.finish_time = self.current_clock

            self.finished_tasks.append(self.current_task)
            print(f"Escalonador: Tarefa t{self.current_task.task_id} finalizada no clock {self.current_clock}")
            self.current_task = None
            self.current_quantum = 0
    
    def apply_aging(self):
        """Aplica aging para prioridade dinâmica"""        
        for task in self.ready_queue:
            task.dynamic_priority -= 1  # Aumenta prioridade dinâmica
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

    def send_end_signal_to_emissor(self):
        """Envia sinal de FIM para o Emissor"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.host, self.port_emissor))
                message = "FIM".encode()
                sock.send(message)
                print("Escalonador: Sinal de FIM enviado ao Emissor")
        except Exception as e:
            print(f"Erro ao enviar sinal de FIM ao Emissor: {e}")
            
    def check_simulation_end(self):
        """Verifica se a simulação deve terminar"""
        return (self.all_tasks_emitted and 
                not self.current_task and 
                not self.ready_queue and 
                len(self.finished_tasks) > 0)
                
    def finish_simulation(self):
        """Finaliza a simulação"""
        self.simulation_finished = True
        
        # Envia sinal de fim para Clock e Emissor
        self.send_end_signal_to_clock()
        self.send_end_signal_to_emissor()
        
        # Gera arquivo de saída
        self.generate_output_file()
        
        print("Simulação finalizada!")

    def generate_output_file(self):
        """Gera arquivo de saída com resultados da simulação no formato correto"""
        try:
            import math
            
            # 1. LINHA 1: Timeline de execução separado por ";"
            # Remove "idle" do timeline (só mostra tarefas executadas)
            timeline_filtered = [item for item in self.execution_timeline if item != "idle"]
            timeline_str = ";".join(timeline_filtered)
            
            # 2. LINHAS DAS TAREFAS: ID;clock de ingresso na fila;clock de finalização;turnaround time;waiting time
            task_lines = []
            total_turnaround_time = 0
            total_waiting_time = 0
            
            # Ordena tarefas por ID para saída consistente
            sorted_tasks = sorted(self.finished_tasks, key=lambda t: t.task_id)
            
            for task in sorted_tasks:
                # Cálculos CORRETOS conforme definições padrão:
                # - Turnaround time = tempo de finalização - tempo de chegada (tempo total no sistema)
                # - Waiting time = turnaround time - burst time (tempo esperando, não executando)
                turnaround_time = task.finish_time - task.arrival_time
                waiting_time = turnaround_time - task.burst_time
                
                total_turnaround_time += turnaround_time
                total_waiting_time += waiting_time
                
                # Formato: ID;clock de ingresso na fila;clock de finalização;turnaround time;waiting time
                task_line = f"t{task.task_id};{task.ready_queue_entry_time};{task.finish_time};{turnaround_time};{waiting_time}"
                task_lines.append(task_line)
            
            # 3. LINHA FINAL: Médias arredondadas para cima com 1 casa decimal
            num_tasks = len(self.finished_tasks)
            if num_tasks > 0:
                avg_turnaround = total_turnaround_time / num_tasks
                avg_waiting = total_waiting_time / num_tasks
                
                # Arredonda para cima com 1 casa decimal
                avg_turnaround_rounded = math.ceil(avg_turnaround * 10) / 10
                avg_waiting_rounded = math.ceil(avg_waiting * 10) / 10
            else:
                avg_turnaround_rounded = 0.0
                avg_waiting_rounded = 0.0
            
            # 4. CONSTRÓI O ARQUIVO NO FORMATO EXATO
            output_lines = []
            
            # Linha 1: Timeline
            output_lines.append(timeline_str)
            
            # Linhas das tarefas
            for task_line in task_lines:
                output_lines.append(task_line)
            
            # Linha final: Médias
            averages_line = f"{avg_turnaround_rounded};{avg_waiting_rounded}"
            output_lines.append(averages_line)
            
            # 5. SALVA O ARQUIVO
            filename = f"resultado_{self.algorithm}.txt"
            with open(filename, 'w') as f:
                f.write('\n'.join(output_lines))
            
            print(f"Escalonador: Arquivo de saída gerado: {filename}")
                        
        except Exception as e:
            print(f"Erro ao gerar arquivo de saída: {e}")
            import traceback
            traceback.print_exc()

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