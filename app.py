import os
import shutil
import webview
from flask import Flask, redirect, render_template, request, url_for
from zipfile import ZipFile
from algorithm import plagiarism_checker
from compare_files import comparison
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
    session_data['count_matrix'] = plag_check_obj.count_matrix
    session_data['corpus'] = plag_check_obj.corpus
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
    percentage = request.form['percentage']
    file1txt = session_data['corpus'][student1]
    file2txt = session_data['corpus'][student2]
    file1lines,file2lines = file1txt.split('\n'),file2txt.split('\n')
    file1lines,file2lines = [x for x in file1lines if x],[y for y in file2lines if y]
    count_matrix = session_data['count_matrix'].transpose()
    count_matrix = count_matrix[[student1,student2]]
    count_matrix = count_matrix.loc[(count_matrix[student1]>1) & (count_matrix[student2]>1)]

    comparison_obj = comparison(count_matrix,file1txt,file2txt)
    comparison_obj.generate_plots()
    comparison_obj.longest_common_string()
    longest_common_str=comparison_obj.longest_common_substring.rstrip('{\n\t')

    return render_template("file_compare.html", extracted=extracted , longest_substring=longest_common_str , student1=student1, student2=student2, percentage=percentage, text1=file1lines, text2=file2lines)

@app.route("/chatgpt")
def chatgpt():
    assignment_aim = session_data['assignment_aim']
    filepath = session_data['filepath']

    webscrape_data(assignment_aim, filepath)

webview.create_window('PDRS',app)

if __name__ == '__main__':
    # app.run(debug=True)
    webview.start()