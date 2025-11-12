# Analisador CH Bot

Assistente Telegram que executa análises rápidas de partidas do Brasileirão a partir de um CSV local e de uma pipeline opcional que coleta dados via API-Football. O bot roda em modo polling, mantém um servidor Flask simples para “keep-alive” e pode ser controlado por scripts de start/stop.

## Visão geral da estrutura

```
AnalisadorCHBot/
├── main.py                # Entrada do bot (polling + keep-alive)
├── ia_adaptativa.py       # Lê o CSV e gera respostas do comando /analisar
├── keep_alive.py          # Servidor Flask em thread separada
├── data_pipeline.py       # Pipeline opcional para atualizar dados via API
├── historico.csv          # Base local com confrontos (usada no /analisar)
├── requirements.txt       # Dependências
└── logs/                  # Logs de execução e pipeline
```

Scripts auxiliares na raiz (`start.sh`, `stop.sh`, `restart.sh`, `status.sh`) controlam o processo em um Codespace/servidor.

## Pré-requisitos

- Python 3.12+
- `pip` e `venv`
- Token de bot Telegram válido (`TELEGRAM_TOKEN`)
- (Opcional) Chave da API-Football (`API_FOOTBALL_KEY`) para reprocessar dados.

## Passo a passo de setup

1. **Clonar e entrar no projeto**
   ```bash
   git clone https://github.com/caiquehrs5/analise-ch-boot.git
   cd analise-ch-boot
   ```
2. **Criar e ativar o ambiente virtual**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
3. **Instalar dependências**
   ```bash
   pip install -r AnalisadorCHBot/requirements.txt
   ```

## Variáveis de ambiente

Crie `AnalisadorCHBot/.env` (ou exporte no shell) com:

```
TELEGRAM_TOKEN=seu_token_do_bot
API_FOOTBALL_KEY=chave_api_football  # opcional, usado pelo data_pipeline
```

> Dica: valide o token antes de iniciar o bot.
> ```bash
> curl "https://api.telegram.org/bot$TELEGRAM_TOKEN/getMe"
> ```

## Dados do Brasileirão

- **Uso imediato**: o arquivo `AnalisadorCHBot/historico.csv` já acompanha alguns confrontos e o bot passa a usar esse dataset automaticamente.
- **Atualizar CSV via API-Football**:
  ```bash
  cd AnalisadorCHBot
  python data_fetcher.py  # gera historico_2023.csv
  python data_pipeline.py # gera fixtures_brasileirao_2025.csv (fallback público se API falhar)
  ```
  Substitua/atualize `historico.csv` conforme sua necessidade.

Se `historico.csv` não existir, o comando `/analisar` retornará um aviso solicitando a geração da base.

## Executando o bot manualmente

```bash
cd AnalisadorCHBot
python main.py
```

- A primeira thread que sobe é o `keep_alive.py`, que tenta usar a porta 5000 (tenta 5000-5009). Se a porta estiver ocupada, finalize o processo antigo (`lsof -i :5000` / `kill <PID>`).
- O bot usa polling. O log “HTTP 409 Conflict” indica outra instância ativa; encerre processos duplicados antes de reiniciar.

## Usando os scripts de serviço

Na raiz do projeto:

```bash
bash start.sh    # inicia em background (nohup -> ../nohup.out)
bash status.sh   # mostra PIDs ativos
bash stop.sh     # encerra processos
bash restart.sh  # stop + start
```

Os scripts evitam múltiplas instâncias e direcionam logs para `nohup.out`.

## Comandos disponíveis no Telegram

- `/start` – mensagem de boas-vindas e uptime.
- `/status` – mostra se o bot está ativo e a origem dos dados.
- `/analisar TIME_A x TIME_B` – procura confrontos no `historico.csv` e retorna vitórias, gols e últimos jogos. Exemplo: `/analisar Corinthians x Vasco da Gama`.

Entradas como `analisar Corinthians x Vasco` (sem a barra) também funcionam; se o padrão não for reconhecido, o bot sugere o formato correto.

## Testes rápidos da API do Telegram

```bash
curl "https://api.telegram.org/bot$TELEGRAM_TOKEN/getMe"
curl "https://api.telegram.org/bot$TELEGRAM_TOKEN/sendMessage" \
  -d chat_id=<seu_chat_id> \
  -d text="Teste da API"
```
Use `getUpdates` para descobrir o `chat_id` se necessário.

## Solução de problemas

- **Port 5000 already in use** – finalize o processo mostrado por `lsof -i :5000` ou ajuste o range em `keep_alive.py`.
- **HTTP 409 Conflict** – outra instância do bot já está chamando `getUpdates`. Encerre processos duplicados antes de reiniciar.
- **“Base … não encontrada”** – gere ou copie `historico.csv` para `AnalisadorCHBot/`.
- **Token inválido** – verifique a variável `TELEGRAM_TOKEN`; o log acusará “InvalidToken” e o bot irá abortar.

## Próximos passos sugeridos

- Automatizar a geração do CSV (CI ou cron) usando `data_pipeline.py`.
- Documentar processos de deploy específicos caso o bot rode fora do Codespace.
- Adicionar testes unitários para `ia_adaptativa.py` (ex.: `test_fetcher.py` como referência).

Com isso você tem um guia completo, do setup ao deploy em background, para operar o Analisador CH Bot.
