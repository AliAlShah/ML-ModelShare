from fileinput import filename
from flask import Flask, flash, redirect, session, url_for, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from io import BytesIO
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
        isround = request.form["mround"]
        dictionary = request.files["mdictionary"]
        parameterorder = request.form["mparameterorder"]

        instructionsfilename = instructions.filename
        new_instruct = instructionsfilename.split(".")
        
        dictionaryfilename = dictionary.filename
        new_dictionary = dictionaryfilename.split(".")

        nparameters = len(parameterorder.split(","))

        filename = data.filename
        new_data = filename.split(".")
        if new_data[1] == "pickle":
            if new_instruct[1] == "txt":
                if new_dictionary[1] == "txt":

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
                else:
                    flash("Dictionary has to be a text file")
            else:
                flash("Instructions have to be a .txt file")
        else:
            flash("Model has to be a .pickle file")

            
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
    
    my_dict = {}
    for n in new_lines:
        my_dict[n[0]] = int(n[1])
    
    
    if request.method == "POST":
        inputvalue = []
        for i in range(mymodel.numberofparameters):
            form_name = f"{str(i)},"
            inputvalue.append(request.form[form_name])

        should_predict = True

        for i in range(0, len(inputvalue)):
            try:
                inputvalue[i] = int(inputvalue[i])
            except:
                inputvalue[i] = my_dict[inputvalue[i]]
                
                    
                
        x = BytesIO(mymodel.data)
        m = pickle.load(x)
        prediction = ""

        print(should_predict)
        if should_predict ==  True:
            try:
                prediction = m.predict([inputvalue])
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
    return render_template("search.html")

@app.route("/download/<instructname>")
def download_instruct(instructname):
    mymodel = models.query.filter_by(filename=instructname).first()
    return send_file(BytesIO(mymodel.instructions), attachment_filename="openFileInNotepad")


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)