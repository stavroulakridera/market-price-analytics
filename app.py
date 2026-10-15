
import streamlit as st

st.set_page_config(
    page_title="Market Price Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
    }
    [data-testid="stSidebar"] {
        background-color: #14263d;
    }
    [data-testid="stSidebar"] * {
        color: white;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("📊 Market Price Analytics")
    st.caption("Σύστημα Παρακολούθησης Τιμών")
    st.divider()

    page = st.radio(
        "ΜΕΝΟΥ",
        [
            "🏠 Αρχική",
            "📈 Ανατιμήσεις",
            "📉 Υποτιμήσεις",
            "🏢 Μητρώο Προμηθευτών",
            "🗂️ Μητρώο Κατηγοριών",
            "📥 Εισαγωγή Excel",
            "📊 Στατιστικά & Αναφορές",
            "🕘 Ιστορικό Εισαγωγών",
            "⚙️ Ρυθμίσεις"
        ],
        label_visibility="collapsed"
    )

if page == "🏠 Αρχική":
    st.title("🏠 Κεντρικός Πίνακας")
    st.write("Σύστημα Παρακολούθησης Ανατιμήσεων και Υποτιμήσεων")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Σύνολο Ανατιμήσεων", "0")
    with col2:
        st.metric("Σύνολο Υποτιμήσεων", "0")
    with col3:
        st.metric("Προμηθευτές", "0")
    with col4:
        st.metric("Ανατιμήσεις > 3%", "0")

    st.divider()
    st.info("Δεν έχουν εισαχθεί ακόμη δεδομένα.")

elif page == "📈 Ανατιμήσεις":
    st.title("📈 Ανατιμήσεις")
    st.info("Εδώ θα εμφανίζονται οι ανατιμήσεις των προϊόντων.")

elif page == "📉 Υποτιμήσεις":
    st.title("📉 Υποτιμήσεις")
    st.info("Εδώ θα εμφανίζονται οι υποτιμήσεις των προϊόντων.")

elif page == "🏢 Μητρώο Προμηθευτών":
    st.title("🏢 Μητρώο Προμηθευτών")
    st.info("Εδώ θα διαχειριζόμαστε τα ΑΦΜ και τις επωνυμίες.")

elif page == "🗂️ Μητρώο Κατηγοριών":
    st.title("🗂️ Μητρώο Κατηγοριών")
    st.info("Εδώ θα αντιστοιχίζουμε τις κατηγορίες προϊόντων.")

elif page == "📥 Εισαγωγή Excel":
    st.title("📥 Εισαγωγή Excel")
    st.info("Εδώ θα εισάγουμε τα Draft των αλυσίδων.")

elif page == "📊 Στατιστικά & Αναφορές":
    st.title("📊 Στατιστικά & Αναφορές")
    st.info("Εδώ θα εμφανίζονται τα διαγράμματα και οι αναφορές.")

elif page == "🕘 Ιστορικό Εισαγωγών":
    st.title("🕘 Ιστορικό Εισαγωγών")
    st.info("Εδώ θα εμφανίζεται το ιστορικό των αρχείων.")

elif page == "⚙️ Ρυθμίσεις":
    st.title("⚙️ Ρυθμίσεις")
    st.info("Εδώ θα διαχειριζόμαστε τις ρυθμίσεις της εφαρμογής.")
