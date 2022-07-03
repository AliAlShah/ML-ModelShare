from flask import Flask, flash, redirect, session, url_for, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from io import BytesIO
import difflib
import pickle
import os

app = Flask(__name__)
app.secret_key = "Im The Best"
app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://hmnnapyknlmwzg:85e545ccbae5247376329fd8d4412dab30a6d9796c00230abeb488bd2bfb6529@ec2-44-198-82-71.compute-1.amazonaws.com:5432/d3lrki06atuot9"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

load_dotenv()
print(os.getenv("DATABASEURL"))

class models(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    filename = db.Column(db.String(50))
    filedescription = db.Column(db.String(200))
    data = db.Column(db.LargeBinary)
    instructions = db.Column(db.LargeBinary)
    isround = db.Column(db.String(50))
    dictionary = db.Column(db.LargeBinary)
    parameterorder = db.Column(db.String(50))
    numberofparameters = db.Column(db.Integer())

    def __init__(self, filename, filedescription, data, instructions, isround, dictionary, parameterorder, numberofparameters):
        self.filename = filename
        self.filedescription = filedescription
        self.data = data
        self.instructions = instructions
        self.isround = isround
        self.dictionary = dictionary
        self.parameterorder = parameterorder
        self.numberofparameters = numberofparameters

@app.route("/", methods=["POST", "GET"])
def home():
    if request.method == "POST":
        
        name = request.form["mname"]
        description = request.form["mdescription"]
        data = request.files["model"]
        instructions = request.files["minstruct"]
        try:
            isround = request.form["mround"]
        except:
            isround = "off"
        dictionary = request.files["mdictionary"]
        parameterorder = request.form["mparameterorder"]
        parameterorder = parameterorder.replace(" ", "")

        nparameters = len(parameterorder.split(","))

        if models.query.filter_by(filename=name).count() > 0:
            flash("This name has already been used!", "warning")
        else:
            model = models(
                filename=name,
                filedescription=description,
                data=data.read(),
                instructions=instructions.read(),
                isround=isround,
                dictionary=dictionary.read(),
                parameterorder=parameterorder,
                numberofparameters=nparameters)
            db.session.add(model)
            db.session.commit()
            return redirect(url_for("view_model", name=name))

            
    return render_template('index.html')

@app.route("/view")
def view():
    return render_template("view.html", values=models.query.all())

@app.route("/<name>", methods=["POST", "GET"])
def view_model(name):
    mymodel = models.query.filter_by(filename=name).first()
    text_data = BytesIO(mymodel.dictionary).readlines()
    new_lines = []
    for i in range(0, len(text_data)):
        text_data[i] = text_data[i].strip().decode("utf-8")
        new_lines.append(text_data[i].split(":"))
    
    just_names = []
    for i in new_lines:
        just_names.append(f"{i[0]},{i[2]}".split(","))

    my_dict = {}
    for n in new_lines:
        my_dict[f"{n[0].lower()},{n[2]}"] = n[1]
    
    if request.method == "POST":
        inputvalue = []
        for i in range(mymodel.numberofparameters):
            form_name = f"{str(i)},"
            inputvalue.append(f"{request.form[form_name].lower()},{i}".split(","))
        
        should_predict = True

        for i in range(0, len(inputvalue)):
            try:
                inputvalue[i][0] = int(inputvalue[i][0])
            except:
                try:
                    inputvalue[i][0] = float(inputvalue[i][0])
                except:
                    try:
                        inputvalue[i][0] = int(my_dict[",".join(inputvalue[i])])
                    except:
                        try:
                            print(f"input value : {inputvalue[i]}")
                            wanted_list = [x[0].lower() for x in just_names if x[1] == inputvalue[i][1]]
                            print(f"wanted list: {wanted_list}")
                            closest_match = difflib.get_close_matches(inputvalue[i][0], wanted_list, n=3, cutoff=0.5)
                            
                            if len(closest_match) > 0:
                                flash(f"We could not predict the result, you typed {inputvalue[i][0]} did you mean: {closest_match}")

                            else:
                                flash(f"We could not predict the result, mabey you have a spelling mistake when typing {inputvalue[i][0]} in input box number: {inputvalue[i][1]}, or the creator of the model hasnt thought of your input")

                            should_predict = False

                        except:
                            flash(f"We could not predict the result, mabey you have a spelling mistake when typing {inputvalue[i][0]} in input box number: {inputvalue[i][1]}, or the creator of the model hasnt thought of your input")
                            should_predict = False

        new_input_value = []
        for i in inputvalue:
            new_input_value.append(i[0])       

        x = BytesIO(mymodel.data)
        m = pickle.load(x)
        prediction = ""

        if should_predict ==  True:
            try:
                prediction = m.predict([new_input_value])
            except:
                flash("Could not predict value, uploaded model may be corupt or you may have missed a parameter")

            if mymodel.isround == "on":
                prediction = round(prediction[0])
            
            flash(f"Prediction: {str(prediction)}")
        
    return render_template("viewmodel.html", model=mymodel, parameters=mymodel.parameterorder.split(","), l=mymodel.numberofparameters)


@app.route("/search", methods=["POST", "GET"])
def search():
    if request.method == "POST":
        searched_name = request.form["searchedname"]
        if models.query.filter_by(filename=searched_name).count() > 0:
            return redirect(url_for("view_model", name=searched_name))
        else:
            flash("No Models found with that name")
    return render_template("search.html")

@app.route("/download/<instructname>")
def download_instruct(instructname):
    mymodel = models.query.filter_by(filename=instructname).first()
    return send_file(BytesIO(mymodel.instructions), attachment_filename="openFileInNotepad")

@app.route("/howto")
def howto():
    return render_template("howto.html")


if __name__ == "__main__":
    db.init_app(app)
    db.create_all()
    app.run(debug=True)