class Task:
    def __init__(self, task_id: int, arrival_time: int, burst_time: int, priority: int):
        """
        Inicializa uma nova instância de Tarefa.

        Args:
            task_id (int): O identificador único da tarefa (ex: "0").
            arrival_time (int): O tempo de ingresso da tarefa na fila de prontas (unidade de clock).
            burst_time (int): A duração prevista de execução da tarefa (unidade de clock).
            priority (int): A prioridade da tarefa. Menor valor numérico = maior prioridade.
        """
        self.task_id = task_id
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.priority = priority
        self.remaining_time = burst_time # Tempo restante para execução

    