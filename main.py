import sys
import multiprocessing
import time

from Task import Task
from Clock import Clock
from Emissor import Emissor
from Escalonador import Escalonador

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

def run_clock_process(host, port_clock, port_emissor, port_escalonador, clock_delay, emissor_escalonador_delay):
    """Função para executar o processo do Clock"""
    try:
        print(f"[CLOCK] Iniciando processo do Clock (PID: {multiprocessing.current_process().pid})")
        clock = Clock(host, port_clock, clock_delay, port_emissor, port_escalonador, emissor_escalonador_delay)
        clock.start_clock()
    except Exception as e:
        print(f"[CLOCK] Erro no processo do Clock: {e}")

def run_emissor_process(host, port_emissor, port_escalonador, port_clock, tasks):
    """Função para executar o processo do Emissor"""
    try:
        print(f"[EMISSOR] Iniciando processo do Emissor (PID: {multiprocessing.current_process().pid})")
        emissor = Emissor(host, port_emissor, port_escalonador, port_clock, tasks)
        emissor.start_server()
    except Exception as e:
        print(f"[EMISSOR] Erro no processo do Emissor: {e}")

def run_escalonador_process(host, port_escalonador, port_clock, algorithm):
    """Função para executar o processo do Escalonador"""
    try:
        print(f"[ESCALONADOR] Iniciando processo do Escalonador (PID: {multiprocessing.current_process().pid})")
        escalonador = Escalonador(host, port_escalonador, port_clock, algorithm)
        escalonador.start_server()
    except Exception as e:
        print(f"[ESCALONADOR] Erro no processo do Escalonador: {e}")

def main():
    """
    Função principal que inicia a simulação com processos separados.
    """

    # Verifica se o número correto de argumentos foi fornecido
    if len(sys.argv) != 3:
        print("Uso: python main.py <arquivo_de_tarefas> <algoritmo>")
        print("Exemplo: python main.py ./entrada00.txt fcfs")
        sys.exit(1)

    tasks_file: str = sys.argv[1]
    algorithm: str = sys.argv[2].lower()

    # Verifica se o algoritmo de escalonamento existe
    if algorithm not in ['fcfs', 'rr', 'sjf', 'srtf', 'prioc', 'priop', 'priod']:
        print("Algoritmo de escalonamento inválido.")
        print("Algoritmos disponíveis: fcfs, rr, sjf, srtf, prioc, priop, priod")
        sys.exit(1)

    # Lê as tarefas do arquivo
    tasks: list[Task] = read_tasks_from_file(tasks_file)
    if not tasks:
        print("Nenhuma tarefa encontrada no arquivo.")
        sys.exit(1)
        
    print("=== SIMULAÇÃO DE ESCALONAMENTO DE TAREFAS ===")
    print(f"Arquivo de tarefas: {tasks_file}")
    print(f"Algoritmo: {algorithm}")
    print(f"Número de tarefas: {len(tasks)}")
    print("=" * 50)
    
    # Lista para armazenar os processos
    processes = []
    
    try:
        # Inicia o processo do Escalonador primeiro (servidor)
        escalonador_process = multiprocessing.Process(
            target=run_escalonador_process,
            args=(HOST, PORT_ESCALONADOR, PORT_CLOCK, algorithm),
            name="Escalonador"
        )
        escalonador_process.start()
        processes.append(escalonador_process)
        print(f"Processo Escalonador iniciado (PID: {escalonador_process.pid})")
        time.sleep(1)  # Aguarda o servidor subir
        
        # Inicia o processo do Emissor (servidor)
        emissor_process = multiprocessing.Process(
            target=run_emissor_process,
            args=(HOST, PORT_EMISSOR, PORT_ESCALONADOR, PORT_CLOCK, tasks),
            name="Emissor"
        )
        emissor_process.start()
        processes.append(emissor_process)
        print(f"Processo Emissor iniciado (PID: {emissor_process.pid})")
        time.sleep(1)  # Aguarda o servidor subir
        
        # Inicia o processo do Clock (cliente)
        clock_process = multiprocessing.Process(
            target=run_clock_process,
            args=(HOST, PORT_CLOCK, PORT_EMISSOR, PORT_ESCALONADOR, CLOCK_DELAY_MS, EMISSOR_ESCALONADOR_DELAY_MS),
            name="Clock"
        )
        clock_process.start()
        processes.append(clock_process)
        print(f"Processo Clock iniciado (PID: {clock_process.pid})")
        
        print("\nTodos os processos iniciados. Aguardando conclusão da simulação...")
        print("Pressione Ctrl+C para interromper.\n")
        
        # Aguarda todos os processos terminarem
        for process in processes:
            process.join()
            print(f"Processo {process.name} (PID: {process.pid}) finalizou com código: {process.exitcode}")
            
    except KeyboardInterrupt:
        print("\nInterrupção detectada. Finalizando processos...")
        
        # Termina todos os processos
        for process in processes:
            if process.is_alive():
                print(f"Terminando processo {process.name} (PID: {process.pid})")
                process.terminate()
                process.join(timeout=5)
                
                # Se não terminou, força a finalização
                if process.is_alive():
                    print(f"Forçando finalização do processo {process.name}")
                    process.kill()
                    process.join()
                    
    except Exception as e:
        print(f"Erro na simulação: {e}")
        
        # Limpa os processos em caso de erro
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join()
                
        sys.exit(1)
    
    print("Simulação concluída.")

if __name__ == "__main__":
    # Necessário para multiprocessing no Windows e algumas versões do Linux
    multiprocessing.set_start_method('spawn', force=True)
    main()