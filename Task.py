class Task:
    def __init__(self, task_id: int, arrival_time: int, burst_time: int, priority: int):
        """
        Inicializa uma tarefa.
        
        Args:
            task_id (int): ID da tarefa
            arrival_time (int): Tempo de chegada
            burst_time (int): Tempo de execução
            priority (int): Prioridade (menor número = maior prioridade)
        """
        self.task_id = task_id
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_time = burst_time  # Tempo restante de execução
        self.priority = priority
        self.original_priority = priority  # Para algoritmos dinâmicos
        
        # Campos para estatísticas
        self.start_time = None  # Quando começou a executar
        self.finish_time = None  # Quando terminou
        self.response_time = None  # Tempo de resposta
        self.has_started = False  # Se já começou a executar
        
    def __str__(self):
        return f"Task(id={self.task_id}, arrival={self.arrival_time}, burst={self.burst_time}, priority={self.priority})"
    
    def __repr__(self):
        return self.__str__()
    
    def is_finished(self):
        """Verifica se a tarefa foi finalizada"""
        return self.remaining_time <= 0
    
    def get_wait_time(self):
        """Calcula o tempo de espera"""
        if self.start_time is not None:
            return self.start_time - self.arrival_time
        return 0
    
    def get_turnaround_time(self):
        """Calcula o tempo de turnaround"""
        if self.finish_time is not None:
            return self.finish_time - self.arrival_time
        return 0
    
    def get_response_time(self):
        """Retorna o tempo de resposta"""
        return self.response_time if self.response_time is not None else 0
    
    def reset_priority(self):
        """Restaura a prioridade original da tarefa"""
        self.priority = self.original_priority
    
    def age_priority(self, aging_factor=1):
        """
        Aplica aging na prioridade da tarefa.
        
        Args:
            aging_factor (int): Fator de envelhecimento (padrão 1)
        """
        if self.priority > 1:  # Não permite prioridade menor que 1
            self.priority = max(1, self.priority - aging_factor)
    
    def execute(self, time_units=1):
        """
        Executa a tarefa por um número específico de unidades de tempo.
        
        Args:
            time_units (int): Número de unidades de tempo para executar
            
        Returns:
            int: Tempo realmente executado
        """
        if self.remaining_time <= 0:
            return 0
            
        actual_time = min(time_units, self.remaining_time)
        self.remaining_time -= actual_time
        return actual_time
    
    def get_statistics(self):
        """
        Retorna um dicionário com todas as estatísticas da tarefa.
        
        Returns:
            dict: Dicionário com estatísticas da tarefa
        """
        return {
            'task_id': self.task_id,
            'arrival_time': self.arrival_time,
            'burst_time': self.burst_time,
            'remaining_time': self.remaining_time,
            'priority': self.priority,
            'original_priority': self.original_priority,
            'start_time': self.start_time,
            'finish_time': self.finish_time,
            'response_time': self.get_response_time(),
            'wait_time': self.get_wait_time(),
            'turnaround_time': self.get_turnaround_time(),
            'is_finished': self.is_finished(),
            'has_started': self.has_started
        }
    
    def copy(self):
        """
        Cria uma cópia da tarefa.
        
        Returns:
            Task: Nova instância da tarefa com os mesmos dados
        """
        new_task = Task(self.task_id, self.arrival_time, self.burst_time, self.original_priority)
        new_task.remaining_time = self.remaining_time
        new_task.priority = self.priority
        new_task.start_time = self.start_time
        new_task.finish_time = self.finish_time
        new_task.response_time = self.response_time
        new_task.has_started = self.has_started
        return new_task