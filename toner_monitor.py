import subprocess
import re
from typing import Optional, Dict
from bs4 import BeautifulSoup

CORES = {
    'Amarelo': 'SupplyPLR0',
    'Magenta': 'SupplyPLR1', 
    'Ciano': 'SupplyPLR2',
    'Preto': 'SupplyPLR3'
}

def _normalize_value(raw: str) -> Optional[int]:
    if not raw:
        return None
    raw = raw.strip()
    if raw.startswith("--"):
        return 0
    m = re.search(r"(\d+)", raw)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None

def _fetch_with_curl(url: str, timeout: int = 8) -> str:
    try:
        result = subprocess.run(
            ["curl", "-k", "-L", url],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise Exception(f"curl falhou: {e.stderr.strip() or e}") from e
    except subprocess.TimeoutExpired as e:
        raise Exception(f"curl expirou: {e}") from e
    
def check_printer_toners(ip):
    try:
        url = f"https://{ip}/hp/device/DeviceStatus/Index"
        html = _fetch_with_curl(url)
        soup = BeautifulSoup(html, "html.parser")

        # Procura todos os spans de interesse
        found = {}
        for color, span_id in CORES.items():
            span = soup.find("span", {"id": span_id})
            if span:
                raw = span.get_text(strip=True)
                val = _normalize_value(raw)
                found[span_id] = val               

        if not found:
            raise Exception("Nenhum span de toner encontrado na página.")

        is_colorida = len(found) > 3

        niveis: Dict[str, Optional[int]] = {}
        if is_colorida:
            for name, span_id  in CORES.items():
                niveis[name] = found.get(span_id)
        else:
            niveis["Preto"] = found.get("SupplyPLR0")   

    except Exception as e:
        print(f"Erro ao acessar impressora {ip}: {e}")
        return None

    return niveis