# AutoEDA
Assignment Project for Introduction to Python Class. Flask Application for Auto EDA.

# To Run
Download the repository and open your Terminal (MacOS) or Command Prompt (Windows OS). If you are running Anaconda, open your Anaconda Prompt and find path to repository with AutoEDA App.

If your are running the App for the first time, create new database by typing "python createdatabase.py" in your Terminal/Prompt. Skip this step if you were running the app before (or you want to keep the old database).

Type "python app.py" to run this app in debug mode. It should be availabe on your local host a few seconds after initialization. You will get an information about the host from your Terminal/Prompt (should be 127.0.0.1:5000/).

Create new account (register) or login to an existing account and explore the possibilities.

In order to Upload file, you need to type in full path for your .csv data (it doesn't have to be in the same directory as app).

Note: there is also automatically created admin account, that have access to all user's databases.

# Dependencies

Flask, sqlite3, numpy, pandas, seaborn, matplotlib.

# Authors

* Kamil Korzen (MSc Data Science @ University of Warsaw, class of '21)
* Jakub Byler (MSc Data Science @ University of Warsaw, class of '21)

App was developed as a final project for Introduction to Python course. This course is a part of the 1. semester Master's Studies in Data Science @ University of Warsaw. This project was supervised by Maciej Wilamowski, PhD.
