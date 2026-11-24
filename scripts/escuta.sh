#!/bin/bash
# Escuta microfone + som do PC e transcreve em pedaços pela Groq (whisper-large-v3-turbo).
# Requer: Linux com PipeWire ou PulseAudio, ffmpeg e curl. Chave: setup.sh (uma vez).
# Uso: escuta.sh [segundos=4] [idioma=pt]   (plano grátis da Groq: 20 pedidos/min, então 4 s é o mínimo)
# Saída: uma linha por pedaço com fala, "[HH:MM:SS] texto". Pare com Ctrl+C ou matando o processo.
SEG=${1:-4}; LANG_=${2:-pt}
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
S=$(mktemp -d /tmp/escuta.XXXXXX)
CONF=${XDG_CONFIG_HOME:-$HOME/.config}/transcriber/groq_key
KEY=${GROQ_API_KEY:-$(cat "$CONF" 2>/dev/null)}
if [ -z "$KEY" ]; then
  echo "SEM_CHAVE: nenhuma chave da Groq configurada. Rode: $(dirname "$0")/setup.sh"
  exit 2
fi
command -v ffmpeg >/dev/null || { echo "SEM_FFMPEG: instale o ffmpeg (ex.: sudo apt install ffmpeg)"; exit 3; }
SRC=$(ffmpeg -hide_banner -sources pulse 2>&1)
MIC=${MIC:-$(echo "$SRC" | grep -oP '^\*\s+\K\S+' | grep -v '\.monitor$' | head -1)}
[ -z "$MIC" ] && MIC=$(echo "$SRC" | grep -oP '\balsa_input\S+' | head -1)
MON=${MON:-$(echo "$SRC" | grep -oP 'bluez_output\S+\.monitor' | head -1)}
[ -z "$MON" ] && MON=$(echo "$SRC" | grep -oP '\S+\.monitor\b' | head -1)
echo "escutando: mic=$MIC som=$MON pedaços=${SEG}s"
ffmpeg -hide_banner -loglevel error -f pulse -i "$MIC" -f pulse -i "$MON" \
  -filter_complex "[0:a][1:a]amix=inputs=2:duration=longest:normalize=0,aresample=16000" -ac 1 \
  -f segment -segment_time "$SEG" -reset_timestamps 1 "$S/p%05d.wav" &
FF=$!
trap 'kill $FF 2>/dev/null; rm -rf "$S"' EXIT
done_n=-1
while kill -0 $FF 2>/dev/null; do
  last=$(ls "$S"/p*.wav 2>/dev/null | tail -1)
  for f in $(ls "$S"/p*.wav 2>/dev/null); do
    [ "$f" = "$last" ] && continue
    n=$(basename "$f" .wav | tr -dc 0-9); n=$((10#$n))
    [ $n -le $done_n ] && continue
    for try in 1 2 3; do
      txt=$(curl -s https://api.groq.com/openai/v1/audio/transcriptions -H "Authorization: Bearer $KEY" \
        --form-string model=whisper-large-v3-turbo --form-string language="$LANG_" \
        --form-string response_format=text -F "file=@$f" | tr '\n' ' ')
      case "$txt" in *rate_limit*) sleep 3;; *) break;; esac
    done
    case "$txt" in *'"error"'*) txt="";; esac
    # descarta ruído: só pontuação, e as alucinações clássicas do whisper no silêncio
    clean=$(echo "$txt" | tr -d '[:punct:][:space:]')
    if [ -n "$clean" ] && ! echo "$txt" | grep -qiE '^\s*(obrigad[oa]( por assistir)?|legendas? pela comunidade.*|tchau)[.! ]*$'; then
      echo "[$(date +%H:%M:%S)] $txt"
    fi
    done_n=$n; rm -f "$f"
  done
  sleep 0.3
done
