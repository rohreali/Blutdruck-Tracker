import streamlit as st
import datetime
from datetime import datetime, timedelta
import plotly.graph_objs as go
import pandas as pd
from github_contents import GithubContents
import streamlit_authenticator as stauth
import os
import base64
import requests
import bcrypt
from github import Github 
import csv
from io import StringIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from io import BytesIO
import numpy as np
import requests
from PIL import Image


# Konstanten
USER_DATA_FILE = "user_data.csv"
USER_DATA_COLUMNS = ["username", "password_hash", "name", "vorname", "geschlecht", "geburtstag", "gewicht", "groesse"]
MEASUREMENTS_DATA_FILE = "measurements_data.csv"
MEASUREMENTS_DATA_COLUMNS = ["username", "datum", "uhrzeit", "systolic", "diastolic", "pulse", "comments"]
MEDICATION_DATA_FILE = "medication_data.csv"
MEDICATION_DATA_COLUMNS = ["username", "Medikament", "morgens", "mittags", "abends", "nachts"]
FITNESS_DATA_FILE = "fitness_data.csv"
FITNESS_DATA_COLUMNS= [ "username", "datum", "uhrzeit", "dauer", "intensitaet", "Art", "Kommentare"]
EMERGENCY_NUMBERS_FILE = "emergency_numbers.csv"
EMERGENCY_NUMBERS_COLUMNS = ["username", "type", "number"]

#alles zu Login, Registrierung und Home Bildschirm

def display_logo(in_sidebar=False):
    base_path = os.path.dirname(__file__)  # Basispfad für relative Pfade
    logo_path = os.path.join(base_path, "Logo.png")  # Pfad zur Logo-Datei
    if in_sidebar:
        # Anzeigen des Logos in der Sidebar
        st.sidebar.image(logo_path, width=100)  # Anpassung der Breite nach Bedarf
    else:
        # Anzeigen des Logos im Hauptbereich
        col1, col2, col3 = st.columns([1,2,1])
        with col3:
            st.image(logo_path, width=150)

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
    if 'medications' not in st.session_state:
        st.session_state['medications'] = []
    if 'fitness_activities' not in st.session_state:
        st.session_state['fitness_activities'] = []

initialize_session_state()

def save_user_profiles_and_upload(user_profiles):
    try:
        # Versuche, die CSV lokal zu speichern
        user_profiles.to_csv(USER_DATA_FILE)
        st.success('Lokales Speichern der Benutzerdaten erfolgreich!')
    except Exception as e:
        st.error(f'Fehler beim lokalen Speichern der Benutzerdaten: {e}')
        return False  # Beendet die Funktion frühzeitig, wenn das lokale Speichern fehlschlägt

    try:
        # Initialisiere GitHub-Repository
        repo = init_github()
        upload_csv_to_github(USER_DATA_FILE, repo)
        return True
    except Exception as e:
        st.error(f'Fehler beim Hochladen der Daten auf GitHub: {e}')
        return False

def register_user(username, password, name, vorname, geschlecht, geburtstag, gewicht, groesse):
    user_profiles = load_user_profiles()
    if username in user_profiles.index:
        st.error("Benutzername bereits vergeben. Bitte wählen Sie einen anderen.")
        return False

    try:
        # Versuch, das Geburtsdatum zu validieren und zu formatieren
        geburtstag = datetime.strptime(geburtstag, '%d-%m-%Y').strftime('%Y-%m-%d')
    except ValueError:
        st.error("Das Geburtsdatum muss im Format TT-MM-JJJJ eingegeben werden.")
        return False

    # Passworthash erzeugen
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Vorbereitung der Benutzerdetails für den neuen Benutzer
    user_details = {
        'password_hash': hashed_pw,
        'name': name,
        'vorname': vorname,
        'geschlecht': geschlecht,
        'geburtstag': geburtstag,
        'gewicht': gewicht,
        'groesse': groesse
    }

    # Hinzufügen der neuen Benutzerdaten zum DataFrame
    user_profiles.loc[username] = user_details
    if save_user_profiles_and_upload(user_profiles):
        st.session_state['users'] = user_profiles  # Benutzerdaten in den Session State laden
        st.success("Benutzer erfolgreich registriert!")
        return True
    else:
        return False

def verify_login(username, password):
    user_profiles = load_user_profiles()
    if username in user_profiles.index:
        # Hier nehmen wir an, dass der Hash als regulärer String gelesen wird
        stored_hash_str = user_profiles.loc[username, 'password_hash']
        if stored_hash_str.startswith("b'") and stored_hash_str.endswith("'"):
            # Entfernen Sie die b''-Klammern und konvertieren Sie den String in Bytes
            stored_hash = stored_hash_str[2:-1].encode().decode('unicode_escape').encode('latin1')
        else:
            # Wenn der String nicht mit b'' beginnt und endet, versuchen Sie, ihn direkt zu verwenden
            stored_hash = stored_hash_str.encode('latin1')
        
        # Verwenden Sie bcrypt, um das eingegebene Passwort zu überprüfen
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            st.session_state['current_user'] = username
            return True
    st.error("Incorrect username or password.")
    return False
    
def user_interface():
    display_logo()
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
        tag = st.text_input("Tag", max_chars=2)
        monat = st.text_input("Monat", max_chars=2)
        jahr = st.text_input("Jahr", max_chars=4)
        # Stelle sicher, dass das Format TT-MM-JJJJ eingehalten wird
        geburtstag = f"{tag.zfill(2)}-{monat.zfill(2)}-{jahr}"
        gewicht = st.number_input("Gewicht (kg)", format='%f')
        groesse = st.number_input("Größe (cm)", format='%f')
        if tag and monat and jahr:
            if register_user(username, password, name, vorname, geschlecht, geburtstag, gewicht, groesse):
                st.session_state['current_user'] = username
                st.session_state['page'] = 'home_screen'
    
if __name__== "_main_":
    user_interface()

def show_registration_form():
    with st.form("registration_form"):
        st.write("Registrieren")
        username = st.text_input("Benutzername")
        password = st.text_input("Passwort", type="password")
        name = st.text_input("Name")
        vorname = st.text_input("Vorname")
        geschlecht = st.radio("Geschlecht", ['Männlich', 'Weiblich', 'Divers'])
        geburtstag = st.date_input("Geburtstag", min_value=datetime(1920, 1, 1))
        gewicht = st.number_input("Gewicht (kg)", format='%f')
        groesse = st.number_input("Größe (cm)", format='%f')
        submit_button = st.form_submit_button("Registrieren")

        if submit_button:
            geburtstag_str = geburtstag.strftime('%d-%m-%Y')
            if register_user(username, password, name, vorname, geschlecht, geburtstag_str, gewicht, groesse):
                st.success("Registrierung erfolgreich!")
            else:
                st.error("Registrierung fehlgeschlagen. Bitte überprüfen Sie die Eingaben.")       
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

#Home Bildschirm
def show_home():
    display_logo()
    st.title('Herzlich Willkommen bei CardioCheck')
    st.subheader('Ihr Blutdruck Tagebuch')
    action = st.selectbox("Aktion wählen", ["Einloggen", "Registrieren"])
    if action == "Registrieren":
        show_registration_form()
    elif action == "Einloggen":
        show_login_form()
def logout():
    # Setzt die session_state Variablen zurück
    st.session_state['current_user'] = None
    st.session_state['page'] = 'home'
    st.info("Sie wurden erfolgreich ausgeloggt.")        

def show_home_screen():
    display_logo()
    st.title('CardioCheck')
    st.markdown("## Willkommen beim CardioCheck Dashboard")

    # Definiert das Layout für die Buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button ("👤 Profil"):
            st.session_state['page']='profile'
        if st.button("💪 Fitness"):
            st.session_state['page']= 'Fitness'
    with col2:
        if st.button("📊 Messungen"):
            st.session_state['page']='measurements'
        if st.button("🆘 Notfall Nr."):
            st.session_state['page']='emergency_numbers'
    with col3:
        if st.button("💊 Medikamenten Plan"):
            st.session_state['page']= 'medication-plan'
        if st.button("ℹ️ Infos"):  
            st.session_state['page']='infos'

    # Spacer zur besseren Positionierung des Logout-Buttons
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")

    # Logout-Button am unteren Ende der Seite
    if st.button("🚪 Logout"):
        logout()

    # Anwenden von zusätzlichem CSS für Stilverbesserungen
    st.markdown("""
        <style>
        .stButton>button {
            width: 100%;
            border-radius: 10px;
            border: 1px solid #FF807A;
            color: #ffffff;
            font-size: 28px;  /* Erhöhte Schriftgröße für optimale Lesbarkeit */
            height: 4.5em;  /* Erhöht die Höhe des Buttons, um den größeren Text aufzunehmen */
            padding: 0.25em 0.5em;
            background-color: #FF807A;
            transition: all 0.3s;
            cursor: pointer;
            line-height: 1.6;
        }
        .stButton>button:hover {
            border: 1px solid #FF6859;
            background-color: #FF6859;
        }
        /* Größere Icons */
        .stButton>button::before {
            font-size: 1.5em; /* Größere Icons */
        }
        </style>
    """, unsafe_allow_html=True)

#hier kommt der Code für Profil 

def show_profile():
    display_logo()
    if st.button("Zurück zum Homebildschirm"):  # Dies fügt den Zurück-Button hinzu
        back_to_home()
        
    st.title('Profil')
    current_user = st.session_state.get('current_user', None)
    if current_user:
        user_profiles = st.session_state['users']
        if current_user in user_profiles.index:
            user_details = user_profiles.loc[current_user]

            # Display user details except for the password
            st.markdown("### Benutzerdetails")
            for detail, value in user_details.items():
                if detail != 'password_hash':  # Exclude password from display
                    if detail == 'gewicht':
                        st.markdown(f"*Gewicht:* {value} kg")  # Add unit kg
                    elif detail == 'groesse':
                        st.markdown(f"*Größe:* {value} cm")  # Add unit cm
                    else:
                        st.markdown(f"*{detail.title()}:* {value}")

            # Allow user to update weight and height
            st.markdown("### Aktualisieren Sie Ihr Gewicht und Größe")
            gewicht = st.number_input("Gewicht (kg)", value=float(user_details['gewicht']) if user_details['gewicht'] else 0, format='%f')
            groesse = st.number_input("Größe (cm)", value=float(user_details['groesse']) if user_details['groesse'] else 0, format='%f')
            if st.button("Update"):
                user_profiles.at[current_user, 'gewicht'] = gewicht
                user_profiles.at[current_user, 'groesse'] = groesse
                save_user_profiles_and_upload(user_profiles)
                st.success("Profil erfolgreich aktualisiert!")
        else:
            st.error("Benutzer nicht gefunden.")
    else:
        st.error("Bitte melden Sie sich an, um Ihr Profil zu sehen.")

    # Display norm values
    st.subheader('Normwerte')
    st.markdown("Systolisch: 120 mmHg")
    st.markdown("Diastolisch: 80 mmHg")
    st.markdown("Puls: 60 - 80")
    
#Ende vom Code Profil

#Hier Alles zu Messungen
def back_to_home():
    st.session_state['page'] = 'home_screen'

def get_start_end_dates_from_week_number(year, week_number):
    first_day_of_year = datetime(year, 1, 1)
    start_of_week = first_day_of_year + timedelta(days=(week_number - 1) * 7)
    start_of_week -= timedelta(days=start_of_week.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week.date(), end_of_week.date()

def add_measurement(datum, uhrzeit, systolic, diastolic, pulse, comments):
    current_user = st.session_state.get('current_user')
    if 'measurements' not in st.session_state:
        st.session_state['measurements'] = []

    # Erstelle eine neue Messung
    new_measurement = {
        "username": current_user,  
        "datum": datum.strftime('%Y-%m-%d'),
        "uhrzeit": uhrzeit.strftime('%H:%M'),
        "systolic": systolic,
        "diastolic": diastolic,
        "pulse": pulse,
        "comments": comments
    }

    # Überprüfen, ob diese Messung bereits existiert
    if new_measurement not in st.session_state['measurements']:
        st.session_state['measurements'].append(new_measurement)
        save_measurements_to_github()
    else:
        st.warning("Diese Messung wurde bereits hinzugefügt.")

def save_measurements_to_github():
    measurement_list = st.session_state.get('measurements', [])
    measurement_df = pd.DataFrame(measurement_list)
    measurement_df.to_csv(MEASUREMENTS_DATA_FILE, index=False)

    g = Github(st.secrets["github"]["token"])
    repo = g.get_repo(f"{st.secrets['github']['owner']}/{st.secrets['github']['repo']}")

    try:
        contents = repo.get_contents(MEASUREMENTS_DATA_FILE)
        updated_csv = contents.decoded_content.decode("utf-8") + "\n" + measurement_df.to_csv(index=False)
        repo.update_file(contents.path, "Update measurement data", updated_csv, contents.sha)
        st.success('Measurement data updated on GitHub successfully!')
    except Exception as e:
        repo.create_file(MEASUREMENTS_DATA_FILE, "Create measurement data file", measurement_df.to_csv(index=False))
        st.success('Measurement CSV created on GitHub successfully!')

def show_measurement_options():
    display_logo(in_sidebar=True)
    st.sidebar.title("Messungen Optionen")
    option = st.sidebar.radio(
        "", ["Neue Messung hinzufügen", "Messhistorie anzeigen", "Trendanalyse"])
    if option == "Neue Messung hinzufügen":
        show_add_measurement_form()
    elif option == "Messhistorie anzeigen":
        show_measurement_history_weekly()
    elif option == "Trendanalyse":
        show_trend_analysis()
def show_add_measurement_form():
    display_logo()
    if st.button('Zurück zum Homebildschirm'):
        back_to_home()
    st.title('Messungen')
    with st.form("measurement_form"):
        datum = st.date_input("Datum", value=datetime.today())
        # Standard-Uhrzeit ohne Schrittweite einstellen
        default_time = datetime.now().time()  # Aktuelle Uhrzeit als Standardwert
        uhrzeit = st.time_input("Uhrzeit", value=default_time)
        
        wert_systolisch = st.number_input("Wert Systolisch (mmHg)", min_value=0)
        wert_diastolisch = st.number_input("Wert Diastolisch (mmHg)", min_value=0)
        puls = st.number_input("Puls (bpm)", min_value=0)
        kommentare = st.text_area("Kommentare")
        submit_button = st.form_submit_button("Messungen speichern")

        if submit_button:
            current_user = st.session_state.get('current_user')
            if current_user is not None:
                add_measurement(datum, uhrzeit, wert_systolisch, wert_diastolisch, puls, kommentare)
                st.success("Messungen erfolgreich gespeichert!")
            else:
                st.error("Sie sind nicht angemeldet. Bitte melden Sie sich an, um Messungen zu speichern.")

def load_measurement_data():
    repo = init_github()
    current_user = st.session_state.get('current_user')
    try:
        contents = repo.get_contents(MEASUREMENTS_DATA_FILE)
        csv_content = contents.decoded_content.decode("utf-8")
        data = pd.read_csv(StringIO(csv_content))
        
        # Filtern der Daten, um nur die des aktuellen Benutzers anzuzeigen
        user_data = data[data['username'] == current_user]
        
        # Entfernen von Duplikaten
        user_data = user_data.drop_duplicates(subset=["datum", "uhrzeit", "systolic", "diastolic", "pulse", "comments"])
        
        return user_data
    except Exception as e:
        st.error(f"Fehler beim Laden der Messdaten: {str(e)}")
        return pd.DataFrame()

def show_measurement_history_weekly():
    display_logo()
    username = st.session_state.get('current_user')
    if not username:
        st.error("Bitte melden Sie sich an, um Ihre Messungen zu sehen.")
        return

    if st.button('Zurück zum Homebildschirm'):
        back_to_home()
    st.title('Messhistorie - Diese Woche')

    week_number = st.number_input('Wochennummer (1-52)', min_value=1, max_value=52, value=datetime.now().isocalendar()[1])
    year_to_view = st.number_input('Jahr', min_value=2020, max_value=datetime.now().year, value=datetime.now().year)

    start_date, end_date = get_start_end_dates_from_week_number(year_to_view, week_number)
    st.write(f"Anzeigen der Messungen für die Woche vom {start_date} bis {end_date}")

    measurement_data = load_measurement_data()

    if not measurement_data.empty:
        weekly_data = measurement_data[(measurement_data['datum'] >= str(start_date)) & (measurement_data['datum'] <= str(end_date))]

        # Dictionary zum Sammeln der Messungen für jeden Wochentag initialisieren
        daily_measurements = {day: [] for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']}

        # Messungen nach Wochentagen gruppieren
        for activity in weekly_data.itertuples():
            activity_date = datetime.strptime(activity.datum, '%Y-%m-%d').date()
            day_name = activity_date.strftime("%a")
            daily_measurements[day_name].append(activity)

        # DataFrame für die Anzeige vorbereiten
        df_week = pd.DataFrame()

        # Messungen für jeden Wochentag in den DataFrame einfügen
        for day, measurements in daily_measurements.items():
            day_data = pd.DataFrame([{
                'Datum': measurement.datum,
                'Uhrzeit': measurement.uhrzeit,
                'Systolisch': measurement.systolic,
                'Diastolisch': measurement.diastolic,
                'Puls': measurement.pulse,
                'Kommentare': measurement.comments
            } for measurement in measurements])
            df_week = pd.concat([df_week, day_data], ignore_index=True)

        # DataFrame anzeigen
        st.table(df_week)

        # Code für den Download-Button
        pdf_file = create_measurement_pdf(df_week)
        st.download_button(
            label="Download Messdaten PDF",
            data=pdf_file,
            file_name="messdaten.pdf",
            mime='application/pdf'
        )
    else:
        st.write("Keine Daten zum Herunterladen verfügbar.")

def show_trend_analysis():
    display_logo()
    # Sicherstellen, dass der Nutzer angemeldet ist
    current_user = st.session_state.get('current_user')
    if not current_user:
        st.error("Bitte melden Sie sich an, um die Trendanalyse zu sehen.")
        return
    if st.button('Zurück zum Homebildschirm'):
        back_to_home()
    st.title('Trendanalyse der Messwerte')

    # Laden der Messdaten für den angemeldeten Nutzer
    measurement_data = load_measurement_data()
    user_measurements = measurement_data[measurement_data['username'] == current_user]

    if user_measurements.empty:
        st.write("Es liegen keine Messdaten zur Analyse vor.")
        return

    # Umwandeln der Datums- und Zeitangaben in Python datetime Objekte für die Analyse
    user_measurements['datetime'] = pd.to_datetime(user_measurements['datum'] + ' ' + user_measurements['uhrzeit'])

    # Datentypen der Messwerte sicherstellen
    user_measurements['systolic'] = pd.to_numeric(user_measurements['systolic'], errors='coerce')
    user_measurements['diastolic'] = pd.to_numeric(user_measurements['diastolic'], errors='coerce')

    # Sortieren der Messungen nach Datum und Zeit
    user_measurements.sort_values(by='datetime', ascending=True, inplace=True)

    # Erstellen der Diagramme für Systolischen Druck, Diastolischen Druck und Puls
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=user_measurements['datetime'], y=user_measurements['systolic'], mode='lines+markers', name='Systolisch'))
    fig.add_trace(go.Scatter(x=user_measurements['datetime'], y=user_measurements['diastolic'], mode='lines+markers', name='Diastolisch'))
    fig.add_trace(go.Scatter(x=user_measurements['datetime'], y=user_measurements['pulse'], mode='lines+markers', name='Puls'))

    # Hinzufügen von roten Markierungen für alarmierende Werte
    high_risk = user_measurements[(user_measurements['systolic'] >= 180) | (user_measurements['diastolic'] >= 110)]
    low_risk = user_measurements[(user_measurements['systolic'] <= 90) | (user_measurements['diastolic'] <= 60)]

    fig.add_trace(go.Scatter(x=high_risk['datetime'], y=high_risk['systolic'], mode='markers', name='Hoher Systolischer Wert', marker=dict(color='red', size=10)))
    fig.add_trace(go.Scatter(x=high_risk['datetime'], y=high_risk['diastolic'], mode='markers', name='Hoher Diastolischer Wert', marker=dict(color='red', size=10)))
    fig.add_trace(go.Scatter(x=low_risk['datetime'], y=low_risk['systolic'], mode='markers', name='Niedriger Systolischer Wert', marker=dict(color='blue', size=10)))
    fig.add_trace(go.Scatter(x=low_risk['datetime'], y=low_risk['diastolic'], mode='markers', name='Niedriger Diastolischer Wert', marker=dict(color='blue', size=10)))

    # Diagramm Layout anpassen
    fig.update_layout(title='Trendanalyse der Messwerte über die Zeit',
                      xaxis_title='Datum und Uhrzeit',
                      yaxis_title='Messwerte',
                      legend_title='Messwerte',
                      margin=dict(l=0, r=0, t=30, b=0))

    # Diagramm anzeigen
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    <div style='background-color: #ffcccc; padding: 10px; border-radius: 5px;'>
    <p style='color: red;'>Bei extrem hohen Werten über 180/110mmHg oder bei extrem tiefen Werten unter 90/60mmHg handelt es sich um Extremwerte und Sie sollten sofort Ihren Arzt kontaktieren.</p>
    </div>
    """, unsafe_allow_html=True)

def create_measurement_pdf(measurement_data):
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    title = Paragraph("Messdaten Report", styles['Title'])
    elements.append(title)

    # Überprüfen Sie die Spaltennamen
    data = [["Datum", "Uhrzeit", "Systolisch", "Diastolisch", "Puls", "Kommentare"]]
    for index, row in measurement_data.iterrows():
        data.append([
            row['Datum'], 
            row['Uhrzeit'], 
            row['Systolisch'], 
            row['Diastolisch'], 
            row['Puls'], 
            row['Kommentare'] or ""
        ])

    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BOX', (0,0), (-1,-1), 2, colors.black),
    ]))
    elements.append(t)
    
    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer


#hier alles zu Messungen fertig

#hier kommt Medi-Plan

def back_to_home():
    st.session_state['page'] = 'home_screen'
    
def add_medication(username, med_name, morgens, mittags, abends, nachts):
    if 'medications' not in st.session_state:
        st.session_state['medications'] = []

    # Erstelle ein neues Medikament
    new_medication = {
        "username": username,
        "med_name": med_name,
        "morgens": morgens,
        "mittags": mittags,
        "abends": abends,
        "nachts": nachts
    }

    # Überprüfen, ob dieses Medikament bereits existiert
    if new_medication not in st.session_state['medications']:
        st.session_state['medications'].append(new_medication)
        save_medications_to_github()
    else:
        st.warning("Dieses Medikament wurde bereits hinzugefügt.")

def save_medications_to_github():
    medication_list = st.session_state['medications']
    medication_df = pd.DataFrame(medication_list)
    medication_df.to_csv(MEDICATION_DATA_FILE, index=False)
    
    g = Github(st.secrets["github"]["token"])
    repo = g.get_repo(f"{st.secrets['github']['owner']}/{st.secrets['github']['repo']}")

    try:
        contents = repo.get_contents(MEDICATION_DATA_FILE)
        updated_csv = contents.decoded_content.decode("utf-8") + "\n" + medication_df.to_csv(index=False)
        repo.update_file(contents.path, "Update medication data", updated_csv, contents.sha)
        st.success('Medication data updated on GitHub successfully!')
    except Exception as e:
        repo.create_file(MEDICATION_DATA_FILE, "Create medication data file", medication_df.to_csv(index=False))
        st.success('Medication CSV created on GitHub successfully!')

def show_medication_plan():
    display_logo()
    display_logo(in_sidebar=True)
    st.sidebar.title("Optionen")
    option = st.sidebar.radio("", ["Neues Medikament hinzufügen", "Medikamentenplan anzeigen"])
    if option == "Neues Medikament hinzufügen":
        if st.button('Zurück zum Homebildschirm'):
            back_to_home()
        st.title('Medikamentenplan')
        with st.form("medication_form"):
            med_name = st.text_input("Medikament")
            morgens = st.number_input("Morgens", step=1, min_value=0)
            mittags = st.number_input("Mittags", step=1, min_value=0)
            abends = st.number_input("Abends", step=1, min_value=0)
            nachts = st.number_input("Nachts", step=1, min_value=0)
            submit_button = st.form_submit_button("Medikament hinzufügen")
        
        if submit_button:
            current_user = st.session_state.get('current_user')
            if current_user is not None:
                add_medication(current_user, med_name, morgens, mittags, abends, nachts)
                st.success("Medikament erfolgreich hinzugefügt!")
            else:
                st.error("Sie sind nicht angemeldet. Bitte melden Sie sich an, um Medikamente hinzuzufügen.")
        
    elif option == "Medikamentenplan anzeigen":
        if st.button('Zurück zum Homebildschirm'):
            back_to_home()
        show_medication_list()

def load_medication_data():
    current_user = st.session_state.get('current_user')
    if current_user is None:
        st.error("Sie sind nicht angemeldet. Bitte melden Sie sich an, um den Medikamentenplan anzuzeigen.")
        return pd.DataFrame()

    repo = init_github()
    try:
        contents = repo.get_contents(MEDICATION_DATA_FILE)
        csv_content = contents.decoded_content.decode("utf-8")
        data = pd.read_csv(StringIO(csv_content))
        user_medication_data = data[data['username'] == current_user]
        
        # Entfernen von Duplikaten
        user_medication_data = user_medication_data.drop_duplicates(subset=["med_name", "morgens", "mittags", "abends", "nachts"])
        
        return user_medication_data
    except Exception as e:
        st.error(f"Fehler beim Laden der Medikamentendaten: {str(e)}")
        return pd.DataFrame()

def show_medication_list():
    st.title('Medikamentenplan')
    
    medication_data = load_medication_data()
    
    # Display the medication plan if data is available
    if not medication_data.empty:
        # Create a nicely styled table
        st.write('<style>div.Widget.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)
        st.write('<style>div.Widget.row-widget.stRadio > div > label{padding:5px;}</style>', unsafe_allow_html=True)
        
        st.markdown("""
            <style>
            .med-table {
                font-family: Arial, sans-serif;
                border-collapse: collapse;
                width: 100%;
                box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
                border-radius: 10px;
                overflow: hidden;
            }
            .med-table td, .med-table th {
                border: 1px solid #dddddd;
                padding: 12px;
                text-align: left;
            }
            .med-table tr:nth-child(even) {
                background-color: #f2f2f2;
            }
            .med-table th {
                background-color: #4CAF50;
                color: white;
            }
            </style>
            """, unsafe_allow_html=True)
        
        st.table(medication_data.style.set_table_attributes('class="med-table"'))
        
        # Check if there's medication data to generate a PDF
        pdf_file = create_medication_pdf(medication_data)
        st.download_button(label="Download Medikamentenplan PDF",
                           data=pdf_file,
                           file_name="medication_plan.pdf",
                           mime='application/pdf')
    else:
        st.write("Es sind keine Medikamentenpläne vorhanden.")

def create_medication_pdf(medication_data):
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Adding title
    title = Paragraph("Medikamentenplan", styles['Title'])
    elements.append(title)

    # Preparing data for the table
    data = [["Medikament", "Morgens", "Mittags", "Abends", "Nachts"]]
    for index, row in medication_data.iterrows():
        data.append([
            row['med_name'], 
            row['morgens'], 
            row['mittags'], 
            row['abends'], 
            row['nachts']
        ])

    # Creating the table
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BOX', (0,0), (-1,-1), 2, colors.black),
    ]))
    elements.append(t)
    
    # Building the PDF
    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer

#hier kommt Fitness        
def back_to_home():
    st.session_state['page'] = 'home_screen'
    
def add_fitness_activity(username, datum, uhrzeit, dauer, intensitaet, art, kommentare):
    if 'fitness_activities' not in st.session_state:
        st.session_state['fitness_activities'] = []
    
    new_activity = {
        'username': username,
        'datum': datum.strftime('%Y-%m-%d'),
        'uhrzeit': uhrzeit.strftime('%H:%M:%S'),
        'dauer': dauer,
        'intensitaet': intensitaet,
        'art': art,
        'kommentare': kommentare
    }

    # Überprüfen, ob diese Aktivität bereits existiert
    if new_activity not in st.session_state['fitness_activities']:
        st.session_state['fitness_activities'].append(new_activity)
        save_fitness_data_to_github()
    else:
        st.warning("Diese Aktivität wurde bereits hinzugefügt.")

def save_fitness_data_to_github():
    fitness_list = st.session_state['fitness_activities']
    fitness_df = pd.DataFrame(fitness_list)
    fitness_df.to_csv(FITNESS_DATA_FILE, index=False)

    repo = init_github()

    try:
        contents = repo.get_contents(FITNESS_DATA_FILE)
        updated_csv = fitness_df.to_csv(index=False)
        repo.update_file(contents.path, "Update fitness data", updated_csv, contents.sha)
        st.success('Fitnessdaten erfolgreich auf GitHub aktualisiert!')
    except Exception as e:
        repo.create_file(FITNESS_DATA_FILE, "Create fitness data file", fitness_df.to_csv(index=False))
        st.success('Fitness CSV erfolgreich auf GitHub erstellt!')

def load_fitness_data():
    repo = init_github()
    current_user = st.session_state.get('current_user')
    try:
        contents = repo.get_contents(FITNESS_DATA_FILE)
        csv_content = contents.decoded_content.decode("utf-8")
        data = pd.read_csv(StringIO(csv_content))
        
        # Filtern der Daten, um nur die des aktuellen Benutzers anzuzeigen
        user_data = data[data['username'] == current_user]
        
        # Entfernen von Duplikaten
        user_data = user_data.drop_duplicates(subset=["datum", "uhrzeit", "dauer", "intensitaet", "art", "kommentare"])
        
        return user_data
    except Exception as e:
        st.error(f"Fehler beim Laden der Fitnessdaten: {str(e)}")
        return pd.DataFrame()

def show_fitness():
    display_logo()
    display_logo(in_sidebar=True)
    username = st.session_state.get('current_user')

    if not username:
        st.error("Bitte melden Sie sich an, um Fitnessdaten zu bearbeiten.")
        return

    if st.button("Zurück zum Homebildschirm"):
        back_to_home()

    st.title('Fitness')

    st.sidebar.title("Optionen")
    fitness_options = ["Aktivität hinzufügen", "History"]
    choice = st.sidebar.radio("", fitness_options)

    if choice == "Aktivität hinzufügen": 
        with st.form("fitness_form"):
            datum = st.date_input("Datum", datetime.now().date())  # Hier wird date.today() verwendet
            uhrzeit = st.time_input("Uhrzeit", datetime.now().time())
            dauer = st.text_input("Dauer")
            intensitaet_options = ["Niedrig", "Moderat", "Hoch", "Sehr hoch"]
            intensitaet = st.selectbox("Intensität", intensitaet_options)
            art = st.text_input("Art")
            kommentare = st.text_area("Kommentare")
            submit_button = st.form_submit_button("Speichern")

            if submit_button:
                add_fitness_activity(username, datum, uhrzeit, dauer, intensitaet, art, kommentare)
                st.success("Fitnessaktivität gespeichert!")

    elif choice == "History":
        show_fitness_history()

def get_start_end_dates_from_week_number(year, week_number):
    """Returns the start and end dates of the given week number for the given year."""
    first_day_of_year = datetime(year, 1, 1)
    start_of_week = first_day_of_year + pd.Timedelta(days=(week_number - 1) * 7)
    start_of_week -= pd.Timedelta(days=start_of_week.weekday())
    end_of_week = start_of_week + pd.Timedelta(days=6)
    return start_of_week.date(), end_of_week.date()

def show_fitness_history():
    username = st.session_state.get('current_user')
    st.title('Fitness History - Diese Woche')

    week_number = st.number_input('Wochennummer (1-52)', min_value=1, max_value=52, value=datetime.now().isocalendar()[1], format='%d')
    year_to_view = st.number_input('Jahr', min_value=2020, max_value=2100, value=datetime.now().year, format='%d')

    start_date, end_date = get_start_end_dates_from_week_number(year_to_view, week_number)
    st.write(f"Anzeigen der Fitnessaktivitäten für die Woche vom {start_date} bis {end_date}")

    fitness_data = load_fitness_data()

    if not fitness_data.empty:
        weekly_data = fitness_data[(fitness_data['datum'] >= str(start_date)) & (fitness_data['datum'] <= str(end_date))]

        # Dictionary zum Sammeln der Aktivitäten für jeden Wochentag initialisieren
        daily_activities = {day: [] for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']}

        # Aktivitäten nach Wochentagen gruppieren
        for activity in weekly_data.itertuples():
            activity_date = datetime.strptime(activity.datum, '%Y-%m-%d').date()
            day_name = activity_date.strftime("%a")
            daily_activities[day_name].append(activity)

        # DataFrame für die Anzeige vorbereiten
        df_week = pd.DataFrame()

        # Aktivitäten für jeden Wochentag in den DataFrame einfügen
        for day, activities in daily_activities.items():
            day_data = pd.DataFrame([{
                'Datum': activity.datum,
                'Uhrzeit': activity.uhrzeit,
                'Dauer': activity.dauer,
                'Intensitaet': activity.intensitaet,
                'Art': activity.art,
                'Kommentare': activity.kommentare
            } for activity in activities])
            df_week = pd.concat([df_week, day_data], ignore_index=True)

        # DataFrame anzeigen
        st.table(df_week)

        # Code für den Download-Button
        pdf_file = create_fitness_pdf(df_week)
        st.download_button(
            label="Download Fitnessdaten PDF",
            data=pdf_file,
            file_name="fitnessdaten.pdf",
            mime='application/pdf'
        )
    else:
        st.write("Keine Daten zum Herunterladen verfügbar.")

def create_fitness_pdf(fitness_data):
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Adding title
    title = Paragraph("Fitness Report", styles['Title'])
    elements.append(title)

    # Data for the table, adapted for fitness data
    data = [["Datum", "Uhrzeit", "Dauer", "Intensität", "Art", "Kommentare"]]
    for index, row in fitness_data.iterrows():
        data.append([
            row['Datum'], 
            row['Uhrzeit'], 
            row['Dauer'], 
            row['Intensitaet'], 
            row['Art'], 
            row['Kommentare'] or ""
        ])

    # Create the table with the data
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BOX', (0,0), (-1,-1), 2, colors.black),
    ]))
    elements.append(t)
    
    # Build the PDF
    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer
    
# Notfallnummern
def go_to_home():
    st.session_state['page'] = 'home_screen'
def initialize_emergency_numbers():
    if 'emergency_numbers' not in st.session_state:
        st.session_state['emergency_numbers'] = []
def add_emergency_number(username, number_type, number):
    # Initialisiere die Notfallnummern, wenn noch nicht geschehen
    initialize_emergency_numbers()
    existing_entries = st.session_state['emergency_numbers']
    updated = False

    # Update des bestehenden Eintrags, wenn vorhanden
    for entry in existing_entries:
        if entry['username'] == username and entry['type'] == number_type:
            entry['number'] = number
            updated = True
            break

    # Neuer Eintrag, wenn nicht vorhanden
    if not updated:
        new_entry = {"username": username, "type": number_type, "number": number}
        existing_entries.append(new_entry)

    # Aktualisiere den globalen Zustand
    st.session_state['emergency_numbers'] = existing_entries
    save_emergency_numbers_to_github(existing_entries)

def save_emergency_numbers_to_github(entries):
    emergency_df = pd.DataFrame(entries)
    emergency_df.to_csv(EMERGENCY_NUMBERS_FILE, index=False)

    repo = init_github()

    try:
        contents = repo.get_contents(EMERGENCY_NUMBERS_FILE)
        updated_csv = emergency_df.to_csv(index=False)
        repo.update_file(contents.path, "Update emergency numbers data", updated_csv, contents.sha)
        st.success('Emergency numbers data updated on GitHub successfully!')
    except Exception as e:
        repo.create_file(EMERGENCY_NUMBERS_FILE, "Create emergency numbers data file", emergency_df.to_csv(index=False))
        st.success('Emergency numbers CSV created on GitHub successfully!')

def load_emergency_numbers():
    repo = init_github()
    try:
        contents = repo.get_contents(EMERGENCY_NUMBERS_FILE)
        csv_content = contents.decoded_content.decode("utf-8")
        data = pd.read_csv(StringIO(csv_content))
        st.session_state['emergency_numbers'] = data.to_dict('records')
    except Exception as e:
        st.error(f"Fehler beim Laden der Notfallnummern: {str(e)}")
        st.session_state['emergency_numbers'] = []

def init_github():
    g = Github(st.secrets["github"]["token"])
    repo = g.get_repo(f"{st.secrets['github']['owner']}/{st.secrets['github']['repo']}")
    return repo


def show_emergency_numbers():
    display_logo()
    if st.button("Zurück zum Homebildschirm"):
        go_to_home()

    st.title('Meine Notfallnummern')
    current_user = st.session_state.get('current_user')
    if not current_user:
        st.error("Sie müssen angemeldet sein, um Ihre Notfallnummern anzuzeigen.")
        return

    load_emergency_numbers()  # Stellen Sie sicher, dass dies am Anfang steht

    # Anzeigen allgemeiner Notfallnummern
    st.write("Allgemeine Notfallnummern:")
    st.write("- Polizei: 117")
    st.write("- Feuerwehr: 118")
    st.write("- Krankenwagen: 114")
    st.write("- Rega: 1414")
    st.write("- Toxzentrum: 143")

    # Laden und Anzeigen benutzerspezifischer Notfallnummern
    emergency_data = st.session_state.get('emergency_numbers', [])
    current_numbers = {entry['type']: entry['number'] for entry in emergency_data if entry.get('username') == current_user}

    # Anzeigen der aktuellen Notfallnummern
    if current_numbers:
        for number_type, number in current_numbers.items():
            st.write(f"- {number_type}: {number}")
    else:
        st.write("Keine Notfallnummern gespeichert.")

    # Eingabe neuer Notfallnummern
    with st.form("emergency_numbers_form"):
        number_types = ['Hausarzt', 'Notfallkontakt']
        inputs = {}
        for number_type in number_types:
            inputs[number_type] = st.text_input(f'{number_type}', value=current_numbers.get(number_type, ''))
        submit_button = st.form_submit_button("Speichern")

        if submit_button:
            for number_type, number in inputs.items():
                if number and (number != current_numbers.get(number_type)):
                    add_emergency_number(current_user, number_type, number)
            st.experimental_rerun()  # Neu laden der Seite zur Aktualisierung der angezeigten Daten

#Info- Page
def go_to_home():
    st.session_state['page'] = 'home_screen'
def setup_sidebar():
    st.sidebar.title("Optionen")  # Titel nur einmal aufrufen
    info_options = st.sidebar.radio("Kategorie auswählen", ["Blutdruck", "Bewegung und Blutdruck"])
    return info_options

def show_info_pages():
    display_logo()
    display_logo(in_sidebar=True)
    info_options = setup_sidebar()

    if st.button("Zurück zum Homebildschirm"):
        go_to_home()

    st.title('Gesundheitsinformationen')

    # Funktion zum Lesen des Textes aus der Datei
    def read_text_from_file(filename):
        base_path = os.path.dirname(__file__)  # Basispfad für relative Pfade
        filepath = os.path.join(base_path, filename)  # Pfad zur Datei
        encodings = ['utf-8', 'ISO-8859-1']  # Verschiedene Zeichenformate ausprobieren
        for encoding in encodings:
            try:
                with open(filepath, "r", encoding=encoding) as file:
                    return file.read()
            except FileNotFoundError as e:
                st.error(f"Datei nicht gefunden: {filepath}")
                raise e
            except UnicodeDecodeError:
                continue
        st.error("Fehler beim Lesen der Datei. Bitte überprüfen Sie das Zeichenformat.")
        return ""

    blutdruck_info = read_text_from_file("blutdruck_info.txt")
    bewegung_blutdruck_info = read_text_from_file("bewegung_blutdruck_info.txt")

    if info_options == "Blutdruck":
        st.markdown("### Informationen zum Blutdruck")
        st.markdown(blutdruck_info)
    elif info_options == "Bewegung und Blutdruck":
        st.markdown("### Informationen zu Bewegung und Blutdruck")
        st.markdown(bewegung_blutdruck_info)

    elif st.session_state['page'] == 'infos':
        show_info_pages()

# Infotexte fertig

# Display pages based on session state
if st.session_state['page'] == 'home':
    show_home()
elif st.session_state['page'] == 'home_screen':
    show_home_screen()
elif st.session_state['page'] == 'profile':
    show_profile()
elif st.session_state['page'] == 'measurements':
    show_measurement_options()
elif st.session_state['page'] == 'medication-plan':
    show_medication_plan()
elif st.session_state['page'] == 'Fitness':
    show_fitness()
elif st.session_state['page'] == 'emergency_numbers':
    show_emergency_numbers()
elif st.session_state['page'] == 'infos':
    show_info_pages()   
