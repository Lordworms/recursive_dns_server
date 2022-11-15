from http import server
import readline
import pycurl
import pydig
import random
from io import BytesIO
from resolve import *
import time
import dns.resolver
Record_LIM=1000
def getCurl(url):
    url=url
    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL,url)
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    #print('TOTAL_TIME: %f' % c.getinfo(c.TOTAL_TIME))
    #print('CONNECT_TIME: %f' % c.getinfo(c.CONNECT_TIME))
    #print('PRETRANSFER_TIME: %f' % c.getinfo(c.PRETRANSFER_TIME))
    #print('STARTTRANSFER_TIME: %f' % c.getinfo(c.STARTTRANSFER_TIME))
    #print('NAME_LOOK_UP_TIME:%f'%c.getinfo(c.NAMELOOKUP_TIME))
    res=c.getinfo(c.NAMELOOKUP_TIME)
    c.close()
    return res
def getIpp(str=None):
    str='www.'+str
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

if __name__=='__main__':
    f=open('./topdomain.txt')
    my_resolver = dns.resolver.Resolver()
    my_resolver.nameservers = ['8.8.8.8']
    data=[]
    cnt=0
    LIM=10
    for line in f.readlines():
        cnt=cnt+1
        line=line.strip().split()
        line=line[0]
        data.append(line)
        if cnt==LIM:
            break
    # randomly launch 1000 request 
    max_iterate=1000
    greater=0
    for i in range(0,max_iterate):
        index=random.randint(0,LIM-1)
        print("url:{}\n".format(data[index]))
        start=time.time()
        client_recursive=getIp(data[index])
        end=time.time()
        client_time=end-start
        start=time.time()
        getIpp(data[index])
        end=time.time()
        server_time=end-start
        if float(client_time)<float(server_time):
            greater+=1
        print("client_time:{}\nserver_time:{}".format(end-start,server_time))
    print("client is faster:{}".format(greater))
    print("resolver is faster:{}".format(max_iterate-greater))