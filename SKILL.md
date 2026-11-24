---
name: transcriber
description: Escuta ao vivo o microfone e o som do computador (reunião, call, aula, vídeo tocando), transcreve em tempo real pela Groq e ajuda durante a conversa, respondendo só quando for útil. Funciona em Linux, macOS e Windows. Use quando o usuário pedir "escuta a reunião", "transcreve em tempo real", "fica ouvindo e me ajuda", "liga o transcriber", "ouve o áudio do PC", ou entrar numa call e quiser apoio ao vivo, mesmo sem citar a skill.
argument-hint: "[segundos por pedaço, padrão 4] [idioma, padrão pt]"
allowed-tools: Bash, Monitor, TaskStop, Read, Grep
---

# transcriber: ouvir a conversa e ajudar ao vivo

`scripts/transcriber.py` grava microfone + som do computador, corta em pedaços e transcreve cada um
no whisper-large-v3-turbo da Groq. Sai uma linha por pedaço com fala: `[HH:MM:SS] texto`.
Roda com `uv run`, que instala as dependências (soundcard, numpy) sozinho em Linux, macOS e Windows.

`<skill>` abaixo é a pasta desta skill (`~/.claude/skills/transcriber`; no Windows,
`%USERPROFILE%\.claude\skills\transcriber`).

## Ligar

Rode pelo `Monitor` (cada linha vira um evento), nunca em primeiro plano:

```
Monitor: command = "uv run -q <skill>/scripts/transcriber.py listen 4 pt", timeout_ms = 1800000
```

- Pedaço mínimo 4 s: o plano grátis da Groq aceita 20 pedidos/min.
- O Monitor vence em 30 min: quando o aviso de fim chegar, ligue de novo na hora, sem perguntar.
- A primeira linha ("escutando: mic=... som=...") mostra os dispositivos: diga ao usuário em uma linha.
  Para trocar: `uv run -q <skill>/scripts/transcriber.py devices` lista, e as variáveis
  `TRANSCRIBER_MIC` e `TRANSCRIBER_SYSTEM` escolhem por parte do nome.

## O que a saída pode dizer antes de transcrever

| Linha | O que fazer |
|---|---|
| `uv: command not found` | instalar o uv (tabela abaixo) e ligar de novo |
| `SEM_CHAVE` ou `CHAVE_INVALIDA` | configurar a chave (seção abaixo) |
| `SEM_SOM_DO_SISTEMA` no Mac | segue só com o microfone; para ouvir o PC, ajudar a instalar o BlackHole (abaixo) |
| `ERRO_DISPOSITIVO` | rodar `devices` e escolher outro com as variáveis |

Instalar o uv:

| Sistema | Comando |
|---|---|
| Linux e macOS | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Windows (PowerShell) | `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` |

## Primeira vez: a chave da Groq

Cada pessoa usa a própria chave (grátis):

1. Criar em https://console.groq.com/keys (login com Google ou GitHub, sem cartão).
2. A pessoa roda num terminal dela `uv run <skill>/scripts/transcriber.py setup`: ele pede a chave
   sem mostrar, confere na Groq e salva no diretório de configuração do sistema. Se ela colar a
   chave no chat, rode `... setup <chave>` por ela.
3. Ligar a escuta de novo. (`GROQ_API_KEY` no ambiente também serve.)

## Som do computador no Mac: BlackHole

O macOS não deixa gravar o som do sistema direto. Uma vez só:

1. `brew install blackhole-2ch` (ou o instalador em https://existential.audio/blackhole).
2. Abrir **Configuração de Áudio e MIDI** → **+** → **Criar Dispositivo de Saída Múltipla** →
   marcar os alto-falantes (ou fone) **e** o BlackHole 2ch.
3. Em Ajustes → Som → Saída, escolher esse dispositivo. O script acha o BlackHole sozinho.
4. Na primeira vez, o macOS pede permissão de microfone para o terminal: aceitar.

No Windows e no Linux o som do sistema já vem pelo loopback, sem instalar nada.

## Durante a conversa

- O usuário está falando com outras pessoas: leia de relance. Resposta curta, uma a três linhas,
  com a palavra-chave em negrito no começo (**Risco:**, **Resposta:**, **Número:**, **Pergunta:**).
  Parágrafo longo ninguém lê no meio de uma call.
- Responda só quando ajudar: uma pergunta que ele precisa responder, um número ou fato que dá
  para conferir, um risco ou erro no que foi dito, uma decisão sendo tomada. Fora isso, "Ouvindo."
  ou nada.
- Antes de afirmar algo do projeto, confira no código, no banco ou nos docs; palpite numa reunião
  vira compromisso.
- A transcrição erra nomes e termos técnicos: interprete pelo contexto, não corrija o usuário por
  erro do whisper.
- Conversa que virou pessoal, ou alguém pediu para não gravar: pare na hora (`TaskStop` no Monitor)
  e avise que parou.

## Desligar e fechar

`TaskStop` no Monitor. Depois entregue um resumo curto: decisões, pendências com dono, números
citados e o que ficou em aberto. A transcrição não é salva em disco; se o usuário quiser guardá-la,
salve o que veio pelo Monitor num arquivo onde ele pedir.
