# Automatización de cuentas de cobro

Script que automatiza el proceso de radicación de cuentas de cobro en el sistema Mercurio del DANE: subida del PDF, llenado del formulario y envío al siguiente paso del workflow.

---

## Requisitos previos

### 1. Python

Descarga e instala Python 3.10 o superior desde [python.org](https://www.python.org/downloads/).

### 2. uv

`uv` es el gestor de dependencias que usa este proyecto. Para instalarlo abre una terminal y ejecuta:

**Mac / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Cierra y vuelve a abrir la terminal después de instalar.

---

## Instalación

Abre una terminal en la carpeta del proyecto y ejecuta:

```bash
uv run python setup_env.py
```

Este script hace todo lo necesario:
- Instala las dependencias del proyecto
- Instala el navegador Chromium
- Crea la carpeta `data/`
- Te pide las credenciales de producción y de prueba, y crea los archivos de configuración

Durante la configuración se te pedirán los siguientes valores:

| Variable | Descripción | Ejemplo |
|---|---|---|
| `MERCURIO_USER` | Tu usuario de acceso a Mercurio | `JPEREZ` |
| `MERCURIO_PASSWORD` | Tu contraseña de Mercurio | |
| `CONTRACT_MONTHS` | Número de meses del contrato | `10` |
| `SUPERVISOR_USER` | Usuario del supervisor en Mercurio | `CADURANG` |

Se crean dos archivos: `.env` (producción) y `.env.test` (pruebas). Ambos requieren los mismos valores.

---

## Preparar los documentos

Antes de ejecutar, crea una carpeta dentro de `data/` con el número de la cuenta de cobro en dos dígitos y coloca el PDF dentro:

```
data/
  01/
    31InformeActividadesCertificadoCumplimiento.pdf
  02/
    31InformeActividadesCertificadoCumplimiento.pdf
```

---

## Uso

```bash
uv run python main.py --ccNo 1
```

Reemplaza `1` con el número de la cuenta de cobro que vas a radicar.

Si el PDF se llama `31InformeActividadesCertificadoCumplimiento.pdf`, el script lo renombra automáticamente al nombre estándar de Mercurio `[USUARIO][CONTRATO][AÑO]CTA[CUENTA][TOTAL]` (ej. `SACORREDORM879344026CTA0909.pdf`). Si ya tiene el formato nuevo, no se cambia.

El script abre el navegador automáticamente, realiza todos los pasos y al finalizar muestra un mensaje de confirmación. Presiona Enter en la terminal para cerrarlo.

---

## Modo de prueba

Si quieres revisar el formulario antes de enviarlo, usa la opción `--test`:

```bash
uv run python main.py --ccNo 1 --test
```

El script pausará justo antes de indexar el documento para que puedas verificar que todo esté correcto. En modo prueba se usan las credenciales del archivo `.env.test` (configurado con `uv run python setup_env.py` → opción `test`).
