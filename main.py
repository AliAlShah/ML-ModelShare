from distutils.log import debug
from fileinput import filename
from itertools import count
from flask import Flask, flash, redirect, session, url_for, render_template, request
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.secret_key = "Im The Best"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///models.sqlite3'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class models(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    filename = db.Column(db.String(50))
    filedescription = db.Column(db.String(200))
    data = db.Column(db.LargeBinary)

    def __init__(self, filename, filedescription, data):
        self.filename = filename
        self.filedescription = filedescription
        self.data = data

@app.route("/", methods=["POST", "GET"])
def home():
    if request.method == "POST":
        name = request.form["mname"]
        description = request.form["mdescription"]
        data = request.files["model"]
        filename = data.filename
        new_data = filename.split(".")
        if new_data[1] == "pickle":

            x = models.query.filter_by(filename=name).count()
            print(x)
            if x > 0:
                flash("This name has already been used!", "warning")
            else:
                model = models(filename=name, filedescription=description, data=data.read())
                db.session.add(model)
                db.session.commit()
        else:
            flash("Model has to be a .pickle file")

    return render_template('index.html')

@app.route("/view")
def view():
    return render_template("view.html", values=models.query.all())

@app.route("/<name>", methods=["POST", "GET"])
def view_model(name):
    mymodel = models.query.filter_by(filename=name).first()

    if request.method == "POST":
        parameters = request.form["parameters"]
        parameters = parameters.split(",")

        for i in range(0, len(parameters)):
            try:
                parameters[i] = int(parameters[i])
            except:
                break
        print(parameters)

    return render_template("viewmodel.html", model=mymodel)


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)