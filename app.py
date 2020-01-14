from flask import Flask, redirect, url_for, render_template, request
import sqlite3
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib
import random
import string

app = Flask(__name__)

logged=False
userID=None
dataset=None
msg=""

@app.route('/')
def homepage():
    return render_template('homepage.html', content=logged)

@app.route('/register', methods=["POST", "GET"])
def register():
    global logged, userID, msg, dataset
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if find_by_username(username):
            msg="User already exists"
            return render_template("register.html", message=msg)
        else:
            connection = sqlite3.connect('data.db')
            cursor = connection.cursor()

            cursor.execute("INSERT INTO users VALUES (NULL, ?, ?)", (username, password))

            connection.commit()
            connection.close()
            msg=None
            return redirect(url_for("homepage"))

@app.route('/login', methods=["POST", "GET"])
def login():
    global logged, userID, msg, dataset
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        result = find_by_username(username)
        if result:
            if result[2]==password:
                logged=True
                userID=result[0]
                msg=None
                return redirect(url_for("homepage"))
            else:
                msg="Wrong password!"
                return render_template("login.html", message=msg)
        else:
            msg="User doesn't exist!"
            return render_template("login.html", message=msg)

@app.route('/logout', methods=["GET"])
def logout():
    global logged, userID, dataset, msg
    logged=False
    userID=None
    dataset=None
    msg=None
    return redirect(url_for("homepage"))


#data================================================================
@app.route("/data", methods=["POST", "GET"])
def data():
    global logged, userID, msg, dataset
    if logged==True:
        if request.method == "GET":
            return render_template("data.html")
        elif request.method == "POST":
            filename = request.form["filename"]
            path = request.form["path"]

            result=find_by_filename(filename, userID)
            if result:
                msg="File with this name already exists!"
                return render_template("data.html", message=msg)
            else:
                connection = sqlite3.connect('data.db')
                cursor = connection.cursor()

                cursor.execute("INSERT INTO data VALUES (NULL, ?, ?, ?)", (userID, filename, path))

                connection.commit()
                connection.close()

                msg=None
                return redirect(url_for("show"))

    else:
        return redirect(url_for("homepage"))

@app.route('/notes', methods = ['GET'])
def notes():
    global logged, userID, dataset, msg
    note = None
    if logged:
        if request.method == 'GET':
            return render_template('notes.html')
        elif request.method == 'POST':
            note = request.form['note']

    else:
        return redirect(url_for('homepage'))

@app.route("/show", methods=["GET"])
def show():
    global logged, userID
    if logged==True:
        if userID==1:
            connection = sqlite3.connect('data.db')
            cursor = connection.cursor()

            result = cursor.execute("SELECT users.username, data.filename FROM users INNER JOIN data ON users.id = data.user_id")
            rows = result.fetchall()
            datasets=[]

            connection.commit()
            connection.close()

            for row in rows:
                datasets.append({"username": row[0], "filename": row[1]})
            data = pd.DataFrame(datasets)

            return render_template('show.html',  tables=[data.to_html(classes='data')], titles=data.columns.values)
        else:
            connection = sqlite3.connect('data.db')
            cursor = connection.cursor()

            result = cursor.execute("SELECT filename, path FROM data WHERE user_id=?",(userID,))

            rows = result.fetchall()
            datasets = []

            connection.commit()
            connection.close()

            for row in rows:
                datasets.append({"filename": row[0], "path": row[1]})
            data = pd.DataFrame(datasets)

            return render_template('show.html',  tables=[data.to_html(classes='data')], titles=data.columns.values)

    else:
        return redirect(url_for("homepage"))

@app.route("/datalab", methods = ["GET"])
def datalab():
    global logged, userID, dataset, msg
    msg=None
    if logged==True:
        return render_template('datalab.html', tables=[dataset.to_html(classes='data')], titles=dataset.columns.values)
    else:
        return redirect(url_for("homepage"))

@app.route("/select", methods=["GET", "POST"])
def select():
    global logged, userID, dataset, msg
    dataset = None
    if logged==True:
        if request.method == "GET":
            return render_template("select.html")
        elif request.method == "POST":
            filename=request.form["filename"]

            result = find_by_filename(filename, userID)
            if result:
                path=result[3]
                dataset = pd.read_csv(path, sep=';', decimal=',')
                msg=None
                return redirect(url_for("datalab"))
            else:
                msg="There is no such file!"
                return render_template("select.html", message=msg)
    else:
        return redirect(url_for("homepage"))

@app.route('/delete', methods=["GET", "POST"])
def delete():
    global logged, userID, dataset, msg
    if logged==True:
        if request.method == "GET":
            return render_template("delete.html")
        elif request.method == "POST":

            filename = request.form["filename"]
            result = find_by_filename(filename, userID)

            if result:
                connection=sqlite3.connect("data.db")
                cursor=connection.cursor()

                cursor.execute("DELETE FROM data WHERE filename=? AND user_id =?", (filename, userID))

                connection.commit()
                connection.close()

                msg=None
                return redirect(url_for("show"))
            else:
                msg="There is no such file!"
                return render_template("delete.html", message = msg)

    else:
        return redirect(url_for("homepage"))

@app.route("/update", methods=["POST", "GET"])
def update():
    global logged, userID, msg, dataset
    if logged==True:
        if request.method == "GET":
            return render_template("update.html")
        elif request.method == "POST":
            filename = request.form["filename"]
            path = request.form["path"]

            result=find_by_filename(filename, userID)
            if result:
                connection = sqlite3.connect('data.db')
                cursor = connection.cursor()

                cursor.execute("UPDATE data SET path = ? WHERE filename=? AND user_id =?", (path, filename, userID))

                connection.commit()
                connection.close()

                msg=None
                return render_template("show.html", message=msg)
            else:
                msg="There is no such file!"
                return render_template("update.html", message=msg)

    else:
        return redirect(url_for("homepage"))

#eda
@app.route('/dist', methods=['POST', 'GET'])
def dist():
    global logged, dataset, msg, userID
    if logged==True:
        if request.method == "GET":
            return render_template("dist.html", message=None)
        elif request.method == "POST":
            variables = request.form["variables"]

            try:
                plt.figure()
                sns.distplot(dataset[variables])
                plt.savefig("static/fig.png")

                randomstring = ''.join(random.choice(string.ascii_letters) for item in range(10))

                msg = f"static/fig.png?{randomstring}"
            except:
                return render_template("dist.html", message = "Error")

            return render_template("dist.html", message=msg)
    else:
        return redirect(url_for("homepage"))

@app.route('/bar', methods=['POST', 'GET'])
def bar():
    global logged, dataset, msg, userID
    if logged==True:
        if request.method == "GET":
            return render_template("bar.html", message=None)
        elif request.method == "POST":
            xvar = request.form["X"]
            yvar = request.form["Y"]

            try:
                plt.figure()
                sns.barplot(x=dataset[xvar],y=dataset[yvar],data=dataset)
                plt.xticks(rotation=90)
                plt.tight_layout()
                plt.savefig("static/fig.png")

                randomstring = ''.join(random.choice(string.ascii_letters) for item in range(10))

                msg = f"static/fig.png?{randomstring}"
            except:
                return render_template("bar.html", message = "Error")

            return render_template("bar.html", message=msg)
    else:
        return redirect(url_for("homepage"))

@app.route('/hex', methods=['POST', 'GET'])
def hex():
    global logged, dataset, msg, userID
    if logged==True:
        if request.method == "GET":
            return render_template("hex.html", message=None)
        elif request.method == "POST":
            xvar = request.form["X"]
            yvar = request.form["Y"]

            try:
                plt.figure()
                sns.jointplot(x=dataset[xvar],y=dataset[yvar],data=dataset,kind='hex')
                #plt.xticks(rotation=90)
                plt.tight_layout()
                plt.savefig("static/fig.png")

                randomstring = ''.join(random.choice(string.ascii_letters) for item in range(10))

                msg = f"static/fig.png?{randomstring}"
            except:
                return render_template("hex.html", message = "Error")

            return render_template("hex.html", message=msg)
    else:
        return redirect(url_for("homepage"))

@app.route('/cor', methods=['POST', 'GET'])
def cor():
    global dataset, logged, msg, userID
    if logged==True:
        if request.method == "GET":
            return render_template("cor.html", message=None)
        elif request.method == "POST":
            variables = request.form["variables"]
            try:
                variables = variables.replace(', ', ',')
                listed = np.array(variables.split(','))
            except:
                return render_template("cor.html", message="Error")

            try:
                plt.figure()
                sns.heatmap(dataset[listed].corr(),cmap='coolwarm',annot=True)
                plt.tight_layout()
                plt.savefig("static/fig.png")

                randomstring = ''.join(random.choice(string.ascii_letters) for item in range(10))

                msg = f"static/fig.png?{randomstring}"
            except:
                return render_template("cor.html", message = "Error")

            return render_template("cor.html", message=msg)
    else:
        return redirect(url_for("homepage"))

@app.route('/box', methods=['POST', 'GET'])
def box():
    global logged, dataset, msg, userID
    if logged==True:
        if request.method == "GET":
            return render_template("box.html", message=None)
        elif request.method == "POST":
            xvar = request.form["X"]
            yvar = request.form["Y"]

            try:
                plt.figure()
                sns.boxplot(x=dataset[xvar], y=dataset[yvar], data=dataset, palette="coolwarm")
                plt.xticks(rotation=90)
                plt.tight_layout()
                plt.savefig("static/fig.png")

                randomstring = ''.join(random.choice(string.ascii_letters) for item in range(10))

                msg = f"static/fig.png?{randomstring}"
            except:
                return render_template("box.html", message = "Error")

            return render_template("box.html", message=msg)
    else:
        return redirect(url_for("homepage"))

@app.route('/lmplot', methods=['POST', 'GET'])
def lmplot():
    global logged, dataset, msg, userID
    if logged:
        if request.method == 'GET':
            return render_template('lmplot.html', message = None)
        elif request.method == 'POST':
            xvar = request.form["X"]
            yvar = request.form["Y"]

            try:
                plt.figure()
                sns.lmplot(x = dataset[xvar], y = dataset[yvar], data = dataset)
                plt.savefig('static/fig.png')

                randomstring = ''.join(random.choice(string.ascii_letters) for item in range(10))

                msg = f"static/fig.png?{randomstring}"
            except:
                return render_template('lmplot.html', message = "Error")

            return render_template('lmplot.html', message = msg)
        else:
            return redirect(url_for('homepage'))

@app.route('/desc', methods=['POST', 'GET'])
def desc():
    global logged, dataset, msg, userID
    if logged:
        if request.method == 'GET':
            return render_template('desc.html', message = None)
        elif request.method == 'POST':
            df = dataset

            try:
                df.describe()

                randomstring = ''.join(random.choice(string.ascii_letters) for item in range(10))
                msg = f'static/fig.png?(randomstring)'

            except:
                return render_template('desc.html', message = 'Error')

            return render_template('desc.html', message = msg)
        else:
            return redirect(url_for('homepage'))

#functions===========================================================

def find_by_username(username):
    connection = sqlite3.connect('data.db')
    cursor=connection.cursor()

    result = cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = result.fetchone()

    if row is not None:
        user=row
    else:
        user=None

    connection.close()
    return user

def find_by_filename(filename, userID):
    connection = sqlite3.connect('data.db')
    cursor=connection.cursor()

    result = cursor.execute("SELECT * FROM data WHERE filename = ? AND user_id= ?", (filename, userID))
    row = result.fetchone()

    if row is not None:
        data=row
    else:
        data=None

    connection.close()
    return data

if __name__ == "__main__":
    app.run(debug=True)
