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
- Make (opcional)  
- (Opcional) `siege` ou `ab` para testes de carga  

---

## 📦 Instalação e arranque

1. Clone o repositório  
   ```bash
   git clone https://github.com/a74872/SPD
   cd SPD

