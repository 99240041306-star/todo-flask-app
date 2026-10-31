
from flask import Flask, request, jsonify, render_template, redirect, url_for
import logging

from db import (
    init_db,
    create_task,
    get_all_tasks,
    get_task_by_id,
    update_task,
    delete_task,
)

app = Flask(__name__)

# Default DB for normal app run
# Authentication can be added later if needed
# Session management can also be implemented as needed
# JWT tokens can be integrated for secure API access

app.config["DB_NAME"] = "tasks.db"

# Initialize the database when the app starts (including on Render/Gunicorn).
init_db(app.config["DB_NAME"])

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# ------------------------
# Health Check
# # ------------------------
# @app.route("/")
# def health_check():
#     return {"status": "OK"}


# ------------------------
# TEMPLATE ROUTES
# ------------------------
@app.route("/", methods=["GET"])
def tasks_page():
    try:
        tasks = get_all_tasks(app.config["DB_NAME"])
        return render_template("tasks.html", tasks=tasks)
    except Exception as e:
        logging.error(f"Error rendering tasks page: {e}")
        return "Internal Server Error", 500


@app.route("/add-task", methods=["GET", "POST"])
def add_task_page():
    if request.method == "POST":
        try:
            title = request.form.get("title")
            description = request.form.get("description", "")
            due_date = request.form.get("due_date")
            status = request.form.get("status", "pending")

            if not title or not due_date:
                return "Title and Due Date are required", 400

            create_task(
                title,
                description,
                due_date,
                status,
                app.config["DB_NAME"],
            )

            logging.info("Task created from template")
            return redirect(url_for("tasks_page"))

        except Exception as e:
            logging.error(f"Error creating task from template: {e}")
            return "Internal Server Error", 500

    return render_template("add_task.html")


# ------------------------
# HTML FORM ACTION ROUTES
# ------------------------
@app.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
def edit_task_page(task_id):
    task = get_task_by_id(task_id, app.config["DB_NAME"])
    if not task:
        return "Task not found", 404

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description", "")
        due_date = request.form.get("due_date")
        status = request.form.get("status", "pending")

        if not title or not due_date:
            return "Title and Due Date are required", 400

        update_task(
            task_id,
            title,
            description,
            due_date,
            status,
            app.config["DB_NAME"],
        )
        return redirect(url_for("tasks_page"))

    return render_template("edit_task.html", task=task)


@app.route("/tasks/<int:task_id>/complete", methods=["POST"])
def complete_task_page(task_id):
    task = get_task_by_id(task_id, app.config["DB_NAME"])
    if task:
        update_task(
            task_id,
            task["title"],
            task["description"],
            task["due_date"],
            "completed",
            app.config["DB_NAME"],
        )
    return redirect(url_for("tasks_page"))


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task_page(task_id):
    delete_task(task_id, app.config["DB_NAME"])
    return redirect(url_for("tasks_page"))


# ------------------------
# API ROUTES
# ------------------------
@app.route("/api/tasks", methods=["POST"])
def create_task_api():
    if request.method == "POST":
        try:
            data = request.get_json()

            title = data.get("title")
            description = data.get("description", "")
            due_date = data.get("due_date")
            status = data.get("status", "pending")

            if not title or not due_date:
                return jsonify({"error": "Title and due_date are required"}), 400

            create_task(
                title,
                description,
                due_date,
                status,
                app.config["DB_NAME"],
            )

            logging.info("Task created successfully")
            return jsonify({"message": "Task created"}), 201

        except Exception as e:
            logging.error(f"Error creating task: {e}")
            return jsonify({"error": "Internal server error"}), 500


@app.route("/api/tasks", methods=["GET"])
def get_tasks_api():
    try:
        tasks = get_all_tasks(app.config["DB_NAME"])
        return jsonify(tasks), 200
    except Exception as e:
        logging.error(f"Error fetching tasks: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/tasks/<int:task_id>", methods=["GET"])
def get_task_by_id_api(task_id):
    try:
        task = get_task_by_id(task_id, app.config["DB_NAME"])
        if not task:
            return jsonify({"error": "Task not found"}), 404

        return jsonify(task), 200

    except Exception as e:
        logging.error(f"Error fetching task {task_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def update_task_api(task_id):
    try:
        task = get_task_by_id(task_id, app.config["DB_NAME"])
        if not task:
            return jsonify({"error": "Task not found"}), 404

        data = request.get_json()

        title = data.get("title", task["title"])
        description = data.get("description", task["description"])
        due_date = data.get("due_date", task["due_date"])
        status = data.get("status", task["status"])

        update_task(
            task_id,
            title,
            description,
            due_date,
            status,
            app.config["DB_NAME"],
        )

        logging.info(f"Task {task_id} updated")
        return jsonify({"message": "Task updated"}), 200

    except Exception as e:
        logging.error(f"Error updating task {task_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task_api(task_id):
    try:
        task = get_task_by_id(task_id, app.config["DB_NAME"])
        if not task:
            return jsonify({"error": "Task not found"}), 404

        delete_task(task_id, app.config["DB_NAME"])

        logging.info(f"Task {task_id} deleted")
        return jsonify({"message": "Task deleted"}), 200

    except Exception as e:
        logging.error(f"Error deleting task {task_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ------------------------
# APP START
# ------------------------
if __name__ == "__main__":
    init_db(app.config["DB_NAME"])
    app.run(debug=True)
