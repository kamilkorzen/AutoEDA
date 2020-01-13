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
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if find_by_username(username):
            return "User already exists"
        else:
            connection = sqlite3.connect('data.db')
            cursor = connection.cursor()

            cursor.execute("INSERT INTO users VALUES (NULL, ?, ?)", (username, password))

            connection.commit()
            connection.close()
            return redirect(url_for("homepage", content=logged))

@app.route('/login', methods=["POST", "GET"])
def login():
    global logged, userID
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
                return redirect(url_for("homepage", content=logged))
            else:
                return "Wrong password!"
        else:
            return "User doesn't exist!"
@app.route('/logout', methods=["GET"])
def logout():
    global logged, userID, dataset
    logged=False
    userID=None
    dataset=None
    return redirect(url_for("homepage", content=logged))


#data================================================================
@app.route("/data", methods=["POST", "GET"])
def data():
    global logged, userID
    if logged==True:
        if request.method == "GET":
            return render_template("data.html")
        elif request.method == "POST":
            filename = request.form["filename"]
            path = request.form["path"]

            result=find_by_filename(filename, userID)
            if result:
                return "File with this name already exists!"
            else:
                connection = sqlite3.connect('data.db')
                cursor = connection.cursor()

                cursor.execute("INSERT INTO data VALUES (NULL, ?, ?, ?)", (userID, filename, path))

                connection.commit()
                connection.close()
                return redirect(url_for("homepage", content=logged))

    else:
        return redirect(url_for("homepage", content=logged))

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
        return redirect(url_for("homepage", content=logged))

@app.route("/datalab", methods = ["GET"])
def datalab():
    global logged, userID, dataset, msg
    msg=None
    if logged==True:
        return render_template('datalab.html', tables=[dataset.to_html(classes='data')], titles=dataset.columns.values)
    else:
        return redirect(url_for("homepage", content=logged))

@app.route("/select", methods=["GET", "POST"])
def select():
    global logged, userID, dataset, msg
    dataset = None
    if logged==True:
        if request.method == "GET":
            return render_template("select.html", message=msg)
        elif request.method == "POST":
            filename=request.form["filename"]

            result = find_by_filename(filename, userID)
            if result:
                path=result[3]
                dataset = pd.read_csv(path, sep=';', decimal=',')
                msg=""
                return redirect(url_for("datalab", content=logged))
            else:
                msg="There is no such file!"
                return redirect(url_for("select", content=logged))
    else:
        return redirect(url_for("homepage", content=logged))

@app.route('/delete', methods=["GET", "POST"])
def delete():
    global logged, userID, dataset
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

                return redirect(url_for("homepage", content=logged))
            else:
                return redirect(url_for("homepage", content=logged))

    else:
        return redirect(url_for("homepage", content=logged))

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


# sns.heatmap(df[v1].corr(),cmap='coolwarm',annot=True)
# sns.boxplot(x=df["stolica woj.."], y=df[v1[1]],data=df, palette="coolwarm")
# sns.lmplot(x=v1[1] ,y=v1[2] ,data=df)
# df.describe()
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

