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
  <img src="assets/diagrama_arquitetura.jpg" width="600" alt="diagrama_arquitetura.jpg">
</p>

---

## 🛠️ Pré-requisitos

- Docker & Docker Compose  
- Make  
- git
- (Opcional) `siege` ou `ab` para testes de carga  

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

> **⚠️ Aviso:** se não for enviada nenhuma mensagem (nem heartbeats nem outra frame) durante **600 s**, a conexão com o RabbitMQ será encerrada e **será necessário reiniciar o container**.

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

> **⚠️ Aviso:** se não for enviada nenhuma mensagem (nem heartbeats nem outra frame) durante **600 s**, a conexão com o RabbitMQ será encerrada e **será necessário reiniciar o container**.

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

> **⚠️ Aviso:** se não for enviada nenhuma mensagem (nem heartbeats nem outra frame) durante **600 s**, a conexão com o RabbitMQ será encerrada e **será necessário reiniciar o container**.

---

## 📋 Exemplos de uso pelo terminal, em caso da interface http://localhost/ apresentar algum erro:

1. Gravar um par chave-valor
   ```bash
   curl -X PUT http://localhost/api -H "Content-Type: application/json" -d '{"key":"minha_chave","value":"123"}'

2. Eliminar um par chave-valor
   ```bash
   curl -X DELETE http://localhost/api?key=minha_chave

3. Ler um par chave-valor
   ```bash
   curl http://localhost/api?key=minha_chave

4. Listar todos os pares chave-valor
   ```bash
   curl http://localhost/api/all

---

## 💻 Demo Terminal

---

---

## 🌐 Demo Frontend
- **Put**: Para inserir um novo par chave-valor através do frontend basta digitar no formulário o nome da chave e o valor (ambos strings) e clicar em “Salvar”. O frontend envia então uma requisição PUT para /api com um corpo JSON contendo os campos key e value, e devolve de imediato um HTTP 200 OK com {"status":"queued"}, indicando que a operação foi enfileirada no RabbitMQ. Um serviço consumidor retira em background essa mensagem da fila add_key e executa o INSERT ou UPDATE na tabela kv_store do PostgreSQL (atualizando também o cache Redis, se existir). Por fim, para confirmar que a inserção decorreu com sucesso, abra o pgAdmin4 (ou ligue-se via psql) à base de dados bd_spd e consulte a tabela kv_store – se encontrar a linha com a chave e o valor indicados, significa que o par foi efetivamente gravado.
<p align="left">
  <img src="assets/put.jpg" width="600" alt="put.jpg">
</p>

- **Get**: Para efetuar uma leitura (GET) de um par chave-valor, basta introduzir o nome da chave no campo de pesquisa e premir “Pesquisar”. O frontend envia imediatamente uma requisição GET para /api?key=<nome_da_chave>; se o valor estiver no cache Redis, recebe de imediato HTTP 200 OK com {"data":{"key":"<nome_da_chave>","value":"<valor>"},"source":"redis"}; em caso de cache miss, a API vai ao PostgreSQL, retorna o valor e guarda-o no Redis para consultas futuras, respondendo também com HTTP 200 OK e "source":"postgres". Para confirmar, abra o pgAdmin4 (ou use psql) e verifique se a linha existe na tabela kv_store ou volte a fazer GET para a mesma chave e observe "source":"redis" no resultado.
<p align="left">
  <img src="assets/get_1.jpg" width="600" alt="get_1.jpg">
</p>

<p align="left">
  <img src="assets/get_2.jpg" width="600" alt="get_2.jpg">
</p>

- **Delete**: Para eliminar um par chave-valor, escreva o nome da chave no campo correspondente e clique em “Eliminar”. O frontend dispara uma requisição DELETE para /api?key=<nome_da_chave> e devolve de imediato HTTP 200 OK com {"status":"queued"}, sinalizando que a operação foi enfileirada em del_key. O consumidor processa essa mensagem em background, remove a entrada da tabela kv_store no PostgreSQL e invalida a chave no Redis. Para verificar a exclusão, recorra ao pgAdmin4 (ou psql) e confirme que a linha já não está presente, ou faça um GET para essa chave e receba HTTP 404 Not Found.
<p align="left">
  <img src="assets/delete.jpg" width="600" alt="delete.jpg">
</p>

<p align="left">
  <img src="assets/delete_confirmation.jpg" width="600" alt="delete_confirmation.jpg">
</p>

- **List**:

---

## 🧪 Testes de carga
- **Siege**: Ver o ficheiro [commands_siege.txt](commands_siege.txt)
- **ApacheBench**: Ver o ficheiro [commands_ab.txt](commands_ab.txt)
- **RabitMQ**: Pode ver e gerir em tempo real praticamente tudo o que se passa no broker: http://localhost:15672/#/
- **Mais dados**:Ver [Sistemas_Distribuidos.pdf](Sistemas_Distribuidos.pdf) ("Discussão de Resultads - pag. 15")

---

## 🚀 Resultados típicos para grandes testes de carga:

- 1 000 000 de pedidos sem perda de mensagens (com basic_qos(prefetch_count=50)).
- Tempo de processamento reduzido de 45min para 7min após optimização de conexões.

---

## 📄 Licença
- Este projecto está licenciado sob Vasile's Rules.
- Desenvolvido por Vasile Karpa – 2025
- Contacto: a74872@ualg.pt