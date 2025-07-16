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
