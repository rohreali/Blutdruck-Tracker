import streamlit as st
import pandas as pd
from datetime import date
from github_contents import GithubContents

import streamlit as st

# Create a login form
st.title("Cardio Check")
username = st.text_input("Benutzername")
password = st.text_input("Passwort", type="password")

if st.button("Log-in"):
    # Check if the user exists
    if username in users and users[username] == password:
        st.write("Login successful!")
    else:
        st.write("Invalid username or password.")
