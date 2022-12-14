import logging
import argparse
import dns.message
import dns.name
import dns.query
import dns.rdata
import dns.rdataclass
import dns.rdatatype

from dns.exception import DNSException, Timeout

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

def collect_results(name: str, dns_cache: dict) -> dict:
    full_response = {}
    target_name = dns.name.from_text(name)
    # lookup A
    response = lookup(target_name, dns.rdatatype.A, dns_cache)
    arecords = []
    for answers in response.answer:
        a_name = answers.name
        for answer in answers:
            if answer.rdtype == 1:  # A record
                arecords.append({"name": a_name, "address": str(answer)})
    '''
    # lookup AAAA
    response = lookup(target_name, dns.rdatatype.AAAA, dns_cache)
    aaaarecords = []
    for answers in response.answer:
        aaaa_name = answers.name
        for answer in answers:
            if answer.rdtype == 28:  # AAAA record
                aaaarecords.append({"name": aaaa_name, "address": str(answer)})
    
    # lookup CNAME
    response = lookup(target_name, dns.rdatatype.CNAME, dns_cache)
    cnames = []
    for answers in response.answer:
        for answer in answers:
            cnames.append({"name": answer, "alias": name})
    # lookup MX
    response = lookup(target_name, dns.rdatatype.MX, dns_cache)
    mxrecords = []
    for answers in response.answer:
        mx_name = answers.name
        for answer in answers:
            if answer.rdtype == 15:  # MX record
                mxrecords.append({"name": mx_name,
                                  "preference": answer.preference,
                                  "exchange": str(answer.exchange)})
    '''
    #full_response["CNAME"] = cnames
    full_response["A"] = arecords
    #full_response["AAAA"] = aaaarecords
    #full_response["MX"] = mxrecords

    dns_cache.get('response_cache')[name] = full_response

    return full_response

def lookup_recurse(target_name: dns.name.Name,
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
                update_cache(response, dns_cache)
            response, resolved = lookup_additional(response, target_name,
                                                   qtype, resolved, dns_cache)

        elif response.authority and not resolved:
            response, resolved = lookup_authority(response, target_name,
                                                  qtype, resolved, dns_cache)
        return response, resolved

    except Timeout:
        # logging.debug("Timeout")
        return dns.message.Message(), False
    except DNSException:
        # logging.debug("DNSException")
        return dns.message.Message(), False


def lookup(target_name: dns.name.Name,
           qtype: dns.rdata.Rdata,
           dns_cache: dict) -> dns.message.Message:
    i = 0
    resolved = False
    while i < len(ROOT_SERVERS):
        ip_from_cache = ""
        find_name = str(target_name)
        next_dot = str(target_name).find('.')

        while not ip_from_cache and next_dot > -1:
            ip_from_cache = dns_cache.get(find_name)
            find_name = str(find_name)[next_dot+1:]
            next_dot = find_name.find('.')
        if ip_from_cache:
            ip_ = ip_from_cache
            logging.debug("--------Found target in cache--------\n")

        else:
            ip_ = ROOT_SERVERS[i]

        try:
            response, resolved = lookup_recurse(target_name, qtype, ip_, resolved, dns_cache)

            if response.answer:
                answer_type = response.answer[0].rdtype
                if qtype != dns.rdatatype.CNAME  and answer_type == dns.rdatatype.CNAME:
                    target_name = dns.name.from_text(str(response.answer[0][0]))
                    resolved = False
                    logging.debug("--------- look up cname ----------- %s \n %s", target_name, response.answer[0])
                    response = lookup(target_name, qtype, dns_cache)
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

def update_cache(response: dns.message.Message, dns_cache):
    domain_name = response.authority[0].to_text().split(" ")[0]

    arecords = []
    rrsets = response.additional
    for rrset in rrsets:
        for rr_ in rrset:
            if rr_.rdtype == dns.rdatatype.A:
                arecords.append(str(rr_))
                dns_cache[domain_name] = str(rr_)

def lookup_additional(response,
                      target_name: dns.name.Name,
                      qtype: dns.rdata.Rdata,
                      resolved,
                      dns_cache: dict):
    rrsets = response.additional
    for rrset in rrsets:
        for rr_ in rrset:
            if rr_.rdtype == dns.rdatatype.A:
                response, resolved = lookup_recurse(target_name, qtype,
                                                    str(rr_), resolved, dns_cache)
            if resolved:
                break
        if resolved:
            break
    return response, resolved


def lookup_authority(response,
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
                    ns_arecords = lookup(str(rr_), dns.rdatatype.A, dns_cache)
                    ns_ip = str(ns_arecords.answer[0][0])
                    dns_cache[str(rr_)] = ns_ip

                response, resolved = lookup_recurse(target_name, qtype,
                                                    ns_ip, resolved, dns_cache)
            elif rr_.rdtype == dns.rdatatype.SOA:
                resolved = True
                break
        if resolved:
            break

    return response, resolved


def print_results(results: dict) -> None:
    print("print_results")
    for rtype, fmt_str in FORMATS:
        for result in results.get(rtype, []):
            print(fmt_str.format(**result))


def main(str):
    global count
    dns_cache = {}
    dns_cache['response_cache'] = {}
    domain_names=[str]
    for a_domain_name in domain_names:
        count = 0
        cache_result = dns_cache.get('response_cache').get(a_domain_name)
        if cache_result:
           return cache_result['A']
        else:
            res=collect_results(a_domain_name, dns_cache)
            if len(res['A'])==0:
                return -1
            else :
                return res['A'][0]['address']
            print_results(res)
        logging.debug("count %s", count)