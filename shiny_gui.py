from shiny import App, ui, reactive, render
import os
import shutil
import subprocess
from werkzeug.utils import secure_filename
import threading
from flask import Flask, send_from_directory

# Absolute path to the results folder
RESULTS_FOLDER = "results"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

execution_logs = []
is_processing = False

def run_bash_script(filepath, session):
    global execution_logs, is_processing
    execution_logs.clear()
    is_processing = True
    try:
        process = subprocess.Popen(
            f"bash batch_results.sh {filepath} {RESULTS_FOLDER}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        for line in iter(process.stdout.readline, ""):
            log_line = line.strip()
            execution_logs.append(log_line)
            session.send_custom_message("log_update", log_line)  # Push log updates to the frontend
        process.stdout.close()
        process.wait()
        if process.returncode != 0:
            error_msg = process.stderr.read()
            execution_logs.append(f"Error occurred during execution: {error_msg}")
            session.send_custom_message("log_update", f"Error occurred during execution: {error_msg}")
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        execution_logs.append(error_msg)
        session.send_custom_message("log_update", error_msg)
    finally:
        # Fix file names to remove carriage returns
        for file in os.listdir(RESULTS_FOLDER):
            sanitized_name = file.replace('\r', '')
            if sanitized_name != file:
                os.rename(os.path.join(RESULTS_FOLDER, file), os.path.join(RESULTS_FOLDER, sanitized_name))
        is_processing = False
        session.send_custom_message("log_update", "Processing complete!")

# Flask application for static file serving
flask_app = Flask(__name__)

@flask_app.route("/download/<filename>")
def download_file(filename):
    """Route to download result files from the RESULTS_FOLDER."""
    try:
        return send_from_directory(RESULTS_FOLDER, filename, as_attachment=True)
    except FileNotFoundError:
        return f"File {filename} not found in results folder.", 404

# Shiny app UI
app_ui = ui.page_fluid(
    ui.h2("Genetic Variant Summarization Tool"),
    ui.row(
        ui.column(
            6,
            ui.input_file("file_input", "Upload Input File:", multiple=False, accept=".txt"),
        ),
        ui.column(
            6,
            ui.input_action_button("start_button", "Start Summarization", class_="btn-primary"),
        ),
    ),
    ui.hr(),
    ui.h4("Execution Logs"),
    ui.div(
        ui.output_text_verbatim("logs_output", placeholder=True),
        class_="logs-output",
        style="height: 300px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; background-color: #f9f9f9;"
    ),
    ui.hr(),
    ui.h4("Download Results"),
    ui.output_ui("results_links"),
    ui.tags.script(
        """
        const socket = new WebSocket("ws://" + window.location.host + "/__websocket__");
        socket.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            if (msg.custom_message_type === "log_update") {
                const logOutput = document.querySelector(".logs-output pre");
                logOutput.textContent += msg.message + "\\n";
                logOutput.scrollTop = logOutput.scrollHeight;  // Auto-scroll to bottom
            }
        };
        """
    ),
    ui.tags.style(
        """
        .btn-primary {
            background-color: #007bff;
            border-color: #007bff;
            color: white;
        }
        .btn-primary:hover {
            background-color: #0056b3;
        }
        """
    ),
)

# Shiny app server
def server(input, output, session):
    @reactive.Effect
    def observe_upload():
        if input.file_input() and input.start_button():
            # Reset logs and start processing
            file_info = input.file_input()[0]
            filename = secure_filename(file_info["name"])
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            # Copy file from datapath to the uploads folder
            shutil.copy(file_info["datapath"], filepath)

            # Clear previous results in the RESULTS_FOLDER
            for f in os.listdir(RESULTS_FOLDER):
                os.remove(os.path.join(RESULTS_FOLDER, f))

            # Start bash script in a separate thread
            threading.Thread(target=run_bash_script, args=(filepath, session)).start()

    @output
    @render.text
    @reactive.Calc
    def logs_output():
        # Display static logs in case WebSocket is unavailable
        return "\n".join(execution_logs)

    @output
    @render.ui
    @reactive.Calc
    def results_links():
        # Generate static download links for results
        if not is_processing and os.listdir(RESULTS_FOLDER):
            links = [
                ui.tags.a(
                    file,
                    href=f"/download/{file}",  # Point to the download route
                    class_="btn btn-secondary",
                    style="margin: 5px;",
                    target="_blank",
                )
                for file in os.listdir(RESULTS_FOLDER)
            ]
            return ui.div(*links)

# Combine Flask with Shiny
app = App(app_ui, server)
app._flask = flask_app

