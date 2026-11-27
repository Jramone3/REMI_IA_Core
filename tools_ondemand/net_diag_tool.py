import socket

def dns_lookup(domain: str) -> dict:
    try:
        ips = sorted({info[4][0] for info in socket.getaddrinfo(domain.strip(), None)})
        return {"domain": domain, "addresses": ips}
    except Exception as e:
        return {"domain": domain, "error": str(e)}

def network_probe(host: str, port: int = 443, timeout: float = 3.0) -> dict:
    try:
        with socket.create_connection((host.strip(), int(port)), timeout=max(0.5, min(float(timeout), 8.0))):
            return {"host": host, "port": int(port), "reachable": True}
    except Exception as e:
        return {"host": host, "port": int(port), "reachable": False, "error": str(e)}
