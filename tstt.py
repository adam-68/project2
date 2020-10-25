from flask import Flask, request, jsonify, render_template, redirect
import webbrowser

app = Flask(__name__)

config = {
    "sitekey": "6Le11awZAAAAANZZoBvLmQ-EYGRHkxPAjuJcGBKu",
    "domain": "supersklep.pl"
}


@app.route('/')
def index():
	return render_template('index.html', sitekey=config['sitekey'], domain=config['domain'])


if __name__ == "__main__":
    webbrowser.open('http://{}:5000/'.format(config['domain']))
    app.run()
