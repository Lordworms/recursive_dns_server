"""
resolve.py: a recursive resolver built using dnspython
"""
import logging
import argparse
# from datetime import datetime
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

# current as of 19 March 2018
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
    """
    This function parses final answers into the proper data structure that
    print_results requires. The main work is done within the `lookup` function.
    """
    full_response = {}
    target_name = dns.name.from_text(name)
    # lookup CNAME
    response = lookup(target_name, dns.rdatatype.CNAME, dns_cache)
    cnames = []
    for answers in response.answer:
        for answer in answers:
            cnames.append({"name": answer, "alias": name})
    # lookup A
    response = lookup(target_name, dns.rdatatype.A, dns_cache)
    arecords = []
    for answers in response.answer:
        a_name = answers.name
        for answer in answers:
            if answer.rdtype == 1:  # A record
                arecords.append({"name": a_name, "address": str(answer)})
    # lookup AAAA
    response = lookup(target_name, dns.rdatatype.AAAA, dns_cache)
    aaaarecords = []
    for answers in response.answer:
        aaaa_name = answers.name
        for answer in answers:
            if answer.rdtype == 28:  # AAAA record
                aaaarecords.append({"name": aaaa_name, "address": str(answer)})
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

    full_response["CNAME"] = cnames
    full_response["A"] = arecords
    full_response["AAAA"] = aaaarecords
    full_response["MX"] = mxrecords

    dns_cache.get('response_cache')[name] = full_response

    return full_response

def lookup_recurse(target_name: dns.name.Name,
                   qtype: dns.rdata.Rdata,
                   ip_,
                   resolved,
                   dns_cache: dict) -> dns.message.Message:
    """
    This function uses a recursive resolver to find the relevant answer to the
    query.

    TODO: replace this implementation with one which asks the root servers
    and recurses to find the proper answer.
    """
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
    """
    This function uses a recursive resolver to find the relevant answer to the
    query.

    TODO: replace this implementation with one which asks the root servers
    and recurses to find the proper answer.
    """

    # logging.debug("---------Start Lookup-------\n")
    i = 0
    resolved = False
    while i < len(ROOT_SERVERS):

        # logging.debug("--------Check target in cache--------\n")
        ip_from_cache = ""
        find_name = str(target_name)
        next_dot = str(target_name).find('.')

        while not ip_from_cache and next_dot > -1:
            ip_from_cache = dns_cache.get(find_name)
            find_name = str(find_name)[next_dot+1:]
            next_dot = find_name.find('.')

        # logging.debug("--------If target not in cache check with root server--------\n")
        if ip_from_cache:
            ip_ = ip_from_cache
            logging.debug("--------Found target in cache--------\n")

        else:
            ip_ = ROOT_SERVERS[i]

        try:
            response, resolved = lookup_recurse(target_name, qtype, ip_, resolved, dns_cache)

            if response.answer:
                answer_type = response.answer[0].rdtype
                # logging.debug("--------If CNAME found in answer--------\n")
                if qtype != dns.rdatatype.CNAME  and answer_type == dns.rdatatype.CNAME:
                    target_name = dns.name.from_text(str(response.answer[0][0]))
                    resolved = False
                    logging.debug("--------- look up cname ----------- %s \n %s", target_name, response.answer[0])
                    response = lookup(target_name, qtype, dns_cache)
                return response

            elif response.authority and response.authority[0].rdtype == dns.rdatatype.SOA:
                # logging.debug("---------Got SOA authority-------")
                break
            else:
                i += 1

        except Timeout:
            # logging.debug("Timeout")
            i += 1
        except DNSException:
            # logging.debug("DNSException")
            i += 1
    return response

def update_cache(response: dns.message.Message, dns_cache):
    """
    Update cache with intermediate results
    """
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
    """
    Recursively lookup additional
    """
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
    """
    Recursively lookup authority
    """
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
    """
    take the results of a `lookup` and print them to the screen like the host
    program would.
    """
    print("print_results")
    for rtype, fmt_str in FORMATS:
        for result in results.get(rtype, []):
            print(fmt_str.format(**result))


def main():
    """
    if run from the command line, take args and call
    printresults(lookup(hostname))
    """
    # start_time = datetime.now()
    global count

    dns_cache = {}
    dns_cache['response_cache'] = {}
    '''
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("name", nargs="+",
                                 help="DNS name(s) to look up")
    argument_parser.add_argument("-v", "--verbose",
                                 help="increase output verbosity",
                                 action="store_true")
    program_args = argument_parser.parse_args()
    print(program_args)
    '''
    domain_names=['google.com']
    #for a_domain_name in program_args.name:
    for a_domain_name in domain_names:
        count = 0
        cache_result = dns_cache.get('response_cache').get(a_domain_name)
        if cache_result:
            # logging.debug("Got response in cache")
            print_results(cache_result)
        else:
            print_results(collect_results(a_domain_name, dns_cache))
        logging.debug("count %s", count)
    # end_time = datetime.now()
    # logging.debug("Time: %s", end_time - start_time)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()