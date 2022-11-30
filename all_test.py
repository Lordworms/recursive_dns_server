import data_generator
from client_resolve import Local_Dns_Resolver,get_ip
from test_generator import Test_Generator
import json
import dns.resolver
if __name__=='__main__':
    data_path="/Users/xiangyanxin/personal/GraduateCourse/Advanced_Networking/project/code/response_time_check/data/raw_data"
    loader=Test_Generator(data_path)
    #loader.getEvaluate(data_path)
    #loader.getPerformanceEvaluate(data_path)
    #loader.plotData(data_path)
    #loader.getHopCount(data_path)
    #loader.plotMissRate()
    #loader.plotResolveTime()
    #loader.plotHopCount()
    #loader.getPingTime()
    loader.plotTTFB()