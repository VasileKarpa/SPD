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
   - Proxy reverso e balanceamento de carga entre `api1` e `api2`  

---

## 🛠️ Pré-requisitos

- Docker & Docker Compose  
- Make  
- git instalado
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

## 📋 Exemplos de uso, pelo terminal em caso da interface em: http://localhost/ apresentar algum erro:

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

## 🧪 Testes de carga
- **Siege**: Ver o ficheiro [commands_siege.txt](commands_siege.txt)
- **ApacheBench**: Ver o ficheiro [commands_ab.txt](commands_ab.txt)

---

## 🚀 Resultados típicos para grandes testes de carga:

- 1 000 000 de pedidos sem perda de mensagens (com basic_qos(prefetch_count=50)).
- Tempo de processamento reduzido de 45min para 7min após optimização de conexões.

---

## 📄 Licença
- Este projecto está licenciado sob Vasile's Rules.
- Desenvolvido por Vasile Karpa – 2025
- Contacto: a74872@ualg.pt