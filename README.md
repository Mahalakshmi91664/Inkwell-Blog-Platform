# Inkwell-Blog-Platform
Inkwell is a modern, minimalist blog platform designed to bridge the gap between creative writing and simple technology. The application follows a Client-Server architecture, ensuring a clean separation between the user interface and the data management logic.

## 🚀 Features
- User Authentication (Sign In/Register).
- Create and manage blog posts.
- Responsive UI for a smooth user experience.
- RESTful API communication between frontend and backend.

--------IMPORTANT------------
1. Start the Backend Server
Run the application:

Bash
python app.py
The server will start running at: http://127.0.0.1:5000

2. Launch the Frontend
Open the index.html file in any modern web browser while the backend server is running.

----------Troubleshooting---------

If you see a "Cannot connect to server" error:

Check if app.py is currently running in your terminal.

Ensure you have installed flask-cors and initialized it in your Python code (CORS(app)).

Verify that both frontend and backend are using the same port (default is 5000).
