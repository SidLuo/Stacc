# Stacc - A Flask-Based Food Ordering Application

Stacc is a web application built with Flask that allows users to order food from local businesses. It provides user and business owner interfaces with features such as user registration and login, menu browsing, order management, discount management, and basic analytics.

## Features

*   **User Interface:**
    *   User registration and login.
    *   Browse local businesses.
    *   View business menus.
    *   Place orders.
    *   View order history.
    *   Rate businesses.
    *   Apply discounts.
*   **Business Owner Interface:**
    *   Business registration and login.
    *   Manage menu items (add, modify, delete).
    *   Manage categories.
    *   Manage opening hours.
    *   View and accept orders.
    *   Mark orders as complete.
    *   Manage discounts.
    *   View basic analytics.
    *   Request payouts via PayPal (Note: PayPal integration may require updated API keys).
*   **Location-Based Services:**
    *   Uses longitude and latitude to display businesses.
    *   Zomato API integration to find nearby cafes.

## Technologies Used

*   **Flask:** A micro web framework for Python.
*   **Flask-SQLAlchemy:** An extension for using SQLAlchemy with Flask, providing tools for database interactions.
*   **SQLite:** A lightweight, file-based database (default).
*   **HTML/CSS:** For the user interface.
*   **Materialize CSS:** A CSS framework for a responsive and visually appealing design.
*   **PayPal API:** For processing payments to business owners.
*   **Zomato API:** For location-based cafe search

## Setup and Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```

2.  **Create a virtual environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate.bat  # On Windows
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Initialize the database:**

    ```bash
    ./init-db.sh # or python init-db.py if the shell script is not executable
    ```

5.  **(Optional) Configure the application:**

    *   Create an `instance` folder in the project root.
    *   Create a `config.py` file inside the `instance` folder to override default configuration values. For example, set a strong `SECRET_KEY` for production:

        ```python
        # instance/config.py
        SECRET_KEY = 'your_secret_key_here'
        ```

6.  **(Important) Update PayPal API Keys:**

    *   The PayPal API keys in `flaskr/business.py` are likely defunct and need to be updated with your own Sandbox or Live API credentials.

7.  **Run the application:**

    ```bash
    ./run.sh # or flask run
    ```

## Directory Structure
