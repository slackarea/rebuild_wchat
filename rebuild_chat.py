import os
from jinja2 import Template, Environment, FileSystemLoader
from fpdf import FPDF
import shutil
import hashlib
import regex
import pandas as pd
import numpy as np
import emoji
from collections import Counter
import plotly.express as px
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import matplotlib.pyplot as plt
from pathlib import Path
import json
from fpdf.enums import XPos, YPos
from gps_analyzer import *
from url_analyzer import *
from flask import Flask
from flask_restx import Api, Namespace, Resource


class chat_manager(Resource):
    #questa funzione servirà per estrarre il file zip contente la chat e ritorno l'hash del file zip
    def extract_chat(self, name):

        if os.path.exists("./chat"):
            shutil.rmtree("./chat")


        md5_hash = hashlib.md5()
        with open(name,"rb") as f:
        # Read and update hash in chunks of 4K
            for byte_block in iter(lambda: f.read(4096),b""):
                md5_hash.update(byte_block)
        shutil.unpack_archive(name, "./chat")

        return md5_hash.hexdigest()    


    def ios_chat(self, user,data):
            
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


    def android_chat(self, user,data):
            
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

class html(Resource):
    def makeHTML(self, user,recived, cleaned_data):
        
        folder="./html/"
        if os.path.exists(folder):
            shutil.rmtree(folder)

        os.mkdir(folder)
        shutil.copyfile("style.css","html/style.css")
        shutil.copytree("./libs","./html/libs")


        file_html_path = folder+"index_wa.html"
        
        if os.path.exists(file_html_path):
            os.remove(file_html_path) 
        if " " in user:
            first_name, last_name = user.split(" ", 1)
        else:
            first_name, last_name = user, ""

        i = open(file_html_path, mode='x', encoding="utf8")
        file_loader = FileSystemLoader("templates")
    
        env = Environment(loader=file_loader)
        start=env.get_template("start.txt")
        end=env.get_template("end.txt")
        day_template=env.get_template("day_template.txt")
        message_template=env.get_template("message_template.txt")
        media_template=env.get_template("media_template.txt")

        #i.write(start.render(name=user))
        i.write(start.render(first_name=first_name, last_name=last_name, full_name=user))


        message_date = ""
        p=""

        for m in cleaned_data:
            mess = m[4]
            if (m[0]=="sent"):
                p="start"
            else:
                p="end"
            
            if m[1] != message_date:
                message_date = m[1]
                i.write((day_template.render(day=m[1])))
            
            #posizione conterrà l'inizio della stringa "<allegato:"
            attacched=-1
            position_ios = m[4].find("<allegato:") or m[4].find("<attached:")
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
    def dayHTML(self, user,recived,cleaned_data):    
        dayPath="./day_by_day/"
        
        #utilizzato per capire quando chiudere la chat del giorno
        message_date = ""
        i=None
        if " " in user:
            first_name, last_name = user.split(" ", 1)
        else:
            first_name, last_name = user, ""
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
        i.write(start.render(first_name=first_name, last_name=last_name, full_name=user))
        i.write((day_template.render(day=message_date)))

            
        for m in cleaned_data:
            mess = m[4]

            if (m[0]=="sent"):
                p="start"
            else:
                p="end"
            
            if m[1] != message_date:
                message_date = m[1]
                d=str(m[1]).replace("/","-")
                i.write(end.render())
                i.close()
                i = open(dayPath+d+".html", mode='x', encoding="utf8")
                indexHTML.write("<a href=\""+d+".html"+"\">"+m[1]+"</a><br>")
                i.write(start.render(first_name=first_name, last_name=last_name, full_name=user))
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



class sentiment(Resource):
    def sentiment_analysis(self,cleaned_data,file_report):
    
            df = pd.DataFrame(cleaned_data, columns=["Type","Date", 'Time', 'Author', 'Message'])
            df['Date'] = pd.to_datetime(df['Date'])
            file_report.cell(200, 10, txt = "Autori dei messaggi scambiati: "+str(df.Author.unique()),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')
            file_report.cell(200, 10, txt = "Numero totale di messaggi "+str(df.shape[0]),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')  
            file_report.cell(200,10, txt="Numero media scambiati "+str(df[df["Message"].str.contains('<allegato: ')].shape[0]),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')


            def split_count(text):
                emoji_list = []
                data = regex.findall(r'\X',text)
                for word in data:
                    if any(char in emoji.EMOJI_DATA for char in word):
                        emoji_list.append(word)
                return emoji_list
            df['emoji'] = df["Message"].apply(split_count)
            emojis = sum(df['emoji'].str.len())
            file_report.cell(200,10, txt="Numero emojis "+str(emojis),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')

            #search for urls
            URL_PATTERN = r'(https?://\S+)'
            url_list = []
            data= regex.findall(URL_PATTERN, df.Message.to_string())
            for url in data:
                url_list.append(url)
            with open('url_list.json', "w") as f:
                    f.write(json.dumps(url_list, default=str, indent=4))
            df['urlcount'] = df.Message.apply(lambda x: regex.findall(URL_PATTERN, x)).str.len()
            links = np.sum(df.urlcount)
            file_report.cell(200,10, txt="Numero link scambiati "+str(links),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')
            url_analyzer.url_whois()

            #search for social network links
            SOCIAL_PATTERN = r'(?:(?:http|https):\/\/)?(?:www.)?(?:instagram.com|twitter.com|facebook.com|tiktok.com)\/([A-Za-z0-9-_]+)'
            social_list = []
            data= regex.findall(SOCIAL_PATTERN, df.Message.to_string())
            for social in data:
                social_list.append(social)
            with open('social_list.json', "w") as f:
                    f.write(json.dumps(social_list, default=str, indent=4))
            df['socialcount'] = df.Message.apply(lambda x: regex.findall(SOCIAL_PATTERN, x)).str.len()
            socials = np.sum(df.socialcount)
            file_report.cell(200,10, txt="Numero link social network scambiati "+str(socials),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')

            #search for videocall links
            VIDEOCALL_PATTERN = r'(?:(?:http|https):\/\/)?(?:www.)?(?:meet.google.com|zoom.us|teams.microsoft.com)\/([A-Za-z0-9-_]+)'
            videocall_list = []
            data= regex.findall(VIDEOCALL_PATTERN, df.Message.to_string())
            for videocall in data:
                videocall_list.append(videocall)
            with open('videocall_list.json', "w") as f:
                    f.write(json.dumps(videocall_list, default=str, indent=4))
            df['videocallcount'] = df.Message.apply(lambda x: regex.findall(VIDEOCALL_PATTERN, x)).str.len()
            videocalls = np.sum(df.videocallcount)
            file_report.cell(200,10, txt="Numero link videochiamate scambiati "+str(videocalls),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')

            SHOPPING_PATTERN = r'(?:(?:http|https):\/\/)?(?:www.)?(?:amazon.it|ebay.it|subito.it|kijiji.it|aliexpress.com)\/([A-Za-z0-9-_]+)'
            shopping_list = []
            data= regex.findall(SHOPPING_PATTERN, df.Message.to_string())
            for shopping in data:
                shopping_list.append(shopping)
            with open('shopping_list.json', "w") as f:
                    f.write(json.dumps(shopping_list, default=str, indent=4))
            df['shoppingcount'] = df.Message.apply(lambda x: regex.findall(SHOPPING_PATTERN, x)).str.len()
            shoppings = np.sum(df.shoppingcount)
            file_report.cell(200,10, txt="Numero link shopping scambiati "+str(shoppings),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')

            #search for italian fiscal codes
            CODICEFISCALEPATTERN = r'([A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z])'
            df['codicefiscalecount'] = df.Message.apply(lambda x: regex.findall(CODICEFISCALEPATTERN, x)).str.len()
            codicefiscale = np.sum(df.codicefiscalecount)
            file_report.cell(200,10, txt="Numero codici fiscali scambiati "+str(codicefiscale),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')


            #search for italian phone numbers
            NUMTELPATTERN = r'(\+39\d{9,10})'
            df['numtelcount'] = df.Message.apply(lambda x: regex.findall(NUMTELPATTERN, x)).str.len()
            numtels = np.sum(df.numtelcount)
            file_report.cell(200,10, txt="Numero numeri di telefono scambiati "+str(numtels),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')

            #search for emails
            EMAILPATTERN = r'(\S+@\S+)'
            email_list = []
            data= regex.findall(EMAILPATTERN, df.Message.to_string())
            for email in data:
                email_list.append(email)
            with open('email_list.json', "w") as f:
                    f.write(json.dumps(email_list, default=str, indent=4))
            df['emailcount'] = df.Message.apply(lambda x: regex.findall(EMAILPATTERN, x)).str.len()
            emails = np.sum(df.emailcount)
            file_report.cell(200,10, txt="Numero email scambiate "+str(emails),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')

            #search for gps positions
            GPSPATTERN= r'https?://maps\.google\.com/\?q=\d+\.\d+,\d+\.\d+'
            gps_list = []
            data= regex.findall(GPSPATTERN, df.Message.to_string())
            df['gpscount'] = df.Message.apply(lambda x: regex.findall(GPSPATTERN, x)).str.len()
            gps = np.sum(df.gpscount)
            file_report.cell(200,10, txt="Numero posizioni GPS scambiate "+str(gps),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')
            for el in data:
                gps_list.append(el)
            #print (gps_list)
            if(gps_list):
                with open('gps_list.json', "w") as f:
                        f.write(json.dumps(gps_list, default=str, indent=4))
                gps_analysis.gps_map()

            

            media_messages_df = df[df["Message"].str.contains('<allegato: ')]
            messages_df = df.drop(media_messages_df.index)
            messages_df['Letter_Count'] = messages_df['Message'].apply(lambda s : len(s))
            
            #count words without considering prepositions and conjunctions in Italian language
            with open('congiunzioni_preposizioni.json', "r") as f:
                data = json.load(f)
            cong= set(data['congiunzioni'])
            prep= set(data['preposizioni'])
            articles= set(data['articoli'])
            def word_count(text):
                words= text.split()
                c= 0
                for word in words:
                    if word not in cong and word not in prep and word not in articles:
                        c+=1
                return c
            messages_df['Word_Count'] = messages_df['Message'].apply(word_count)
            #messages_df['Word_Count'] = messages_df['Message'].apply(lambda s : len(s.split(' ')))
            messages_df["MessageCount"]=1

            total_emojis_list = list(set([a for b in messages_df.emoji for a in b]))
            total_emojis = len(total_emojis_list)

            total_emojis_list = list([a for b in messages_df.emoji for a in b])
            emoji_dict = dict(Counter(total_emojis_list))
            emoji_dict = sorted(emoji_dict.items(), key=lambda x: x[1], reverse=True)
            

            
            l = df.Author.unique()
            for i in range(len(l)):
            # Filtering out messages of particular user
                req_df= messages_df[messages_df["Author"] == l[i]]
                # req_df will contain messages of only one particular user
                file_report.cell(200,10, txt=(f' - Stats of {l[i]} -'),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')
                # shape will print number of rows which indirectly means the number of messages
                file_report.cell(200,10, txt=(f'Messages Sent {req_df.shape[0]}'),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')
                #Word_Count contains of total words in one message. Sum of all words/ Total Messages will yield words per message
                words_per_message = (np.sum(req_df['Word_Count']))/req_df.shape[0]
                file_report.cell(200,10, txt=(f'Average Words per message {words_per_message}'),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')
                #Word_Count contains of total words in one message.
                total_words = np.sum(req_df['Word_Count'])
                file_report.cell(200,10, txt=(f'Total Words Sent {total_words}'),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')
                #media conists of media messages
                media = media_messages_df[media_messages_df['Author'] == l[i]].shape[0]
                file_report.cell(200,10, txt=(f'Media Messages Sent {media}'),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')
                # emojis conists of total emojis
                emojis = sum(req_df['emoji'].str.len())
                file_report.cell(200,10, txt=(f'Emojis Sent {emojis}'),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')
                #links consist of total links
                links = sum(req_df["urlcount"])   
                file_report.cell(200,10, txt=(f'Links Sent {links}'),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')
                #numtels consist of total numtels
                numtels = sum(req_df["numtelcount"])
                file_report.cell(200,10, txt=(f'Numeri di telefono scambiati {numtels}'),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')
                #emails consist of total emails
                emails = sum(req_df["emailcount"])
                file_report.cell(200,10, txt=(f'Email scambiate {emails}'),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')
                #gps consist of total gps
                gps = sum(req_df["gpscount"])
                file_report.cell(200,10, txt=(f'Posizioni GPS scambiate {gps}'),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')

            file_report.add_page()
            emoji_df = pd.DataFrame(emoji_dict, columns=['emoji', 'count'])
            fig = px.pie(emoji_df, values='count', names='emoji')
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.write_image("fig1.png")
            file_report.cell(200,10, txt="  ",new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')    
            file_report.cell(200,10, txt="Percentuale emoji utilizzate",new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')
            file_report.image("fig1.png",w=180,h=100)
            
        
            for i in range(len(l)):
                dummy_df = messages_df[messages_df['Author'] == l[i]]
                text = " ".join(review for review in dummy_df.Message)
                stopwords = set(STOPWORDS)
                #Generate a word cloud image
                wordcloud = WordCloud(stopwords=stopwords, background_color="white").generate(text)
                wordcloud.to_file("fig2.png")

            file_report.cell(200,10, txt="  ",new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')    
            file_report.cell(200,10, txt="Cloud Word",new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')
            file_report.image("fig2.png",w=180,h=100)

        
            return l