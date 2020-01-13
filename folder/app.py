from flask import Flask, redirect, url_for, render_template, request
import sqlite3
import pandas as pd


app = Flask(__name__)

logged=False
userID=None
dataset=None

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

@app.route("/datalab")
def datalab():
    global logged, userID, dataset
    if logged==True:
        return render_template('datalab.html', tables=[dataset.to_html(classes='data')], titles=dataset.columns.values)
    else:
        return redirect(url_for("homepage", content=logged))

@app.route("/select", methods=["GET", "POST"])
def select():
    global logged, userID, dataset
    dataset = None
    if logged==True:
        if request.method == "GET":
            return render_template("select.html")
        elif request.method == "POST":
            filename=request.form["filename"]

            result = find_by_filename(filename, userID)
            if result:
                path=result[3]
                dataset = pd.read_csv(path, sep=';')
                return redirect(url_for("datalab", content=logged))
            else:
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

