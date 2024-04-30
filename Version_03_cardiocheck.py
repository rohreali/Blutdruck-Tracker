def show_home_screen():
    display_logo()
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
        if st.button("Medikamenten Plan"):
            st.session_state['page'] = 'medication-plan'
        if st.button("Infos"):
            st.session_state['page'] = 'infos'

        st.write("")  # Füge einen leeren Platzhalter ein für visuellen Abstand
        st.write("")  # Du kannst mehrere Zeilen hinzufügen, je nach benötigtem Abstand
        st.write("")
        st.write("")
        st.write("")
        st.write("")
        st.write("")
        st.write("")

        if st.button("Logout"):
            logout()
