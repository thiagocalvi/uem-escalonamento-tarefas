import sys

from Task import Task
from Clock import Clock

# Configurações
HOST: str = '127.0.0.1'  # Endereço localhost
PORT_CLOCK: int = 4000 # Porta do Clock
PORT_EMISSOR: int = 4001 # Porta do Emissor de Tarefas 
PORT_ESCALONADOR: int = 4002 # Porta do Escalonador de Tarefas 
CLOCK_DELAY_MS: int = 100 # Delay do clock em milissegundos 
EMISSOR_ESCALONADOR_DELAY_MS: int = 5 # Atraso entre o envio para Emissor e Escalonador 

def read_tasks_from_file(file_path) -> list[Task]:
    """
    Lê o arquivo de texto "file_path".txt contendo as tarefas, uma em cada linha, no formato t0;0;6;2
    e retorna uma fila de objetos Task.
    
    Args:
        file_path (str): Caminho para o arquivo txt contendo as tarefas.
    Returns:
        list[Task]: Fila de objetos Task representando as tarefas lidas do arquivo.
    """
    tasks: list[Task] = []
    
    with open(file_path, 'r') as file:
        for line in file:
            parts = line.strip().split(';')
            if len(parts) == 4:
                task_id = int(parts[0][1])
                arrival_time = int(parts[1].strip())
                burst_time = int(parts[2].strip())
                priority = int(parts[3].strip())
                task = Task(task_id, arrival_time, burst_time, priority)
                tasks.append(task)
    return tasks

def main():
    """
    Função principal que inicia a simulação.
    """

    # Verifica se o número correto de argumentos foi fornecido
    if len(sys.argv) != 3:
        print("Uso: python main.py <algoritmo> <arquivo_de_tarefas>")
        print("Exemplo: python main.py fcfs tasks.txt")
        sys.exit(1)

    tasks_file: str = sys.argv[1]
    algorithm: str = sys.argv[2].lower()

    # Verifica se o arquivo de escalonamento existe
    if algorithm not in ['fcfs', 'rr', 'sjf', 'srtf', 'prioc', 'priop', 'priod']:
        print("Algoritmo de escalonamento inválido.")
        sys.exit(1)

    # Lê as tarefas do arquivo
    tasks: list[Task] = read_tasks_from_file(tasks_file)
    if not tasks:
        print("Nenhuma tarefa encontrada no arquivo.")
        sys.exit(1)
    
    # Inicia o servidor de clock

    # Inicia o servidor de emissor de tarefas

    # Inicia o servidor de escalonador de tarefas


if __name__ == "__main__":
    main()