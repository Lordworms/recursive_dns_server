import json
import pandas as pd
from urllib.parse import urlparse
import os
root_data_path='/Users/xiangyanxin/personal/GraduateCourse/Advanced_Networking/project/code/response_time_check/data'
#combine different csv file and generate the file
class DataGenerator:
    def __init__(self,data_paths):
        self.data_path=data_paths

    def change_type(byte):    
        if isinstance(byte,bytes):
            return str(byte,encoding="utf-8")  
        return json.JSONEncoder.default(byte)
    
    def transfer(self):
        saved_data=[]
        f=open(os.path.join(root_data_path,"raw_data"),"w")
        for path in self.data_path:
            data=pd.read_csv(path)
            links=data["url"]
            for url in links:
                sub_data={}
                form=urlparse(url)
                domain=form.netloc
                sub_data["domain_name"]=domain
                saved_data.append(sub_data)    
        
        raw_data=json.dumps(saved_data)
        f.write(raw_data)
        f.close()
        print("total data number is {}".format(len(saved_data)))