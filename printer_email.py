import os
import sys
from collections import defaultdict
from datetime import datetime
from dotenv import load_dotenv
from email.message import EmailMessage
import smtplib

from printer_monitor import check_printer_toners, get_printer_page_source
from printers import PRINTERS

load_dotenv()
smtp_server = os.getenv("SMTP_SERVER")
smtp_port = int(os.getenv("SMTP_PORT", "587"))
smtp_user = os.getenv("SMTP_USER")
smtp_pass = os.getenv("SMTP_PASS")
email_recipients = [d.strip() for d in os.getenv("EMAIL_RECIPIENTS", "").split(",") if d.strip()]

def generate_email_alert(results: list, threshold: int) -> str:
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    lines = []
    lines.append("⚠️ *Alerta de Toner com Nível Baixo*  ")
    lines.append(f"Atualizado em: {now}  ")
    lines.append("")
    lines.append(f"Limite de atenção: cartuchos com nível ≤ {threshold}%")
    lines.append("")
    lines.append("Impressoras com cartuchos críticos (ordenado por prédio, depois por nível crescente):")
    lines.append("")

    grouped = defaultdict(list)
    for printer in results:
        building = printer["predio"]
        critical = []
        for name, level in printer["levels"].items():
            if level is not None and level <= threshold:
                critical.append((name, level))
        if critical:
            critical.sort(key=lambda x: x[1])
            grouped[building].append((printer, critical))

    if not grouped:
        lines.append("Nenhum cartucho crítico no momento.")
        return "\n".join(lines)

    for building in sorted(grouped.keys()):
        lines.append(f"🏢 {building}  ")
        for printer, crits in sorted(grouped[building], key=lambda x: x[0]["nome"]):
            lines.append(f"  🖨️ {printer['nome']}  ")
            for name, level in crits:
                emoji = {
                    "Ciano": "🟦",
                    "Magenta": "🟪",
                    "Amarelo": "🟨",
                    "Preto": "⬛",
                }.get(name, "")
                lines.append(f"    {emoji} {name}: {level}%")
        lines.append("")

    lines.append("Este é um alerta automático gerado pelo sistema de monitoramento de impressoras.")
    return "\n".join(lines)

def send_email(content: str):
    msg = EmailMessage()
    msg["From"] = smtp_user
    msg["To"] = email_recipients
    msg["Subject"] = "Alerta de Toner com Nível Baixo"
    msg.set_content(content)

    with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

def main():
    results = []
    threshold = 15
    for printer in PRINTERS:
        try:
            page_source = get_printer_page_source(printer['ip'])
            levels = check_printer_toners(page_source)
            results.append({
                "nome": printer["nome"],
                "predio": printer["local"],
                "levels": levels
            })
            print(printer['ip'])
        except Exception:
            continue

    email_text = generate_email_alert(results, threshold)

    low_exists = any(
        level is not None and level <= threshold
        for entry in results
        for level in entry["levels"].values()
    )

    print(email_text)
    print("#" * 20)
    if low_exists:
        send_email(content=email_text)
        print("E-mail enviado")

    sys.exit(0)

if __name__ == "__main__":
    main()