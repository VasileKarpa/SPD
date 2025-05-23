# scale_monitor.py
import psutil, time, os, subprocess

# percentagem de RAM a partir da qual escalamos
THRESHOLD = 70
# nome do serviço a escalar (tal como no docker-compose)
SERVICE = "api"
# passo de escala
STEP = 1

def get_mem_usage_pct():
    return psutil.virtual_memory().percent

def scale_to(replicas):
    subprocess.run([
        "docker", "compose", "up", "-d",
        "--no-recreate", f"--scale", f"{SERVICE}={replicas}"
    ])

def main():
    current = 2  # arrancamos sempre com 2 réplicas
    scale_to(current)

    while True:
        pct = get_mem_usage_pct()
        if pct > THRESHOLD:
            current += STEP
            print(f"[Scaler] RAM {pct}% > {THRESHOLD}% → subindo para {current} réplicas")
            scale_to(current)
        time.sleep(5)

if __name__=="__main__":
    main()
