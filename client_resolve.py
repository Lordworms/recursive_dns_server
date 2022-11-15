import logging
import argparse
import dns.message
import dns.name
import dns.query
import dns.rdata
import dns.rdataclass
import dns.rdatatype
import dns.resolver
import pydig
from dns.exception import DNSException, Timeout

def get_ip(domain):  
  ip_list = []
  try:
    A = dns.resolver.query(domain, 'A')
    for i in A.response.answer:
      for j in i.items:
        if isinstance(j, dns.rdtypes.IN.A.A):  
          ip_list.append(j.address)
         
    AAAA = dns.resolver.query(domain, 'AAAA')
    for i in AAAA.response.answer:
      for j in i.items:
        if isinstance(j, dns.rdtypes.IN.AAAA.AAAA):  
          ip_list.append(j.address)
  except Exception as e:
    return ip_list[0]
    
  return ip_list[0]

FORMATS = (("CNAME", "{alias} is an alias for {name}"),
           ("A", "{name} has address {address}"),
           ("AAAA", "{name} has IPv6 address {address}"),
           ("MX", "{name} mail is handled by {preference} {exchange}"))
ROOT_SERVERS = ("198.41.0.4",
                "199.9.14.201",
                "192.33.4.12",
                "199.7.91.13",
                "192.203.230.10",
                "192.5.5.241",
                "192.112.36.4",
                "198.97.190.53",
                "192.36.148.17",
                "192.58.128.30",
                "193.0.14.129",
                "199.7.83.42",
                "202.12.27.33")
count = 0

class Local_Dns_Resolver():
    def __init__(self):
        self.dns_cache={}
        self.dns_cache['response_cache'] = {}
    def collect_results(self,name: str, dns_cache: dict) -> dict:
        full_response = {}
        target_name = dns.name.from_text(name)
        # lookup A
        response = self.lookup(target_name, dns.rdatatype.A, self.dns_cache)
        arecords = []
        for answers in response.answer:
            a_name = answers.name
            for answer in answers:
                if answer.rdtype == 1:  # A record
                    arecords.append({"name": a_name, "address": str(answer)})
        full_response["A"] = arecords
        self.dns_cache.get('response_cache')[name] = full_response
        return full_response

    def lookup_recurse(self,target_name: dns.name.Name,
                    qtype: dns.rdata.Rdata,
                    ip_,
                    resolved,
                    dns_cache: dict) -> dns.message.Message:
        global count
        count += 1
        outbound_query = dns.message.make_query(target_name, qtype)
        try:
            response = dns.query.udp(outbound_query, ip_, 3)
            if response.answer:
                # logging.debug("\n---------Got Answer-------\n")
                resolved = True
                return response, resolved

            elif response.additional:
                if response.authority:
                    self.update_cache(response, self.dns_cache)
                response, resolved = self.lookup_additional(response, target_name,
                                                    qtype, resolved, self.dns_cache)

            elif response.authority and not resolved:
                response, resolved = self.lookup_authority(response, target_name,
                                                    qtype, resolved, self.dns_cache)
            return response, resolved

        except Timeout:
            # logging.debug("Timeout")
            return dns.message.Message(), False
        except DNSException:
            # logging.debug("DNSException")
            return dns.message.Message(), False


    def lookup(self,target_name: dns.name.Name,
            qtype: dns.rdata.Rdata,
            dns_cache: dict) -> dns.message.Message:
        i = 0
        resolved = False
        while i < len(ROOT_SERVERS):
            ip_from_cache = ""
            find_name = str(target_name)
            next_dot = str(target_name).find('.')

            while not ip_from_cache and next_dot > -1:
                ip_from_cache = self.dns_cache.get(find_name)
                find_name = str(find_name)[next_dot+1:]
                next_dot = find_name.find('.')
            if ip_from_cache:
                ip_ = ip_from_cache
                logging.debug("--------Found target in cache--------\n")

            else:
                ip_ = ROOT_SERVERS[i]

            try:
                response, resolved = self.lookup_recurse(target_name, qtype, ip_, resolved, self.dns_cache)

                if response.answer:
                    answer_type = response.answer[0].rdtype
                    if qtype != dns.rdatatype.CNAME  and answer_type == dns.rdatatype.CNAME:
                        target_name = dns.name.from_text(str(response.answer[0][0]))
                        resolved = False
                        logging.debug("--------- look up cname ----------- %s \n %s", target_name, response.answer[0])
                        response = self.lookup(target_name, qtype, self.dns_cache)
                    return response

                elif response.authority and response.authority[0].rdtype == dns.rdatatype.SOA:
                    break
                else:
                    i += 1

            except Timeout:
                i += 1
            except DNSException:
                i += 1
        return response

    def update_cache(self,response: dns.message.Message, dns_cache):
        domain_name = response.authority[0].to_text().split(" ")[0]

        arecords = []
        rrsets = response.additional
        for rrset in rrsets:
            for rr_ in rrset:
                if rr_.rdtype == dns.rdatatype.A:
                    arecords.append(str(rr_))
                    self.dns_cache[domain_name] = str(rr_)

    def lookup_additional(self,response,
                        target_name: dns.name.Name,
                        qtype: dns.rdata.Rdata,
                        resolved,
                        dns_cache: dict):
        rrsets = response.additional
        for rrset in rrsets:
            for rr_ in rrset:
                if rr_.rdtype == dns.rdatatype.A:
                    response, resolved = self.lookup_recurse(target_name, qtype,
                                                        str(rr_), resolved, self.dns_cache)
                if resolved:
                    break
            if resolved:
                break
        return response, resolved


    def lookup_authority(self,response,
                        target_name: dns.name.Name,
                        qtype: dns.rdata.Rdata,
                        resolved,
                        dns_cache: dict):
        rrsets = response.authority
        ns_ip = ""
        for rrset in rrsets:
            for rr_ in rrset:
                if rr_.rdtype == dns.rdatatype.NS:
                    ns_ip = dns_cache.get(str(rr_))
                    if not ns_ip:
                        ns_arecords = self.lookup(str(rr_), dns.rdatatype.A, self.dns_cache)
                        ns_ip = str(ns_arecords.answer[0][0])
                        self.dns_cache[str(rr_)] = ns_ip

                    response, resolved = self.lookup_recurse(target_name, qtype,
                                                        ns_ip, resolved, self.dns_cache)
                elif rr_.rdtype == dns.rdatatype.SOA:
                    resolved = True
                    break
            if resolved:
                break

        return response, resolved


    def print_results(self,results: dict) -> None:
        print("print_results")
        for rtype, fmt_str in FORMATS:
            for result in results.get(rtype, []):
                print(fmt_str.format(**result))

    def default_look(self,domain_name):
        str='www.'+domain_name
        resolver = pydig.Resolver(
        executable='/usr/bin/dig',     
        nameservers=[
            '8.8.8.8',
        ],
        additional_args=[
            '+time=10',
        ]
        )
        return resolver.query(str,"A")

    def getIp(self,str):
        global count
        domain_names=[str]
        for a_domain_name in domain_names:
            count = 0
            cache_result = self.dns_cache.get('response_cache').get(a_domain_name)
            if cache_result:
                #print("hit!")
                return cache_result['A']
            else:
                res=self.collect_results(a_domain_name, self.dns_cache)
                if len(res['A'])==0:
                    return self.default_look(str)
                else :
                    return res['A'][0]['address']
                print_results(res)
            logging.debug("count %s", count)
        
