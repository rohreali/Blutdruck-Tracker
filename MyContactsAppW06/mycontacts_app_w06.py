
import streamlit as st
import streamlit_authenticator as stauth    
import pandas as pd
from datetime import date
from github_contents import GithubContents
import api_calls

# Set constants
DISPLAY_COLUMNS_DICT = {
    'name': 'Name',
    'street': 'Strasse',
    'postal_code': 'PLZ',
    'city': 'Ort',
    'lat': 'Breitengrad',
    'lon': 'Längengrad'
}
LOGIN_FILE = 'login_hashed_password_list.csv'

# Set page configuration
st.set_page_config(page_title="My Contacts", page_icon="🎂", layout="wide",  
                   initial_sidebar_state="expanded")

# ------------------- Initialization functions -------------------
def authenticate():
    """ Initialize the authentication status."""
    if 'credentials' not in st.session_state:
        login_df = pd.read_csv(LOGIN_FILE, index_col=0)
        credentials =  {'usernames':login_df.to_dict(orient="index")}
        st.session_state['credentials'] = credentials
    else:
        credentials = st.session_state['credentials']

    # the next code line automatically generates the session states
    # name, username, authentication_status
    authenticator = stauth.Authenticate(credentials,cookie_name='login-cookie', cookie_key='')
    authenticator.login()

    # use the authentication status to display messages
    if st.session_state["authentication_status"] is True:
        authenticator.logout()
    elif st.session_state["authentication_status"] is False:
        st.error('Username/password is incorrect')
    elif st.session_state["authentication_status"] is None:
        st.warning('Please enter your username and password')


def init_github():
    """Initialize the GithubContents object."""
    if 'github' not in st.session_state:
        st.session_state.github = GithubContents(
            st.secrets["github"]["owner"],
            st.secrets["github"]["repo"],
            st.secrets["github"]["token"])
        
def get_csv_file_name():
    username = st.session_state['username']
    return 'user_data/' + username + '.csv'

def init_dataframe():
    """Initialize or load the dataframe."""
    filename = get_csv_file_name()
    if 'df' in st.session_state:
        pass
    elif st.session_state.github.file_exists(filename):
        st.session_state.df = st.session_state.github.read_df(filename)
    else:
        data_columns = list(DISPLAY_COLUMNS_DICT.keys())
        st.session_state.df = pd.DataFrame(columns=data_columns)

# ------------------- Update functions -------------------
def update_mycontacts_table(new_entry):
    """Update the DataFrame and Github with a new entry."""
    init_dataframe() # make sure the DataFrame is up to date

    df = st.session_state.df
    new_entry_df = pd.DataFrame([new_entry])
    df = pd.concat([df, new_entry_df], ignore_index=True)
    st.session_state.df = df

    # Save the updated DataFrame to GitHub
    name = new_entry['name']
    filename = get_csv_file_name()
    msg = f"Add contact '{name}' to the file {filename}"
    st.session_state.github.write_df(filename, df, msg)


# ------------------- Display functions -------------------
def display_sidebar():
    """Display the sidebar in the app. Add a new entry to the DataFrame."""
    new_entry = {
        'name':  st.sidebar.text_input(DISPLAY_COLUMNS_DICT['name']),  
        'street':  st.sidebar.text_input(DISPLAY_COLUMNS_DICT['street']),  
        'postal_code':  st.sidebar.text_input(DISPLAY_COLUMNS_DICT['postal_code']),  
        'city':  st.sidebar.text_input(DISPLAY_COLUMNS_DICT['city']),   
    } 

    # check wether all data is defined, otherwise show an error message
    for key, value in new_entry.items():
        if value == "":
            st.sidebar.error(f"Bitte ergänze das Feld '{key}'")
            return
        
    # --- the subsequent code is only executed if all fields are filled ---
    # get the coordinates from the Nominatim API    
    lat, lon, error= api_calls.get_coordinate_from_nominatim(new_entry['street'], new_entry['postal_code'], new_entry['city'])  

    new_entry['lat'] = lat
    new_entry['lon'] = lon

    # display latitude and longitude in the sidebar
    st.sidebar.write("Breitengrad:", lat)
    st.sidebar.write("Längengrad:", lon)
    
     # if there is an error, show the error message and return, no new entry will be added
    if len(error) > 0:   #
        st.sidebar.error(error)

    # add the new entry to the DataFrame if the "Add" button is clicked
    if st.sidebar.button("Add"):
        update_mycontacts_table(new_entry)

def display_dataframe():
    """Display the DataFrame in the app."""
    if not st.session_state.df.empty:
        df = st.session_state.df.rename(columns=DISPLAY_COLUMNS_DICT)
        st.dataframe(df)
    else:
        st.write("No data to display.")

def display_poem():
    """Display a poem in the app in a nice frame"""
    df = st.session_state.df
    if df.empty:
        return
    with st.spinner("Generating a poem with Mistral AI on Hugging Face..."):
        last_name = st.session_state.df.iloc[-1]["name"]
        huggerface_token = st.secrets["huggingface"]["token"]
        poem = api_calls.get_ai_poem(last_name, huggerface_token)
        poem = poem.replace("\n", "<br>")  # format the poem for HTML

    st.markdown(
        f"""
        <div style='border: 2px solid #f63366; border-radius: 5px; padding: 10px;'>
        <p style='text-align: center; color: #f63366; font-size: 20px; font-weight: bold;'>
        Das Gedicht zum letzten Eintrag (by Mistral AI)
        </p>
        <p style='text-align: center;'>
        {poem}
        </p>
        </div>
        """,
        unsafe_allow_html=True
    )

def display_map():
    """Display the map in the app."""
    st.map(st.session_state.df.dropna(),latitude='lat',longitude='lon', zoom=10)

# ------------------- Main -------------------
def main():
    authenticate()  # sets the authentication status

    # check if the user is authenticated, otherwise stop the app
    if st.session_state['authentication_status'] != True:
        return  
    
    # display the app
    st.title("Mein Kontakte-App 🎂 (Woche 5)")
    init_github()
    init_dataframe()
    display_sidebar()
    display_dataframe()
    display_poem()
    display_map()

if __name__ == "__main__":
    main()
