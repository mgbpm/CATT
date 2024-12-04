from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os
import subprocess
from werkzeug.utils import secure_filename
import threading
import time

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a strong secret key
UPLOAD_FOLDER = "uploads"
RESULTS_FOLDER = "results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Global variable to store logs and process status
execution_logs = []
is_processing = False

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    global execution_logs, is_processing
    execution_logs = []  # Clear logs for a new process
    is_processing = True

    # Get uploaded file
    if "file" not in request.files:
        flash("No file part")
        return redirect(url_for("index"))

    file = request.files["file"]

    if not file or file.filename == "":
        flash("No selected file")
        return redirect(url_for("index"))

    # Save uploaded file
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Clear old results
    for f in os.listdir(RESULTS_FOLDER):
        os.remove(os.path.join(RESULTS_FOLDER, f))

    # Run the bash script in a separate thread
    threading.Thread(target=run_bash_script, args=(filepath,)).start()
    flash("File uploaded successfully. Summarization in progress.")
    return redirect(url_for("logs"))

def run_bash_script(filepath):
    global execution_logs, is_processing
    try:
        process = subprocess.Popen(
            f"bash batch_summary.sh {filepath} {RESULTS_FOLDER}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        for line in iter(process.stdout.readline, ""):
            execution_logs.append(line.strip())
        process.stdout.close()
        process.wait()
        if process.returncode != 0:
            execution_logs.append("Error occurred during execution.")
            execution_logs.append(process.stderr.read())
    except Exception as e:
        execution_logs.append(f"An error occurred: {str(e)}")
    finally:
        # Fix file names to remove carriage returns
        for file in os.listdir(RESULTS_FOLDER):
            sanitized_name = file.replace('\r', '')
            if sanitized_name != file:
                os.rename(os.path.join(RESULTS_FOLDER, file), os.path.join(RESULTS_FOLDER, sanitized_name))
        is_processing = False

@app.route("/logs")
def logs():
    if is_processing:
        return render_template("logs.html", logs=execution_logs)
    else:
        # Redirect to results page after processing
        return redirect(url_for("results"))

@app.route("/results")
def results():
    result_files = os.listdir(RESULTS_FOLDER)
    return render_template("results.html", files=result_files)

@app.route("/download/<filename>")
def download_file(filename):
    sanitized_filename = filename.replace('\r', '')  # Ensure the filename is sanitized
    return send_from_directory(RESULTS_FOLDER, sanitized_filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

