---
name: transcriber
description: Escuta ao vivo o microfone e o som do PC (reunião, call, aula, vídeo tocando), transcreve em tempo real pela Groq e ajuda durante a conversa, respondendo só quando for útil. Use quando o usuário pedir "escuta a reunião", "transcreve em tempo real", "fica ouvindo e me ajuda", "liga o transcriber", "ouve o áudio do PC", ou entrar numa call e quiser apoio ao vivo, mesmo sem citar a skill.
argument-hint: "[segundos por pedaço, padrão 4] [idioma, padrão pt]"
allowed-tools: Bash, Monitor, TaskStop, Read, Grep
---

# transcriber: ouvir a conversa e ajudar ao vivo

`scripts/escuta.sh` grava microfone + som do PC (PipeWire/Pulse, pelo ffmpeg), corta em pedaços
e transcreve cada um no whisper-large-v3-turbo da Groq. Sai uma linha por pedaço com fala:
`[HH:MM:SS] texto`. Requer Linux com PipeWire ou PulseAudio, `ffmpeg` e `curl`.

## Primeira vez: a chave da Groq

Cada pessoa usa a própria chave (grátis). A chave fica em `~/.config/transcriber/groq_key`
(ou na variável `GROQ_API_KEY`). Se o `escuta.sh` sair com `SEM_CHAVE`, guie a pessoa:

1. Criar a chave em https://console.groq.com/keys (login com Google ou GitHub, sem cartão).
2. Rodar `<pasta da skill>/scripts/setup.sh` num terminal dela: ele pede a chave sem mostrar,
   confere na Groq e salva. Se ela colar a chave no chat, rode `setup.sh <chave>` por ela.
3. Ligar a escuta de novo.

`SEM_FFMPEG`: peça para instalar o ffmpeg (`sudo apt install ffmpeg` no Ubuntu e Debian).

## Ligar

Rode pelo `Monitor` (cada linha vira um evento), nunca em primeiro plano:

```
Monitor: command = "<pasta da skill>/scripts/escuta.sh 4 pt", timeout_ms = 1800000
```

- Pedaço mínimo 4 s: o plano grátis da Groq aceita 20 pedidos/min; com 3 s dá 429.
- O Monitor vence em 30 min: quando o aviso de fim chegar, ligue de novo na hora, sem perguntar.
- Microfone e saída são detectados sozinhos (fone bluetooth ganha da saída do notebook).
  Para forçar: `MIC=<fonte> MON=<fonte>.monitor` antes do comando; a lista sai em
  `ffmpeg -hide_banner -sources pulse`.
- Na primeira linha ("escutando: mic=... som=...") confira as fontes e diga ao usuário em uma linha.

## Durante a conversa

- O usuário está falando com outras pessoas: leia de relance. Resposta curta, uma a três linhas,
  com a palavra-chave em negrito no começo (**Risco:**, **Resposta:**, **Número:**, **Pergunta:**).
  Parágrafo longo ninguém lê no meio de uma call.
- Responda só quando ajudar: uma pergunta que ele precisa responder, um número ou fato que dá
  para conferir, um risco ou erro no que foi dito, uma decisão sendo tomada. Fora isso, "Ouvindo."
  ou nada.
- Antes de afirmar algo do projeto, confira no código, no banco ou nos docs; palpite numa reunião
  vira compromisso.
- A transcrição erra nomes e termos técnicos: interprete pelo contexto, não corrija o usuário por erro
  do whisper.
- Conversa que virou pessoal, ou alguém pediu para não gravar: pare na hora (`TaskStop` no Monitor)
  e avise que parou.

## Desligar e fechar

`TaskStop` no Monitor (o script mata o ffmpeg e apaga os pedaços). Depois entregue um resumo curto:
decisões, pendências com dono, números citados e o que ficou em aberto. A transcrição não é salva
em disco; se o usuário quiser guardá-la, salve o que veio pelo Monitor num arquivo onde ele pedir.
