from dns.resolver import Resolver
from dnslib import DNSRecord, QTYPE, RD, SOA, DNSHeader, RR, A
import logging
import socket
import client_resolve as cr
dns_resolver = Resolver()
dns_resolver.nameservers = ["8.8.8.8", "8.8.4.4"]
local_resolver=cr.Local_Dns_Resolver()
def get_ip_from_domain(domain):
    domain = domain.lower().strip()
    try:
        return local_resolver.getIp(domain);
    except:
        print("did not get the ip")
        return dns_resolver.query(domain, 'A')[0].to_text()
def reply_for_not_found(income_record):
    header = DNSHeader(id=income_record.header.id, bitmap=income_record.header.bitmap, qr=1)
    header.set_rcode(0)  # 3 DNS_R_NXDOMAIN, 2 DNS_R_SERVFAIL, 0 DNS_R_NOERROR
    record = DNSRecord(header, q=income_record.q)
    return record
def reply_for_A(income_record, ip, ttl=None):
    if isinstance(ip,list):
        print(ip)
        ip=ip[0]['address']
    r_data = A(ip)
    header = DNSHeader(id=income_record.header.id, bitmap=income_record.header.bitmap, qr=1)
    domain = income_record.q.qname
    query_type_int = QTYPE.reverse.get('A') or income_record.q.qtype
    record = DNSRecord(header, q=income_record.q, a=RR(domain, query_type_int, rdata=r_data, ttl=ttl))
    return record
def dns_handler(s, message, address):
    try:
        income_record = DNSRecord.parse(message)
    except:
        logging.error('from %s, parse error' % address)
        return
    try:
        qtype = QTYPE.get(income_record.q.qtype)
    except:
        qtype = 'unknown'
    domain = str(income_record.q.qname).strip('.')
    print("get ip for domain ",domain)
    info = '%s -- %s, from %s' % (qtype, domain, address)
    if qtype == 'A':
        ip = get_ip_from_domain(domain)
        if ip:
            print("find {} for domain {}".format(ip,domain))
            #print(income_record)
            response = reply_for_A(income_record, ip=ip, ttl=60)
            s.sendto(response.pack(), address)
            #return logging.info(info)
    # at last
        else:
            print("did not find")
            response = reply_for_not_found(income_record)
            s.sendto(response.pack(), address)
    
    #logging.info(info)

if __name__ == '__main__':
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(('', 53))
    logging.info('dns server is started')
    while True:
        message, address = udp_sock.recvfrom(8192)
        dns_handler(udp_sock, message, address)