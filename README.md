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

## 5. Discentes
- [Matheus Foltran Consonni](https://github.com/MatheusFoltran)
- [Thiago Henrique Calvi](https://github.com/thiagocalvi)