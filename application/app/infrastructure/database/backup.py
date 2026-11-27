
import sqlite3
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parents[3]

DATABASE_PATH = BASE_DIR / "database.db"
BACKUP_DIR = BASE_DIR / "backups"


def realizar_backup():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if not DATABASE_PATH.exists():
        raise FileNotFoundError("Banco de dados não encontrado.")

    horario = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = BACKUP_DIR / f"database_backup_{horario}.db"

    with sqlite3.connect(DATABASE_PATH) as banco_origem:
        with sqlite3.connect(backup_path) as banco_backup:
            banco_origem.backup(banco_backup)

    return backup_path

if __name__ == "__main__":
    caminho = realizar_backup()
    print(f"Backup criado com sucesso: {caminho}")