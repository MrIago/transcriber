# transcriber

Skill do Claude Code que escuta o microfone e o som do computador ao vivo (reunião, call, aula,
vídeo tocando), transcreve em tempo real e ajuda durante a conversa: responde curto quando há uma
pergunta, um número para conferir ou um risco, e fica quieta no resto. No fim, entrega um resumo
com decisões e pendências.

A transcrição usa o whisper-large-v3-turbo da [Groq](https://groq.com), que tem plano grátis.

## Requisitos

- Linux com PipeWire ou PulseAudio (Ubuntu, Fedora, Debian e derivados já vêm assim)
- `ffmpeg` e `curl` (`sudo apt install ffmpeg curl`)
- Claude Code

## Instalação

```bash
git clone https://github.com/MrIago/transcriber ~/.claude/skills/transcriber
```

## Configurar a sua chave da Groq (uma vez)

1. Entre em https://console.groq.com/keys e crie uma chave (login com Google ou GitHub, sem cartão).
2. Rode:

```bash
~/.claude/skills/transcriber/scripts/setup.sh
```

Ele pede a chave sem mostrar o que você digita, confere na Groq e salva em
`~/.config/transcriber/groq_key`, só com permissão do seu usuário. A chave nunca vai para o repositório.

Quem prefere variável de ambiente pode usar `GROQ_API_KEY` no lugar do arquivo.

## Usar

No Claude Code, diga "escuta a reunião" ou "liga o transcriber". Para testar só o script:

```bash
~/.claude/skills/transcriber/scripts/escuta.sh 4 pt
```

- `4` são os segundos de cada pedaço. No plano grátis da Groq (20 pedidos por minuto) 4 é o mínimo.
- `pt` é o idioma (`en`, `es`...).
- Microfone e saída de som são detectados sozinhos. Para escolher, veja as fontes com
  `ffmpeg -hide_banner -sources pulse` e rode com `MIC=<fonte> MON=<fonte>.monitor`.

## Privacidade

O áudio vai em pedaços para a API da Groq e é apagado do disco logo depois. Avise quem está na
conversa que ela está sendo transcrita.
