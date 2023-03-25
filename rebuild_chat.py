import os
import sys
import datetime
from jinja2 import Template, Environment, FileSystemLoader
from fpdf import FPDF
import shutil
import zipfile
import hashlib
import regex
import pandas as pd
import numpy as np
import emoji
from collections import Counter
import plotly.express as px
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import matplotlib.pyplot as plt


#questa funzione servirà per estrarre il file zip contente la chat e ritorno l'hash del file zip
def extract_chat(name):

    if os.path.exists("./chat"):
        shutil.rmtree("./chat")


    md5_hash = hashlib.md5()
    with open(name,"rb") as f:
    # Read and update hash in chunks of 4K
        for byte_block in iter(lambda: f.read(4096),b""):
            md5_hash.update(byte_block)
    shutil.unpack_archive(name, "./chat")

    return md5_hash.hexdigest()    




def ios_chat(user,data):
         
    dataset = data [1:]
    cleaned_data = []
    lista = []

    for line in dataset:
        # Check, whether it is a new line or not
        # If the following characters are in the line -> assumption it is NOT a new line
        if '/' in line and ':' in line and ',' in line and '[' in line:
            # grab the info and cut it out
            date = line.split("[")[1].split(",")[0]
            line2 = line[len(date):]
            time = line2.split(",")[1].split("]")[0]
            line3 = line2[len(time):]
            sender = line3.split("]")[1].split(":")[0]
            line4 = line3[len(sender):]
            message = line4[5:-1]
            message = message.replace(" \u200e", "" ).replace("\n", "<br>")
            position = 'received'
            if sender[1:] == user:
                position = 'sent'
            cleaned_data.append([position, date, time[1:], sender[1:], message])
            lista.append(date)
        # else, assumption -> new line. Append new line to previous 'message'
        else:
            new = cleaned_data[-1][-1] + "<br>" + line
            cleaned_data[-1][-1] = new

    return cleaned_data


def android_chat(user,data):
    
         
    dataset = data [1:]
    cleaned_data = []
    lista = []

    for line in dataset:
        # Check, whether it is a new line or not
        # If the following characters are in the line -> assumption it is NOT a new line
        if '/' in line and ':' in line and ',' in line and '-' in line:
            # grab the info and cut it out
            date = line.split(",")[0]            
            line2 = line[len(date)+1:]
            time = line2.split("-")[0][:-1]
            line3 = line2[len(time)+2:]
            sender = line3.split(":")[0]
            line4 = line3[len(sender)+2:]
            message = line4
            message = message.replace(" \u200e", "" ).replace("\n", "")
            position = 'received'
        
            if sender[1:] == user:
                position = 'sent'
        
            cleaned_data.append([position, date, time[1:], sender[1:], message])
            lista.append(date)
        # else, assumption -> new line. Append new line to previous 'message'
        else:
            new = cleaned_data[-1][-1] + "<br>" + line
            cleaned_data[-1][-1] = new

    return cleaned_data






def makeHTML(user,recived, cleaned_data):
    
    folder="./html/"
    
    if os.path.exists(folder):
        shutil.rmtree(folder)

    os.mkdir(folder)
    shutil.copyfile("style.css","html/style.css")
    shutil.copytree("./libs","./html/libs")


    file_html_path = folder+"index_wa.html"
    
    if os.path.exists(file_html_path):
        os.remove(file_html_path) 
    
    i = open(file_html_path, mode='x', encoding="utf8")
    file_loader = FileSystemLoader("templates")
   
    env = Environment(loader=file_loader)
    start=env.get_template("start.txt")
    end=env.get_template("end.txt")
    day_template=env.get_template("day_template.txt")
    message_template=env.get_template("message_template.txt")
    media_template=env.get_template("media_template.txt")

    i.write(start.render(name=recived))

    message_date = ""
    p=""

    for m in cleaned_data:
        mess = m[4]

        if (m[0]=="sent"):
            p="end"
        else:
            p="start"

        
        if m[1] != message_date:
            message_date = m[1]
            i.write((day_template.render(day=m[1])))
        
        #posizione conterrà l'inizio della stringa "<allegato:"
        attacched=-1
        position_ios = m[4].find("<allegato:")
        position_android= m[4].find("(file allegato)")
        
        if position_ios >-1:
            filename=m[4][position_ios+11:len(m[4])-1]
            attacched=1
        elif position_android > -1:
                filename=m[4][0:position_android-1]
                attacched=1

        mediaPath="../chat/"

        if attacched>-1:
            if(m[4].find(".jpg")>-1):
                #filename = m[4][position+11:len(m[4])-1]
                mess =  "<a href=\"" + mediaPath+filename + "\" data-lightbox=\"" + mediaPath+filename + "\">" + "<img src=\""+ mediaPath+filename +"\">" +"</a>"
    
            elif(m[4].find(".opus") >-1 or m[4].find(".mp3") >-1):
                mess = "<audio controls><source src=\""+ mediaPath+filename +  "\" type='audio/ogg'>Your browser does not support the audio element.</audio>"
            else:
                mess = "<a href=\""+ mediaPath+filename +"\">"+ filename+"</a>"
            i.write(media_template.render(position=p,type=m[0], message=mess,time=m[2][0:5]))
            
        else:
            i.write(message_template.render(position=p,type=m[0], message=mess,time=m[2][0:5]))


              

    i.write(end.render())
    i.close()


#questa funziona crea un indice con il collegamento a tutti i messaggi di un dato giorno
def dayHTML(user,recived,cleaned_data):    
    dayPath="./day_by_day/"
    
    #utilizzato per capire quando chiudere la chat del giorno
    message_date = ""
    i=None

    file_loader = FileSystemLoader("templates")
    env = Environment(loader=file_loader)
    start=env.get_template("start.txt")
    end=env.get_template("end.txt")
    day_template=env.get_template("day_template.txt")
    message_template=env.get_template("message_template.txt")
    media_template=env.get_template("media_template.txt")

    if os.path.exists(dayPath):
        shutil.rmtree(dayPath)

    os.mkdir(dayPath)
    shutil.copyfile("style.css","day_by_day/style.css")
    shutil.copytree("./libs","./day_by_day/libs")

    indexHTML = open(dayPath+"index.html",mode='x', encoding="utf8")
    indexHTML.write("<HTML><HEAD> Index Chat<br></HEAD> <BODY>")

    message_date = cleaned_data[0][1]
    
    i = open(dayPath+str(message_date).replace("/","-")+".html", mode='x', encoding="utf8")
    indexHTML.write("<a href=\""+str(message_date).replace("/","-")+".html\">"+message_date+"</a><br>")
    i.write(start.render(name=recived))
    i.write((day_template.render(day=message_date)))

        
    for m in cleaned_data:
        mess = m[4]

        if (m[0]=="sent"):
            p="end"
        else:
            p="start"

        
        if m[1] != message_date:
            message_date = m[1]
            d=str(m[1]).replace("/","-")
            i.write(end.render())
            i.close()
            i = open(dayPath+d+".html", mode='x', encoding="utf8")
            indexHTML.write("<a href=\""+d+".html"+"\">"+m[1]+"</a><br>")
            i.write(start.render(name=user))
            i.write((day_template.render(day=m[1])))

    
        #posizione conterrà l'inizio della stringa "<allegato:"
        attacched=-1
        position_ios = m[4].find("<allegato:")
        position_android= m[4].find("(file allegato)")
        
        if position_ios >-1:
            filename=m[4][position_ios+11:len(m[4])-1]
            attacched=1
        elif position_android > -1:
                filename=m[4][0:position_android-1]
                attacched=1

        mediaPath="../chat/"

        if attacched>-1:
            if(m[4].find(".jpg")>-1):
                #filename = m[4][position+11:len(m[4])-1]
                mess =  "<a href=" + mediaPath+filename + " data-lightbox=" + mediaPath+filename + "  >" + "<img src=\""+ mediaPath+filename +"\">" +"</a>"
    
            elif(m[4].find(".opus") >-1 or m[4].find(".mp3") >-1):
                mess = "<audio controls><source src=\""+ mediaPath+filename +  "\" type='audio/ogg'>Your browser does not support the audio element.</audio>"
            else:
                mess = "<a href=\""+ mediaPath+filename +"\">"+ filename+"</a>"
            i.write(media_template.render(position=p,type=m[0], message=mess,time=m[2][0:5]))
            
        else:
            i.write(message_template.render(position=p,type=m[0], message=mess,time=m[2][0:5]))


              

    i.write(end.render())
    i.close()
    indexHTML.write("</BODY></HTML>")
    indexHTML.close()




def sentiment_analysis(cleaned_data,file_report):
    df = pd.DataFrame(cleaned_data, columns=["Type","Date", 'Time', 'Author', 'Message'])
    df['Date'] = pd.to_datetime(df['Date'])
    file_report.cell(200, 10, txt = "Autori dei messaggi scambiati: "+str(df.Author.unique()),ln = 1, align = 'L')
    file_report.cell(200, 10, txt = "Numero totale di messaggi "+str(df.shape[0]),ln = 1, align = 'L')  
    file_report.cell(200,10, txt="Numero media scambiati "+str(df[df["Message"].str.contains('<allegato: ')].shape[0]),ln = 1, align = 'L')


    def split_count(text):
        emoji_list = []
        data = regex.findall(r'\X',text)
        for word in data:
            if any(char in emoji.EMOJI_DATA for char in word):
                emoji_list.append(word)
        return emoji_list
    df['emoji'] = df["Message"].apply(split_count)
    emojis = sum(df['emoji'].str.len())
    
    URLPATTERN = r'(https?://\S+)'
    df['urlcount'] = df.Message.apply(lambda x: regex.findall(URLPATTERN, x)).str.len()
    links = np.sum(df.urlcount)
    
    file_report.cell(200,10, txt="Numero emojis "+str(emojis),ln = 1, align = 'L')
    file_report.cell(200,10, txt="Numero link scambiati "+str(links),ln = 1, align = 'L')

    
   
    media_messages_df = df[df["Message"].str.contains('<allegato: ')]
    messages_df = df.drop(media_messages_df.index)
    messages_df['Letter_Count'] = messages_df['Message'].apply(lambda s : len(s))
    messages_df['Word_Count'] = messages_df['Message'].apply(lambda s : len(s.split(' ')))
    messages_df["MessageCount"]=1

    total_emojis_list = list(set([a for b in messages_df.emoji for a in b]))
    total_emojis = len(total_emojis_list)

    total_emojis_list = list([a for b in messages_df.emoji for a in b])
    emoji_dict = dict(Counter(total_emojis_list))
    emoji_dict = sorted(emoji_dict.items(), key=lambda x: x[1], reverse=True)
    
    #for i in emoji_dict:
    #    print(i)
    
    l = df.Author.unique()
    for i in range(len(l)):
       # Filtering out messages of particular user
        req_df= messages_df[messages_df["Author"] == l[i]]
        # req_df will contain messages of only one particular user
        file_report.cell(200,10, txt=(f' - Stats of {l[i]} -'),ln = 1, align = 'L')
        # shape will print number of rows which indirectly means the number of messages
        file_report.cell(200,10, txt=(f'Messages Sent {req_df.shape[0]}'),ln = 1, align = 'L')
        #Word_Count contains of total words in one message. Sum of all words/ Total Messages will yield words per message
        words_per_message = (np.sum(req_df['Word_Count']))/req_df.shape[0]
        file_report.cell(200,10, txt=(f'Average Words per message {words_per_message}'),ln = 1, align = 'L')
        #media conists of media messages
        media = media_messages_df[media_messages_df['Author'] == l[i]].shape[0]
        file_report.cell(200,10, txt=(f'Media Messages Sent {media}'),ln = 1, align = 'L')
        # emojis conists of total emojis
        emojis = sum(req_df['emoji'].str.len())
        file_report.cell(200,10, txt=(f'Emojis Sent {emojis}'),ln = 1, align = 'L')
        #links consist of total links
        links = sum(req_df["urlcount"])   
        file_report.cell(200,10, txt=(f'Links Sent {links}'),ln = 1, align = 'L')

    file_report.add_page()
    emoji_df = pd.DataFrame(emoji_dict, columns=['emoji', 'count'])
    fig = px.pie(emoji_df, values='count', names='emoji')
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.write_image("fig1.png")
    file_report.cell(200,10, txt="  ",ln = 1, align = 'L')    
    file_report.cell(200,10, txt="Percentuale emoji utilizzate",ln = 1, align = 'L')
    file_report.image("fig1.png",w=180,h=100)
    
   
    for i in range(len(l)):
        dummy_df = messages_df[messages_df['Author'] == l[i]]
        text = " ".join(review for review in dummy_df.Message)
        stopwords = set(STOPWORDS)
        #Generate a word cloud image
        wordcloud = WordCloud(stopwords=stopwords, background_color="white").generate(text)
        wordcloud.to_file("fig2.png")

    file_report.cell(200,10, txt="  ",ln = 1, align = 'L')    
    file_report.cell(200,10, txt="Cloud Word",ln = 1, align = 'L')
    file_report.image("fig2.png",w=180,h=100)

    return l

#main
def main(arg):
    
    user=""
    recived=""
    platform=""
    path=""

    if ("-u" and "-f" and "-p") not in arg or len(arg)<7:
        print("#####################################################################")
        print(" ")
        print("Usage: python rebuild_chat.py -p PLATFORM -u CHAT_OWNER -f FILE.ZIP")
        print("")
        print("!! Important !! ")
        print("PLATFORM value are I for Ios and A for Android")
        print("The file ZIP must contanined a folder with chat txt file and media. See test as example\n")
        print("######################################################################")
        sys.exit()
    

    for i in range(len(arg)):
     
        if arg[i] == '-p':
            platform = arg[i+1]
        
        elif arg[i] == "-u":
            user = arg[i+1]
        
        elif arg[i] == "-f":
            path = arg[i+1]

    print("Platform "+platform)
    print("Chat Owner "+user)
    print("File Zip path " + path)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size = 15)

    #hash=extract_chat("ios_test.zip")
    hash=extract_chat(path)
    pdf.cell(200, 10, txt = "hash zip contente la chat estratta:"+str(hash),ln = 1, align = 'L')

    cleaned_data=[]

    #platform="android"
    #file_path = "chat_android.txt"


    #platform="ios"

    file_path = "./chat/"+os.listdir("./chat")[0]+"/chat.txt"

    with open(file_path, mode='r', encoding="utf8") as f:
        data = f.readlines()


    if(platform == "I"):
        user = data[0].split(":")[2].split("]")[1][1:]
        cleaned_data=ios_chat(user, data)
    else:
        user="Pippo"  
        cleaned_data=android_chat(user, data)

    author=sentiment_analysis(cleaned_data, pdf)

    for a in author:
        if a != user:
            recived=a


    makeHTML(user,recived, cleaned_data)
    #sentiment_analysis(cleaned_data, pdf)
    dayHTML(user,recived,cleaned_data)

    pdf.output("report.pdf", "F")
    pdf.close()
    print("#### Task Completed ####")


if __name__ == "__main__":
    
    # Use only for test
    # main(["Python3 script_gi4mp.py", "-p", "A","-u","Pippo","-f","android_test.zip"])
    # main(["Python3 script_gi4mp.py", "-p", "I","-u","Jack","-f","ios_test.zip"])
    main(sys.argv)