# Sinal Acessível

Projeto simples de demonstração de um sistema de acessibilidade urbana.

## O que é este projeto?

- Cadastro de usuário
- Simulação de tempo extra para atravessar
- API em Python + FastAPI
- Frontend em HTML, CSS e JavaScript

## Como rodar localmente

1. Crie um ambiente virtual
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Instale as dependências
   ```bash
   pip install -r requirements.txt
   ```

3. Suba o banco PostgreSQL
   ```bash
   docker compose up -d
   ```

4. Crie um arquivo `.env` com:
   ```env
   DATABASE_URL=postgresql://sinal:sinal_dev@localhost:5432/sinal_acessivel
   ```

5. Rode a API
   ```bash
   uvicorn main:app --reload
   ```

6. Abra o arquivo `index.html` no navegador

## Observações importantes

- O arquivo `python` foi ajustado para funcionar como alias de compatibilidade.
- O projeto foi organizado para ficar mais fácil de entender e rodar.
- O banco foi configurado para uso local com PostgreSQL.
