import datetime
import json
import os
import socket
import string
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog

if getattr(sys, "frozen", False):
    RESOURCE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    PERSIST_DIR = os.path.dirname(sys.executable)
else:
    RESOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
    PERSIST_DIR = RESOURCE_DIR

APP_DIR = PERSIST_DIR
CONFIG_PATH = os.path.join(PERSIST_DIR, "config.json")
LOG_PATH = os.path.join(PERSIST_DIR, "guardiao.log")
MONITOR_PATH = os.path.join(RESOURCE_DIR, "monitor.ps1")
ICON_PATH = os.path.join(RESOURCE_DIR, "guardiao.ico")
ATIVAR_PATH = os.path.join(RESOURCE_DIR, "ativar_bloqueio.ps1")
DESATIVAR_PATH = os.path.join(RESOURCE_DIR, "desativar_bloqueio.ps1")
HOSTS_PATH = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "System32", "drivers", "etc", "hosts")
MARKER_INI = "# === GUARDIAO ANTI-RIOT ==="
LOCK_HOST = "127.0.0.1"
LOCK_PORT = 51337

APPDATA = os.environ.get("APPDATA", "")
LOCALAPPDATA = os.environ.get("LOCALAPPDATA", "")

FOLDER_SHIELD_PATHS = [
    os.path.join(f"{letra}:\\", "Riot Games")
    for letra in string.ascii_uppercase
    if os.path.exists(f"{letra}:\\")
] + [
    os.path.join(os.environ.get("ProgramData", r"C:\ProgramData"), "Riot Games"),
    os.path.join(LOCALAPPDATA, "Riot Games"),
]

CREATE_NO_WINDOW = 0x08000000

DEFAULT_CONFIG = {
    "quit_date": datetime.date.today().isoformat(),
    "guardian_enabled": True,
    "folder_shield": True,
    "network_block": False,
    "watch_dirs": [],
}


def log(mensagem):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {mensagem}\n")
    except OSError:
        pass


def carregar_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    except (OSError, ValueError):
        pass
    return cfg


def salvar_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def dias_livre(quit_date):
    try:
        inicio = datetime.date.fromisoformat(quit_date)
    except ValueError:
        inicio = datetime.date.today()
    return (datetime.date.today() - inicio).days


def hosts_tem_bloqueio():
    try:
        with open(HOSTS_PATH, "r", encoding="utf-8", errors="ignore") as f:
            return MARKER_INI in f.read()
    except OSError:
        return False


def aplicar_escudo():
    for caminho in FOLDER_SHIELD_PATHS:
        if os.path.isdir(caminho) or os.path.exists(caminho):
            continue
        pai = os.path.dirname(caminho)
        if pai and os.path.isdir(pai):
            try:
                with open(caminho, "w", encoding="utf-8") as f:
                    f.write("Bloqueio do Guardiao Anti-Riot. Nao apague.\n")
            except OSError:
                pass


def rodar_elevado(ps1):
    comando = (
        "Start-Process -FilePath powershell.exe -Verb RunAs "
        f"-ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','{ps1}'"
    )
    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", comando],
            creationflags=CREATE_NO_WINDOW,
        )
        return True
    except OSError as e:
        log(f"falha ao elevar: {e!r}")
        return False


class App:
    def __init__(self, root):
        self.root = root
        self.config = carregar_config()
        salvar_config(self.config)
        self.monitor_proc = None
        self.mensagens = []
        self.trava = threading.Lock()

        root.title("Guardião Anti-Riot")
        root.geometry("460x520")
        root.configure(bg="#12141c")
        root.resizable(False, False)
        try:
            root.iconbitmap(ICON_PATH)
        except Exception:
            pass

        tk.Label(root, text="GUARDIÃO ANTI-RIOT", bg="#12141c", fg="#4cc9f0",
                 font=("Segoe UI", 15, "bold")).pack(pady=(18, 4))

        self.lbl_dias = tk.Label(root, text="", bg="#12141c", fg="#f5f7fa",
                                 font=("Segoe UI", 46, "bold"))
        self.lbl_dias.pack(pady=(6, 0))

        self.lbl_sub = tk.Label(root, text="", bg="#12141c", fg="#9aa4b2", font=("Segoe UI", 12))
        self.lbl_sub.pack(pady=(0, 12))

        self.lbl_status = tk.Label(root, text="", bg="#12141c", fg="#c8d0da",
                                   font=("Segoe UI", 10), justify="center")
        self.lbl_status.pack(pady=(0, 14))

        self._botao("Configurar data de início", self.configurar_data)
        self.btn_guarda = self._botao("", self.alternar_guarda)
        self.btn_rede = self._botao("", self.alternar_rede)
        self.btn_escudo = self._botao("", self.alternar_escudo)
        self._botao("Abrir registro", self.abrir_registro)
        self._botao("Encerrar guardião", self.encerrar, cor="#e5484d")

        self.lbl_msg = tk.Label(root, text="Vigilância por eventos: só age quando algo da Riot aparece.",
                                bg="#12141c", fg="#7bd88f", font=("Segoe UI", 10, "italic"),
                                wraplength=400)
        self.lbl_msg.pack(side="bottom", pady=14)

        root.protocol("WM_DELETE_WINDOW", self.esconder)

        if self.config.get("folder_shield"):
            aplicar_escudo()
        if self.config.get("guardian_enabled"):
            self.iniciar_monitor()

        self.atualizar_tudo()
        self.root.after(1000, self.processar_mensagens)
        self.root.after(60000, self.atualizar_periodico)

    def _botao(self, texto, comando, cor="#1f2430"):
        b = tk.Button(self.root, text=texto, command=comando, bg=cor, fg="#f5f7fa",
                      activebackground="#2a3040", activeforeground="#ffffff",
                      font=("Segoe UI", 11), relief="flat", bd=0, padx=10, pady=8,
                      width=30, cursor="hand2")
        b.pack(pady=4)
        return b

    def iniciar_monitor(self):
        if self.monitor_proc and self.monitor_proc.poll() is None:
            return
        if not os.path.exists(MONITOR_PATH):
            return
        try:
            self.monitor_proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", MONITOR_PATH,
                 "-LogPath", LOG_PATH, "-ConfigPath", CONFIG_PATH],
                creationflags=CREATE_NO_WINDOW,
            )
            log("monitor iniciado pelo app")
        except OSError as e:
            log(f"falha ao iniciar monitor: {e!r}")

    def parar_monitor(self):
        p = self.monitor_proc
        if not p or p.poll() is not None:
            self.monitor_proc = None
            return
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)],
                           capture_output=True, creationflags=CREATE_NO_WINDOW)
        except OSError:
            pass
        self.monitor_proc = None

    def atualizar_tudo(self):
        dias = dias_livre(self.config.get("quit_date"))
        self.lbl_dias.config(text=str(dias))
        try:
            inicio = datetime.date.fromisoformat(self.config["quit_date"]).strftime("%d/%m/%Y")
        except (KeyError, ValueError):
            inicio = "?"
        self.lbl_sub.config(text=f"dias livre do LoL   (desde {inicio})")
        self.btn_guarda.config(
            text=("Desativar vigilância" if self.config.get("guardian_enabled")
                  else "Ativar vigilância"))
        self.btn_rede.config(
            text=("Desativar bloqueio de rede" if hosts_tem_bloqueio()
                  else "Ativar bloqueio de rede (admin)"))
        self.btn_escudo.config(
            text=("Desativar escudo de pastas" if self.config.get("folder_shield")
                  else "Ativar escudo de pastas"))
        g = "ATIVO" if self.config.get("guardian_enabled") else "DESLIGADO"
        r = "ligado" if hosts_tem_bloqueio() else "desligado"
        e = "ligado" if self.config.get("folder_shield") else "desligado"
        self.lbl_status.config(text=f"Vigilância: {g}   |   Rede: {r}   |   Escudo: {e}")
        self.config["network_block"] = hosts_tem_bloqueio()

    def atualizar_periodico(self):
        self.atualizar_tudo()
        self.root.after(60000, self.atualizar_periodico)

    def avisar(self, texto):
        with self.trava:
            self.mensagens.append(texto)

    def processar_mensagens(self):
        with self.trava:
            pendentes = self.mensagens[:]
            self.mensagens.clear()
        if pendentes:
            dias = dias_livre(self.config.get("quit_date"))
            corpo = " | ".join(pendentes[:4])
            self.lbl_msg.config(
                text=f"Guardião agiu: {corpo}\nVocê está há {dias} dias livre do LoL. Continue firme!")
        self.root.after(1000, self.processar_mensagens)

    def configurar_data(self):
        atual = self.config.get("quit_date", datetime.date.today().isoformat())
        resp = simpledialog.askstring(
            "Data de início",
            "Desde que data você está livre do LoL? (AAAA-MM-DD)",
            initialvalue=atual, parent=self.root)
        if not resp:
            return
        try:
            nova = datetime.date.fromisoformat(resp.strip())
        except ValueError:
            messagebox.showerror("Data inválida", "Use o formato AAAA-MM-DD.", parent=self.root)
            return
        if nova > datetime.date.today():
            messagebox.showerror("Data inválida", "A data não pode ser no futuro.", parent=self.root)
            return
        self.config["quit_date"] = nova.isoformat()
        salvar_config(self.config)
        log(f"data de inicio alterada para {nova.isoformat()}")
        self.atualizar_tudo()

    def alternar_guarda(self):
        self.config["guardian_enabled"] = not self.config.get("guardian_enabled")
        salvar_config(self.config)
        if self.config["guardian_enabled"]:
            self.iniciar_monitor()
        else:
            self.parar_monitor()
        self.atualizar_tudo()

    def alternar_rede(self):
        if hosts_tem_bloqueio():
            if not messagebox.askyesno("Desativar bloqueio",
                    "Desativar o bloqueio de rede da Riot?\nIsso vai liberar o jogo novamente.",
                    parent=self.root):
                return
            rodar_elevado(DESATIVAR_PATH)
        else:
            if not messagebox.askyesno("Ativar bloqueio",
                    "Vai abrir o pedido de administrador (UAC). Clique em Sim.\n"
                    "Isso bloqueia os servidores da Riot (o jogo fica inutilizável).",
                    parent=self.root):
                return
            rodar_elevado(ATIVAR_PATH)
        self.root.after(6000, self.atualizar_tudo)

    def alternar_escudo(self):
        self.config["folder_shield"] = not self.config.get("folder_shield")
        salvar_config(self.config)
        if self.config["folder_shield"]:
            aplicar_escudo()
        self.atualizar_tudo()

    def abrir_registro(self):
        if os.path.exists(LOG_PATH):
            os.startfile(LOG_PATH)

    def encerrar(self):
        if not messagebox.askyesno("Encerrar guardião",
                "Encerrar o guardião vai DESLIGAR a proteção.\nTem certeza?",
                parent=self.root):
            return
        resp = simpledialog.askstring("Confirmação",
                "Para confirmar, digite: ENCERRAR", parent=self.root)
        if resp != "ENCERRAR":
            messagebox.showinfo("Cancelado", "O guardião continua ativo.", parent=self.root)
            return
        log("guardiao encerrado pelo usuario")
        self.parar_monitor()
        self.root.destroy()

    def esconder(self):
        self.root.withdraw()

    def mostrar(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.atualizar_tudo()


def main():
    trava = socket.socket()
    try:
        trava.bind((LOCK_HOST, LOCK_PORT))
        trava.listen(5)
    except OSError:
        try:
            s = socket.create_connection((LOCK_HOST, LOCK_PORT), timeout=2)
            s.sendall(b"show")
            s.close()
        except OSError:
            pass
        return

    root = tk.Tk()
    app = App(root)

    def ouvinte():
        while True:
            try:
                conn, _ = trava.accept()
                dados = conn.recv(256)
                conn.close()
                if dados == b"show":
                    root.after(0, app.mostrar)
                elif dados.startswith(b"event:"):
                    msg = dados[6:].decode("utf-8", "ignore")
                    root.after(0, app.avisar, msg)
                    root.after(0, app.processar_mensagens)
            except OSError:
                break

    threading.Thread(target=ouvinte, daemon=True).start()
    root.mainloop()


if __name__ == "__main__":
    main()
