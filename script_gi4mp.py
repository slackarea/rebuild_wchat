import os
import datetime
from jinja2 import Template, Environment, FileSystemLoader
from fpdf import FPDF
import shutil
import zipfile
import hashlib
import re as regex
import pandas as pd
import numpy as np
import emoji
from collections import Counter
import plotly.express as px

#import matplotlib.pyplot as plt
#from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator

#questa funzione servirà per estrarre il file zip contente la chat e ritorno l'hash del file zip
def extract_chat():
    md5_hash = hashlib.md5()
    with open("prova.zip","rb") as f:
    # Read and update hash in chunks of 4K
        for byte_block in iter(lambda: f.read(4096),b""):
            md5_hash.update(byte_block)
    shutil.unpack_archive("prova.zip", "provazip")

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
            if sender[1:] != user:
                position = 'sent'
            cleaned_data.append([position, date, time[1:], sender[1:], message])
            lista.append(date)
        # else, assumption -> new line. Append new line to previous 'message'
        else:
            new = cleaned_data[-1][-1] + " " + line
            cleaned_data[-1][-1] = new

    return cleaned_data


def android_chat(user,data):
    print("android")




def makeHTML(user,cleaned_data):
    file_html_path = "index_wa.html"
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

    i.write(start.render(name=user))

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
        position = m[4].find("<allegato:")
        
        if position>-1:
            if(m[4].find(".jpg")>-1):
                filename = m[4][position+11:len(m[4])-1]
                mess =  "<a href=" + m[4][position+11:len(m[4])-1]+ " data-lightbox=" + m[4][position+11:len(m[4])-1]+ "  >" + "<img src=\""+m[4][position+11:len(m[4])-1]+"\">" +"</a>"
    
            elif(m[4].find(".opus") >-1 or m[4].find(".mp3") >-1):
                mess = "<audio controls><source src="+ m[4][position+11:len(m[4])-1] +  " type='audio/ogg'>Your browser does not support the audio element.</audio>"
            else:
                mess = "<a href=\""+m[4][position+11:len(m[4])-1]+"\">"+m[4][position+11:len(m[4])-1]+"</a>"
            i.write(media_template.render(position=p,type=m[0], message=mess,time=m[2][0:5]))
            
        else:
            i.write(message_template.render(position=p,type=m[0], message=mess,time=m[2][0:5]))

    i.write(end.render())
    i.close()


def sentiment_analysis(cleaned_data,file_report):
    df = pd.DataFrame(cleaned_data, columns=["Type","Date", 'Time', 'Author', 'Message'])
    df['Date'] = pd.to_datetime(df['Date'])
    file_report.cell(200, 10, txt = "Autori dei messaggi scambiati: "+str(df.Author.unique()),ln = 1, align = 'L')
    file_report.cell(200, 10, txt = "Numero totale di messaggi "+str(df.shape[0]),ln = 1, align = 'L')  
    file_report.cell(200,10, txt="Numero media scambiati "+str(df[df["Message"].str.contains('<allegato: ')].shape[0]),ln = 1, align = 'L')


    def split_count(text):
        emoji_list = []
        data = regex.findall(r'\\X',text)
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

    
    # questa parte è da rivedere con un dateset completo
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
    
    for i in emoji_dict:
        print(i)
    
    emoji_df = pd.DataFrame(emoji_dict, columns=['emoji', 'count'])
    fig = px.pie(emoji_df, values='count', names='emoji')
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.write_image("fig1.png")
    file_report.image("fig1.png")
    


#main

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size = 15)

hash=extract_chat()
pdf.cell(200, 10, txt = "hash zip contente la chat estratta:"+str(hash),ln = 1, align = 'L')

cleaned_data=[]

platform="ios"

file_path = "chat.txt"

with open(file_path, mode='r', encoding="utf8") as f:
    data = f.readlines()


user =data[0].split(":")[2].split("]")[1][1:]
    
if(platform=="ios"):
    cleaned_data=ios_chat(user, data)
else:
    cleaned_data=android_chat(user, data)

makeHTML(user,cleaned_data)
sentiment_analysis(cleaned_data, pdf)


pdf.output("report.pdf", "F")
pdf.close()


