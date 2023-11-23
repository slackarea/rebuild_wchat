import shutil
import uuid
from pathlib import Path
from fpdf import FPDF
from flask_restx import Resource, Namespace
from rebuild_chat import *
from flask import request, send_file, render_template
import glob 
import os
from vcf import *


api= Namespace('rebuild_wchat')

#route for run the script
@api.route('/run/<platform>&<user>&<file_path>', methods=['POST'])
class Run(Resource):
    def post(self, platform, user, file_path):
            
            if 'file' not in request.files:
                return {'message': 'No file uploaded'}, 400

            uploaded_file = request.files['file']

            if not uploaded_file.filename:
                return {'message': 'No file uploaded'}, 400

            # Save the uploaded file with a UUID
            id_up_file= str(uuid.uuid4())
            file_path = id_up_file + "_" + uploaded_file.filename
            uploaded_file.save(file_path)


            pdf = FPDF()
            pdf.add_page()
            pdf.add_font('Arial', '', 'arial.ttf', uni=True)
            pdf.set_font("Arial", size = 15)

            hash=chat_manager().extract_chat(str(file_path))
           
            #write hash in pdf
            pdf.cell(200, 10, txt = "hash zip contente la chat estratta:"+str(hash),new_x=XPos.LMARGIN, new_y=YPos.NEXT, align = 'L')

            cleaned_data=[]


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
                #user="Pippo"  
                cleaned_data=chat_manager().android_chat(user, data)

            author=sentiment().sentiment_analysis(cleaned_data, pdf)
            #recived=""
            for a in author:
                 if a != user:
                     recived=a

            
           
            html().makeHTML(user,recived, cleaned_data)
            #sentiment_analysis(cleaned_data, pdf)
            html().dayHTML(user,recived,cleaned_data)

            vcf.get_vcf_files(self, uploaded_file.filename)
            vcf.get_vcf_data(self, uploaded_file.filename)
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
            shutil.move("vcf_data.json", dir_path)
            shutil.move("vcf_files.json", dir_path)
            if os.path.exists("GPS_ONLY_COORDS.json"):
                gps_path="gps_info_"+id
                Path(gps_path).mkdir(parents=True, exist_ok=True)
                shutil.move("gps_list.json", gps_path)
                shutil.move("GPS_ONLY_COORDS.json", gps_path)
                shutil.move("gps_map.html", gps_path)
                shutil.move(gps_path, dir_path)
            link_path="link_info_"+id
            Path(link_path).mkdir(parents=True, exist_ok=True)
            shutil.move("url_list.json", link_path)
            shutil.move("email_list.json", link_path)
            shutil.move("social_list.json", link_path)
            shutil.move("videocall_list.json", link_path)
            shutil.move("shopping_list.json", link_path)
            shutil.move("whois_output.json", dir_path)
            shutil.move(link_path, dir_path)
            shutil.make_archive(dir_path, 'zip',dir_path) 
            shutil.rmtree(dir_path)
            os.remove(id_up_file + "_" + uploaded_file.filename)
            print("#### Task Completed ####")

#route for download the zip file
@api.route('/download')
class Download(Resource):
    def get(self):
        #download last zip file
        list_of_files = glob.glob('./*.zip') 
        latest_file = max(list_of_files, key=os.path.getctime)
        return send_file(latest_file, as_attachment=True)

 
        
