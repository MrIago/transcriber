#!/bin/bash
# Configura a chave da Groq do transcriber, uma vez por pessoa.
# Uso: setup.sh [chave]   (sem argumento, pergunta sem mostrar o que você digita)
# A chave fica em ~/.config/transcriber/groq_key, só com permissão do seu usuário.
CONF_DIR=${XDG_CONFIG_HOME:-$HOME/.config}/transcriber
KEY=$1
if [ -z "$KEY" ]; then
  echo "Crie uma chave grátis em https://console.groq.com/keys (login com Google ou GitHub)."
  read -rsp "Cole a chave (gsk_...): " KEY; echo
fi
KEY=$(echo "$KEY" | tr -d '[:space:]')
case "$KEY" in gsk_*) ;; *) echo "A chave da Groq começa com gsk_. Confira e rode de novo."; exit 1;; esac
code=$(curl -s -o /dev/null -w '%{http_code}' https://api.groq.com/openai/v1/models -H "Authorization: Bearer $KEY")
[ "$code" = 200 ] || { echo "A Groq recusou a chave (HTTP $code). Gere outra em https://console.groq.com/keys."; exit 1; }
mkdir -p "$CONF_DIR" && umask 077 && printf '%s' "$KEY" > "$CONF_DIR/groq_key"
echo "Chave salva em $CONF_DIR/groq_key. Pronto para usar."
