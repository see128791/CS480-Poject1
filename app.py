from flask import Flask, render_template
app = Flask(__name__)

@app.get('/')
def home():
    return "Welcome to the Home Page!"

@app.get('/profile')
def profile():
    return render_template('profile.html')

if __name__ == '__main__':
    app.run(debug=True)