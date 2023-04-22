import shutil
import uuid
from pathlib import Path
from fpdf import FPDF
from flask_restx import Resource, Namespace
from rebuild_chat import *

api= Namespace('rebuild_wchat')

@api.route('/run')
class Run(Resource):
    def get(self):
            #arg = request.args
            #test for iOS
            arg = ["-p","I","-u","Pippo","-f","ios_test.zip"]
            #test for android
            #arg = ["-p","A","-u","Pippo","-f","android_test.zip"]
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
                #sys.exit()
            

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
            hash=chat_manager().extract_chat(path)
            pdf.cell(200, 10, txt = "hash zip contente la chat estratta:"+str(hash),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')

            cleaned_data=[]

            #platform="android"
            #file_path = "chat_android.txt"


            #platform="ios"

            if(platform == "I"):
                file_path = "./chat/_chat.txt"
            else:
                file_path = "./chat/chat.txt"

            with open(file_path, mode='r', encoding="utf8") as f:
                data = f.readlines()


            if(platform == "I"):
                user = data[0].split(":")[2].split("]")[1][1:]
                cleaned_data=chat_manager().ios_chat(user, data)
            else:
                user="Pippo"  
                cleaned_data=chat_manager().android_chat(user, data)

            author=sentiment().sentiment_analysis(cleaned_data, pdf)

            for a in author:
                if a != user:
                    recived=a


            html().makeHTML(user,recived, cleaned_data)
            #sentiment_analysis(cleaned_data, pdf)
            html().dayHTML(user,recived,cleaned_data)


            pdf.output("report.pdf")
            id = str(uuid.uuid4())
            #create folder for sentiment analysis output files
            #move all files in the folder
            dir_path="report_sentiment_analysis_"+id
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            shutil.move("report.pdf", dir_path)
            shutil.move("fig1.png", dir_path)
            shutil.move("fig2.png", dir_path)
            shutil.move("chat", dir_path)
            shutil.move("day_by_day", dir_path)
            shutil.move("html", dir_path)
            gps_path="gps_info_"+id
            Path(gps_path).mkdir(parents=True, exist_ok=True)
            shutil.move("gps_list.json", gps_path)
            shutil.move("GPS_ONLY_COORDS.json", gps_path)
            shutil.move("gps_map.html", gps_path)
            shutil.move(gps_path, dir_path)
            shutil.move("url_list.json", dir_path)
            shutil.move("email_list.json", dir_path)
            shutil.move("whois_output.json", dir_path)
            shutil.make_archive(dir_path, 'zip',dir_path) 
            shutil.rmtree(dir_path)
            print("#### Task Completed ####")

