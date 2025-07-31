# Algoritmos de Escalonamento de Tarefas: Implementação e Análise

Este repositório contém a implementação e análise de diferentes algoritmos de escalonamento de tarefas, simulando um serviço de escalonamento em um sistema operacional com características *batch*. O trabalho visa aplicar conceitos de sistemas operacionais, incluindo comunicação entre processos via sockets, para analisar o desempenho dos algoritmos em termos de *turnaround time* e *waiting time*, além de visualizar a linha do tempo de execução das tarefas.

## 1. Objetivo

O principal objetivo é aplicar o conhecimento teórico da disciplina de Sistemas Operacionais (12035) para implementar e analisar na prática diferentes algoritmos de escalonamento de tarefas. Além disso, são implementados conceitos relacionados à comunicação entre processos, especificamente a utilização de sockets. A simulação realizada proverá a análise da execução de tarefas entre diferentes algoritmos de escalonamento, baseada no cálculo de métricas de tempo de execução (*turnaround time*) e tempo de espera (*waiting time*), além da observação da linha do tempo de execução de tarefas no processador.

## 2. Algoritmos de Escalonamento Implementados

Sete (7) algoritmos de escalonamento foram implementados, conforme o material bibliográfico de Maziero (2019):

* **First-Come, First-Served (FCFS)** 
* **Round-Robin (RR)** com quantum fixo de 3 unidades de clock 
* **Shortest Job First (SJF)** 
* **Shortest Remaining Time First (SRTF)** 
* **Escalonamento por prioridades fixas cooperativo (PRIOC)** 
* **Escalonamento por prioridades fixas preemptivo (PRIOP)** 
* **Escalonamento por prioridades dinâmicas (PRIOD)** 

## 3. Arquitetura do Sistema

O sistema é composto por três componentes distintos, implementados como processos separados que se comunicam por meio de sockets.

Os componentes são:

* **Clock:**
    * Responsável por simular o clock da CPU.
    * Inicializado em 0 e incrementado em 1 unidade de tempo a cada 100ms.
    * A cada incremento, envia uma mensagem primeiro ao Emissor de Tarefas e, após 5ms, ao Escalonador de Tarefas.
    * **Porta do Socket:** 4000 

* **Emissor de Tarefas:**
    * Informa o escalonador sobre as tarefas prontas para a fila de tarefas prontas.
    * A emissão é baseada na leitura de um arquivo de entrada.
    * Com cada novo valor de clock recebido, verifica se tarefas devem ser inseridas na fila de prontas.
    * Quando a última tarefa for inserida, envia uma mensagem ao Escalonador informando que todas as tarefas foram emitidas.
    * **Porta do Socket:** 4001 

* **Escalonador de Tarefas:**
    * Implementa todos os algoritmos de escalonamento. O algoritmo ativo é determinado por um argumento de entrada.
    * A cada novo valor de clock recebido, executa o algoritmo ativo e seleciona qual tarefa deve ocupar o processador.
    * Após o término da última tarefa, sinaliza o fim da simulação ao Clock e ao Emissor e escreve o arquivo de saída com os dados da execução.
    * **Porta do Socket:** 4002 

## 4. Tecnologias Utilizadas

* **Linguagem de Programação:** Python 3.13.3 

## 5. Como Executar

### 5.1. Pré-requisitos

* Python 3.x instalado no sistema
* Sistema operacional Linux (testado) ou Windows
* Arquivo de entrada com as tarefas (exemplo: `entrada00.txt`)

### 5.2. Estrutura do Arquivo de Entrada

O arquivo de entrada deve conter as tarefas no formato:
```
ID;tempo_chegada;tempo_execução;prioridade
```

Exemplo (`entrada00.txt`):
```
1;0;5;3
2;0;2;2
3;1;4;1
4;3;1;1
5;5;2;3
```

### 5.3. Execução do Programa

1. **Navegue até o diretório do projeto:**
   ```bash
   cd uem-escalonamento-tarefas
   ```

2. **Execute o programa principal:**
   ```bash
   python3 main.py <arquivo_entrada> <algoritmo>
   ```

   **Algoritmos disponíveis:**
   - `fcfs` - First-Come, First-Served
   - `rr` - Round Robin (quantum = 3)
   - `sjf` - Shortest Job First
   - `srtf` - Shortest Remaining Time First
   - `prioc` - Priority Cooperative
   - `priop` - Priority Preemptive
   - `priod` - Priority Dynamic

3. **Exemplos de execução:**
   ```bash
   # Executa algoritmo FCFS
   python3 main.py entrada00.txt fcfs
   
   # Executa algoritmo Round Robin
   python3 main.py entrada00.txt rr
   
   # Executa algoritmo de prioridades dinâmicas
   python3 main.py entrada00.txt priod
   ```

### 5.4. Saída do Programa

Após a execução, será gerado um arquivo `resultado_<algoritmo>.txt` contendo:

1. **Linha 1:** Timeline de execução das tarefas (formato: t1;t2;t1;...)
2. **Linhas 2-n:** Dados de cada tarefa (formato: ID;ingresso;finalização;turnaround;waiting)
3. **Última linha:** Médias de turnaround time e waiting time

**Exemplo de saída (`resultado_fcfs.txt`):**
```
t1;t1;t1;t1;t1;t2;t2;t3;t3;t3;t3;t4;t5;t5
t1;0;5;5;0
t2;0;7;7;5
t3;1;11;10;6
t4;3;12;9;8
t5;5;14;9;7
8.0;5.2
```

### 5.5. Arquivos Principais

- `main.py` - Programa principal que coordena a execução
- `Clock.py` - Componente responsável pelo controle de tempo
- `Emissor.py` - Componente que emite tarefas baseado no arquivo de entrada
- `Escalonador.py` - Componente que implementa os algoritmos de escalonamento
- `Task.py` - Classe que representa uma tarefa

## 6. Discentes
- [Matheus Foltran Consonni](https://github.com/MatheusFoltran)
- [Thiago Henrique Calvi](https://github.com/thiagocalvi)