"""Script de configuración inicial del proyecto."""

import subprocess
import sys
from pathlib import Path

VARIABLES = [
    ("MERCURIO_USER", "Usuario de Mercurio"),
    ("MERCURIO_PASSWORD", "Contraseña de Mercurio"),
    ("CONTRACT_NUMBER", "Número del contrato (ej. 8793440)"),
    ("CONTRACT_MONTHS", "Meses del contrato (ej. 10)"),
    ("SUPERVISOR_USER", "Usuario del supervisor (ej. CADURANG)"),
]


def instalar_dependencias():
    print("\n📦 Instalando dependencias...")
    subprocess.run(["uv", "sync"], check=True)
    print("✅ Dependencias instaladas.")


def instalar_navegador():
    print("\n🌐 Instalando navegador Chromium...")
    subprocess.run(["uv", "run", "playwright", "install", "chromium"], check=True)
    print("✅ Navegador instalado.")


def crear_carpeta_datos():
    data = Path("data")
    data.mkdir(exist_ok=True)
    gitkeep = data / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()
    print("✅ Carpeta data/ lista.")


def crear_env(path: Path):
    print(f"\n📝 Configurando {path}...\n")
    lines = []
    for key, label in VARIABLES:
        value = input(f"  {label} [{key}]: ").strip()
        if not value:
            print(f"\n  ❌ Error: {key} no puede estar vacío.")
            sys.exit(1)
        lines.append(f"{key}={value}")

    path.write_text("\n".join(lines) + "\n")
    print(f"\n✅ Archivo {path} creado correctamente.")


if __name__ == "__main__":
    print("=" * 50)
    print("  Configuración inicial - ADN Claude")
    print("=" * 50)

    instalar_dependencias()
    instalar_navegador()
    crear_carpeta_datos()

    print("\n--- Credenciales de producción (.env) ---")
    crear_env(Path(".env"))

    print("\n--- Credenciales de prueba (.env.test) ---")
    crear_env(Path(".env.test"))

    print("\n🎉 ¡Configuración completada! Ya puedes ejecutar el script.")
    print("   uv run python main.py --ccNo 1\n")
