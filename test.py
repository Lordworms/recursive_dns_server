import readline
import pycurl
import pydig
from io import BytesIO
Record_LIM=1000
def getConnectTime():
    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, 'https://stackoverflow.com/')
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    body = buffer.getvalue()

    print('TOTAL_TIME: %f' % c.getinfo(c.TOTAL_TIME))
    print('CONNECT_TIME: %f' % c.getinfo(c.CONNECT_TIME))
    print('PRETRANSFER_TIME: %f' % c.getinfo(c.PRETRANSFER_TIME))
    print('STARTTRANSFER_TIME: %f' % c.getinfo(c.STARTTRANSFER_TIME))
    print('NAME_LOOK_UP_TIME:%f'%c.getinfo(c.NAMELOOKUP_TIME))
    c.close()
def getIp(str=None):
    resolver = pydig.Resolver(
     executable='/usr/bin/dig',     
     nameservers=[
         '8.8.8.8',
     ],
     additional_args=[
         '+time=10',
     ]
    )
    print(resolver.query("google.com","A"))

if __name__=='__main__':
    f=open('./domain.txt')
    data=[]
    for line in f.readlines():
        
