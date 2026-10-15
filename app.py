
import streamlit as st
import pandas as pd
from datetime import datetime, timezone

# ============================================================
# ΡΥΘΜΙΣΕΙΣ ΕΦΑΡΜΟΓΗΣ
# ============================================================

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
    padding-bottom: 2rem;
}
[data-testid="stSidebar"] {
    background-color: #19263e;
}
[data-testid="stSidebar"] * {
    color: white;
}
div[data-testid="stMetric"] {
    background-color: #f3f6fb;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #e3e9f2;
}
div[data-testid="stMetric"] * {
    color: #19263e;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# ΒΟΗΘΗΤΙΚΕΣ ΣΥΝΑΡΤΗΣΕΙΣ
# ============================================================

def normalize(value):
    return " ".join(str(value).strip().upper().split())


def valid_greek_afm(afm):
    afm = str(afm).strip()

    if (
        len(afm) != 9
        or not afm.isascii()
        or not afm.isdigit()
        or afm == "000000000"
    ):
        return False

    total = sum(
        int(afm[i]) * (2 ** (8 - i))
        for i in range(8)
    )

    return (total % 11) % 10 == int(afm[8])


def next_supplier_id():
    return max(
        (s["ID"] for s in st.session_state.suppliers),
        default=0
    ) + 1


def add_history(supplier_id, afm, field, old, new, reason):
    st.session_state.supplier_history.append({
        "ΗΜΕΡΟΜΗΝΙΑ (UTC)": datetime.now(
            timezone.utc
        ).strftime("%d/%m/%Y %H:%M:%S"),
        "ID ΠΡΟΜΗΘΕΥΤΗ": supplier_id,
        "ΑΦΜ": afm,
        "ΠΕΔΙΟ": field,
        "ΠΑΛΙΑ ΤΙΜΗ": str(old),
        "ΝΕΑ ΤΙΜΗ": str(new),
        "ΑΙΤΙΟΛΟΓΙΑ": reason,
        "ΧΡΗΣΤΗΣ": "DEMO USER"
    })


# ============================================================
# ΔΟΚΙΜΑΣΤΙΚΑ ΔΕΔΟΜΕΝΑ
# ============================================================

if "suppliers" not in st.session_state:
    st.session_state.suppliers = [
        {
            "ID": 1,
            "ΑΦΜ": "000000000",
            "ΟΝΟΜΑΣΙΑ ΟΠΩΣ ΗΡΘΕ": "ΔΟΚΙΜΑΣΤΙΚΟΣ Α",
            "ΠΡΟΜΗΘΕΥΤΗΣ": "ΔΟΚΙΜΑΣΤΙΚΟΣ ΠΡΟΜΗΘΕΥΤΗΣ Α",
            "ΧΩΡΑ": "Ελλάδα",
            "ΚΑΤΑΣΤΑΣΗ": "Προς έλεγχο"
        },
        {
            "ID": 2,
            "ΑΦΜ": "123456789",
            "ΟΝΟΜΑΣΙΑ ΟΠΩΣ ΗΡΘΕ": "ΔΟΚΙΜΑΣΤΙΚΟΣ Β",
            "ΠΡΟΜΗΘΕΥΤΗΣ": "ΔΟΚΙΜΑΣΤΙΚΟΣ ΠΡΟΜΗΘΕΥΤΗΣ Β",
            "ΧΩΡΑ": "Ελλάδα",
            "ΚΑΤΑΣΤΑΣΗ": "Προς έλεγχο"
        }
    ]


for supplier in st.session_state.suppliers:
    supplier.setdefault("ΟΝΟΜΑΣΙΑ ΟΠΩΣ ΗΡΘΕ", supplier.get("ΠΡΟΜΗΘΕΥΤΗΣ", ""))
    supplier.setdefault("ΧΩΡΑ", "Ελλάδα")
    supplier.setdefault("ΚΑΤΑΣΤΑΣΗ", "Προς έλεγχο")

if "supplier_history" not in st.session_state:
    st.session_state.supplier_history = []



# ============================================================
# ΑΠΟΚΛΕΙΣΤΙΚΑ ΣΥΝΘΕΤΙΚΑ ΔΕΔΟΜΕΝΑ ΕΠΙΔΕΙΞΗΣ
# ============================================================

@st.cache_data
def demo_prices():
    products = ["Γάλα", "Γιαούρτι", "Τυρί", "Ρύζι", "Ζυμαρικά", "Ελαιόλαδο", "Καφές", "Αλεύρι", "Χυμός", "Απορρυπαντικό"]
    categories = ["Γαλακτοκομικά", "Γαλακτοκομικά", "Γαλακτοκομικά", "Τρόφιμα", "Τρόφιμα", "Έλαια", "Ροφήματα", "Τρόφιμα", "Ροφήματα", "Οικιακά"]
    chains = ["Αλυσίδα Α", "Αλυσίδα Β", "Αλυσίδα Γ"]
    rows = []
    for i in range(120):
        old = round(1.25 + (i % 17) * 0.43, 2)
        change = ((i * 7) % 23 - 9) / 100
        new = round(old * (1 + change), 2)
        rows.append({
            "Ημερομηνία": pd.Timestamp("2026-01-01") + pd.Timedelta(days=(i * 2) % 270),
            "Αλυσίδα": chains[i % 3],
            "Προμηθευτής": f"DEMO Προμηθευτής {i % 8 + 1}",
            "Προϊόν": products[i % len(products)],
            "Κατηγορία": categories[i % len(categories)],
            "Προηγούμενη τιμή": old,
            "Νέα τιμή": new,
            "Μεταβολή %": round((new / old - 1) * 100, 2),
        })
    return pd.DataFrame(rows)


def price_table(data, increase=True):
    if data.empty:
        st.info("Δεν υπάρχουν εγγραφές για τα επιλεγμένα φίλτρα.")
        return
    display = data.copy().sort_values("Ημερομηνία", ascending=False)
    display["Ημερομηνία"] = display["Ημερομηνία"].dt.strftime("%d/%m/%Y")
    def color_change(value):
        if increase and value > 3:
            return "background-color: #ffe1e1; color: #8f1515; font-weight: bold"
        if not increase and value < 0:
            return "background-color: #e0f5e7; color: #166534; font-weight: bold"
        return ""
    st.dataframe(display.style.map(color_change, subset=["Μεταβολή %"]),
                 use_container_width=True, hide_index=True, height=410)
    st.download_button("⬇️ Εξαγωγή φιλτραρισμένων δεδομένων CSV (DEMO)",
                       display.to_csv(index=False).encode("utf-8-sig"),
                       file_name="demo_prices.csv", mime="text/csv")


def price_view(increase=True):
    df = demo_prices()
    df = df[df["Μεταβολή %"] > 0] if increase else df[df["Μεταβολή %"] < 0]
    a, b, c = st.columns(3)
    chain = a.selectbox("Αλυσίδα", ["Όλες"] + sorted(df["Αλυσίδα"].unique().tolist()), key=f"chain_{increase}")
    category = b.selectbox("Κατηγορία", ["Όλες"] + sorted(df["Κατηγορία"].unique().tolist()), key=f"category_{increase}")
    search = c.text_input("Αναζήτηση προϊόντος / προμηθευτή", key=f"search_{increase}")
    if chain != "Όλες":
        df = df[df["Αλυσίδα"] == chain]
    if category != "Όλες":
        df = df[df["Κατηγορία"] == category]
    if search.strip():
        df = df[df["Προϊόν"].str.contains(search, case=False, regex=False) |
                df["Προμηθευτής"].str.contains(search, case=False, regex=False)]
    x, y, z = st.columns(3)
    x.metric("Εγγραφές", len(df))
    y.metric("Μέση μεταβολή", f"{df['Μεταβολή %'].mean():.2f}%" if len(df) else "—")
    z.metric("Μέγιστη ανατίμηση" if increase else "Μεγαλύτερη υποτίμηση",
             f"{(df['Μεταβολή %'].max() if increase else df['Μεταβολή %'].min()):.2f}%" if len(df) else "—")
    st.subheader("Αναλυτικός πίνακας")
    if increase:
        st.caption("Κόκκινη επισήμανση μόνο όταν η μεταβολή είναι αυστηρά μεγαλύτερη από 3%.")
    price_table(df, increase)
    if len(df):
        st.subheader("Μεταβολές ανά κατηγορία")
        chart = df.groupby("Κατηγορία")["Μεταβολή %"].mean().sort_values()
        st.bar_chart(chart, horizontal=True)

# ============================================================
# ΠΛΕΥΡΙΚΟ ΜΕΝΟΥ
# ============================================================

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

    st.divider()
    st.caption("Market Price Analytics | DEMO")


# ============================================================
# ΑΡΧΙΚΗ
# ============================================================

if page == "🏠 Αρχική":
    st.title("📊 Κεντρικός Πίνακας")
    st.caption("DEMO με συνθετικά δεδομένα — όχι πραγματικές τιμές αγοράς")
    df = demo_prices()
    inc = df[df["Μεταβολή %"] > 0]
    dec = df[df["Μεταβολή %"] < 0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ανατιμήσεις", len(inc))
    c2.metric("Υποτιμήσεις", len(dec))
    c3.metric("Προμηθευτές μητρώου", len(st.session_state.suppliers))
    c4.metric("Ανατιμήσεις > 3%", int((inc["Μεταβολή %"] > 3).sum()))
    st.divider()
    left, right = st.columns(2)
    with left:
        st.subheader("Εγγραφές ανά κατηγορία")
        st.bar_chart(df.groupby("Κατηγορία").size().rename("Εγγραφές"))
    with right:
        st.subheader("Μέση μεταβολή ανά αλυσίδα")
        st.bar_chart(df.groupby("Αλυσίδα")["Μεταβολή %"].mean())
    st.subheader("Εξέλιξη μέσης ποσοστιαίας μεταβολής")
    monthly = df.assign(Μήνας=df["Ημερομηνία"].dt.to_period("M").dt.to_timestamp())
    st.line_chart(monthly.groupby("Μήνας")["Μεταβολή %"].mean())

elif page == "📈 Ανατιμήσεις":
    st.title("📈 Ανατιμήσεις")
    st.caption("Συνθετικές εγγραφές επίδειξης — οι 16 στήλες του πραγματικού αρχείου θα προστεθούν μετά την ασφαλή αντιστοίχιση.")
    price_view(True)

elif page == "📉 Υποτιμήσεις":
    st.title("📉 Υποτιμήσεις")
    st.caption("Συνθετικές εγγραφές επίδειξης")
    price_view(False)


# ============================================================
# ΜΗΤΡΩΟ ΠΡΟΜΗΘΕΥΤΩΝ
# ============================================================

elif page == "🏢 Μητρώο Προμηθευτών":

    st.title("🏢 Μητρώο Προμηθευτών")
    st.caption(
        "Δοκιμαστική διαχείριση προμηθευτών "
        "με ιστορικό αλλαγών"
    )

    suppliers = st.session_state.suppliers

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Σύνολο", len(suppliers))
    c2.metric(
        "Ενεργοί",
        sum(
            s["ΚΑΤΑΣΤΑΣΗ"] == "Ενεργός"
            for s in suppliers
        )
    )
    c3.metric(
        "Προς έλεγχο",
        sum(
            s["ΚΑΤΑΣΤΑΣΗ"] == "Προς έλεγχο"
            for s in suppliers
        )
    )
    c4.metric(
        "Αλλαγές",
        len(st.session_state.supplier_history)
    )

    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Προμηθευτές",
        "➕ Νέος Προμηθευτής",
        "✏️ Επεξεργασία",
        "🕘 Ιστορικό Αλλαγών",
        "🔍 Έλεγχος ΑΦΜ"
    ])

    # --------------------------------------------------------
    # ΚΑΡΤΕΛΑ 1 — ΠΡΟΜΗΘΕΥΤΕΣ
    # --------------------------------------------------------

    with tab1:
        st.subheader("Κατάλογος Προμηθευτών")

        search = st.text_input(
            "🔍 Αναζήτηση ΑΦΜ ή επωνυμίας"
        )

        status_filter = st.selectbox(
            "Κατάσταση",
            [
                "Όλοι",
                "Ενεργός",
                "Προς έλεγχο",
                "Ανενεργός"
            ]
        )

        filtered = []

        for s in suppliers:
            searchable = " ".join([
                s["ΑΦΜ"],
                s["ΟΝΟΜΑΣΙΑ ΟΠΩΣ ΗΡΘΕ"],
                s["ΠΡΟΜΗΘΕΥΤΗΣ"]
            ]).lower()

            if (
                search.lower() in searchable
                and (
                    status_filter == "Όλοι"
                    or s["ΚΑΤΑΣΤΑΣΗ"] == status_filter
                )
            ):
                filtered.append(s)

        columns = [
            "ID",
            "ΑΦΜ",
            "ΟΝΟΜΑΣΙΑ ΟΠΩΣ ΗΡΘΕ",
            "ΠΡΟΜΗΘΕΥΤΗΣ",
            "ΧΩΡΑ",
            "ΚΑΤΑΣΤΑΣΗ"
        ]

        st.dataframe(
            pd.DataFrame(filtered, columns=columns),
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            f"Εμφανίζονται {len(filtered)} εγγραφές."
        )

        duplicate_afms = {
            s["ΑΦΜ"]
            for s in suppliers
            if sum(
                x["ΑΦΜ"] == s["ΑΦΜ"]
                for x in suppliers
            ) > 1
        }

        if duplicate_afms:
            st.error(
                "Εντοπίστηκαν διπλότυπα ΑΦΜ: "
                + ", ".join(sorted(duplicate_afms))
            )

    # --------------------------------------------------------
    # ΚΑΡΤΕΛΑ 2 — ΝΕΟΣ ΠΡΟΜΗΘΕΥΤΗΣ
    # --------------------------------------------------------

    with tab2:
        st.subheader("➕ Καταχώριση Προμηθευτή")

        with st.form(
            "new_supplier_form",
            clear_on_submit=True
        ):
            afm = st.text_input("ΑΦΜ / VAT ID")

            original_name = st.text_input(
                "Ονομασία όπως ήρθε"
            )

            official_name = st.text_input(
                "Επίσημη επωνυμία"
            )

            country = st.selectbox(
                "Χώρα",
                ["Ελλάδα", "Εξωτερικό"]
            )

            status = st.selectbox(
                "Κατάσταση",
                [
                    "Προς έλεγχο",
                    "Ενεργός",
                    "Ανενεργός"
                ]
            )

            submitted = st.form_submit_button(
                "💾 Αποθήκευση",
                type="primary"
            )

        if submitted:
            afm = normalize(afm)
            original_name = normalize(original_name)
            official_name = normalize(official_name)

            if not afm or not original_name or not official_name:
                st.error("Συμπλήρωσε όλα τα υποχρεωτικά πεδία.")

            elif any(s["ΑΦΜ"] == afm for s in suppliers):
                st.error("Το ΑΦΜ υπάρχει ήδη στο μητρώο.")

            elif country == "Ελλάδα" and not valid_greek_afm(afm):
                st.error(
                    "Το ελληνικό ΑΦΜ δεν περνά "
                    "τον μαθηματικό έλεγχο."
                )

            else:
                if country == "Εξωτερικό":
                    status = "Προς έλεγχο"

                supplier_id = next_supplier_id()

                suppliers.append({
                    "ID": supplier_id,
                    "ΑΦΜ": afm,
                    "ΟΝΟΜΑΣΙΑ ΟΠΩΣ ΗΡΘΕ": original_name,
                    "ΠΡΟΜΗΘΕΥΤΗΣ": official_name,
                    "ΧΩΡΑ": country,
                    "ΚΑΤΑΣΤΑΣΗ": status
                })

                add_history(
                    supplier_id,
                    afm,
                    "ΔΗΜΙΟΥΡΓΙΑ",
                    "",
                    official_name,
                    "Νέα δοκιμαστική καταχώριση"
                )

                st.success(
                    "Ο προμηθευτής προστέθηκε επιτυχώς!"
                )

    # --------------------------------------------------------
    # ΚΑΡΤΕΛΑ 3 — ΕΠΕΞΕΡΓΑΣΙΑ
    # --------------------------------------------------------

    with tab3:
        st.subheader("✏️ Επεξεργασία Προμηθευτή")

        supplier_options = {
            f'{s["ID"]} | {s["ΑΦΜ"]} | {s["ΠΡΟΜΗΘΕΥΤΗΣ"]}':
            s["ID"]
            for s in suppliers
        }

        selected_label = st.selectbox(
            "Επίλεξε προμηθευτή",
            list(supplier_options.keys())
        )

        selected_id = supplier_options[selected_label]

        selected = next(
            s for s in suppliers
            if s["ID"] == selected_id
        )

        st.info(
            "Η αρχική ονομασία διατηρείται "
            "και δεν τροποποιείται."
        )

        st.text_input(
            "Ονομασία όπως ήρθε",
            value=selected["ΟΝΟΜΑΣΙΑ ΟΠΩΣ ΗΡΘΕ"],
            disabled=True
        )

        with st.form(
            f"edit_supplier_{selected_id}"
        ):
            new_afm = st.text_input(
                "ΑΦΜ / VAT ID",
                value=selected["ΑΦΜ"]
            )

            new_name = st.text_input(
                "Επίσημη επωνυμία",
                value=selected["ΠΡΟΜΗΘΕΥΤΗΣ"]
            )

            new_country = st.selectbox(
                "Χώρα",
                ["Ελλάδα", "Εξωτερικό"],
                index=(
                    0 if selected["ΧΩΡΑ"] == "Ελλάδα"
                    else 1
                )
            )

            statuses = [
                "Προς έλεγχο",
                "Ενεργός",
                "Ανενεργός"
            ]

            new_status = st.selectbox(
                "Κατάσταση",
                statuses,
                index=statuses.index(
                    selected["ΚΑΤΑΣΤΑΣΗ"]
                )
            )

            reason = st.text_area(
                "Αιτιολογία αλλαγής",
                placeholder=(
                    "Περιέγραψε γιατί γίνεται η διόρθωση"
                )
            )

            save_edit = st.form_submit_button(
                "💾 Αποθήκευση αλλαγών",
                type="primary"
            )

        if save_edit:
            new_afm = normalize(new_afm)
            new_name = normalize(new_name)
            reason = reason.strip()

            changes = {
                "ΑΦΜ": new_afm,
                "ΠΡΟΜΗΘΕΥΤΗΣ": new_name,
                "ΧΩΡΑ": new_country,
                "ΚΑΤΑΣΤΑΣΗ": new_status
            }

            changed_fields = [
                field
                for field, value in changes.items()
                if selected[field] != value
            ]

            duplicate = any(
                s["ΑΦΜ"] == new_afm
                and s["ID"] != selected_id
                for s in suppliers
            )

            if not changed_fields:
                st.info("Δεν πραγματοποιήθηκε κάποια αλλαγή.")

            elif not reason:
                st.error(
                    "Η αιτιολογία αλλαγής είναι υποχρεωτική."
                )

            elif not new_afm or not new_name:
                st.error(
                    "Το ΑΦΜ και η επωνυμία "
                    "δεν μπορούν να είναι κενά."
                )

            elif duplicate:
                st.error(
                    "Το νέο ΑΦΜ ανήκει ήδη "
                    "σε άλλον προμηθευτή."
                )

            elif (
                new_country == "Ελλάδα"
                and not valid_greek_afm(new_afm)
            ):
                st.error(
                    "Το νέο ελληνικό ΑΦΜ "
                    "δεν είναι μαθηματικά έγκυρο."
                )

            elif (
                new_country == "Εξωτερικό"
                and new_status == "Ενεργός"
            ):
                st.error(
                    "Τα ξένα VAT IDs παραμένουν "
                    "προς έλεγχο στη δοκιμαστική έκδοση."
                )

            else:
                old_afm = selected["ΑΦΜ"]

                for field in changed_fields:
                    add_history(
                        selected_id,
                        old_afm,
                        field,
                        selected[field],
                        changes[field],
                        reason
                    )

                    selected[field] = changes[field]

                st.success(
                    "Οι αλλαγές αποθηκεύτηκαν "
                    "στη δοκιμαστική συνεδρία!"
                )

                st.rerun()

    # --------------------------------------------------------
    # ΚΑΡΤΕΛΑ 4 — ΙΣΤΟΡΙΚΟ
    # --------------------------------------------------------

    with tab4:
        st.subheader("🕘 Ιστορικό Αλλαγών")

        history = st.session_state.supplier_history

        if history:
            st.dataframe(
                pd.DataFrame(history),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info(
                "Δεν υπάρχουν ακόμη αλλαγές."
            )

    # --------------------------------------------------------
    # ΚΑΡΤΕΛΑ 5 — ΕΛΕΓΧΟΣ ΑΦΜ
    # --------------------------------------------------------

    with tab5:
        st.subheader("🔍 Έλεγχος Ελληνικού ΑΦΜ")

        afm_check = st.text_input(
            "ΑΦΜ για έλεγχο"
        )

        if st.button("Έλεγχος εγκυρότητας"):
            if valid_greek_afm(afm_check):
                st.success(
                    "Το ΑΦΜ έχει έγκυρο "
                    "ψηφίο ελέγχου."
                )
            else:
                st.error(
                    "Το ΑΦΜ δεν περνά "
                    "τον μαθηματικό έλεγχο."
                )

        st.caption(
            "Δεν πραγματοποιείται διασταύρωση "
            "με την ΑΑΔΕ ή το VIES."
        )


# ============================================================
# ΜΗΤΡΩΟ ΚΑΤΗΓΟΡΙΩΝ
# ============================================================

elif page == "🗂️ Μητρώο Κατηγοριών":
    st.title("🗂️ Μητρώο Κατηγοριών")
    st.info(
        "Εδώ θα δημιουργήσουμε την αντιστοίχιση "
        "κατηγοριών των αλυσίδων με τις "
        "επίσημες κατηγορίες της υπηρεσίας."
    )


# ============================================================
# ΕΙΣΑΓΩΓΗ EXCEL
# ============================================================

elif page == "📥 Εισαγωγή Excel":
    st.title("📥 Εισαγωγή Excel")
    st.info(
        "Η εισαγωγή πραγματικών υπηρεσιακών Excel είναι απενεργοποιημένη στη δημόσια DEMO. "
        "Θα υλοποιηθεί μόνο σε εγκεκριμένο, προστατευμένο περιβάλλον."
    )


# ============================================================
# ΣΤΑΤΙΣΤΙΚΑ
# ============================================================

elif page == "📊 Στατιστικά & Αναφορές":
    st.title("📊 Στατιστικά & Αναφορές")
    st.caption("Ανάλυση αποκλειστικά συνθετικών δεδομένων")
    df = demo_prices()
    choice = st.selectbox("Ομαδοποίηση", ["Κατηγορία", "Αλυσίδα", "Προμηθευτής"])
    summary = df.groupby(choice).agg(
        Εγγραφές=("Μεταβολή %", "size"),
        Μέση_μεταβολή=("Μεταβολή %", "mean"),
        Μέγιστη_μεταβολή=("Μεταβολή %", "max"),
        Ελάχιστη_μεταβολή=("Μεταβολή %", "min")
    ).round(2).reset_index()
    st.dataframe(summary, use_container_width=True, hide_index=True)
    st.bar_chart(summary.set_index(choice)["Μέση_μεταβολή"], horizontal=True)


# ============================================================
# ΙΣΤΟΡΙΚΟ ΕΙΣΑΓΩΓΩΝ
# ============================================================

elif page == "🕘 Ιστορικό Εισαγωγών":
    st.title("🕘 Ιστορικό Εισαγωγών")
    st.info(
        "Εδώ θα καταγράφονται οι εισαγωγές Excel "
        "και τα αποτελέσματα των ελέγχων."
    )


# ============================================================
# ΡΥΘΜΙΣΕΙΣ
# ============================================================

elif page == "⚙️ Ρυθμίσεις":
    st.title("⚙️ Ρυθμίσεις")

    st.write("Εφαρμογή: Market Price Analytics")
    st.write("Τεχνολογία: Python / Streamlit")
    st.write("Έκδοση: Demo — Analytics & Supplier Registry v3")

    st.warning(
        "Η εφαρμογή είναι δημόσια δοκιμαστική. "
        "Δεν επιτρέπεται η καταχώριση "
        "πραγματικών υπηρεσιακών δεδομένων."
    )
