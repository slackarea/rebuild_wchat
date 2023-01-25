# %%
import os
import datetime
from jinja2 import Template, Environment, FileSystemLoader

# %%
file_path = "chat.txt"
with open(file_path, mode='r', encoding="utf8") as f:
    data = f.readlines()

# %%
utente = input("Inserisci il received: ")

# %%
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
        message = message.replace(" \u200e", "" ).replace("\n", "")
        position = 'received'
        if sender[1:] == utente:
            position = 'sent'
        cleaned_data.append([position, date, time[1:], sender[1:], message])
        lista.append(date)
    # else, assumption -> new line. Append new line to previous 'message'
    else:
        new = cleaned_data[-1][-1] + " " + line
        cleaned_data[-1][-1] = new

# %%
f.close()

# %%
file_html_path = "index_wa.html"
if os.path.exists(file_html_path):
    os.remove(file_html_path) 
i = open(file_html_path, mode='x', encoding="utf8")


# %%
file_loader = FileSystemLoader("templates")
env = Environment(loader=file_loader)
inizio=env.get_template("inizio.txt")
fine=env.get_template("fine.txt")
data_template=env.get_template("data_template.txt")
message_template=env.get_template("message_template.txt")
media_template=env.get_template("media_template.txt")

# %%
i.write(inizio.render())

# %%
data_messaggio = ""

for m in cleaned_data:
    mess = m[4]
    
    if m[1] != data_messaggio:
        data_messaggio = m[1]
        i.write((data_template.render(data=m[1])))
    
    #posizione conterrà l'inizio della stringa "<allegato:"
    posizione = m[4].find("<allegato:")
    
    if posizione>-1:
        if(m[4].find(".jpg")>-1):
            filename = m[4][posizione+11:len(m[4])-1]
            with Image.open(filename) as image:
                width, height = image.size
            print(str(width) + " " + str(height))
   
            mess =  "<a href=" + m[4][posizione+11:len(m[4])-1]+ " data-lightbox=" + m[4][posizione+11:len(m[4])-1]+ "  >" + "<img src=\""+m[4][posizione+11:len(m[4])-1]+"\">" +"</a>"
   
        elif(m[4].find(".opus") >-1 or m[4].find(".mp3") >-1):
            mess = "<audio controls><source src="+ m[4][posizione+11:len(m[4])-1] +  " type='audio/ogg'>Your browser does not support the audio element.</audio>"
        else:
            mess = "<a href=\""+m[4][posizione+11:len(m[4])-1]+"\">"+m[4][posizione+11:len(m[4])-1]+"</a>"
        i.write(media_template.render(tipo=m[0], messaggio=mess,ora=m[2][0:5]))
        
    else:
        i.write(message_template.render(tipo=m[0], messaggio=mess,ora=m[2][0:5]))

# %%
i.write(fine.render())
i.close()


