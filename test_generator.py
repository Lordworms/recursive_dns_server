import urllib.request as requests
import time
from urllib.parse import urlparse
import client_resolve as cr
from client_resolve import get_ip
import os
import pydig
import json
resolvers = {
    "Google": "8.8.8.8/resolve", 
    "Cloudflare": "1.1.1.1/dns-query", 
    "Quad9": "9.9.9.9:5053/dns-query"
}
LIM=1e-3
FAC=1e2
results_path="/Users/xiangyanxin/personal/GraduateCourse/Advanced_Networking/project/code/response_time_check/results"
class Test_Generator:
    def __init__(self,data_path):
        self.data_path=data_path
        self.LDR=cr.Local_Dns_Resolver()
        self.total_miss=0
    
    def query(self,domain,name_server):
        resolver = pydig.Resolver(
        executable='/usr/bin/dig',     
        nameservers=[
            name_server,
        ],
        additional_args=[
            '+time=10',
        ]
        )
        res=resolver.query(domain,"A")
        return res
    
    def local_resolve(self,domain_name):
        resolve_time=None
        start=time.time()
        try:
            ip=self.LDR.getIp(domain_name)
        except:
            ip=get_ip(domain_name)
            self.total_miss+=1
            self.LDR.dns_cache[domain_name]=ip
        stop=time.time()
        resolve_time=stop-start
        #print(ip)
        return resolve_time

    def public_resolve(self,server, site, req_type):
        resolve_time = None
        try:
            start = time.time()
            ip=self.query(site,server)
            stop = time.time()
            respTime = stop - start
            resolve_time = respTime
        except Exception as e:
            print (str(e))
        if server=="127.0.0.1":
            print("find ip:{} for domain:{}".format(ip,site))
        return resolve_time
    
    def getEvaluate(self,domain_path):
        results_file_name=os.path.join(results_path,"dns_resolve_time")
        inf=open(domain_path,"r")
        domains=json.load(inf)
        inf.close()
        evaluate=[]
        k=0
        for data in domains:
            k+=1
            res={}
            domain=data['domain_name']
            res["domain_name"]=domain
            #local_time=self.local_resolve(domain)
            local_time=self.public_resolve("127.0.0.1",domain,'A')
            google_time=self.public_resolve("8.8.8.8",domain,'A')
            cloudflare_time=self.public_resolve("1.1.1.1",domain,'A')
            #fac=google_time/local_time
            #if fac>=LIM and google_time>local_time:
                #local_time*=FAC
            res["local_time"]=str(local_time)
            res["google_dns_time"]=str(google_time)
            res["cloudflare_time"]=str(cloudflare_time)
            evaluate.append(res)
            if k==10:
                break
                print("test {}".format(k))
        data=json.dumps(evaluate)
        with open(results_file_name,"w") as f:
            f.write(data)
        f.close()
        print("total miss is {}/{}".format(self.total_miss,len(domains)))