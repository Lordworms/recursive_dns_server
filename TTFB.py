import requests
import time
import pydig
class HostHeaderSSLAdapter(requests.adapters.HTTPAdapter):
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

    def send(self, request, **kwargs):
        from urllib.parse import urlparse

        connection_pool_kwargs = self.poolmanager.connection_pool_kw

        result = urlparse(request.url)
        resolved_ip = self.query(result.netloc,self.name_server)[0]

        if result.scheme == 'https' and resolved_ip:
            request.url = request.url.replace(
                'https://' + result.hostname,
                'https://' + resolved_ip,
            )
            connection_pool_kwargs['server_hostname'] = result.hostname  # SNI
            connection_pool_kwargs['assert_hostname'] = result.hostname

            # overwrite the host header
            request.headers['Host'] = result.hostname
        else:
            # theses headers from a previous request may have been left
            connection_pool_kwargs.pop('server_hostname', None)
            connection_pool_kwargs.pop('assert_hostname', None)

        return super(HostHeaderSSLAdapter, self).send(request, **kwargs)


url = 'https://www.bilibili.com'

session = requests.Session()
session.mount('https://', HostHeaderSSLAdapter())
start=time.time()
r = session.get(url)
end=time.time()
print("time:{}".format(end-start))
print(r.text)
#r = session.get(url)
#print(r.headers)