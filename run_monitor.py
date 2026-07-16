"""
Trading Assistant AI - Signal Monitor (entry point).

Cach dung:
    python run_monitor.py              # chay nen, canh tin hieu lien tuc
    python run_monitor.py --once       # kiem tra 1 lan roi thoat
    python run_monitor.py --test       # gui thong bao test qua TAT CA kenh dang bat
"""

import os
import sys
import traceback
from datetime import datetime


class _Tee:
    """Ghi stdout ra CA man hinh LAN file log/run.log."""
    def __init__(self, logfile):
        self.terminal = sys.__stdout__
        self.log = open(logfile, "a", encoding="utf-8")
        self.log.write("\n===== RUN {} =====\n".format(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.log.flush()

    def write(self, msg):
        try:
            self.terminal.write(msg)
        except Exception:
            pass
        self.log.write(msg)
        self.log.flush()

    def flush(self):
        try:
            self.terminal.flush()
        except Exception:
            pass
        self.log.flush()


def _setup_log():
    os.makedirs("logs", exist_ok=True)
    tee = _Tee(os.path.join("logs", "run.log"))
    sys.stdout = tee
    sys.stderr = tee


from src.core.config import Config
from src.notifier.factory import create_notifier


def _no_channel_msg(config):
    print("[ERROR] Chua co kenh thong bao nao kha dung. Kiem tra file .env.")
    missing = config.validate_email()
    if missing:
        print("  -> Email dang thieu:", ", ".join(missing))


def _run_test(config, notifier):
    print("Cau hinh email : Gmail={} -> To={}".format(
        config.gmail_user or "(missing)", config.mail_to or "(missing)"))
    print("Kenh dang bat  :", notifier.channel_names())
    print("Dang gui mail test...")
    try:
        ok = notifier.send(
            "[Trading Assistant AI] Test OK",
            "Neu ban nhan duoc thong bao nay, cau hinh da hoat dong.\n"
            "-- Trading Assistant AI")
    except Exception as e:
        print("[FAIL] Loi khi gui:", e)
        traceback.print_exc()
        return
    print("[OK] Da gui. Kiem tra hop thu (ca Spam)." if ok
          else "[FAIL] Gui that bai - xem log loi ben tren.")


def main():
    _setup_log()
    args = sys.argv[1:]
    print("Python:", sys.executable)
    config = Config()

    notifier = create_notifier(config)
    if notifier is None:
        _no_channel_msg(config)
        return

    if "--test" in args or "--test-mail" in args:
        _run_test(config, notifier)
        return

    try:
        from src.scheduler.monitor import Monitor
    except Exception as e:
        print("[ERROR] Khong nap duoc Monitor (thieu thu vien?):", e)
        print("Hay chay SETUP.bat de cai thu vien.")
        traceback.print_exc()
        return

    once = "--once" in args
    Monitor(config, once=once, notifier=notifier).run()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("[FATAL]", e)
        traceback.print_exc()
