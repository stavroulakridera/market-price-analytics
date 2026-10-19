
import streamlit as st
from db import connect, check_schema

st.title("🔌 Έλεγχος Supabase")
st.info("Έλεγχος σύνδεσης μόνο για δοκιμαστικά δεδομένα.")

if st.button("Έλεγχος σύνδεσης"):
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT current_database(), current_user, NOW()"
                )
                database, username, server_time = cur.fetchone()

        st.success("✅ Επιτυχής σύνδεση με Supabase!")
        st.write("Βάση δεδομένων:", database)
        st.write("Χρήστης PostgreSQL:", username)
        st.write("Ώρα server:", str(server_time))

        tables = check_schema()
        st.subheader("Πίνακες σχήματος mpa")
        if tables:
            st.dataframe(
                [{"Πίνακας": name} for name in tables],
                hide_index=True
            )
        else:
            st.warning("Δεν βρέθηκαν πίνακες στο σχήμα mpa.")

    except Exception:
        st.error("❌ Αποτυχία σύνδεσης ή ελέγχου σχήματος.")
        st.info(
            "Έλεγξε το MPA_DATABASE_URL και τα Logs. "
            "Μην κοινοποιήσεις κωδικούς σύνδεσης."
        )
