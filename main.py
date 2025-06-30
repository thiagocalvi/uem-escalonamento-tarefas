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
    def start_server(self):
        """Inicia o servidor do clock e aceita conexões"""
        self.clock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clock_socket.bind((self.host, self.port_clock))
        self.clock_socket.listen(2)  # Máximo 2 conexões (emissor + escalonador)
        
        print(f"Clock iniciado na porta {self.port_clock}")
        print("Aguardando conexões do Emissor e Escalonador...")
        
        # Aceita primeira conexão (pode ser emissor ou escalonador)
        conn1, addr1 = self.clock_socket.accept()
        print(f"Primeira conexão aceita: {addr1}")
        
        # Aceita segunda conexão
        conn2, addr2 = self.clock_socket.accept()
        print(f"Segunda conexão aceita: {addr2}")

if __name__ == "__main__":
    main()

'''
Acredito que faça mais sentido iniciar o servidor em cada uma das funções, e não na main.
Na main, deve ter a função de inicialização de cada processo (Clock, Emissor, Escalonador), não do servidor.
Assim, ao iniciar o processo, já inicia o servidor por consequencia.
Só teria que definir o start_processo e start_server em cada uma das classes correspondentes (Clock, Emissor, Escalonador).

A ideia é demonstrada no código abaixo:

import sys
import multiprocessing
import time
from Task import Task
from Clock import Clock
from Emissor import Emissor  # Você vai criar esse
from Escalonador import Escalonador  # Você vai criar esse

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
                task_id = int(parts[0][1:])  # Remove o 't' e converte para int
                arrival_time = int(parts[1].strip())
                burst_time = int(parts[2].strip())
                priority = int(parts[3].strip())
                task = Task(task_id, arrival_time, burst_time, priority)
                tasks.append(task)
    return tasks

def start_clock_process():
    """Função para iniciar o processo Clock"""
    print("Iniciando processo Clock...")
    clock = Clock(
        host=HOST,
        port_clock=PORT_CLOCK,
        clock_delay=CLOCK_DELAY_MS,
        port_emissor=PORT_EMISSOR,
        port_escalonador=PORT_ESCALONADOR,
        emissor_escalonador_delay=EMISSOR_ESCALONADOR_DELAY_MS
    )
    clock.start_clock()

def start_emissor_process(tasks_file: str):
    """Função para iniciar o processo Emissor"""
    print("Iniciando processo Emissor...")
    # Aguarda um pouco para garantir que o Clock já está rodando
    time.sleep(1)
    
    emissor = Emissor(
        host=HOST,
        port_clock=PORT_CLOCK,
        port_escalonador=PORT_ESCALONADOR,
        tasks_file=tasks_file
    )
    emissor.start()

def start_escalonador_process(algorithm: str, tasks_file: str):
    """Função para iniciar o processo Escalonador"""
    print("Iniciando processo Escalonador...")
    # Aguarda um pouco para garantir que o Clock já está rodando
    time.sleep(1)
    
    escalonador = Escalonador(
        host=HOST,
        port_clock=PORT_CLOCK,
        port_emissor=PORT_EMISSOR,
        algorithm=algorithm,
        output_file=f"resultado_{algorithm}.txt"
    )
    escalonador.start()

def main():
    """
    Função principal que inicia a simulação.
    """
    # Verifica se o número correto de argumentos foi fornecido
    if len(sys.argv) != 3:
        print("Uso: python main.py <arquivo_de_tarefas> <algoritmo>")
        print("Exemplo: python main.py tasks.txt fcfs")
        sys.exit(1)
    
    tasks_file: str = sys.argv[1]
    algorithm: str = sys.argv[2].lower()
    
    # Verifica se o algoritmo é válido
    if algorithm not in ['fcfs', 'rr', 'sjf', 'srtf', 'prioc', 'priop', 'priod']:
        print("Algoritmo de escalonamento inválido.")
        print("Algoritmos válidos: fcfs, rr, sjf, srtf, prioc, priop, priod")
        sys.exit(1)
    
    # Lê as tarefas do arquivo para validar
    try:
        tasks: list[Task] = read_tasks_from_file(tasks_file)
        if not tasks:
            print("Nenhuma tarefa encontrada no arquivo.")
            sys.exit(1)
        print(f"Arquivo lido com sucesso: {len(tasks)} tarefas encontradas")
    except FileNotFoundError:
        print(f"Arquivo {tasks_file} não encontrado.")
        sys.exit(1)
    except Exception as e:
        print(f"Erro ao ler arquivo: {e}")
        sys.exit(1)
    
    print(f"Iniciando simulação com algoritmo: {algorithm.upper()}")
    print(f"Arquivo de tarefas: {tasks_file}")
    print("-" * 50)
    
    # Cria os processos
    clock_process = multiprocessing.Process(target=start_clock_process)
    emissor_process = multiprocessing.Process(target=start_emissor_process, args=(tasks_file,))
    escalonador_process = multiprocessing.Process(target=start_escalonador_process, args=(algorithm, tasks_file))
    
    try:
        # Inicia os processos
        print("Iniciando processos...")
        
        # 1. Inicia o Clock primeiro (ele é o servidor)
        clock_process.start()
        
        # 2. Aguarda um pouco e inicia os outros (eles são clientes)
        time.sleep(0.5)
        emissor_process.start()
        escalonador_process.start()
        
        print("Todos os processos iniciados!")
        print("Simulação em andamento...")
        print("Use Ctrl+C para interromper")
        
        # Aguarda os processos terminarem
        escalonador_process.join()  # Escalonador termina primeiro
        emissor_process.join()      # Emissor termina depois
        clock_process.join()        # Clock termina por último
        
        print("-" * 50)
        print("Simulação concluída!")
        print(f"Arquivo de saída gerado: resultado_{algorithm}.txt")
        
    except KeyboardInterrupt:
        print("\nInterrompendo simulação...")
        
        # Termina os processos
        if clock_process.is_alive():
            clock_process.terminate()
        if emissor_process.is_alive():
            emissor_process.terminate()
        if escalonador_process.is_alive():
            escalonador_process.terminate()
            
        # Aguarda a finalização
        clock_process.join()
        emissor_process.join()
        escalonador_process.join()
        
        print("Simulação interrompida.")
    
    except Exception as e:
        print(f"Erro durante a simulação: {e}")
        
        # Termina os processos em caso de erro
        if clock_process.is_alive():
            clock_process.terminate()
        if emissor_process.is_alive():
            emissor_process.terminate()
        if escalonador_process.is_alive():
            escalonador_process.terminate()
'''