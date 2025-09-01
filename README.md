
# Kanmind API

Kanmind is the backend for a collaborative Kanban board application. It's a REST API built with **Django** and the **Django REST Framework**, providing endpoints for user authentication, board management, task tracking, and comments.

-----

## ✨ Features

  * **User Authentication**: Secure registration and token-based login.
  * **Board Management**: Create, view, update, and delete Kanban boards (CRUD).
  * **Collaboration**: Add members to boards to share access and work on tasks together.
  * **Task Management**: Full CRUD functionality for tasks within boards.
  * **Task Properties**: Assign tasks a status (`To Do`, `In Progress`, etc.), priority (`Low`, `Medium`, `High`), a due date, an assignee, and a reviewer.
  * **Commenting**: Add comments to tasks to discuss details.
  * **Permission System**: A granular permission system ensures that only authorized users (owners, members) can access or modify boards and tasks.

-----

## 🚀 Setup and Installation

Follow these steps to set up and run the project locally.

### Prerequisites

  * Python 3.8+
  * pip

### Installation Steps

1.  **Clone the repository:**

    ```bash
    git clone <your-repository-url>
    cd kanmind
    ```

2.  **Create and activate a virtual environment:**

      * **For macOS/Linux:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
      * **For Windows:**
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```

3.  **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the database migrations:**

    ```bash
    python manage.py migrate
    ```

5.  **Start the development server:**

    ```bash
    python manage.py runserver
    ```

The server will now be running at `http://127.0.0.1:8000/`.

-----

## 🔧 Configuration

  * **SECRET\_KEY**: The `SECRET_KEY` is currently hardcoded in `kanmind_hub/settings.py`. For a production environment, this should be moved to an environment variable.

  * **CORS**: Cross-Origin Resource Sharing (CORS) is configured to allow requests from `http://localhost:5500/` and `http://127.0.0.1:5500/`. If your frontend is running on a different address, adjust the `CORS_ALLOWED_ORIGINS` list in the `settings.py` file.

-----

## 📡 API Endpoints

All endpoints are accessible via the `/api/` prefix. Token authentication is required for most endpoints.

### Authentication (`/api/`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/registration/` | Registers a new user. |
| `POST` | `/login/` | Logs in a user and returns an authentication token. |
| `GET` | `/email-check/` | Checks if a user with a given email address exists. |

### Boards (`/api/boards/`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET`, `POST` | `/` | Lists all boards the user has access to or creates a new board. |
| `GET`, `PUT/PATCH`, `DELETE` | `/<id>/` | Retrieves, updates, or deletes a specific board. |

### Tasks (`/api/tasks/`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET`, `POST` | `/` | Lists all accessible tasks or creates a new task on a board. |
| `GET`, `PUT/PATCH`, `DELETE` | `/<id>/` | Retrieves, updates, or deletes a specific task. |
| `GET` | `/assigned-to-me/` | Lists all tasks assigned to the current user. |
| `GET` | `/reviewing/` | Lists all tasks the current user is set to review. |

### Comments (`/api/tasks/<task_pk>/comments/`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET`, `POST` | `/` | Lists all comments for a task or creates a new one. |
| `GET`, `PUT/PATCH`, `DELETE` | `/<id>/` | Retrieves, updates, or deletes a specific comment. |