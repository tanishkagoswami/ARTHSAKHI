# ARTHSAKHI

ARTHSAKHI is a Flask-based financial awareness and learning platform designed to help users improve financial literacy through interactive modules, scam checking, educational content, and chatbot support.

## Features

- Financial literacy dashboard
- Interactive learning modules
- Scam checker page
- AI chatbot support
- Clean and responsive UI
- Flask backend with modular templates

## Project Structure

    ARTHSAKHI/
    │── app.py
    │── models.py
    │── requirements.txt
    │── README.md
    │── .gitignore
    │
    ├── static/
    │   ├── css/
    │   │   └── style.css
    │   └── js/
    │       └── app.js
    │
    └── templates/
        ├── base.html
        ├── index.html
        ├── dashboard.html
        ├── learn.html
        ├── module_detail.html
        ├── scam_checker.html
        └── chatbot.html

## Tech Stack

- Backend: Flask
- Frontend: HTML, CSS, JavaScript
- Templating: Jinja2
- Environment Management: Python virtual environment (`venv`)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/tanishkagoswami/ARTHSAKHI.git
cd ARTHSAKHI
```

2. Create a virtual environment:

```bash
python -m venv venv
```

3. Activate the virtual environment:

On Windows:

```bash
venv\Scripts\activate
```

On Mac/Linux:

```bash
source venv/bin/activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Project

Start the Flask app:

```bash
python app.py
```

Then open:

```bash
http://127.0.0.1:5000/
```

## Environment Variables

If the project uses Gemini API or any secret keys, create a `.env` file in the root folder.

Example:

```env
GEMINI_API_KEY=your_api_key_here
```

## Modules

- Home Page
- Dashboard
- Learn
- Module Detail
- Scam Checker
- Chatbot

## Future Improvements

- User authentication
- Progress tracking
- Database integration
- Improved scam detection
- Better chatbot responses
- Cloud deployment

## Author

**Tanishka Goswami**  
B.Tech CSE (AI & ML) Student  
VIT-AP University

## License

This project is for educational and academic purposes.