import os
import json
import zipfile

#operazioni su file vcf (virtual contact file)
extension='.vcf'
class vcf:
    def get_vcf_files(self, path):
             with zipfile.ZipFile(path, 'r') as zip_file:
                 zip_file.extractall('./extracted')
             vcf_files = []
             path_ext = os.listdir('./extracted')
             for file in path_ext:
                 if file.endswith(extension):
                     vcf_files.append(file)
             with open ('vcf_files.json','w', encoding='utf8') as f:
                 f.write(json.dumps(vcf_files, indent=4, ensure_ascii=False))

    def get_vcf_data(self, path):
        with open('vcf_files.json','r') as f:
            vcf_files = json.loads(f.read())
        vcf_data = []
        for file in vcf_files:
            with open('./extracted/'+file, 'r') as f:
                vcf_data.append(f.read())
        with open('vcf_data.json','w', encoding='utf8') as f:
            f.write(json.dumps(vcf_data, indent=4, ensure_ascii=False))
        




