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
    venv\\Scripts\\activate.bat  # On Windows
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
```
.
├── Diaries/
├── Pitch/ # Potentially a presentation framework (e.g., Reveal.js)
├── flaskr/ # Main Flask application package
│   ├── init.py # Application factory and core setup
│   ├── database.py # SQLAlchemy database initialization
│   ├── models.py # Database models (User, Owner, Item, Order, etc.)
│   ├── user.py # User-specific blueprint (authentication, orders, Browse)
│   ├── business.py # Business owner-specific blueprint (menu, orders, analytics)
│   ├── static/ # Static assets (CSS, images)
│   │   ├── uploads/ # Directory for uploaded files
│   │   └── *.css # CSS stylesheets (e.g., style.css, materialize.min.css)
│   └── templates/ # HTML templates
│       ├── user/ # User-related templates
│       ├── business/ # Business-related templates
│       └── *.html # Base templates (e.g., base.html, base_user.html)
├── geoencode.html # HTML file related to geographical encoding
├── init-db.sh # Shell script to initialize the database
├── instance/ # Instance-specific configuration and SQLite database
├── requirements.txt # Python dependencies
├── run.bat # Batch script to run on Windows
├── run.sh # Shell script to run the Flask application on Linux/macOS
├── setup.cfg
├── setup.py
├── test/ # Test files and directories
└── tests/
```

## Usage

1.  **Access the application in your browser:** Open `http://127.0.0.1:5000/` after running the application.

2.  **Register as a user or business owner:** Follow the prompts on the application's interface to create an account.

3.  **Explore the application's features:**
    *   As a user, you can browse businesses, place orders, and track your order history.
    *   As a business owner, you can manage your menu, view incoming orders, and analyze sales data.

## Notes

*   This application is a work in progress and may have limitations or require further development for production use.
*   **PayPal Integration:** The PayPal API keys provided in `flaskr/business.py` are for a sandbox environment and are likely expired. You will need to replace them with your own valid PayPal API credentials (client ID and secret) from your PayPal Developer account (sandbox or live) for payment functionality to work.
*   **Security:** For a production environment, consider implementing more robust security measures, including environment variables for sensitive keys, stricter input validation, and comprehensive error handling.
*   **Scalability:** The current setup uses SQLite, which is suitable for development and small-scale deployments. For larger applications, consider migrating to a more robust database system like PostgreSQL or MySQL.

## Contributing

Contributions are welcome! If you find a bug, have a feature request, or want to improve the codebase, please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name` or `bugfix/your-bug-name`).
3.  Make your changes.
4.  Write clear and concise commit messages.
5.  Push your branch (`git push origin feature/your-feature-name`).
6.  Open a pull request to the `main` branch of this repository.

Please ensure your code adheres to the existing style and conventions.
