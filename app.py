from flask import Flask, flash, redirect, session, url_for, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from io import BytesIO
import difflib
import pickle


app = Flask(__name__)
app.secret_key = "Im The Best"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///models.sqlite3'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

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

    text_data = list(BytesIO(mymodel.dictionary).readlines())
    new_lines = []
    for i in range(0, len(text_data)):
        text_data[i] = text_data[i].strip().decode("utf-8")
        new_lines.append(text_data[i].split(":"))
    
    just_names = []
    for i in new_lines:
        just_names.append(i[0])
    print(f"just names: {just_names}")
    
    my_dict = {}
    for n in new_lines:
        my_dict[f"{n[0].lower()},{n[2]}"] = int(n[1])
    print(my_dict)
    
    if request.method == "POST":
        inputvalue = []
        for i in range(mymodel.numberofparameters):
            form_name = f"{str(i)},"
            inputvalue.append(f"{request.form[form_name].lower()},{i}".split(","))
        
        print(inputvalue)
        should_predict = True

        for i in range(0, len(inputvalue)):
            try:
                inputvalue[i][0] = int(inputvalue[i][0])
            except:
                try:
                    inputvalue[i][0] = int(my_dict[",".join(inputvalue[i])])
                except:
                    try:
                        print(f"input value [i][0]= {inputvalue[i][0]}")
                        closest_match = difflib.get_close_matches(inputvalue[i][0], just_names, n=10, cutoff=0.5)
                        flash(f"We could not predict the result, you typed {inputvalue[i][0]} did you mean: {closest_match}")
                        should_predict = False
                    except:
                        flash(f"We could not predict the result, mabye you have a spelling mistake when typing {inputvalue[i][0]} or the creator of the model hasnt thought of your input")
                        should_predict = False

        print(inputvalue)
        new_input_value = []
        for i in inputvalue:
            new_input_value.append(i[0])       
        print(new_input_value)

        x = BytesIO(mymodel.data)
        m = pickle.load(x)
        prediction = ""

        print(should_predict)
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


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)