import os
import shutil
from flask import Flask, redirect, render_template, request, url_for
from zipfile import ZipFile
from algorithm import plagiarism_checker
from codediff import codediff
from webscraping_module import webscraping

app = Flask(__name__)

session_data = {}
extracted = False

def fetch_data(filepath):
    plag_check_obj = plagiarism_checker(filepath)
    plag_check_obj.get_file_content()
    plag_check_obj.vectorize_content()
    plag_check_obj.compute_pairwise_cosine_similarity()
    plag_check_obj.compute_similarity_score()
    plag_check_obj.detect_top_programming_lang()
    plag_check_obj.compute_similarity_matrix()
    plag_check_obj.plot_top_50_words()
    plag_check_obj.generate_network_plot()
    plag_check_obj.generate_heatmap()

    session_data['filepath'] = filepath
    session_data['data'] = plag_check_obj.pairwise_similarity_score
    session_data['plag_highest'] = plag_check_obj.highest_plagiarism_score
    session_data['top_lang'] = plag_check_obj.toplang

def webscrape_data(assignment_aim,filepath):
    webscraping_obj = webscraping(assignment_aim,filepath)
    webscraping_obj.get_links()
    webscraping_obj.scrape_data()

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():
    extracted=False
    return render_template("educator.html")

def clear_submissions_directory():
    submissions_folder = os.path.join(os.getcwd(), 'submissions')
    for filename in os.listdir(submissions_folder):
        file_path = os.path.join(submissions_folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

@app.route("/extract", methods=['POST'])
def extract():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        return redirect(request.url)

    if file:
        # Check if the file is a ZIP file
        if file.filename.endswith('.zip'):

            print("checked zip")
            assignment_aim = request.form['assignment_aim']
            print("assignment aim : ", assignment_aim)
            analysis_name = request.form['analysis_name']
            # Check if the 'submissions' directory exists, if not, create it
            submissions_folder = os.path.join(os.getcwd(), 'submissions')
            if not os.path.exists(submissions_folder):
                os.makedirs(submissions_folder, exist_ok=True)
            
            clear_submissions_directory()
            print("clear earlier directory")

            zip_path = os.path.join(submissions_folder, file.filename)
            file.save(zip_path)

            with ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(submissions_folder)

            os.remove(zip_path)

            filepath = zip_path.replace('.zip', '')
            print(filepath)

            if analysis_name:
                session_data['analysis_name']=analysis_name
            else:
                session_data['analysis_name']=False

            # calling webscraping and gpt scraping
            if assignment_aim:
                webscrape_data(assignment_aim,filepath)

            fetch_data(filepath)

            return redirect("/result")

        else:
            return "Uploaded file is not a ZIP file."

    return redirect("/home", extracted=False)

@app.route("/result")
def result():
    extracted = True
    data = session_data['data']
    plag_highest = session_data['plag_highest']
    top_lang = session_data['top_lang']

    if data is None:
        return "Data not found. Please sort first."

    return render_template("report.html", data=data, plag_highest=plag_highest, top_lang=top_lang,extracted=extracted, analysis_name=session_data['analysis_name'])

@app.route("/list")
def list():
    extracted = True
    data = session_data['data']
    return render_template("list.html", data=data,extracted=extracted)

@app.route("/heatmap")
def heatmap():
    extracted = True
    return render_template("heatmap.html",extracted=extracted)

@app.route("/cluster")
def cluster():
    extracted = True
    return render_template("cluster.html",extracted=extracted)

@app.route("/topwords")
def topwords():
    extracted = True
    return render_template("topwords.html",extracted=extracted)

@app.route("/singlecomparison", methods=['POST'])
def single_comparison():
    extracted = True
    data = session_data['data']
    student = request.form['student']
    newdata = []
    
    for i in data:
        if i[0] == student:
            newdata.append([student, i[1], i[2]])
        if i[1] == student:
            newdata.append([student, i[0], i[2]])
    
    # print(newdata)
    return render_template("singlecomparison.html", data=newdata,extracted=extracted)


@app.route("/compare", methods=['POST'])
def compare():
    extracted = True
    print("comparing...")
    
    student1 = request.form['student1']
    student2 = request.form['student2']

    path = session_data['filepath']
    full_path1 = path + "/" + student1
    full_path2 = path + "/" + student2

    print(full_path1)

    texts = codediff(full_path1, full_path2)
    text1=texts[0]
    text2=texts[1]
    l = min(len(text1), len(text2))

    if len(text1) > len(text2):
        remaining = 1
    else:
        remaining = -1

    return render_template("codecompare.html", text1=text1, text2=text2, student1=student1, student2=student2, l=l, remaining=remaining, extracted=extracted)

@app.route("/chatgpt")
def chatgpt():
    assignment_aim = session_data['assignment_aim']
    filepath = session_data['filepath']

    webscrape_data(assignment_aim, filepath)

if __name__ == '__main__':
    app.run(debug=True)