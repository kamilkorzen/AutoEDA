# # /Users/kamilkorzen/Kamil/Education/MScDSBA/3_Python_and_SQL/AutoEDA/data.csv

from flask import Flask, redirect, url_for, render_template, request
import sqlite3
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib
import random
import string
from datetime import date

matplotlib.use('Agg')

app = Flask(__name__)

logged=False
userID=None
dataset=None
msg=""

@app.route('/', methods = ["POST", "GET"])
def homepage():
    global logged, userID, msg, dataset
    if logged:
        if request.method == "GET":

            connection = sqlite3.connect('data.db')
            cursor = connection.cursor()

            cursor.execute('SELECT id, note, date FROM notes WHERE user_id==?', (userID,))
            rows = cursor.fetchall()

            if len(rows)>20:
                cursor.execute("DELETE FROM notes WHERE id=? AND user_id =?", (rows[0][0], userID))

            notes=[]

            connection.commit()
            connection.close()

            for row in rows:
                notes.append({"Note": row[1], "Date": row[2]})
            data = pd.DataFrame(notes)
            data = data.reindex(index=data.index[::-1])

            return render_template('homepage.html',  tables=[data.to_html(classes='data')], titles=data.columns.values, content = logged)

        elif request.method == "POST":
            note = request.form["note"]
            connection = sqlite3.connect("data.db")
            cursor = connection.cursor()
            cursor.execute("INSERT INTO notes VALUES (NULL, ?, ?, ?)", (userID, note, date.today()))
            connection.commit()
            connection.close()
            msg = None

            connection = sqlite3.connect("data.db")
            cursor = connection.cursor()
            result = cursor.execute("SELECT note FROM notes WHERE user_id=?", (userID,))
            rows = result.fetchall()
            notes = []

            connection.commit()
            connection.close()

            for row in rows:
                notes.append({"note": row[0]})
            data = pd.DataFrame(notes)

            return redirect(url_for("homepage"))

    return render_template('homepage.html', content = logged)

@app.route('/register', methods=["POST", "GET"])
def register():
    global logged, userID, msg, dataset
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if find_by_username(username):
            msg="USER ALREADY EXISTS"
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
                msg="WRONG PASSWORD"
                return render_template("login.html", message=msg)
        else:
            msg="USER DOESN'T EXIST"
            return render_template("login.html", message=msg)

@app.route('/logout', methods=["GET"])
def logout():
    global logged, userID, dataset, msg
    logged=False
    userID=None
    dataset=None
    msg=None
    return redirect(url_for("homepage"))

@app.route("/data", methods=["POST", "GET"])
def data():
    global logged, userID, msg, dataset
    if logged==True:
        if request.method == "GET":
            return render_template("data.html")
        elif request.method == "POST":
            filename = request.form["filename"]
            path = request.form["path"]
            try:
                a=pd.read_csv(path, sep=';', decimal=',')
                del a
            except:
                msg="This is not CSV file in UTF-8 format!"
                return render_template("data.html", message=msg)
            result=find_by_filename(filename, userID)
            if result:
                msg="FILE WITH THIS NAME ALREADY EXISTS"
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

@app.route('/delete', methods=["GET", "POST"])
def delete():
    global logged, userID, dataset, msg
    if logged==True:
        connection = sqlite3.connect('data.db')
        cursor=connection.cursor()

        cursor.execute("SELECT filename FROM data WHERE user_id=?", (userID,))
        filenames = cursor.fetchall()

        connection.commit()
        connection.close()
        if request.method == "GET":
            return render_template("delete.html", filenames=filenames)
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
                return redirect(url_for("homepage"))
            else:
                msg="THERE IS NO SUCH FILE"
                return render_template("delete.html", message = msg, filenames=filenames)

    else:
        return redirect(url_for("homepage"))

@app.route("/update", methods=["POST", "GET"])
def update():
    global logged, userID, msg, dataset
    if logged==True:
        connection = sqlite3.connect('data.db')
        cursor=connection.cursor()

        cursor.execute("SELECT filename FROM data WHERE user_id=?", (userID,))
        filenames = cursor.fetchall()

        connection.commit()
        connection.close()
        if request.method == "GET":
            return render_template("update.html", filenames=filenames)
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
                return redirect(url_for("homepage"))
            else:
                msg="THERE IS NO SUCH FILE"
                return render_template("update.html", message=msg, filenames=filenames)

    else:
        return redirect(url_for("homepage"))

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

@app.route("/datalab", methods = ["GET", "POST"])
def datalab():
    global logged, userID, dataset, msg
    if logged==True:
        connection = sqlite3.connect('data.db')
        cursor=connection.cursor()

        cursor.execute("SELECT filename FROM data WHERE user_id=?", (userID,))
        filenames = cursor.fetchall()

        connection.commit()
        connection.close()

        if request.method == "GET":
            if dataset is not None:
                data=dataset.describe()
                data=data.round(2)

                plt.figure(figsize=(0.7*len(dataset.columns),0.7*len(dataset.columns)), dpi = 100)
                sns.heatmap(dataset.corr(), cmap='coolwarm', annot=True)
                plt.tight_layout()
                plt.savefig("static/fig.png", transparent=True)
                plt.close()

                randomstring = ''.join(random.choice(string.ascii_letters) for item in range(10))

                info, con, dis = get_info(dataset)

                msg = None
                return render_template('datalab.html', tables=[data.to_html(classes='data')], titles=data.columns.values, message=msg, filepath = f"static/fig.png?{randomstring}", filenames=filenames, info=info, con=con, dis=dis)
            else:
                msg=None
                return render_template('datalab.html', message=msg, filenames=filenames)
        elif request.method == "POST":
            filename=request.form["filename"]

            result = find_by_filename(filename, userID)
            if result:
                path=result[3]
                dataset = pd.read_csv(path, sep=';', decimal=',')
                msg=None
                return redirect(url_for("datalab"))
            else:
                msg="THERE IS NO SUCH FILE"
                return render_template("datalab.html", message=msg, filenames=filenames)

    else:
        return redirect(url_for("homepage"))

@app.route("/datalab/<varname>")
def variable(varname):
    global logged, dataset, msg, userID
    if logged==True:
        if request.method == "GET":
            if dataset is not None:
                listed=plotter(varname, dataset)
                return render_template('variable.html', message=msg, listed=listed, variable=varname)
            else:
                msg=None
                return redirect(url_for('datalab.html'))
    else:
        return redirect(url_for("homepage"))

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

def get_info(df):
    discrete=0
    continuous=0
    info=[]
    for i, item in enumerate(df.columns):
        if df[item].dtype == 'float64':
            continuous+=1
            inf=[]

            inf.append(item)
            inf.append('continuous')
            inf.append(f"Mean: {df[item].mean()}")
            inf.append(f"Q1: {df[item].quantile(0.25)}")
            inf.append(f"Median: {df[item].median()}")
            inf.append(f"Q3: {df[item].quantile(0.75)}")
            inf.append(f"Max: {df[item].max()}")
            inf.append(f"Min: {df[item].min()}")
            inf.append(f"Var: {df[item].var()}")
            inf.append(f"Std: {df[item].std()}")

            plt.figure()
            sns.distplot(df[item], hist=False)
            plt.title(f"{item} distribution")
            plt.tight_layout()
            plt.savefig(f"static/fig{i}.png", transparent=True)
            plt.close()

            randomstring = ''.join(random.choice(string.ascii_letters) for item in range(10))
            inf.append(f"static/fig{i}.png?{randomstring}")

            info.append(inf)
        elif df[item].dtype == 'int64' or df[item].dtype == 'object':
            discrete+=1
            inf=[]

            inf.append(item)
            inf.append('discrete')
            inf.append(f"Levels: {df[item].nunique()}")
            inf.append(f"Mode: {df[item].mode()[0]}")
            inf.append(f"Mode Freq.: {sum(df[item] == df[item].mode()[0])}")
            inf.append(f"Mode as %: {(sum(df[item] == df[item].mode()[0]))/len(df[item])}")

            plt.figure()
            sns.countplot(x=item, data=df)
            if df[item].dtype == 'object':
                plt.xticks(rotation=90)
            plt.title(f"{item} distribution")
            plt.tight_layout()
            plt.savefig(f"static/fig{i}.png", transparent=True)
            plt.close()
            randomstring = ''.join(random.choice(string.ascii_letters) for item in range(10))
            inf.append(f"static/fig{i}.png?{randomstring}")

            info.append(inf)

    return (info, f"Continuous Variables: {continuous}", f"Discrete Variables: {discrete}")

def plotter(var, dataset):
    listed=[]
    for i, item in enumerate(dataset.columns):
        if item!=var:
            if dataset[item].dtype=='float64' and dataset[var].dtype=='float64':
                plt.figure()
                sns.lmplot(x = item, y = var, data = dataset)
                plt.title(f"Scatter plot: {var} vs {item}")
                plt.xlabel(item)
                plt.ylabel(var)
                plt.tight_layout()
                plt.savefig(f"static/plot{i}.png", transparent=True)
                plt.close()

                randomstring = ''.join(random.choice(string.ascii_letters) for i in range(10))

                listed.append([item, f"/static/plot{i}.png?{randomstring}"])
            elif dataset[item].dtype in ['int64', 'object'] and dataset[var].dtype=='float64':
                plt.figure()
                sns.boxplot(x = item, y = var, data = dataset)
                plt.xlabel(item)
                plt.ylabel(var)
                plt.title(f"Box plot: {var} vs {item}")
                plt.xticks(rotation=90)
                plt.tight_layout()
                plt.savefig(f"static/plot{i}.png", transparent=True)
                plt.close()

                randomstring = ''.join(random.choice(string.ascii_letters) for i in range(10))

                listed.append([item, f"/static/plot{i}.png?{randomstring}"])
            elif dataset[item].dtype == 'float64' and dataset[var].dtype in ['int64', 'object']:
                plt.figure()
                sns.barplot(x=item, y=var, data=dataset, orient="h")
                plt.xlabel(item)
                plt.ylabel(var)
                plt.title(f"Bar plot: {var} vs {item}")
                plt.tight_layout()
                plt.savefig(f"static/plot{i}.png", transparent=True)
                plt.close()

                randomstring = ''.join(random.choice(string.ascii_letters) for i in range(10))

                listed.append([item, f"/static/plot{i}.png?{randomstring}"])
            elif dataset[item].dtype in ['int64', 'object'] and dataset[var].dtype in ['int64', 'object']:
                plt.figure()
                sns.countplot(x = var, hue = item, data = dataset)
                plt.xticks(rotation=90)
                plt.xlabel(var)
                plt.title(f"Count plot: {var} vs {item}")
                plt.tight_layout()
                plt.savefig(f"static/plot{i}.png", transparent=True)
                plt.close()

                randomstring = ''.join(random.choice(string.ascii_letters) for i in range(10))

                listed.append([item, f"/static/plot{i}.png?{randomstring}"])
    return listed

if __name__ == "__main__":
    app.run(debug = False)
