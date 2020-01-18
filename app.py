# # # # # # # # TO DO LIST # # # # # # # #
# # 0. Pandas Profiling as inspiration.
# # 1. Aesthetics of the App (base.html).
# # 2. Dropdown Lists instead of typing.
# # 3. Interactive Charts (d3.js?).
# # /Users/kamilkorzen/Kamil/Education/MScDSBA/3_Python_and_SQL/AutoEDA/cluster.csv

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

@app.route('/', methods = ["POST", "GET"])
def homepage():
    global logged, userID, msg, dataset
    if logged:
        if request.method == "GET":
            return render_template("homepage.html", content = logged)
        elif request.method == "POST":
            note = request.form["note"]
            connection = sqlite3.connect("data.db")
            cursor = connection.cursor()
            cursor.execute("INSERT INTO notes VALUES (NULL, ?, ?)", (userID, note))
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
                plt.title('Correlation Heatmap')
                plt.tight_layout()
                plt.savefig("static/fig.png")

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
                sns.lmplot(x = xvar, y = yvar, data = dataset)
                plt.savefig('static/fig.png')

                randomstring = ''.join(random.choice(string.ascii_letters) for item in range(10))

                msg = f"static/fig.png?{randomstring}"
            except:
                return render_template('lmplot.html', message = "Error")

            return render_template('lmplot.html', message = msg)
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

def get_info(df):
    discrete=0
    continuous=0
    info=[]
    for i, item in enumerate(df.columns):
        if df[item].dtype == 'float64':
            continuous+=1
            inf=[]

            inf.append(f"Name: {item}")
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
            plt.tight_layout()
            plt.savefig(f"static/fig{i}.png")
            randomstring = ''.join(random.choice(string.ascii_letters) for item in range(10))
            inf.append(f"static/fig{i}.png?{randomstring}")

            info.append(inf)
        elif df[item].dtype == 'int64' or df[item].dtype == 'object':
            discrete+=1
            inf=[]

            inf.append(f"Name: {item}")
            inf.append('discrete')
            inf.append(f"Number of levels: {df[item].nunique()}")
            inf.append(f"Mode: {df[item].mode()[0]}")
            inf.append(f"Mode frequency: {sum(df[item] == df[item].mode()[0])}")
            inf.append(f"Mode as %: {(sum(df[item] == df[item].mode()[0]))/len(df[item])}")

            plt.figure()
            sns.countplot(x=item, data=df)
            if df[item].dtype == 'object':
                plt.xticks(rotation=90)
            plt.tight_layout()
            plt.savefig(f"static/fig{i}.png")
            randomstring = ''.join(random.choice(string.ascii_letters) for item in range(10))
            inf.append(f"static/fig{i}.png?{randomstring}")

            info.append(inf)

    return (info, f"Number of continuous variables: {continuous}", f"Number of discrete variables: {discrete}")


if __name__ == "__main__":
    app.run(debug=True)
