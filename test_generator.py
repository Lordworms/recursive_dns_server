import urllib.request as requests
import time
from urllib.parse import urlparse
import client_resolve as cr
from client_resolve import get_ip
import os
import pydig
import numpy as np
import json
import random
import matplotlib.pyplot as plt
import re
import pexpect
import requests
import matplotlib.ticker as mticker  
import statsmodels.api as sa
from pythonping import ping
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
def getCurlRes(domain,ip=None):
    if ip is not None:
        query="curl -w \"@curl-format.txt\" -o /dev/null"
    else:
        query=query="curl -w \"@curl-format.txt\" -o /dev/null"+domain
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
    def request(self,domain):
        pass
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
    
    def getResolveTime(self,domain_path):
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
    def hopCount(self,domain,server):
        ip=self.query(domain,server)[0]
        query_str="traceroute "+ip
        res=pexpect.spawn(query_str)
        ans=0
        while True:
            line=res.readline()
            if not line:break
            string=line.decode("utf-8") 
            string=string.strip().split()
            if string[0].isdigit():
                ans=int(string[0])
            if ans>=25:
                break
            print('ans is now {}'.format(ans))
        return ans
    def getHopCount(self,domain_path):
        inf=open(domain_path,"r")
        domains=json.load(inf)
        uni_domains=[]
        for domain in domains:
            if domain['domain_name'] not in uni_domains:
                uni_domains.append(domain['domain_name'])
        eval=[]
        results_file_name=os.path.join(results_path,"hop_count")
        for domain in uni_domains:
            domain_eval={}
            try:
                domain_eval['domain_name']=domain
                print("domain {} for local ".format(domain))
                domain_eval['local_hop_count']=self.hopCount(domain,'127.0.0.1')
                print("domain {} for google ".format(domain))
                domain_eval['google_hop_count']=self.hopCount(domain,'8.8.8.8')
                print("domain {} for cloudflare ".format(domain))
                domain_eval['cloudflare_hop_count']=self.hopCount(domain,'1.1.1.1')
                eval.append(domain_eval)
            except:
                print("failed:",domain)
                data=json.dumps(eval)
                with open(results_file_name,"w") as f:
                    f.write(data)
                f.close()
        data=json.dumps(eval)
        with open(results_file_name,"w") as f:
            f.write(data)
        f.close()  

    def getPingTime(self):
        domain_path='/Users/xiangyanxin/personal/GraduateCourse/Advanced_Networking/project/code/response_time_check/data/raw_data'
        inf=open(domain_path,"r")
        domains=json.load(inf)
        uni_domains=[]
        for domain in domains:
            if domain['domain_name'] not in uni_domains:
                uni_domains.append(domain['domain_name'])
        results_file_name=os.path.join(results_path,"ping_time")
        def pingTime(host):
            ping_result = ping(target=host, count=10, timeout=2)
            return ping_result.rtt_avg_ms
        eval=[]
        for domain in uni_domains:
            try:
                domain_eval={}
                print("ping time for {}".format(domain))
                domain_eval['domain']=domain
                localIp=self.query(domain,'127.0.0.1')[0]
                googleIp=self.query(domain,'8.8.8.8')[0]
                cloudIp=self.query(domain,'1.1.1.1')[0]
                domain_eval['local_ping_time']=pingTime(localIp)
                domain_eval['google_ping_time']=pingTime(googleIp)
                domain_eval['cloudflare_ping_time']=pingTime(cloudIp)
                print("results!:",domain_eval)
                eval.append(domain_eval)
            except:
                print("failed for domain {}".format(domain))
                data=json.dumps(eval)
                with open(results_file_name,"w") as f:
                    f.write(data)
                f.close()
        data=json.dumps(eval)
        with open(results_file_name,"w") as f:
            f.write(data)
        f.close()         

    def getFFTB():
        pass
    def plotData(self,domain_path):
        inf=open(domain_path,"r")
        domains=json.load(inf)
        table={}
        for domain in domains:
            if domain["domain_name"] not in table:
                table[domain['domain_name']]=0
            table[domain['domain_name']]+=1
        new_table=sorted(table.items(),key=lambda x:x[1],reverse=True)
        total_file_name=os.path.join(results_path,"top_5_domain.png")
        names=['google','github','gmail','leetcode','canvas']
        for i in range(5):
            plt.bar(names[i],new_table[i][1])
        plt.title("Top 5 domains in our data")
        plt.legend()
        plt.savefig(total_file_name)
        plt.cla()
        data=[]
        for i in range(5):
            data.append(float(new_table[i][1]))
        data.append(float(len(domains)-sum(data)))
        total_file_name=os.path.join(results_path,"data_composition.png")
        names=['google','github','gmail','leetcode','canvas','others']
        plt.pie(data,labels=names,autopct='%1.2f%%')
        plt.title("data composition")
        plt.savefig(total_file_name)

    def plotMissRate(self):
        path="/Users/xiangyanxin/personal/GraduateCourse/Advanced_Networking/project/code/response_time_check/results/miss_rate"
        f=open(path,'r')
        data=json.load(f)
        t=np.linspace(0,len(data),len(data))
        plt.plot(t,data)
        plt.title("cache miss rate")
        plt.savefig(os.path.join(results_path,"miss_rate.png"))
    
    def plotHopCount(self):
        path="/Users/xiangyanxin/personal/GraduateCourse/Advanced_Networking/project/code/response_time_check/results/hop_count"
        f=open(path,'r')
        data=json.load(f)
        f.close()
        local=[]
        google=[]
        cloudflare=[]
        total=len(data)
        gt=0
        for eval in data:
            local.append(int(eval['local_hop_count']))
            google.append(int(eval['google_hop_count']))
            cloudflare.append(int(eval['cloudflare_hop_count']))
            lhc=int(eval['local_hop_count'])
            ghc=int(eval['google_hop_count'])
            chc=int(eval['cloudflare_hop_count'])
            if lhc<=ghc or lhc<=chc:
                gt+=1
        ecdf1=sa.distributions.ECDF(local)
        ecdf2=sa.distributions.ECDF(google)
        ecdf3=sa.distributions.ECDF(cloudflare)
        x=np.linspace(min(local),max(local))
        y1=ecdf1(x)
        y2=ecdf2(x)
        y3=ecdf3(x)
        plt.step(x,y1,color='red',label='local')
        plt.step(x,y2,color='blue',label='google_dns')
        plt.step(x,y3,color='green',label='cloudflare')
        plt.legend()
        plt.savefig(os.path.join(results_path,"hop_count_res.png"))
        print("greater rate if {}".format(float(gt)/float(len(data))))
    def plotPingTime(self):
        path="/Users/xiangyanxin/personal/GraduateCourse/Advanced_Networking/project/code/response_time_check/results/ping_time"
        f=open(path,'r')
        data=json.load(f)
        f.close()
        local=[]
        google=[]
        cloudflare=[]
        for domain in data:
            lt=float(domain['local_ping_time'])
            gt=float(domain['google_ping_time'])
            ft=float(domain['cloudflare_ping_time'])
            local.append(lt)
            google.append(gt)
            cloudflare.append(ft)
        ecdf1=sa.distributions.ECDF(local)
        ecdf2=sa.distributions.ECDF(google)
        ecdf3=sa.distributions.ECDF(cloudflare)
        x=np.linspace(min(local),max(local))
        y1=ecdf1(x)
        y2=ecdf2(x)
        y3=ecdf3(x)
        #plt.gca().xaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f ms'))
        plt.step(x,y1,color='red',label='local')
        plt.step(x,y2,color='blue',label='google_dns')
        plt.step(x,y3,color='green',label='cloudflare')
        plt.legend()
        #plt.show()
        plt.savefig(os.path.join(results_path,"TTFB.png"))

    def plotResolveTime(self):
         path="/Users/xiangyanxin/personal/GraduateCourse/Advanced_Networking/project/code/response_time_check/results/dns_resolve_time"
         f=open(path,'r')
         data=json.load(f)
         f.close()
         local=[]
         google=[]
         cloudflare=[]
         total=len(data)
         less_than=0
         less_than_50=0
         greater_than=0
         for eval in data:
            if eval['local_time']!='[]' and eval['cloudflare_time']!='[]' and eval['google_dns_time']!='[]':
                local.append(int(eval['local_time']))
                google.append(int(eval['google_dns_time']))
                cloudflare.append(int(eval['cloudflare_time']))
                lt=int(eval['local_time'])
                gt=int(eval['google_dns_time'])
                ct=int(eval['cloudflare_time'])
                if lt<=gt and lt<=ct:
                    greater_than+=1
                if lt>gt and lt>ct:
                    less_than+=1
                    if abs(gt-lt)<50:
                        less_than_50+=1
         ecdf1=sa.distributions.ECDF(local)
         ecdf2=sa.distributions.ECDF(google)
         ecdf3=sa.distributions.ECDF(cloudflare)
         x=np.linspace(min(local),1000)
         y1=ecdf1(x)
         y2=ecdf2(x)
         y3=ecdf3(x)
         plt.gca().xaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f ms'))
         plt.step(x,y1,color='red',label='local')
         plt.step(x,y2,color='blue',label='google_dns')
         plt.step(x,y3,color='green',label='cloudflare')
         plt.legend()
         plt.savefig(os.path.join(results_path,'resolve_time.png'))
         print("less than percent is {}".format(float(less_than)/float(total)))
         print("less than 50 percent is {}".format(float(less_than_50)/float(less_than)))
         print("greater than percent is {}".format(float(greater_than)/float(total)))
    def plotTTFB(self):
        path="/Users/xiangyanxin/personal/GraduateCourse/Advanced_Networking/project/code/response_time_check/results/ping_time"
        f=open(path,'r')
        data=json.load(f)
        f.close()
        local=[]
        google=[]
        cloudflare=[]
        k=0
        results_file_name=os.path.join(results_path,"TTFB")
        eval=[]
        for domain in data:
            try:
                evaluate={}
                k+=1
                print("test {} for domain {}".format(k,domain['domain']))
                flag=random.randint(1,4)
                if flag!=1:
                    getRes(domain['domain'],'127.0.0.1')
                lt=float(domain['local_ping_time'])+float(getRes(domain['domain'],'127.0.0.1'))
                gt=float(domain['google_ping_time'])+float(getRes(domain['domain'],'8.8.8.8'))
                ft=float(domain['cloudflare_ping_time'])+float(getRes(domain['domain'],'1.1.1.1'))
                print("time is {},{},{}".format(lt,gt,ft))
                local.append(lt)
                google.append(gt)
                cloudflare.append(ft)
                evaluate['local']=lt
                evaluate['google']=gt
                evaluate['cloudflare']=ft
                eval.append(evaluate)
            except:
                data=json.dumps(eval)
                with open(results_file_name,"w") as f:
                    f.write(data)
                f.close()
        data=json.dumps(eval)
        with open(results_file_name,"w") as f:
            f.write(data)
        f.close()
        ecdf1=sa.distributions.ECDF(local)
        ecdf2=sa.distributions.ECDF(google)
        ecdf3=sa.distributions.ECDF(cloudflare)
        x=np.linspace(min(local),max(local))
        y1=ecdf1(x)
        y2=ecdf2(x)
        y3=ecdf3(x)
        #plt.gca().xaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f ms'))
        plt.step(x,y1,color='red',label='local')
        plt.step(x,y2,color='blue',label='google_dns')
        plt.step(x,y3,color='green',label='cloudflare')
        plt.legend()
        #plt.show()
        plt.savefig(os.path.join(results_path,"TTFB.png"))

    def demo(self):
        ip0=self.query("google.com","8.8.8.8")
        print(ip0)
        ip0=self.query("google.com","1.1.1.1")
        print(ip0)
        ip0=self.query("google.com","127.0.0.1")
        print(ip0)