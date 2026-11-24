# transcriber

Skill do Claude Code que escuta o microfone e o som do computador ao vivo (reunião, call, aula,
vídeo tocando), transcreve em tempo real e ajuda durante a conversa: responde curto quando há uma
pergunta, um número para conferir ou um risco, e fica quieta no resto. No fim, entrega um resumo
com decisões e pendências.

Funciona em **Linux, macOS e Windows**. A transcrição usa o whisper-large-v3-turbo da
[Groq](https://groq.com), que tem plano grátis.

## 1. Instalar o uv

O [uv](https://docs.astral.sh/uv/) roda o script e instala as dependências sozinho.

```bash
# Linux e macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```powershell
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 2. Instalar a skill

```bash
git clone https://github.com/MrIago/transcriber ~/.claude/skills/transcriber
```

No Windows (PowerShell): `git clone https://github.com/MrIago/transcriber $HOME\.claude\skills\transcriber`

## 3. Configurar a sua chave da Groq (uma vez)

1. Entre em https://console.groq.com/keys e crie uma chave (login com Google ou GitHub, sem cartão).
2. Rode e cole a chave quando pedir:

```bash
uv run ~/.claude/skills/transcriber/scripts/transcriber.py setup
```

Ele confere a chave na Groq e salva só para o seu usuário, fora do repositório:

| Sistema | Onde fica |
|---|---|
| Linux | `~/.config/transcriber/groq_key` |
| macOS | `~/Library/Application Support/transcriber/groq_key` |
| Windows | `%APPDATA%\transcriber\groq_key` |

A variável de ambiente `GROQ_API_KEY` também serve, no lugar do arquivo.

## 4. Só no Mac: o som do computador

O macOS não deixa gravar o som do sistema direto. Sem isto, a skill ouve só o microfone.

1. `brew install blackhole-2ch` (ou o instalador em https://existential.audio/blackhole).
2. Abra **Configuração de Áudio e MIDI**, clique em **+** → **Criar Dispositivo de Saída Múltipla**
   e marque os alto-falantes (ou o fone) **e** o BlackHole 2ch.
3. Em **Ajustes → Som → Saída**, escolha esse dispositivo.
4. Na primeira vez, aceite a permissão de microfone para o terminal.

No Linux (PipeWire ou PulseAudio) e no Windows o som do sistema já funciona, sem instalar nada.

## Usar

No Claude Code, diga "escuta a reunião" ou "liga o transcriber". Para testar só o script:

```bash
uv run ~/.claude/skills/transcriber/scripts/transcriber.py listen 4 pt
uv run ~/.claude/skills/transcriber/scripts/transcriber.py devices
```

- `4` são os segundos de cada pedaço. No plano grátis da Groq (20 pedidos por minuto) 4 é o mínimo.
- `pt` é o idioma (`en`, `es`...).
- `devices` lista microfones e saídas. Para escolher, use `TRANSCRIBER_MIC` e `TRANSCRIBER_SYSTEM`
  com parte do nome do dispositivo.

## Privacidade

O áudio vai em pedaços para a API da Groq e não é salvo em disco. Avise quem está na conversa que
ela está sendo transcrita.
