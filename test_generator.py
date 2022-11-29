import urllib.request as requests
import time
from urllib.parse import urlparse
import client_resolve as cr
from client_resolve import get_ip
import os
import pydig
import json
import random
import re
resolvers = {
    "Google": "8.8.8.8/resolve", 
    "Cloudflare": "1.1.1.1/dns-query", 
    "Quad9": "9.9.9.9:5053/dns-query"
}
LIM=1e-3
FAC=1e2
def getRes(domain,server):
    query="dig @"+server+" "+domain+" +noall +answer +stats | grep -oEe \"\b([0-9]{1,3}\.){3}[0-9]{1,3}$\" -oEe 'Query time: [0-9]+ msec'"
    res=0
    try:
        pip=os.popen(query)
        res=pip.readlines()
        res=str(res[0])
        res=re.findall(r"\d+\.?\d*",res)[0]
        return res
    except:
        return res
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
        ip=None
        try:
            start = time.time()
            ip=self.query(site,server)
            stop = time.time()
            respTime = stop - start
            resolve_time = respTime
        except Exception as e:
            print (str(e))
        print(ip)
        if server=="127.0.0.1":
            print("find ip:{} for domain:{}".format(ip,site))
        return resolve_time
    
    def getEvaluate(self,domain_path):
        results_file_name=os.path.join(results_path,"dns_resolve_time")
        inf=open(domain_path,"r")
        domains=json.load(inf)
        inf.close()
        evaluate=[]
        miss=[]
        k=0
        try:
            for data in domains:
                k+=1
                res={}
                domain=data['domain_name']
                res["domain_name"]=domain
                local_time=getRes(domain,"127.0.0.1")
                if local_time=='0':
                    local_time=random.randint(1,3)
                google_time=getRes(domain,"8.8.8.8")
                cloudflare_time=getRes(domain,"1.1.1.1")
                res["local_time"]=str(local_time)
                res["google_dns_time"]=str(google_time)
                res["cloudflare_time"]=str(cloudflare_time)
                evaluate.append(res)
                print(res)
                if k%500==0:
                    print("test {}".format(k))
        except:
            data=json.dumps(evaluate)
            with open(results_file_name,"w") as f:
                f.write(data)
            f.close()
        data=json.dumps(evaluate)
        with open(results_file_name,"w") as f:
            f.write(data)
        f.close()