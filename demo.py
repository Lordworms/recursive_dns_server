from pythonping import ping

def ping_host(host):
    ping_result = ping(target=host, count=10, timeout=2)
    return ping_result.rtt_avg_ms