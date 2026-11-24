#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["soundcard>=0.4.3", "numpy"]
# ///
"""Escuta microfone + som do computador e transcreve ao vivo pela Groq (Linux, macOS e Windows).

Uso (com uv, que instala as dependências sozinho):
  uv run transcriber.py setup [chave]       configura a chave da Groq, uma vez por pessoa
  uv run transcriber.py devices             lista microfones e saídas de som
  uv run transcriber.py listen [seg] [lang] escuta; padrão 4 s em pt. Uma linha por fala: [HH:MM:SS] texto
Variáveis: GROQ_API_KEY (no lugar do arquivo), TRANSCRIBER_MIC e TRANSCRIBER_SYSTEM (parte do nome do dispositivo).
"""
import io, json, os, queue, re, sys, threading, time, uuid, urllib.error, urllib.request, wave
from datetime import datetime
from pathlib import Path

RATE, OUT_RATE, BLOCK = 48000, 16000, 4800  # grava a 48 kHz (nativo em quase todo hardware) e manda 16 kHz
API = "https://api.groq.com/openai/v1"
HALLUCINATIONS = re.compile(r"^\s*(obrigad[oa]( por assistir)?|legendas? pela comunidade.*|tchau|thanks for watching|thank you)[.!\s]*$", re.I)

for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8", line_buffering=True)
    except Exception: pass

def config_file() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "transcriber" / "groq_key"

def http(req) -> tuple[int, str]:
    req.add_header("User-Agent", "transcriber-skill/1.0")
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e: return e.code, e.read().decode("utf-8", "replace")
    except Exception as e: return 0, str(e)

def setup(args):
    key = args[0] if args else ""
    if not key:
        import getpass
        print("Crie uma chave grátis em https://console.groq.com/keys (login com Google ou GitHub, sem cartão).")
        key = getpass.getpass("Cole a chave (gsk_...): ")
    key = key.strip()
    if not key.startswith("gsk_"): sys.exit("A chave da Groq começa com gsk_. Confira e rode de novo.")
    code, _ = http(urllib.request.Request(f"{API}/models", headers={"Authorization": f"Bearer {key}"}))
    if code != 200: sys.exit(f"A Groq recusou a chave (HTTP {code}). Gere outra em https://console.groq.com/keys.")
    f = config_file(); f.parent.mkdir(parents=True, exist_ok=True); f.write_text(key, encoding="utf-8")
    try: os.chmod(f, 0o600)
    except Exception: pass
    print(f"Chave salva em {f}. Pronto para usar.")

def load_key() -> str:
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key and config_file().exists(): key = config_file().read_text(encoding="utf-8").strip()
    if not key:
        print(f"SEM_CHAVE: nenhuma chave da Groq configurada. Rode: uv run {Path(__file__).resolve()} setup", flush=True)
        sys.exit(2)
    return key

def find(devices, hint):
    hint = (hint or "").lower()
    return next((d for d in devices if hint and hint in d.name.lower()), None)

def pick_devices(sc):
    mics = sc.all_microphones(include_loopback=False)
    mic = find(mics, os.environ.get("TRANSCRIBER_MIC")) or sc.default_microphone()
    system, note = None, ""
    hint = os.environ.get("TRANSCRIBER_SYSTEM")
    if sys.platform == "darwin":
        # macOS não grava o som do sistema sozinho: precisa de um dispositivo virtual como o BlackHole
        system = find(mics, hint) or find(mics, "blackhole")
        if system and mic and system.name == mic.name: mic = next((m for m in mics if "blackhole" not in m.name.lower()), None)
        if not system: note = "SEM_SOM_DO_SISTEMA: no Mac, instale o BlackHole (brew install blackhole-2ch) e crie um Dispositivo de Saída Múltipla. Ouvindo só o microfone."
    else:
        loops = [m for m in sc.all_microphones(include_loopback=True) if getattr(m, "isloopback", False)]
        spk = sc.default_speaker()
        system = find(loops, hint) or find(loops, spk.name if spk else "") or (loops[0] if loops else None)
        if not system: note = "SEM_SOM_DO_SISTEMA: nenhuma saída de som para gravar. Ouvindo só o microfone."
    if not mic and not system: sys.exit("SEM_DISPOSITIVO: nenhum microfone nem saída de som encontrados.")
    return mic, system, note

def devices(_):
    import soundcard as sc
    print("Microfones:"); [print("  ", m.name) for m in sc.all_microphones()]
    print("Som do sistema (loopback):"); [print("  ", m.name) for m in sc.all_microphones(include_loopback=True) if getattr(m, "isloopback", False)]
    mic, system, note = pick_devices(sc)
    print("Escolhidos:", mic.name if mic else "-", "|", system.name if system else "-"); note and print(note)

def recorder(dev, q, stop):
    import numpy as np
    if sys.platform == "win32":
        import ctypes; ctypes.windll.ole32.CoInitializeEx(None, 0)  # COM em cada thread que grava
    try:
        with dev.recorder(samplerate=RATE, channels=1, blocksize=BLOCK) as r:
            while not stop.is_set(): q.put(np.asarray(r.record(numframes=BLOCK)).reshape(-1))
    except Exception as e:
        print(f"ERRO_DISPOSITIVO: {dev.name}: {e}", flush=True)

def to_wav(samples) -> bytes:
    import numpy as np
    n = len(samples) // 3 * 3
    down = samples[:n].reshape(-1, 3).mean(axis=1)  # 48k -> 16k
    pcm = (np.clip(down, -1, 1) * 32767).astype("<i2").tobytes()
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(OUT_RATE); w.writeframes(pcm)
    return buf.getvalue()

def transcribe(key, wav, lang) -> str:
    b = uuid.uuid4().hex
    parts = [("model", "whisper-large-v3-turbo"), ("language", lang), ("response_format", "text")]
    body = b"".join(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in parts)
    body += f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="a.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode() + wav + f"\r\n--{b}--\r\n".encode()
    for _ in range(3):
        req = urllib.request.Request(f"{API}/audio/transcriptions", data=body, headers={"Authorization": f"Bearer {key}", "Content-Type": f"multipart/form-data; boundary={b}"})
        code, text = http(req)
        if code == 200: return " ".join(text.split())
        if code == 429: time.sleep(3); continue
        if code == 401: print("CHAVE_INVALIDA: a Groq recusou a chave. Rode o setup de novo.", flush=True); sys.exit(2)
        return ""
    return ""

def listen(args):
    import numpy as np, soundcard as sc
    seg = max(1.0, float(args[0])) if args else 4.0
    lang = args[1] if len(args) > 1 else "pt"
    key = load_key()
    mic, system, note = pick_devices(sc)
    print(f"escutando: mic={mic.name if mic else '-'} som={system.name if system else '-'} pedaços={seg:g}s", flush=True)
    note and print(note, flush=True)
    stop = threading.Event(); qs = []
    for dev in (mic, system):
        if dev:
            q = queue.Queue(); qs.append(q)
            threading.Thread(target=recorder, args=(dev, q, stop), daemon=True).start()
    jobs = queue.Queue()
    def worker():
        while True:
            stamp, wav = jobs.get()
            text = transcribe(key, wav, lang)
            if re.sub(r"[\W_]+", "", text) and not HALLUCINATIONS.match(text): print(f"[{stamp}] {text}", flush=True)
    threading.Thread(target=worker, daemon=True).start()
    size = int(seg * RATE)
    try:
        while True:
            # espera pelo relógio, não pelos dispositivos: no Windows o loopback não entrega nada em silêncio
            time.sleep(seg)
            mixed = np.zeros(size, dtype="float32")
            for q in qs:
                got = []
                while not q.empty(): got.append(q.get())
                if got:
                    a = np.concatenate(got)[-size:]
                    mixed[size - len(a):] += a
            if np.abs(mixed).max() > 0.003: jobs.put((datetime.now().strftime("%H:%M:%S"), to_wav(mixed)))
    except KeyboardInterrupt:
        stop.set()

if __name__ == "__main__":
    cmd, rest = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ("listen", [])
    {"setup": setup, "devices": devices, "listen": listen}.get(cmd, lambda _: sys.exit(__doc__))(rest)
