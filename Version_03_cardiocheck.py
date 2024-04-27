# Import necessary libraries
import streamlit as st
from datetime import datetime, date, time
import plotly.graph_objs as go
import pandas as pd
from github_contents import GithubContents
import streamlit_authenticator as stauth
import os
import base64
import requests
import bcrypt
from github import Github 


# Konstanten
USER_DATA_FILE = "user_data.csv"
USER_DATA_COLUMNS = ["username", "password_hash", "name", "vorname", "geschlecht", "geburtstag", "gewicht", "groesse"]

def init_github():
    g = Github(st.secrets["github"]["token"])
    repo = g.get_repo(f"{st.secrets['github']['owner']}/{st.secrets['github']['repo']}")
    return repo

def upload_csv_to_github(file_path, repo):
    file_name = os.path.basename(file_path)
    with open(file_path, "rb") as file:
        content = file.read()
    try:
        contents = repo.get_contents(file_name)
        repo.update_file(contents.path, "Update user data", content, contents.sha)
        st.success('CSV updated on GitHub successfully!')
    except:
        repo.create_file(file_name, "Create user data file", content)
        st.success('CSV created on GitHub successfully!')

def load_user_profiles():
    if os.path.exists(USER_DATA_FILE):
        return pd.read_csv(USER_DATA_FILE, index_col="username")
    return pd.DataFrame(columns=USER_DATA_COLUMNS).set_index("username")

def initialize_session_state():
    if 'page' not in st.session_state:
        st.session_state['page'] = 'home'
    if 'users' not in st.session_state:
        st.session_state['users'] = load_user_profiles()
    if 'measurements' not in st.session_state:
        st.session_state['measurements'] = []
    if 'current_user' not in st.session_state:
        st.session_state['current_user'] = None

initialize_session_state()

def save_user_profiles_and_upload(user_profiles):
    user_profiles.to_csv(USER_DATA_FILE)
    repo = init_github()
    upload_csv_to_github(USER_DATA_FILE, repo)

def register_user(username, password, name, vorname, geschlecht, geburtstag, gewicht, groesse):
    user_profiles = load_user_profiles()
    if username in user_profiles.index:
        st.error("Username already taken. Please choose another.")
        return False
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user_profiles.loc[username] = [hashed_pw, name, vorname, geschlecht, geburtstag, gewicht, groesse]
    save_user_profiles_and_upload(user_profiles)
    st.success("User registered successfully!")
    return True

def verify_login(username, password):
    user_profiles = load_user_profiles()
    if username in user_profiles.index and bcrypt.checkpw(password.encode('utf-8'), user_profiles.loc[username, 'password_hash'].encode('utf-8')):
        st.session_state['current_user'] = username
        return True
    st.error("Incorrect username or password.")
    return False

def user_interface():
    st.title('User Registration and Login')
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if verify_login(username, password):
            st.session_state['page'] = 'home_screen'

    if st.button("Register"):
        name = st.text_input("Name")
        vorname = st.text_input("Vorname")
        geschlecht = st.radio("Geschlecht", ['Männlich', 'Weiblich', 'Divers'])
        geburtstag = st.date_input("Geburtstag")
        gewicht = st.number_input("Gewicht (kg)", format='%f')
        groesse = st.number_input("Größe (cm)", format='%f')
        if register_user(username, password, name, vorname, geschlecht, geburtstag, gewicht, groesse):
            st.session_state['current_user'] = username
            st.session_state['page'] = 'home_screen'

if __name__== "_main_":
    user_interface()
def add_measurement(username, new_measurement):
    user_data = st.session_state['users'].get(username)
    if user_data:
        # Check if the objects are instances of date and time before conversion
        if isinstance(new_measurement['datum'], date):
            new_measurement['datum'] = new_measurement['datum'].isoformat()
        if isinstance(new_measurement['uhrzeit'], time):
            new_measurement['uhrzeit'] = new_measurement['uhrzeit'].strftime('%H:%M:%S')
        
        user_data['details']['measurements'].append(new_measurement)
        save_user_profiles_and_upload()

st.session_state['users'] = load_user_profiles()
def back_to_home():
    if st.button("Zum Home Bildschirm"):
        st.session_state['page'] = 'home_screen'

def store_detailed_user_profile(username, details):
    if username in st.session_state['users']:
        st.session_state['users'][username]['details'] = details
        save_user_profiles_and_upload()
    else:
        st.error("User not found. Please register.")

def store_additional_info(username, vorerkrankungen, medikamente, medication_times):
    user_details = st.session_state['users'][username]['details']
    user_details['vorerkrankungen'] = vorerkrankungen
    user_details['medikamente'] = medikamente
    user_details['medication_times'] = medication_times
    store_detailed_user_profile(username, user_details)

def register_user(username, password):
    if username not in st.session_state['users']:
        st.session_state['users'][username] = {
            'password': password,
            'details': {
                'measurements': [],
                'medication_plan': [],
                'fitness_activities': []
            }
        }
        save_user_profiles_and_upload()
        return True
    st.error("Benutzername bereits vergeben. Bitte wählen Sie einen anderen.")
    return False

def verify_login(username, password):
    user = st.session_state['users'].get(username)
    return user and user['password'] == password

def add_medication(username, med_name, morgens, mittags, abends, nachts):
    user_data = st.session_state['users'].get(username)
    if user_data:
        # Ensure the 'medication_plan' key exists
        if 'medication_plan' not in user_data['details']:
            user_data['details']['medication_plan'] = []
        new_medication = {
            'Medikament': med_name,
            'Morgens': morgens,
            'Mittags': mittags,
            'Abends': abends,
            'Nachts': nachts,
        }
        user_data['details']['medication_plan'].append(new_medication)
        save_user_profiles_and_upload()
        


def show_medication_plan():
    back_to_home()
    username = st.session_state.get('current_user')
    
    if not username:
        st.error("Bitte melden Sie sich an, um den Medikamentenplan zu bearbeiten.")
        return
    
    st.title('Medikamentenplan')
    user_data = st.session_state['users'][username]['details']
    medication_plan = user_data.get('medication_plan', [])
    
    # Form for new medication entry
    with st.form("medication_form"):
        med_name = st.text_input("Medikament")
        morgens = st.text_input("Morgens")
        mittags = st.text_input("Mittags")
        abends = st.text_input("Abends")
        nachts = st.text_input("Nachts")
        submit_button = st.form_submit_button("Medikament hinzufügen")
        
        if submit_button:
            add_medication(username, med_name, morgens, mittags, abends, nachts)
    
    # Display the current medication plan
    if medication_plan:
        for med in medication_plan:
            st.text(f"Medikament: {med['Medikament']}, Morgens: {med['Morgens']}, Mittags: {med['Mittags']}, Abends: {med['Abends']}, Nachts: {med['Nachts']}")
    else:
        st.write("Keine Medikamente hinzugefügt.")
        
def add_fitness_activity(username, datum, uhrzeit, dauer, intensitaet, art, kommentare):
    user_data = st.session_state['users'].get(username)
    if user_data:
        # Ensure the 'fitness_activities' key exists
        if 'fitness_activities' not in user_data['details']:
            user_data['details']['fitness_activities'] = []
        new_activity = {
            'Datum': datum.strftime('%Y-%m-%d'),
            'Uhrzeit': uhrzeit.strftime('%H:%M:%S'),
            'Dauer': dauer,
            'Intensitaet': intensitaet,
            'Art': art,
            'Kommentare': kommentare
        }
        user_data['details']['fitness_activities'].append(new_activity)
        save_user_profiles_and_upload()
        
def get_start_end_dates_from_week_number(year, week_number):
    """Returns the start and end dates of the given week number for the given year."""
    first_day_of_year = datetime(year, 1, 1)
    start_of_week = first_day_of_year + pd.Timedelta(days=(week_number - 1) * 7)
    start_of_week -= pd.Timedelta(days=start_of_week.weekday())
    end_of_week = start_of_week + pd.Timedelta(days=6)
    return start_of_week.date(), end_of_week.date()
        
def show_fitness():
    back_to_home()
    username = st.session_state.get('current_user')
    
    if not username:
        st.error("Bitte melden Sie sich an, um Fitnessdaten zu bearbeiten.")
        return
    
    st.title('Fitness')
    
    # Menu options on the side, allowing the user to select what to do
    fitness_options = ["Aktivität hinzufügen", "History"]
    choice = st.sidebar.selectbox("Fitness Optionen", fitness_options)
    
    if choice == "Aktivität hinzufügen":
        # Form for new fitness activity entry
        with st.form("fitness_form"):
            datum = st.date_input("Datum", date.today())
            uhrzeit = st.time_input("Uhrzeit", datetime.now().time())
            dauer = st.text_input("Dauer")
            intensitaet = st.text_input("Intensitaet")
            art = st.text_input("Art")
            kommentare = st.text_area("Kommentare")
            submit_button = st.form_submit_button("Speichern")
            
            if submit_button:
                add_fitness_activity(username, datum, uhrzeit, dauer, intensitaet, art, kommentare)
                st.success("Fitnessaktivität gespeichert!")
    
    elif choice == "History":
        show_fitness_history()
            
def show_fitness_history():
    username = st.session_state.get('current_user')
    st.title('Fitness History - Diese Woche')

    # Allow the user to navigate through weeks
    week_number = st.number_input('Wochennummer (1-52)', min_value=1, max_value=52, value=datetime.now().isocalendar()[1], format='%d')
    year_to_view = st.number_input('Jahr', min_value=2020, max_value=2100, value=datetime.now().year, format='%d')

    # Get the start and end dates of the specified week
    start_date, end_date = get_start_end_dates_from_week_number(year_to_view, week_number)
    st.write(f"Anzeigen der Fitnessaktivitäten für die Woche vom {start_date} bis {end_date}")

    user_data = st.session_state['users'][username]['details']
    fitness_activities = user_data.get('fitness_activities', [])

    # Create a DataFrame for all days of the week
    week_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    df_week = pd.DataFrame(week_days, columns=['Datum'])
    df_week['Art'] = ""
    df_week['Dauer'] = ""
    df_week['Intensitaet'] = ""

    # Fill the DataFrame with fitness activities for the selected week
    for activity in fitness_activities:
        activity_date = datetime.strptime(activity['Datum'], '%Y-%m-%d').date()
        if start_date <= activity_date <= end_date:
            day_name = activity_date.strftime("%a")
            idx = week_days.index(day_name)
            df_week.at[idx, 'Dauer'] = activity['Dauer']
            df_week.at[idx, 'Intensitaet'] = activity['Intensitaet']
            df_week.at[idx, 'Art'] = activity['Art']

    # Set 'Datum' as index
    df_week.set_index('Datum', inplace=True)

    # Display the DataFrame
    if not df_week.empty:
        st.table(df_week)
    else:
        st.write(f"Keine Fitnessaktivitäten für die Woche {week_number} im Jahr {year_to_view} vorhanden.")

# Function to store emergency numbers
def store_emergency_numbers(username, emergency_numbers):
    user_details = st.session_state['users'][username]['details']
    user_details['emergency_numbers'] = emergency_numbers
    store_detailed_user_profile(username, user_details)

# Function to display the emergency numbers page
def show_emergency_numbers():
    back_to_home()
    username = st.session_state.get('current_user')
    
    if not username:
        st.error("Bitte melden Sie sich an, um eigene Notfallnummern hinzuzufügen.")
        return
    
    st.title('Notfallnummern')
    
    # Fixed emergency numbers display
    st.write("Krankenhaus: 114")
    st.write("Polizei: 117")
    st.write("Feuerwehr: 118")
    st.write("Rega: 1414")
    
    # Form for user's personal emergency numbers
    user_data = st.session_state['users'][username]['details']
    if 'emergency_numbers' not in user_data:
        user_data['emergency_numbers'] = {}

    emergency_numbers = user_data['emergency_numbers']

    with st.form("emergency_numbers_form"):
        for number_type in ['Hausarzt', 'Eigene']:
            emergency_numbers[number_type] = st.text_input(number_type, emergency_numbers.get(number_type, ''))
        submit_button = st.form_submit_button("Speichern")
        
        if submit_button:
            user_data['emergency_numbers'] = emergency_numbers
            save_user_profiles_and_upload()
            st.success("Persönliche Notfallnummern gespeichert!")

    # Display only the saved personal emergency numbers
    if emergency_numbers:
        st.subheader("Gespeicherte Notfallnummern:")
        for number_type, number in emergency_numbers.items():
            if number:  # Only display if number is not empty
                st.write(f"{number_type}: {number}")
                
def save_info_text(username, info_type, text):
    user_data = st.session_state['users'].get(username)
    if user_data:
        user_data['details'][info_type] = text
        save_user_profiles_and_upload()

def show_info_page():
    back_to_home()
    username = st.session_state.get('current_user')
    if not username:
        st.error("Bitte melden Sie sich an.")
        return
    
    st.title('Gesundheitsinformationen')
    info_options = st.sidebar.selectbox("Kategorie auswählen", ["Blutdruck", "Fitness"])

    # Lade den gespeicherten Text aus dem Benutzerprofil
    user_details = st.session_state['users'].get(username, {}).get('details', {})
    saved_text = user_details.get(f'{info_options.lower()}_info', 'Hier Info-Text eingeben')

    # Texteingabe für den Infotext
    text_input = st.text_area(f"Informationen zu {info_options}", value=saved_text)

    # Speicherbutton
    if st.button('Speichern'):
        save_info_text(username, f'{info_options.lower()}_info', text_input)
        st.success(f"Informationen zu {info_options} gespeichert!")
        
def show_registration_form():
    with st.form("register_form"):
        st.write("Registrieren")
        username = st.text_input("Benutzername")
        password = st.text_input("Passwort", type="password")
        name = st.text_input("Name")
        vorname = st.text_input("Vorname")
        geschlecht = st.radio("Geschlecht", ['Männlich', 'Weiblich', 'Divers'])
        geburtstag = st.date_input("Geburtstag")
        gewicht = st.number_input("Gewicht (kg)", format='%f')
        groesse = st.number_input("Größe (cm)", format='%f')
        
        # Überprüfen der Eingaben vor dem Senden
        if st.form_submit_button("Register"):
            st.write("Eingabeüberprüfung:")
            st.write("Username:", username, type(username))
            st.write("Password:", password, type(password))
            st.write("Name:", name, type(name))
            st.write("Vorname:", vorname, type(vorname))
            st.write("Geschlecht:", geschlecht, type(geschlecht))
            st.write("Geburtstag:", geburtstag, type(geburtstag))
            st.write("Gewicht:", gewicht, type(gewicht))
            st.write("Größe:", groesse, type(groesse))

            if register_user(username, password, name, vorname, geschlecht, geburtstag, gewicht, groesse):
                st.session_state['current_user'] = username
                st.session_state['page'] = 'detailed_registration'
def show_login_form():
    with st.form("login_form"):
        st.write("Einloggen")
        username = st.text_input("Benutzername")
        password = st.text_input("Passwort", type="password")
        if st.form_submit_button("Login"):
            if verify_login(username, password):
                st.session_state['current_user'] = username
                st.session_state['page'] = 'home_screen'
            else:
                st.error("Benutzername oder Passwort ist falsch.")

def show_home():
    st.title('Herzlich Willkommen bei CardioCheck')
    st.subheader('Ihr Blutdruck Tagebuch')
    action = st.selectbox("Aktion wählen", ["Einloggen", "Registrieren"])
    if action == "Registrieren":
        show_registration_form()
    elif action == "Einloggen":
        show_login_form()

def show_home_screen():
    back_to_home()
    st.title('CardioCheck')
    st.markdown("## Home Bildschirm")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Profil"):
            st.session_state['page'] = 'profile'
        if st.button("Fitness"):
            st.session_state['page'] = 'Fitness'
    with col2:
        if st.button("Messungen"):
            st.session_state['page'] = 'measurements'
        if st.button("Notfall Nr."):
            st.session_state['page'] = 'emergency_numbers'
    with col3:
        if st.button("Medi-Plan"):
            st.session_state['page'] = 'medication-plan'
        if st.button("Infos"):
            st.session_state['page'] = 'infos'

def show_detailed_registration():
    username = st.session_state.get('current_user', None)
    if not username:
        st.error("User not found. Please register.")
        st.session_state['page'] = 'home'
        return

    with st.form("user_detailed_registration"):
        st.title('CardioCheck - Detaillierte Registrierung')
        st.subheader('Bitte füllen Sie die weiteren Felder aus')
        name = st.text_input("Name")
        vorname = st.text_input("Vorname")
        geschlecht = st.radio("Geschlecht", ['Männlich', 'Weiblich', 'Divers'])
        geburtstag = st.date_input("Geburtstag", datetime.today())  # Corrected line here
        gewicht = st.number_input("Gewicht (kg)", min_value=1.0)
        groesse = st.number_input("Größe (cm)", min_value=1.0)
        
        if st.form_submit_button("Weiter"):  # Added submit button
            user_details = {
                'name': name,
                'vorname': vorname,
                'geschlecht': geschlecht,
                'geburtstag': geburtstag.strftime('%Y-%m-%d'),
                'gewicht': gewicht,
                'groesse': groesse,
                'measurements': []
            }
            store_detailed_user_profile(username, user_details)
            st.session_state['page'] = 'additional_info'

def show_additional_info():
    back_to_home()
    username = st.session_state.get('current_user')
    st.title('Weitere Angaben')
    with st.form("additional_info"):
        vorerkrankungen = st.text_area("Vorerkrankungen")
        medikamente = st.text_area("Medikamente")
        medication_times = {
            'morgens': st.checkbox('morgens'),
            'mittags': st.checkbox('mittags'),
            'abends': st.checkbox('abends'),
            'nachts': st.checkbox('nachts')
        }
        if st.form_submit_button("Fertig"):
            store_additional_info(username, vorerkrankungen, medikamente, medication_times)
            st.success("Weitere Angaben gespeichert! Registrierung abgeschlossen.")

def show_profile():
    back_to_home()
    st.title('Profil')
    current_user = st.session_state.get('current_user', None)
    if current_user:
        user_details = st.session_state['users'].get(current_user, {}).get('details', {})
        gewicht = user_details.get('gewicht', 'Nicht angegeben')
        groesse = user_details.get('groesse', 'Nicht angegeben')
        st.markdown(f"**Gewicht:** {gewicht} kg")
        st.markdown(f"**Größe:** {groesse} cm")
    with st.form("zielwerte_form"):
        st.subheader('Zielwerte')
        st.text_input("Systolisch")
        st.text_input("Diastolisch")
        st.text_input("Puls")
        st.selectbox("Auswahl", ['Option 1', 'Option 2'])
        if st.form_submit_button("Ändern"):
            st.success("Zielwerte aktualisiert!")
    st.markdown("Systolisch: 120 mmHg")
    st.markdown("Diastolisch: 80 mmHg")
    st.markdown("Puls: 60 - 90")
    
def show_trend_analysis(measurements):
    # Prepare data for plotting
    dates_times = [f"{m['datum']} {m['uhrzeit']}" for m in measurements]  # Use f-string for safe concatenation

    systolic_values = [m['systolic'] for m in measurements]
    diastolic_values = [m['diastolic'] for m in measurements]

    # Create traces for the systolic and diastolic values
    trace1 = go.Bar(
        x=dates_times,
        y=systolic_values,
        name='Systolisch'
    )
    
    trace2 = go.Bar(
        x=dates_times,
        y=diastolic_values,
        name='Diastolisch'
    )

    # Layout configuration
    layout = go.Layout(
        title='Trendanalyse für Blutdruckwerte',
        xaxis=dict(title='Datum und Uhrzeit'),
        yaxis=dict(title='Blutdruckwert'),
        barmode='group'
    )

    # Combine traces into a figure
    fig = go.Figure(data=[trace1, trace2], layout=layout)

    # Display the figure
    st.plotly_chart(fig, use_container_width=True)

    
def show_measurements():
    back_to_home()
    st.title('Messungen')

    # Menu options on the side, allowing the user to select what to do
    menu_options = ["Neue Messung hinzufügen", "History", "Trendanalyse"]
    choice = st.sidebar.selectbox("Optionen", menu_options)
    username = st.session_state['current_user']

    if choice == "Neue Messung hinzufügen":

        if not username:
            st.error('Bitte melden Sie sich an, um Messungen hinzuzufügen.')
            return
        
        with st.form("new_measurement"):
            # Correct use of date and time
            datum = st.date_input("Datum", date.today())
            uhrzeit = st.time_input("Uhrzeit", datetime.now().time())
            systolic_value = st.number_input("Wert Systolisch (mmHg)", min_value=0, max_value=300, step=1)
            diastolic_value = st.number_input("Wert Diastolisch (mmHg)", min_value=0, max_value=300, step=1)
            pulse = st.number_input("Puls (bpm)", min_value=0, max_value=200, step=1)
            comments = st.text_area("Sonstiges/Bemerkungen")
            submit_measurement = st.form_submit_button("Speichern")

            if submit_measurement:
                # Prepare the measurement data to be saved
                new_measurement = {
                    'datum': datum.isoformat(),  # Convert date to string
                    'uhrzeit': uhrzeit.strftime('%H:%M:%S'),  # Convert time to string
                    'systolic': systolic_value,
                    'diastolic': diastolic_value,
                    'pulse': pulse,
                    'comments': comments
                }
                add_measurement(username, new_measurement)
                st.success("Messung gespeichert!")
                # Reload the measurements to the session state after saving
                st.session_state['measurements'] = st.session_state['users'][username]['details']['measurements']

    elif choice == "History":
        st.subheader("History")
        # Ensure we're displaying the measurements from the user's profile
        user_measurements = st.session_state['users'][username]['details']['measurements']
        for measurement in user_measurements:
            date_str = measurement['datum']
            time_str = measurement['uhrzeit']
            st.markdown(f"""
                `{date_str} {time_str}` **Systolisch:** `{measurement['systolic']} mmHg` \
                **Diastolisch:** `{measurement['diastolic']} mmHg` **Puls:** `{measurement['pulse']} bpm` \
                **Bemerkungen:** `{measurement['comments']}`
            """)

    elif choice == "Trendanalyse":
        st.subheader("Trendanalyse")
        # Display the trend analysis using measurements from the user's profile
        user_measurements = st.session_state['users'][username]['details']['measurements']
        show_trend_analysis(user_measurements)
        

# Display pages based on session state
if st.session_state['page'] == 'home':
    show_home()
elif st.session_state['page'] == 'detailed_registration':
    show_detailed_registration()
elif st.session_state['page'] == 'additional_info':
    show_additional_info()
elif st.session_state['page'] == 'home_screen':
    show_home_screen()
elif st.session_state['page'] == 'profile':
    show_profile()
elif st.session_state['page'] == 'measurements':
    show_measurements()
elif st.session_state['page'] == 'medication-plan':
    show_medication_plan()
elif st.session_state['page'] == 'Fitness':
    show_fitness()
elif st.session_state['page'] == 'emergency_numbers':
    show_emergency_numbers()
elif st.session_state['page'] == 'infos':
    show_info_page()            
