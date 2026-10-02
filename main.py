import argparse
import os
import sys
import time
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import Page, sync_playwright

URL = "https://gestiondocumental.dane.gov.co/mercurio/index.jsp"
DELAY = 1
DATA_DIR = Path(__file__).parent / "data"
PDF_NAMES = ("31InformeActividadesCertificadoCumplimiento.pdf", "31InfoActiCertiCumplimiento.pdf")


def step(page, action):
    action()
    time.sleep(DELAY)
    page.wait_for_load_state("networkidle")


def cerrar_sesion(page):
    page.click('text=Salir')
    time.sleep(DELAY)


def validar_archivos(cc_no: int) -> Path:
    carpeta = DATA_DIR / f"{cc_no:02d}"
    if not carpeta.is_dir():
        print(f"Error: no existe la carpeta '{carpeta}'")
        sys.exit(1)

    # Preferir archivo ya en formato nuevo (...CTA0909.pdf); si no, el nombre antiguo
    nuevos = sorted(carpeta.glob(f"*CTA{cc_no:02d}[0-9][0-9].pdf"))
    antiguos = [carpeta / n for n in PDF_NAMES if (carpeta / n).is_file()]
    pdf = nuevos[0] if nuevos else antiguos[0] if antiguos else None
    if pdf is None:
        print(f"Error: no existe {' ni '.join(PDF_NAMES)} ni un archivo con formato nuevo en '{carpeta}'")
        sys.exit(1)

    print(f"Archivo encontrado: {pdf}")
    return pdf


def ir_a_bandeja_workflow(page: Page) -> None:
    """Desde la página principal valida y navega a la bandeja de workflow.

    Verifica que WorkFlow tenga exactamente 1 pendiente, hace click,
    valida que haya 1 documento en la bandeja y que esté en paso 20/22.
    Cierra sesión y termina el script si alguna validación falla.
    """
    page.wait_for_selector('a[href*="BandejaRutas"]')
    workflow_link = page.locator('a[href*="BandejaRutas"]')
    workflow_count = int(workflow_link.inner_text().strip())

    if workflow_count != 1:
        print(f"WorkFlow tiene {workflow_count} pendiente(s), se esperaba 1. Cerrando sesión.")
        cerrar_sesion(page)
        sys.exit(1)

    print("WorkFlow tiene 1 pendiente. Continuando...")
    step(page, lambda: workflow_link.click())

    doc_count = page.locator('a[href*="expedientes"]').count()
    if doc_count != 1:
        print(f"Se esperaba 1 documento en bandeja, hay {doc_count}. Cerrando sesión.")
        cerrar_sesion(page)
        sys.exit(1)

    paso = page.locator('table tbody tr').first.locator('td').nth(8).inner_text().strip()
    if not paso.startswith("20/22"):
        print(f"Paso inesperado: '{paso}', se esperaba '20/22'. Cerrando sesión.")
        cerrar_sesion(page)
        sys.exit(1)

    print(f"Documento en paso {paso}.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ccNo", type=int, required=True, help="Número de cuenta de cobro")
    parser.add_argument("--test", action="store_true", help="Modo prueba: pausa para confirmación manual")
    args = parser.parse_args()

    pdf_path = validar_archivos(args.ccNo)

    env_file = ".env.test" if args.test else ".env"
    load_dotenv(env_file)
    user = os.environ["MERCURIO_USER"]
    password = os.environ["MERCURIO_PASSWORD"]
    contract_months = os.environ["CONTRACT_MONTHS"]
    supervisor_user = os.environ["SUPERVISOR_USER"]
    numero_contrato = os.environ["CONTRACT_NUMBER"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Aceptar diálogos automáticamente (ej. "Ya existe una sesión abierta")
        page.on('dialog', lambda d: d.accept())

        # Login
        step(page, lambda: page.goto(URL))
        step(page, lambda: page.fill('input[placeholder="Ingresar nombre de usuario"]', user))
        step(page, lambda: page.fill('input[placeholder="Ingresar contraseña"]', password))
        step(page, lambda: page.click('button:has-text("Ingresar")'))

        # --- Primera visita al workflow: abrir expediente ---
        ir_a_bandeja_workflow(page)

        step(page, lambda: page.click('a[href*="javascript:selectDoc0();expedientes();"]'))

        step(page, lambda: page.locator('table tbody tr').first.locator('a').first.click())

        # Mostrar opciones → Anexar al Expediente
        page.click('button:has-text("Mostrar opciones")')
        time.sleep(0.5)
        page.wait_for_load_state("networkidle")
        step(page, lambda: page.frame_locator('iframe[name="opcionesExpediente"]').get_by_role('link', name='Anexar al Expediente').click())

        # Renombrar el PDF con nombre antiguo al nombre estándar de Mercurio (ej. SACORREDORM879344026CTA0909)
        anio = f"{date.today().year % 100:02d}"
        if pdf_path.name in PDF_NAMES:
            nombre_archivo = f"{user.upper()}{numero_contrato}{anio}CTA{args.ccNo:02d}{int(contract_months):02d}.pdf"
            pdf_path = pdf_path.rename(pdf_path.with_name(nombre_archivo))
            print(f"Archivo renombrado: {pdf_path}")

        # Subir el PDF
        step(page, lambda: page.set_input_files('input[type="file"]', str(pdf_path)))

        # Código asunto: abre popup de búsqueda
        with page.context.expect_page() as popup_info:
            page.get_by_text('*Código Asunto:').click()
        popup = popup_info.value
        popup.wait_for_load_state("networkidle")
        time.sleep(DELAY)

        popup.get_by_role('textbox', name='Ingrese id asunto').fill('340.21.2')
        time.sleep(0.5)
        popup.get_by_role('button', name='Buscar').click()
        popup.wait_for_load_state("networkidle")
        time.sleep(DELAY)

        popup.get_by_role('row', name='340.21.2 CONTRATOS POR').click()
        time.sleep(0.5)
        popup.locator('button[name="enviar"]').first.click()
        time.sleep(DELAY)

        # Tipo de documento
        tipo_doc = "Formato Único De Informe De Actividades y Certificado De Cumplimiento"
        page.get_by_role('combobox').last.click()
        time.sleep(0.5)
        step(page, lambda: page.get_by_role('option', name=tipo_doc).click())

        # Descripción
        descripcion = pdf_path.stem  # Mercurio exige el nombre nomenclado en la descripción
        print(f"Descripción: {descripcion}")
        page.locator('#descripcion').fill(descripcion)
        time.sleep(5)
        page.wait_for_load_state("networkidle")

        if args.test:
            input("Modo test: revisa el formulario y presiona Enter para indexar...")

        # Indexar el anexo
        step(page, lambda: page.get_by_role('button', name='Indexar Anexo').click())

        # Click en DOCUMENTOS para recargar y confirmar
        page.frame_locator('iframe[name="carpetasExpediente"]').get_by_role('link', name='DOCUMENTOS').click()
        time.sleep(0.5)
        page.wait_for_load_state("networkidle")
        time.sleep(DELAY)

        # Validar documento con fecha de hoy
        hoy = date.today().strftime("%d/%m/%Y")
        iframe = page.frame_locator('iframe[name="iFrameDocumentos"]')
        filas = iframe.locator('table tbody tr')
        fechas_origen = [filas.nth(i).locator('td').nth(6).inner_text().strip()
                         for i in range(filas.count())]
        if not any(hoy in f for f in fechas_origen):
            print(f"No se encontró documento con fecha de origen {hoy}. Revisar manualmente.")
        else:
            print(f"Documento con fecha {hoy} encontrado correctamente.")

        # Volver a Inicio
        step(page, lambda: page.locator('#inicio').click())

        # --- Segunda visita al workflow ---
        ir_a_bandeja_workflow(page)

        # Gestión → Siguiente Paso
        page.get_by_text('Gestión').click()
        time.sleep(0.5)
        step(page, lambda: page.get_by_text('Siguiente Paso').click())

        # Seleccionar gestor: buscar por SUPERVISOR_USER y hacer click en la fila
        step(page, lambda: page.get_by_role('textbox').fill(supervisor_user))
        page.locator('table tbody tr').filter(has_text=supervisor_user).first.click()
        time.sleep(0.5)
        step(page, lambda: page.get_by_role('button', name='Aceptar').click())

        # Validar mensaje de confirmación
        page.wait_for_selector('text=Documento enviado')
        msg = page.locator('text=Documento enviado').first.inner_text()
        print(f"Proceso completado exitosamente. {msg}")

        input("Presiona Enter para cerrar el navegador...")
        browser.close()


if __name__ == "__main__":
    main()