import sys
import multiprocessing
import time
import signal
import os
import atexit
from pathlib import Path

from Task import Task
from Clock import Clock
from Emissor import Emissor
from Escalonador import Escalonador

# Configurações
HOST: str = '127.0.0.1'
PORT_CLOCK: int = 4000
PORT_EMISSOR: int = 4001
PORT_ESCALONADOR: int = 4002
CLOCK_DELAY_MS: int = 100
EMISSOR_ESCALONADOR_DELAY_MS: int = 5

# Lista global de processos para cleanup
processes = []

def read_tasks_from_file(file_path: str) -> list[Task]:
    """
    Lê o arquivo de texto contendo as tarefas.
    
    Args:
        file_path (str): Caminho para o arquivo txt contendo as tarefas.
    Returns:
        list[Task]: Lista de objetos Task representando as tarefas lidas do arquivo.
    """
    tasks: list[Task] = []
    
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            print(f"Erro: Arquivo '{file_path}' não encontrado.")
            return []
        
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if not line or line.startswith('#'):  # Pula linhas vazias e comentários
                    continue
                    
                parts = line.split(';')
                if len(parts) == 4:
                    try:
                        # Extrai o número do ID da tarefa (t0 -> 0, t1 -> 1, etc.)
                        task_id_str = parts[0].strip()
                        if task_id_str.startswith('t'):
                            task_id = int(task_id_str[1:])
                        else:
                            task_id = int(task_id_str)
                            
                        arrival_time = int(parts[1].strip())
                        burst_time = int(parts[2].strip())
                        priority = int(parts[3].strip())
                        
                        # Validações básicas
                        if arrival_time < 0 or burst_time <= 0 or priority < 1:
                            print(f"Aviso: Valores inválidos na linha {line_num}: {line}")
                            continue
                            
                        task = Task(task_id, arrival_time, burst_time, priority)
                        tasks.append(task)
                        
                    except ValueError as e:
                        print(f"Erro ao processar linha {line_num}: {line} - {e}")
                        continue
                else:
                    print(f"Formato inválido na linha {line_num}: {line}")
                    print("Formato esperado: id;arrival_time;burst_time;priority")
                    
    except FileNotFoundError:
        print(f"Erro: Arquivo '{file_path}' não encontrado.")
        return []
    except PermissionError:
        print(f"Erro: Sem permissão para ler o arquivo '{file_path}'.")
        return []
    except Exception as e:
        print(f"Erro inesperado ao ler arquivo '{file_path}': {e}")
        return []
    
    if not tasks:
        print("Nenhuma tarefa válida encontrada no arquivo.")
        return []
    
    # Ordena tarefas por tempo de chegada
    tasks.sort(key=lambda t: t.arrival_time)
    
    print(f"Sucesso: {len(tasks)} tarefa(s) carregada(s) do arquivo '{file_path}'")
    return tasks

def signal_handler(signum, frame):
    """Handler para sinais de interrupção"""
    print(f"\nSinal {signum} recebido. Finalizando processos...")
    cleanup_processes(processes)
    sys.exit(0)

def cleanup_processes(process_list):
    """Limpa os processos de forma segura"""
    if not process_list:
        return
        
    print("Finalizando processos...")
    
    for process in process_list:
        if process.is_alive():
            print(f"  Terminando processo {process.name} (PID: {process.pid})")
            process.terminate()
    
    # Aguarda processos terminarem
    time.sleep(2)
    
    # Força finalização se necessário
    for process in process_list:
        if process.is_alive():
            print(f"  Forçando finalização do processo {process.name}")
            process.kill()
            try:
                process.join(timeout=1)
            except:
                pass

def run_clock_process(host, port_clock, port_emissor, port_escalonador, clock_delay, emissor_escalonador_delay):
    """Função para executar o processo do Clock"""
    try:
        print(f"[CLOCK] Iniciando processo do Clock (PID: {os.getpid()})")
        clock = Clock(host, port_clock, clock_delay, port_emissor, port_escalonador, emissor_escalonador_delay)
        clock.start_clock()
        print(f"[CLOCK] Processo finalizado normalmente")
    except KeyboardInterrupt:
        print(f"[CLOCK] Processo interrompido por sinal")
    except Exception as e:
        print(f"[CLOCK] Erro no processo do Clock: {e}")

def run_emissor_process(host, port_emissor, port_escalonador, port_clock, tasks):
    """Função para executar o processo do Emissor"""
    try:
        print(f"[EMISSOR] Iniciando processo do Emissor (PID: {os.getpid()})")
        emissor = Emissor(host, port_emissor, port_escalonador, port_clock, tasks)
        emissor.start_server()
        print(f"[EMISSOR] Processo finalizado normalmente")
    except KeyboardInterrupt:
        print(f"[EMISSOR] Processo interrompido por sinal")
    except Exception as e:
        print(f"[EMISSOR] Erro no processo do Emissor: {e}")

def run_escalonador_process(host, port_escalonador, port_clock, algorithm):
    """Função para executar o processo do Escalonador"""
    try:
        print(f"[ESCALONADOR] Iniciando processo do Escalonador (PID: {os.getpid()})")
        escalonador = Escalonador(host, port_escalonador, port_clock, algorithm)
        escalonador.start_server()
        print(f"[ESCALONADOR] Processo finalizado normalmente")
    except KeyboardInterrupt:
        print(f"[ESCALONADOR] Processo interrompido por sinal")
    except Exception as e:
        print(f"[ESCALONADOR] Erro no processo do Escalonador: {e}")

def validate_ports():
    """Valida se as portas estão disponíveis"""
    import socket
    
    ports = [PORT_CLOCK, PORT_EMISSOR, PORT_ESCALONADOR]
    
    for port in ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind((HOST, port))
        except OSError as e:
            print(f"Erro: Porta {port} não está disponível: {e}")
            return False
    
    return True

def print_task_summary(tasks):
    """Imprime resumo das tarefas carregadas"""
    print("\n=== RESUMO DAS TAREFAS ===")
    print(f"{'ID':<4} {'Chegada':<8} {'Burst':<6} {'Prioridade':<10}")
    print("-" * 32)
    
    for task in tasks:
        print(f"{task.task_id:<4} {task.arrival_time:<8} {task.burst_time:<6} {task.priority:<10}")
    
    print("-" * 32)
    print(f"Total: {len(tasks)} tarefa(s)")
    print(f"Tempo total simulado estimado: {max(task.arrival_time + task.burst_time for task in tasks)}")

def main():
    """Função principal que inicia a simulação com processos separados."""
    
    global processes
    
    # Configura handlers para sinais
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Registra função de cleanup para ser chamada na saída
    atexit.register(cleanup_processes, processes)
    
    print("=== SIMULADOR DE ESCALONAMENTO DE TAREFAS ===")
    print(f"Host: {HOST}")
    print(f"Portas: Clock={PORT_CLOCK}, Emissor={PORT_EMISSOR}, Escalonador={PORT_ESCALONADOR}")
    print(f"Delays: Clock={CLOCK_DELAY_MS}ms, Emissor-Escalonador={EMISSOR_ESCALONADOR_DELAY_MS}ms")
    print("=" * 50)
    
    # Verifica argumentos
    if len(sys.argv) != 3:
        print("\nUso: python main.py <arquivo_de_tarefas> <algoritmo>")
        print("Exemplo: python main.py ./entrada00.txt fcfs")
        print("\nAlgoritmos disponíveis:")
        print("  fcfs  - First Come First Served")
        print("  rr    - Round Robin")
        print("  sjf   - Shortest Job First")
        print("  srtf  - Shortest Remaining Time First")
        print("  prioc - Priority Cooperative")
        print("  priop - Priority Preemptive")
        print("  priod - Priority Dynamic")
        sys.exit(1)

    tasks_file: str = sys.argv[1]
    algorithm: str = sys.argv[2].lower()

    # Valida algoritmo
    valid_algorithms = {
        'fcfs': 'First Come First Served',
        'rr': 'Round Robin',
        'sjf': 'Shortest Job First',
        'srtf': 'Shortest Remaining Time First',
        'prioc': 'Priority Cooperative',
        'priop': 'Priority Preemptive',
        'priod': 'Priority Dynamic'
    }
    
    if algorithm not in valid_algorithms:
        print(f"\nErro: Algoritmo '{algorithm}' não reconhecido.")
        print("Algoritmos disponíveis:")
        for alg, desc in valid_algorithms.items():
            print(f"  {alg:<6} - {desc}")
        sys.exit(1)

    print(f"\nAlgoritmo selecionado: {algorithm.upper()} ({valid_algorithms[algorithm]})")
    
    # Valida se as portas estão disponíveis
    if not validate_ports():
        print("Erro: Algumas portas não estão disponíveis. Verifique se não há outros processos rodando.")
        sys.exit(1)
    
    # Lê as tarefas
    tasks: list[Task] = read_tasks_from_file(tasks_file)
    if not tasks:
        print("Erro: Nenhuma tarefa válida encontrada. Verifique o arquivo de entrada.")
        sys.exit(1)
    
    # Imprime resumo das tarefas
    print_task_summary(tasks)
    
    print("\n=== INICIANDO SIMULAÇÃO ===")
    
    try:
        # Inicia o processo do Escalonador primeiro (servidor)
        escalonador_process = multiprocessing.Process(
            target=run_escalonador_process,
            args=(HOST, PORT_ESCALONADOR, PORT_CLOCK, algorithm),
            name="Escalonador"
        )
        escalonador_process.start()
        processes.append(escalonador_process)
        print(f"✓ Processo Escalonador iniciado (PID: {escalonador_process.pid})")
        time.sleep(1)  # Aguarda o servidor subir
        
        # Inicia o processo do Emissor (servidor)
        emissor_process = multiprocessing.Process(
            target=run_emissor_process,
            args=(HOST, PORT_EMISSOR, PORT_ESCALONADOR, PORT_CLOCK, tasks),
            name="Emissor"
        )
        emissor_process.start()
        processes.append(emissor_process)
        print(f"✓ Processo Emissor iniciado (PID: {emissor_process.pid})")
        time.sleep(1)  # Aguarda o servidor subir
        
        # Inicia o processo do Clock (cliente)
        clock_process = multiprocessing.Process(
            target=run_clock_process,
            args=(HOST, PORT_CLOCK, PORT_EMISSOR, PORT_ESCALONADOR, CLOCK_DELAY_MS, EMISSOR_ESCALONADOR_DELAY_MS),
            name="Clock"
        )
        clock_process.start()
        processes.append(clock_process)
        print(f"✓ Processo Clock iniciado (PID: {clock_process.pid})")
        time.sleep(1)  # Aguarda o servidor subir
        
        print("\n✓ Todos os processos iniciados com sucesso!")
        print("✓ Simulação em andamento...")
        print("  (Pressione Ctrl+C para interromper)")
        
        # Aguarda todos os processos terminarem
        for process in processes:
            process.join()
            exit_code = process.exitcode
            status = "✓ Sucesso" if exit_code == 0 else f"✗ Código {exit_code}"
            print(f"  {process.name} (PID: {process.pid}): {status}")
        
        print("\n=== SIMULAÇÃO CONCLUÍDA ===")
        
    except KeyboardInterrupt:
        print("\n⚠ Interrupção detectada pelo usuário.")
        cleanup_processes(processes)
        
    except Exception as e:
        print(f"\n✗ Erro durante a simulação: {e}")
        cleanup_processes(processes)
        sys.exit(1)

if __name__ == "__main__":
    # Necessário para multiprocessing no Windows
    multiprocessing.set_start_method('spawn', force=True)
    main()