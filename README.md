## Índice

1. [Sistema Distribuído de Armazenamento de Pares Chave-Valor](#Sistema Distribuído de Armazenamento de Pares Chave-Valor)  
2. [Instalação](#instalação)  
2. [Instalação](#instalação) 
2. [Instalação](#instalação) 
2. [Instalação](#instalação) 
2. [Instalação](#instalação) 
2. [Instalação](#instalação) 
2. [Instalação](#instalação) 
2. [Instalação](#instalação) 
2. [Instalação](#instalação) 
2. [🌐 Demo Frontend](#frontend) 
3. [🧪 Testes de carga com siege e build sem print de logs (modo detached) vs com print de logs](#siege)  
4. [💉 Testes de carga com ab e build sem print de logs (modo detached) vs com print de logs](#ab)  
5. [📝 Nota Importante dos testes de carga](#nota)  
6. [🚀 Resultados típicos para grandes testes de carga](#resultados)  
7. [📄 Licença](#licenca)



# Sistema Distribuído de Armazenamento de Pares Chave-Valor

Um sistema distribuído de leitura e escrita de pares chave-valor, baseado em micro-serviços orquestrados por Docker Compose. Inclui:

- **Duas réplicas de API** (api1 e api2) em FastAPI  
- **Cache Redis** para aceleração de leituras  
- **Base de dados PostgreSQL** para persistência  
- **RabbitMQ** como broker de mensagens duráveis (filas add_key e del_key)  
- **Serviço consumidor** que processa operações em background  
- **Nginx** como proxy reverso e balanceador de carga  

---

## 🚀 Funcionalidades principais

- **Cache-aside**: leituras vão primeiro ao Redis e, em caso de cache-miss, ao PostgreSQL, guardando depois em cache.  
- **Escrita/remoção assíncrona**: PUT/DELETE enfileiram mensagens no RabbitMQ; o consumer aplica insert/update/delete em PostgreSQL e atualiza o cache.  
- **Durabilidade e fiabilidade**: filas duráveis + mensagens persistentes + acknowledgements garantem que nenhuma operação se perde, mesmo em falhas.  
- **Ordenação e at-most-once**: cada mensagem inclui timestamp e apenas operações mais recentes são aplicadas.  
- **Escalabilidade horizontal**: basta aumentar réplicas de APIs ou de consumers conforme a carga.  

---

## 🏗️ Arquitectura

1. **FastAPI (api1 & api2)**  
   - Endpoints HTTP:  
     - `GET  /api?key=<chave>` → devolve valor e origem (`redis` ou `postgres`)  
     - `GET  /api/all`           → lista todos os pares  
     - `PUT  /api`               → Coloca em fila operação de escrita  
     - `DELETE /api`             → Coloca em fila operação de remoção  

2. **RabbitMQ**  
   - Filas duráveis `add_key` e `del_key`  
   - Mensagens com `delivery_mode=2` (persistentes) e timestamp  

3. **Consumer (workers)**  
   - Lê filas em paralelo, com `basic_qos(prefetch_count=…)`  
   - Aplica `INSERT … ON CONFLICT …` ou `DELETE` em PostgreSQL  
   - Atualiza ou elimina entradas no Redis  

4. **Redis**  
   - Cache-aside de valores  
   - TTL definido pela aplicação ou sem expiração (conforme necessidade)  

5. **PostgreSQL**  
   - Tabela `kv_store(key TEXT PRIMARY KEY, value TEXT, last_updated TIMESTAMP)`  

6. **Nginx**  
   - Proxy reverso e balanço/gestao de carga entre `api1` e `api2`  

---

## 🏛️ Diagrama de arquitetura do sistema

<p align="left">
  <img src="assets/diagrama_arquitetura.jpg" width="500" alt="diagrama_arquitetura.jpg">
</p>

- **Mais detalhes**:Ver [Sistemas_Distribuidos.pdf](Sistemas_Distribuidos.pdf) ("Implementações avaliadas - pag. 10")
---

## 🛠️ Pré-requisitos

- Docker & Docker Compose  
- Make  
- git
- (Opcional) `siege` ou `ab` para testes de carga  
- (Opcional) Em Windows, instalar Ubuntu

---

## 📦 Instalação e arranque Linux V1

1. Clone o repositório  
   ```bash
   git clone https://github.com/a74872/SPD

2. Ir para a pasta onde o clone foi realizado o clone
   ```bash
   cd SPD

3. Utilize o Makefile (recomendado)
   ```bash
   make

4. Ou manualmente
   ```bash
   docker-compose down --volumes
   docker-compose build --no-cache
   docker-compose up

5. Espere o build acabar, e aceda à interface em: http://localhost/

> **Para mais detalhes** ver [Sistemas_Distribuidos.pdf](Sistemas_Distribuidos.pdf) ("Automação e reprodutibilidade - pag. 10").

---

## 📦 Instalação e arranque Linux V2

1. Clone o repositório  
   ```bash
   git clone https://github.com/a74872/SPD

2. Ir para a pasta onde o clone foi realizado o clone
   ```bash
   cd SPD

3. Utilize o ficheiro start.sh
   ```bash
   chmod +x start.sh
   ./start.sh

4. Ou manualmente
   ```bash
   docker-compose down --volumes
   docker-compose build --no-cache
   docker-compose up

5. Espere o build acabar, e aceda à interface em: http://localhost/

> **Para mais detalhes** ver [Sistemas_Distribuidos.pdf](Sistemas_Distribuidos.pdf) ("Automação e reprodutibilidade - pag. 10").

---

## 📦 Instalação e arranque Windows

1. Clone o repositório
   ```cmd
   git clone https://github.com/a74872/SPD
   cd SPD

2. Ir para a pasta onde o clone foi realizado o clone
   ```cmd
   cd SPD

3. Fazer Build
   ```cmd
   docker-compose down --volumes
   docker compose build --no-cache
   docker-compose up

4. Espere o build acabar, e aceda à interface em: http://localhost/

> **Para mais detalhes** ver [Sistemas_Distribuidos.pdf](Sistemas_Distribuidos.pdf) ("Automação e reprodutibilidade - pag. 10").

---

## ☁️ Instalação e uso em cloud e standalone
- **Este projeto** pode ser executado tanto em ambiente standalone (no seu PC de desenvolvimento Windows, macOS ou Linux) como em qualquer cloud provider (Google Cloud, AWS, Azure, DigitalOcean, …), desde que disponha de uma máquina virtual (VM) com Docker e Docker Compose instalados.

- **Implantação em ambiente cloud e criação da VM :** Escolha o seu provider (GCP, AWS, Azure, DigitalOcean…). Crie uma instância com SO Linux (Ubuntu/Debian) ou Windows Server. Garanta que tem pelo menos 2 vCPUs e 4 GB RAM para testes leves (ou mais para cargas elevadas).

- **Configurar a VM :** Abra SSH (Linux/macOS) ou RDP/PowerShell remota (Windows). Os restantes passos e pré-requisitos (instalação do Docker, Docker Compose, Makefile ou start.sh, clonagem do repositório e comandos de arranque) já foram descritos anteriormente (acima) para os ambientes Windows e Linux.

---

## 💻 Demo Terminal (em caso da interface http://localhost/ apresentar algum erro)
- **Put**: 
Para inserir um par chave-valor no terminal utilize curl -X PUT http://localhost/api -H "Content-Type: application/json" -d '{"key":"minha_chave","value":"123"}' e obterá de imediato {"status":"queued"} com código HTTP 200 OK, indicando que a operação foi enfileirada; pode confirmar no pgAdmin4 ou em psql com SELECT * FROM kv_store; e verificar que a chave foi inserida.
1. Gravar um par chave-valor
   ```bash
   curl -X PUT http://localhost/api -H "Content-Type: application/json" -d '{"key":"minha_chave","value":"123"}'

- **Delete**: 
Para eliminar o par utilize curl -X DELETE http://localhost/api?key=minha_chave, que também retornará {"status":"queued"} com HTTP 200 OK, e depois confirme que a linha foi removida na tabela kv_store.
2. Eliminar um par chave-valor
   ```bash
   curl -X DELETE http://localhost/api?key=minha_chave

- **Get**: 
Para ler o valor dessa chave use curl http://localhost/api?key=minha_chave e receberá {"data":{"key":"minha_chave","value":"123"},"source":"postgres"} (ou "redis" se tiver cache), mostrando de onde veio a resposta.
3. Ler um par chave-valor
   ```bash
   curl http://localhost/api?key=minha_chave

- **List**: 
Por fim, para listar todos os pares armazenados use curl http://localhost/api/all, que devolverá {"data":[{"key":"outra_chave","value":"abc"},…]}, e pode novamente comparar com o conteúdo da tabela no pgAdmin4 ou via psql.
4. Listar todos os pares chave-valor
   ```bash
   curl http://localhost/api/all

---

<h2 id="frontend">🌐 Demo Frontend</h2>

- **Put**: 
Para inserir um novo par chave-valor através do frontend basta digitar no formulário o nome da chave e o valor (ambos strings) e clicar em “Salvar”. O frontend envia então uma requisição PUT para /api com um corpo JSON contendo os campos key e value, e devolve de imediato um HTTP 200 OK com {"status":"queued"}, indicando que a operação foi enfileirada no RabbitMQ. Um serviço consumidor retira em background essa mensagem da fila add_key e executa o INSERT ou UPDATE na tabela kv_store do PostgreSQL (atualizando também o cache Redis, se existir). Por fim, para confirmar que a inserção decorreu com sucesso, abra o pgAdmin4 (ou ligue-se via psql) à base de dados bd_spd e consulte a tabela kv_store – se encontrar a linha com a chave e o valor indicados, significa que o par foi efetivamente gravado.
<p align="center">
  <img src="assets/put.jpg" width="600" alt="put.jpg">
</p>

- **Get**: 
Para efetuar uma leitura (GET) de um par chave-valor, basta introduzir o nome da chave no campo de pesquisa e premir “Pesquisar”. O frontend envia imediatamente uma requisição GET para /api?key=<nome_da_chave>; se o valor estiver no cache Redis, recebe de imediato HTTP 200 OK com {"data":{"key":"<nome_da_chave>","value":"<valor>"},"source":"redis"}; em caso de cache miss, a API vai ao PostgreSQL, retorna o valor e guarda-o no Redis para consultas futuras, respondendo também com HTTP 200 OK e "source":"postgres". Para confirmar, abra o pgAdmin4 (ou use psql) e verifique se a linha existe na tabela kv_store ou volte a fazer GET para a mesma chave e observe "source":"redis" no resultado.
<p align="center">
  <img src="assets/get_1.jpg" width="600" alt="get_1.jpg">
</p>

<p align="center">
  <img src="assets/get_2.jpg" width="600" alt="get_2.jpg">
</p>

- **Delete**: 
Para eliminar um par chave-valor, escreva o nome da chave no campo correspondente e clique em “Eliminar”. O frontend dispara uma requisição DELETE para /api?key=<nome_da_chave> e devolve de imediato HTTP 200 OK com {"status":"queued"}, sinalizando que a operação foi enfileirada em del_key. O consumidor processa essa mensagem em background, remove a entrada da tabela kv_store no PostgreSQL e invalida a chave no Redis. Para verificar a exclusão, recorra ao pgAdmin4 (ou psql) e confirme que a linha já não está presente, ou faça um GET para essa chave e receba HTTP 404 Not Found.
<p align="center">
  <img src="assets/delete.jpg" width="600" alt="delete.jpg">
</p>

<p align="center">
  <img src="assets/delete_confirmation.jpg" width="600" alt="delete_confirmation.jpg">
</p>

- **List**: 
Para listar todos os pares chave-valor, basta carregar no botão “Listar tudo” no frontend, que envia uma única requisição GET para /api/all; a API responderá com status 200 OK e um JSON contendo o array de objetos com cada key e value, e o frontend renderiza imediatamente essa lista (por exemplo, numa tabela), pelo que, para confirmar, pode igualmente abrir o pgAdmin4 ou usar psql com SELECT * FROM kv_store; e verificar que os resultados no banco coincidem com os apresentados.
<p align="center">
  <img src="assets/list.jpg" width="400" alt="list.jpg">
</p>

---

<h2 id="siege">🧪 Testes de carga com siege e build sem print de logs (modo detached) vs com print de logs</h2>

- **Siege**: Ver o ficheiro [commands_siege.txt](siege/commands_siege.txt)
- **Resultados sem print de logs**: Em apenas cerca de 11min (693,86 segundos) foram processadas 1 632 000 requisições com o Siege, mantendo 0 perdas de dados, o que traduz um throughput médio de cerca de 2 351 req/s. Estes resultados assentam em vários factores de optimização: as APIs correm em modo detached (docker compose up -d), eliminando o overhead de I/O de logs em tempo real; o basic_qos(prefetch_count=50) no consumidor garante elevado débito sem riscos de mensagem perdida; as ligações ao RabbitMQ e ao PostgreSQL são reutilizadas, evitando o custo de abrir e fechar conexões a cada operação; e a estratégia cache-aside com Redis (no caso do get) reduz drasticamente a latência das leituras repetidas. No seu conjunto, estas escolhas permitem ao sistema escalar de forma linear sob cargas massivas, mantendo latências controladas e fiabilidade total, exemplo de grafico na figura da esquerda.
---
- **Resultados com print de logs**: Em apenas cerca de 11min (693,86 segundos) foram processadas 1 632 000 requisições com o Siege, mantendo 0 perdas de dados, o que traduz um throughput médio de cerca de 2 351 req/s. Estes resultados assentam em vários factores de optimização: as APIs correm em modo detached (docker compose up -d), eliminando o overhead de I/O de logs em tempo real; o basic_qos(prefetch_count=50) no consumidor garante elevado débito sem riscos de mensagem perdida; as ligações ao RabbitMQ e ao PostgreSQL são reutilizadas, evitando o custo de abrir e fechar conexões a cada operação; e a estratégia cache-aside com Redis (no caso do get) reduz drasticamente a latência das leituras repetidas. No seu conjunto, estas escolhas permitem ao sistema escalar de forma linear sob cargas massivas, mantendo latências controladas e fiabilidade total, exemplo de grafico na figura da direita.

<p align="center">
  <img src="assets/siege_com_d.jpg" width="400" alt="siege_com_d.jpg">, <img src="assets/siege_com_d.jpg" width="400" alt="siege_com_d.jpg">,
</p>

---

<h2 id="ab">💉 Testes de carga com ab e build sem print de logs (modo detached) vs com print de logs</h2>

- **ApacheBench**: Ver o ficheiro [commands_ab.txt](ab/commands_ab.txt)
- **Resultados sem print de logs**: Em cerca de 12min (727,89 segundos) o ApacheBench processou 1 632 000 requisições com 255 clientes concorrentes, mantendo 0 perdas de dados, o que corresponde a um throughput médio de aproximadamente 2 241 requisições por segundo. Estes resultados foram alcançados graças a várias otimizações: as APIs foram executadas em modo detached (docker compose up -d), eliminando o overhead de I/O associado ao streaming de logs em tempo real; foi configurado basic_qos(prefetch_count=50) no consumidor para maximizar o débito sem comprometer a fiabilidade das mensagens; as ligações TCP ao RabbitMQ e ao PostgreSQL são mantidas abertas e reutilizadas, evitando custos de estabelecimento de conexão em cada operação; e a estratégia cache-aside com Redis (no caso do get) aliviou significativamente a carga de leituras no PostgreSQL, reduzindo as latências. Em conjunto, estes fatores permitem ao sistema lidar com elevados níveis de concorrência mantendo a latência sob controlo e garantindo 100 % de consistência dos dados, exemplo de grafico na figura da esquerda.

- **Resultados com print de logs**: Em apenas cerca de 12min (693,86 segundos) foram processadas 1 632 000 requisições com o Siege, mantendo 0 perdas de dados, o que traduz um throughput médio de cerca de 2 351 req/s. Estes resultados assentam em vários factores de optimização: as APIs correm em modo detached (docker compose up -d), eliminando o overhead de I/O de logs em tempo real; o basic_qos(prefetch_count=50) no consumidor garante elevado débito sem riscos de mensagem perdida; as ligações ao RabbitMQ e ao PostgreSQL são reutilizadas, evitando o custo de abrir e fechar conexões a cada operação; e a estratégia cache-aside com Redis (no caso do get) reduz drasticamente a latência das leituras repetidas. No seu conjunto, estas escolhas permitem ao sistema escalar de forma linear sob cargas massivas, mantendo latências controladas e fiabilidade total, exemplo de grafico na figura da direita.

<p align="center">
  <img src="assets/ab_com_d.jpg" width="400" alt="siege_com_d.jpg">, <img src="assets/siege_com_d.jpg" width="400" alt="siege_com_d.jpg">,
</p>

---

<h2 id="nota">📝 Nota Importante dos testes de carga</h2>

Durante os testes de carga verificámos que executar o sistema em modo “foreground” (i.e. **docker compose up** sem -d) introduz um overhead de I/O que impacta diretamente o desempenho. Cada log enviado para o terminal—print()s da aplicação, mensagens do Nginx, UVicorn e RabbitMQ—obriga a múltiplas operações de flush, parsing e formatação, consumindo CPU e I/O de disco. Quando geramos centenas ou milhares de logs por segundo, o próprio terminal se torna um fator limitador, impondo throttling e constantes sincronizações de buffer para não perder saída, o que retarda significativamente o processamento de pedidos.

Em contrapartida, ao usar **docker compose up -d**, os containers correm em background sem despejar logs para o terminal, eliminando esse overhead de I/O. Nos nossos benchmarks, isso traduziu-se em throughput muito mais elevado e latências menores — prova de que a forma como gerimos o logging é um factor crítico a ter em conta em cenários de alta carga.

---

<h2 id="resultados">🚀 Resultados típicos para grandes testes de carga:</h2>

- 1 000 000 de pedidos sem perda de mensagens (com basic_qos(prefetch_count=50)).
- Tempo de processamento reduzido de 45min para 7min após optimização de conexões.
- **RabitMQ**: Pode ver e gerir em tempo real praticamente tudo o que se passa no broker: http://localhost:15672/#/
- **Mais dados**:Ver [Sistemas_Distribuidos.pdf](Sistemas_Distribuidos.pdf) ("Discussão de Resultads - pag. 15")

<p align="left">
  <img src="assets/teste_carga_million.jpg" width="400" alt="teste_carga_million.jpg">
</p>

---

<h2 id="licenca">📄 Licença</h2>

- Este projecto está licenciado sob Vasile's Rules.
- Desenvolvido por Vasile Karpa – 2025
- Contacto: a74872@ualg.pt