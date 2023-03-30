import json
import whois


class url_analyzer:
      
    def url_whois():
        output= []
        with open('url_list.json', 'r') as f:
            data = json.load(f)
            for url in data:
                #print(url)
                w = whois.whois(url)
                output.append(w)
                #print(w)
        with open('whois_output.json', 'w') as f:
            f.write(json.dumps(output,default=str, indent=4))
        return("file whois_output.json creato")

        
