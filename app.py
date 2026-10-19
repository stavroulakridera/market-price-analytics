
import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from io import BytesIO
import re

# ============================================================
# ΕΛΕΓΧΟΣ DRAFT (μόνο συνθετικά δεδομένα στη δημόσια DEMO)
# ============================================================
DRAFT_HEADERS = {
    "Ανατιμήσεις": [
        "ΑΦΜ", "ΠΡΟΜΗΘΕΥΤΗΣ", "ΣΟΥΠΕΡ ΜΑΡΚΕΤ", "ΚΑΤΗΓΟΡΙΑ", "ΠΡΟΪΟΝ", "BARCODE",
        "Τιμή αγοράς χονδρικής πριν την 19-09-2023",
        "Τιμή αγοράς χονδρικής πριν την τελευταία ανατίμηση",
        "Τιμή αγοράς χονδρικής μετά την τελευταία ανατίμηση",
        "Ημερομηνία ανακοίνωσης της τελευταίας ανατίμησης από τον προμηθευτή",
        "Ημερομηνία εφαρμογής της τελευταίας ανατίμησης από τον προμηθευτή",
    ],
    "Υποτιμήσεις": [
        "ΑΦΜ", "ΠΡΟΜΗΘΕΥΤΗΣ", "ΣΟΥΠΕΡ ΜΑΡΚΕΤ", "ΚΑΤΗΓΟΡΙΑ", "ΠΡΟΪΟΝ", "BARCODE",
        "Τιμή αγοράς χονδρικής πριν την 19-09-2023", "ΠΑΛΙΑ ΤΙΜΗ", "ΝΕΑ ΤΙΜΗ",
        "Ημερομηνία παλιάς τιμής έως και", "Ημερομηνία εφαρμογής της νέας τιμής",
    ],
}



# Επίσημος κατάλογος κατηγοριών από τον χρήστη (χωρίς υπηρεσιακές εγγραφές).
PRODUCT_CATEGORIES = ['ΑΛΕΥΡΙ', 'ΑΛΛΑΝΤΙΚΑ', 'ΑΝΑΨΥΚΤΙΚΑ', 'ΑΠΟΡΡΥΠΑΝΤΙΚΑ ΠΑΝΤΟΣ ΕΙΔΟΥΣ', 'ΑΡΤΟΣΚΕΥΑΣΜΑΤΑ', 'ΑΥΓΑ', 'ΑΦΡΟΛΟΥΤΡΟ Η ΑΝΤΙΣΤΟΙΧΑ', 'ΒΟΥΤΥΡΑ ΚΑΙ ΜΑΡΓΑΡΙΝΕΣ', 'ΓΑΛΑ ΒΡΕΦΙΚΗΣ ΗΛΙΚΙΑΣ', 'ΓΑΛΑ ΕΒΑΠΟΡΕ', 'ΓΑΛΑ ΥΨΗΛΗΣ ΠΑΣΤΕΡΙΩΣΗΣ (ΜΑΚΡΑΣ ΔΙΑΡΚΕΙΑΣ) ΠΛΗΡΕΣ ΚΑΙ ΜΕ ΧΑΜΗΛΑ ΛΙΠΑΡΑ', 'ΓΑΛΑ ΦΡΕΣΚΟ ΠΛΗΡΕΣ ΚΑΙ ΜΕ ΧΑΜΗΛΑ ΛΙΠΑΡΑ', 'ΓΙΑΟΥΡΤΙ ΚΑΙ ΕΠΙΔΟΡΠΙΑ ΓΙΑΟΥΡΤΙΟΥ', 'ΕΛΑΙΟΛΑΔΟ', 'ΖΑΧΑΡΗ ΚΑΙ ΓΛΥΚΑΝΤΙΚΕΣ ΟΥΣΙΕΣ', 'ΖΥΜΑΡΙΚΑ', 'ΚΑΤΕΨΥΓΜΕΝΑ ΛΑΧΑΝΙΚΑ', 'ΚΑΤΕΨΥΓΜΕΝΑ ΨΑΡΙΑ', 'ΚΑΤΕΨΥΓΜΕΝΕΣ ΖΥΜΕΣ', 'ΚΑΥΣΙΜΕΣ ΥΛΕΣ (ΚΑΥΣΟΞΥΛΑ, PELLETS, ΜΠΡΙΚΕΤΕΣ)', 'ΚΑΦΕΣ ΣΥΣΚΕΥΑΣΜΕΝΟΣ', 'ΚΕΤΣΑΠ', 'ΚΟΝΣΕΡΒΕΣ', 'ΚΡΑΣΙ', 'ΚΡΕΜΑ ΒΡΕΦΙΚΗΣ ΗΛΙΚΙΑΣ', 'ΚΡΕΜΕΣ ΚΑΙ ΡΥΖΟΓΑΛΟ', 'ΜΑΓΙΟΝΕΖΕΣ', 'ΜΑΡΜΕΛΑΔΕΣ ΚΑΙ ΕΙΔΗ ΕΠΑΛΕΙΨΗΣ', 'ΜΠΥΡΑ', 'ΜΩΡΟΜΑΝΤΗΛΑ', 'ΝΕΡΟ', 'ΝΩΠΟ ΚΟΤΟΠΟΥΛΟ ΚΑΙ ΜΕΡΗ ΚΟΤΟΠΟΥΛΟΥ', 'ΝΩΠΟ ΜΟΣΧΑΡΙ', 'ΝΩΠΟ ΧΟΙΡΙΝΟ', 'ΌΣΠΡΙΑ', 'ΠΑΝΕΣ ΑΚΡΑΤΕΙΑΣ', 'ΠΑΝΕΣ ΓΙΑ ΜΩΡΑ', 'ΠΡΟΪΟΝΤΑ ΒΡΩΜΗΣ', 'ΠΡΟΪΟΝΤΑ ΞΥΡΙΣΜΑΤΟΣ', 'ΠΡΟΪΟΝΤΑ ΣΤΟΜΑΤΙΚΗΣ ΥΓΙΕΙΝΗΣ', 'ΡΥΖΙ', 'ΣΑΛΤΣΕΣ ΚΑΙ ΚΥΒΟΙ ΖΩΜΩΝ', 'ΣΑΜΠΟΥΑΝ ΓΙΑ ΜΩΡΑ', 'ΣΑΜΠΟΥΑΝ ΚΑΙ ΠΡΟΪΟΝΤΑ ΠΕΡΙΠΟΙΗΣΗΣ ΜΑΛΛΙΩΝ', 'ΣΑΠΟΥΝΙΑ ΣΕ ΥΓΡΗ ΚΑΙ ΣΤΕΡΕΗ ΚΑΤΑΣΤΑΣΗ', 'ΣΕΡΒΙΕΤΕΣ Η ΤΑΜΠΟΝ', 'ΣΟΚΟΛΑΤΑ (ΣΤΕΡΕΗ ΚΑΙ ΡΟΦΗΜΑΤΑ)', 'ΣΟΚΟΛΑΤΟΥΧΟ ΓΑΛΑ', 'ΣΠΟΡΕΛΑΙΑ', 'ΤΡΟΦΕΣ ΓΙΑ ΓΑΤΕΣ', 'ΤΡΟΦΕΣ ΓΙΑ ΣΚΥΛΟΥΣ', 'ΤΥΡΙ', 'ΦΡΥΓΑΝΙΕΣ', 'ΦΥΤΙΚΑ ΡΟΦΗΜΑΤΑ', 'ΧΑΛΒΑΣ', 'ΧΑΡΤΙ ΚΟΥΖΙΝΑΣ', 'ΧΑΡΤΙ ΥΓΕΙΑΣ', 'ΧΥΜΟΙ', 'ΧΥΜΟΣ ΤΟΜΑΤΑΣ', 'ΨΩΜΙ ΚΑΙ ΨΩΜΙ ΓΙΑ ΤΟΣΤ', 'ΑΛΛΑ']

def normalize_category(value):
    return " ".join(str(value).split()).upper()

CATEGORY_LOOKUP = {normalize_category(item): item for item in PRODUCT_CATEGORIES}

# Επίσημες αλυσίδες σούπερ μάρκετ, όπως δόθηκαν από τον χρήστη.
SUPERMARKET_CHAINS = [
    "BAZAAR", "DISCOUNT MARKT", "LIDL", "MARKET IN", "METRO AEBE",
    "ΑΒ ΒΑΣΙΛΟΠΟΥΛΟΣ", "ΑΝΕΔΗΚ ΚΡΗΤΙΚΟΣ", "ΓΑΛΑΞΙΑΣ",
    "ΜΑΣΟΥΤΗΣ", "ΣΚΛΑΒΕΝΙΤΗΣ", "ΣΥΝΚΑ", "ΧΑΛΚΙΑΔΑΚΗΣ",
]

def normalize_chain(value):
    return " ".join(str(value).split()).upper()

CHAIN_LOOKUP = {normalize_chain(item): item for item in SUPERMARKET_CHAINS}

# Αντιστοιχίσεις DEMO: παραμένουν μόνο στη συνεδρία, όχι στο SharePoint.
# Κλειδί: (αλυσίδα, ονομασία κατηγορίας που δηλώνει η αλυσίδα).
# Η επίσημη κατηγορία είναι πάντοτε μία από τις PRODUCT_CATEGORIES.
def mapping_key(chain, raw_category):
    return (normalize_chain(chain), normalize_category(raw_category))


def resolve_product_category(chain, raw_category, mappings):
    key = mapping_key(chain, raw_category)
    if key in mappings:
        return mappings[key]
    official = CATEGORY_LOOKUP.get(normalize_category(raw_category))
    if official:
        return {"Κατηγορία": official, "Υποκατηγορία": ""}
    return None


def clean_identifier(value):
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return text[:-2] if re.fullmatch(r"\d+\.0", text) else text


def validate_draft(frame, kind, category_mappings=None):
    category_mappings = category_mappings or {}
    headers = DRAFT_HEADERS[kind]
    missing = [h for h in headers if h not in frame.columns]
    if missing:
        return None, ["Λείπουν στήλες: " + ", ".join(missing)]
    df = frame.loc[:, headers].copy().dropna(how="all")
    issues = []
    old_col, new_col = (headers[7], headers[8])
    for index, row in df.iterrows():
        excel_row = index + 2
        afm = clean_identifier(row["ΑΦΜ"])
        if not valid_greek_afm(afm):
            issues.append((excel_row, "ΑΦΜ", "Μη έγκυρο ή κενό ΑΦΜ"))
        for col in ["ΠΡΟΜΗΘΕΥΤΗΣ", "ΣΟΥΠΕΡ ΜΑΡΚΕΤ", "ΚΑΤΗΓΟΡΙΑ", "ΠΡΟΪΟΝ"]:
            if pd.isna(row[col]) or not str(row[col]).strip():
                issues.append((excel_row, col, "Υποχρεωτικό πεδίο"))
        if pd.notna(row["ΚΑΤΗΓΟΡΙΑ"]) and str(row["ΚΑΤΗΓΟΡΙΑ"]).strip():
            matched = resolve_product_category(row["ΣΟΥΠΕΡ ΜΑΡΚΕΤ"], row["ΚΑΤΗΓΟΡΙΑ"], category_mappings)
            if matched is None:
                issues.append((excel_row, "ΚΑΤΗΓΟΡΙΑ", "Δεν βρέθηκε αντιστοίχιση — προσθέστε την στο Μητρώο Κατηγοριών"))
        if pd.notna(row["ΣΟΥΠΕΡ ΜΑΡΚΕΤ"]) and str(row["ΣΟΥΠΕΡ ΜΑΡΚΕΤ"]).strip() and normalize_chain(row["ΣΟΥΠΕΡ ΜΑΡΚΕΤ"]) not in CHAIN_LOOKUP:
            issues.append((excel_row, "ΣΟΥΠΕΡ ΜΑΡΚΕΤ", "Δεν υπάρχει στον επίσημο κατάλογο αλυσίδων"))
        old = pd.to_numeric(row[old_col], errors="coerce")
        new = pd.to_numeric(row[new_col], errors="coerce")
        if pd.isna(old) or pd.isna(new) or old <= 0 or new <= 0:
            issues.append((excel_row, "ΤΙΜΕΣ", "Απαιτούνται θετικές αριθμητικές τιμές"))
        elif (kind == "Ανατιμήσεις" and new <= old) or (kind == "Υποτιμήσεις" and new >= old):
            issues.append((excel_row, "ΤΙΜΕΣ", "Η κατεύθυνση της μεταβολής δεν συμφωνεί με το DRAFT"))
        for col in headers[9:11]:
            if pd.isna(pd.to_datetime(row[col], errors="coerce", dayfirst=True)):
                issues.append((excel_row, col, "Μη έγκυρη ή κενή ημερομηνία"))
    key_cols = ["ΑΦΜ", "ΣΟΥΠΕΡ ΜΑΡΚΕΤ", "ΠΡΟΪΟΝ", "BARCODE", headers[10]]
    duplicate = df.assign(ΑΦΜ=df["ΑΦΜ"].map(clean_identifier)).duplicated(subset=key_cols, keep=False)
    for index in df.index[duplicate]:
        issues.append((index + 2, "ΔΙΠΛΟΤΥΠΟ", "Πιθανή διπλή εγγραφή μέσα στο DRAFT"))
    report = pd.DataFrame(issues, columns=["Γραμμή Excel", "Πεδίο", "Παρατήρηση"])
    return df, report


def synthetic_draft(kind):
    cols = DRAFT_HEADERS[kind]
    old, new = (1.20, 1.30) if kind == "Ανατιμήσεις" else (1.30, 1.20)
    return pd.DataFrame([
        ["", "DEMO ΠΡΟΜΗΘΕΥΤΗΣ", "BAZAAR", "ΑΛΕΥΡΙ", "DEMO ΠΡΟΪΟΝ", "0000000000000",
         1.10, old, new, "2026-10-01", "2026-10-05"]
    ], columns=cols)


# ============================================================
# ΡΥΘΜΙΣΕΙΣ ΕΦΑΡΜΟΓΗΣ
# ============================================================

st.set_page_config(
    page_title="Market Price Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

from auth import require_login, admin_screen
current_user = require_login()

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
            "ΧΩΡΑ": "Ελλάδα"
        },
        {
            "ID": 2,
            "ΑΦΜ": "123456789",
            "ΟΝΟΜΑΣΙΑ ΟΠΩΣ ΗΡΘΕ": "ΔΟΚΙΜΑΣΤΙΚΟΣ Β",
            "ΠΡΟΜΗΘΕΥΤΗΣ": "ΔΟΚΙΜΑΣΤΙΚΟΣ ΠΡΟΜΗΘΕΥΤΗΣ Β",
            "ΧΩΡΑ": "Ελλάδα"
        }
    ]


for supplier in st.session_state.suppliers:
    supplier.setdefault("ΟΝΟΜΑΣΙΑ ΟΠΩΣ ΗΡΘΕ", supplier.get("ΠΡΟΜΗΘΕΥΤΗΣ", ""))
    supplier.setdefault("ΧΩΡΑ", "Ελλάδα")
    supplier.pop("ΚΑΤΑΣΤΑΣΗ", None)  # Παλιές συνεδρίες χωρίς πεδίο κατάστασης

if "supplier_history" not in st.session_state:
    st.session_state.supplier_history = []



# ============================================================
# ΑΠΟΚΛΕΙΣΤΙΚΑ ΣΥΝΘΕΤΙΚΑ ΔΕΔΟΜΕΝΑ ΕΠΙΔΕΙΞΗΣ
# ============================================================

@st.cache_data
def demo_prices():
    products = ["Γάλα", "Γιαούρτι", "Τυρί", "Ρύζι", "Ζυμαρικά", "Ελαιόλαδο", "Καφές", "Αλεύρι", "Χυμός", "Απορρυπαντικό"]
    categories = ["ΓΑΛΑ ΦΡΕΣΚΟ ΠΛΗΡΕΣ ΚΑΙ ΜΕ ΧΑΜΗΛΑ ΛΙΠΑΡΑ", "ΓΙΑΟΥΡΤΙ ΚΑΙ ΕΠΙΔΟΡΠΙΑ ΓΙΑΟΥΡΤΙΟΥ", "ΤΥΡΙ", "ΑΛΕΥΡΙ", "ΖΥΜΑΡΙΚΑ", "ΕΛΑΙΟΛΑΔΟ", "ΚΑΦΕΣ ΣΥΣΚΕΥΑΣΜΕΝΟΣ", "ΡΥΖΙ", "ΧΥΜΟΙ", "ΑΠΟΡΡΥΠΑΝΤΙΚΑ ΠΑΝΤΟΣ ΕΙΔΟΥΣ"]
    chains = ["BAZAAR", "LIDL", "ΣΚΛΑΒΕΝΙΤΗΣ"]
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


INCREASE_COLUMNS = [
    "ΗΜΕΡΟΜΗΝΙΑ ΑΡΧΕΙΟΥ ΑΝΑΤΙΜΗΣΗΣ",
    "ΑΦΜ",
    "Ονομασία (όπως ήρθε)",
    "ΠΡΟΜΗΘΕΥΤΗΣ",
    "ΣΟΥΠΕΡ ΜΑΡΚΕΤ",
    "ΚΑΤΗΓΟΡΙΑ",
    "ΠΡΟΪΟΝ",
    "BARCODE",
    "Τιμή αγοράς χονδρικής πριν την 19-09-2023",
    "Τιμή αγοράς χονδρικής πριν την τελευταία ανατίμηση",
    "Τιμή αγοράς χονδρικής μετά την τελευταία ανατίμηση",
    "Ημερομηνία ανακοίνωσης της τελευταίας ανατίμησης από τον προμηθευτή",
    "Ημερομηνία εφαρμογής της τελευταίας ανατίμησης από τον προμηθευτή",
    "ΑΝΑΤΙΜΗΣΗ ΣΕ €",
    "ΠΟΣΟΣΤΙΑΙΑ ΑΝΑΤΙΜΗΣΗ(ΤΕΛΕΥΤΑΙΑ ΜΕ ΠΡΟ ΤΕΛΕΥΤΑΙΑ)",
    "ΠΟΣΟΣΤΙΑΙΑ ΑΝΑΤΙΜΗΣΗ (ΤΕΛΕΥΤΑΙΑ ΣΕ ΣΧΕΣΗ ΜΕ 19/9)",
]


def increase_table_demo(data):
    """16-column synthetic display; no real supplier or SharePoint data."""
    rows = []
    for i, (_, item) in enumerate(data.iterrows()):
        previous = float(item["Προηγούμενη τιμή"])
        latest = float(item["Νέα τιμή"])
        baseline = round(previous * (0.95 + (i % 4) * 0.02), 2)
        rows.append({
            INCREASE_COLUMNS[0]: (item["_week_wednesday"] if "_week_wednesday" in item.index else item["Ημερομηνία"]).strftime("%d/%m/%Y"),
            INCREASE_COLUMNS[1]: "DEMO",
            INCREASE_COLUMNS[2]: item["Προμηθευτής"],
            INCREASE_COLUMNS[3]: item["Προμηθευτής"],
            INCREASE_COLUMNS[4]: item["Αλυσίδα"],
            INCREASE_COLUMNS[5]: item["Κατηγορία"],
            INCREASE_COLUMNS[6]: item["Προϊόν"],
            INCREASE_COLUMNS[7]: f"DEMO-{i+1:06d}",
            INCREASE_COLUMNS[8]: baseline,
            INCREASE_COLUMNS[9]: previous,
            INCREASE_COLUMNS[10]: latest,
            INCREASE_COLUMNS[11]: item["Ημερομηνία"].strftime("%d/%m/%Y"),
            INCREASE_COLUMNS[12]: item["Ημερομηνία"].strftime("%d/%m/%Y"),
            INCREASE_COLUMNS[13]: round(latest - previous, 2),
            INCREASE_COLUMNS[14]: round((latest / previous - 1) * 100, 2),
            INCREASE_COLUMNS[15]: round((latest / baseline - 1) * 100, 2),
        })
    return pd.DataFrame(rows, columns=INCREASE_COLUMNS)


def price_table(data, increase=True):
    if data.empty:
        st.info("Δεν υπάρχουν εγγραφές για τα επιλεγμένα φίλτρα.")
        return
    display = data.copy().sort_values("Ημερομηνία", ascending=False)
    if increase:
        display = increase_table_demo(display)
        highlight_col = INCREASE_COLUMNS[14]
        styled = display.style.map(
            lambda v: "background-color: #ffe1e1; color: #8f1515; font-weight: bold"
            if pd.notna(v) and v > 3 else "", subset=[highlight_col]
        )
        column_config = {
            col: st.column_config.NumberColumn(format="%.2f €")
            for col in [INCREASE_COLUMNS[8], INCREASE_COLUMNS[9], INCREASE_COLUMNS[10], INCREASE_COLUMNS[13]]
        }
        column_config.update({
            col: st.column_config.NumberColumn(format="%.2f%%")
            for col in [INCREASE_COLUMNS[14], INCREASE_COLUMNS[15]]
        })
    else:
        display["Ημερομηνία"] = display["Ημερομηνία"].dt.strftime("%d/%m/%Y")
        styled = display.style.map(
            lambda v: "background-color: #e0f5e7; color: #166534; font-weight: bold" if v < 0 else "",
            subset=["Μεταβολή %"],
        )
        column_config = {
            "Προηγούμενη τιμή": st.column_config.NumberColumn(format="%.2f €"),
            "Νέα τιμή": st.column_config.NumberColumn(format="%.2f €"),
            "Μεταβολή %": st.column_config.NumberColumn(format="%.2f%%"),
        }
    st.dataframe(styled, use_container_width=True, hide_index=True, height=470,
                 column_config=column_config)
    st.download_button(
        "⬇️ Εξαγωγή φιλτραρισμένου πίνακα CSV (DEMO)",
        display.to_csv(index=False).encode("utf-8-sig"),
        file_name="demo_anatimiseis.csv" if increase else "demo_ypotimiseis.csv",
        mime="text/csv",
    )


def price_view(increase=True):
    df = demo_prices()
    df = df[df["Μεταβολή %"] > 0] if increase else df[df["Μεταβολή %"] < 0]
    st.subheader("Φίλτρα πίνακα")
    a, b, c = st.columns(3)
    chain = a.selectbox("Αλυσίδα", ["Όλες"] + sorted(df["Αλυσίδα"].unique().tolist()), key=f"chain_{increase}")
    category = b.selectbox("Κατηγορία", ["Όλες"] + sorted(df["Κατηγορία"].unique().tolist()), key=f"category_{increase}")
    supplier = c.selectbox("Προμηθευτής", ["Όλοι"] + sorted(df["Προμηθευτής"].unique().tolist()), key=f"supplier_{increase}")
    d, e = st.columns([2, 1])
    search = d.text_input("🔍 Αναζήτηση προϊόντος ή προμηθευτή", key=f"search_{increase}")
    if increase:
        # Περίοδος Πέμπτη–Τετάρτη: κάθε ημερομηνία αντιστοιχεί
        # στην αμέσως επόμενη (ή ίδια) Τετάρτη.
        wednesdays = df["Ημερομηνία"].dt.normalize() + pd.to_timedelta(
            (2 - df["Ημερομηνία"].dt.weekday) % 7, unit="D"
        )
        df = df.assign(_week_wednesday=wednesdays)
        available_weeks = sorted(df["_week_wednesday"].dt.date.unique(), reverse=True)
        selected_wednesday = e.selectbox(
            "Περίοδος Ανατιμήσεων (Πέμπτη–Τετάρτη)",
            options=[None] + available_weeks,
            format_func=lambda x: "Όλες οι εβδομάδες" if x is None else (
                f"{(x - timedelta(days=6)):%d/%m/%Y} – {x:%d/%m/%Y}"
            ),
            key="week_increase",
        )
        if selected_wednesday is not None:
            st.caption(f"Ημερομηνία αναφοράς: {selected_wednesday:%d/%m/%Y} (Τετάρτη)")
    else:
        date_range = e.date_input(
            "Περίοδος", value=(df["Ημερομηνία"].min().date(), df["Ημερομηνία"].max().date()),
            key="dates_decrease",
        )
    if chain != "Όλες":
        df = df[df["Αλυσίδα"] == chain]
    if category != "Όλες":
        df = df[df["Κατηγορία"] == category]
    if supplier != "Όλοι":
        df = df[df["Προμηθευτής"] == supplier]
    if search.strip():
        df = df[df["Προϊόν"].str.contains(search.strip(), case=False, regex=False) |
                df["Προμηθευτής"].str.contains(search.strip(), case=False, regex=False)]
    if increase:
        if selected_wednesday is not None:
            df = df[df["_week_wednesday"].dt.date == selected_wednesday]
    elif isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start, end = date_range
        df = df[df["Ημερομηνία"].dt.date.between(start, end)]

    x, y, z, w = st.columns(4)
    x.metric("Εγγραφές", len(df))
    y.metric("Μέση μεταβολή", f"{df['Μεταβολή %'].mean():.2f}%" if len(df) else "—")
    z.metric("Μέγιστη ανατίμηση" if increase else "Μεγαλύτερη υποτίμηση",
             f"{(df['Μεταβολή %'].max() if increase else df['Μεταβολή %'].min()):.2f}%" if len(df) else "—")
    w.metric("Ανατιμήσεις > 3%" if increase else "Εγγραφές μείωσης",
             int((df["Μεταβολή %"] > 3).sum()) if increase else len(df))

    st.subheader("Αναλυτικός πίνακας")
    if increase:
        st.caption("Κόκκινο μόνο για μεταβολές αυστηρά > 3%. Κάνε κλικ σε μια κεφαλίδα για ταξινόμηση.")
    else:
        st.caption("Πράσινη επισήμανση υποτιμήσεων. Κάνε κλικ σε μια κεφαλίδα για ταξινόμηση.")
    price_table(df, increase)

    st.subheader("Συγκεντρωτικός πίνακας ανά κατηγορία")
    if not df.empty:
        summary = df.groupby("Κατηγορία", as_index=False).agg(
            Εγγραφές=("Προϊόν", "size"),
            Μέση_μεταβολή=("Μεταβολή %", "mean"),
            Ελάχιστη_μεταβολή=("Μεταβολή %", "min"),
            Μέγιστη_μεταβολή=("Μεταβολή %", "max"),
        ).rename(columns={
            "Μέση_μεταβολή": "Μέση μεταβολή %",
            "Ελάχιστη_μεταβολή": "Ελάχιστη μεταβολή %",
            "Μέγιστη_μεταβολή": "Μέγιστη μεταβολή %",
        })
        for col in ["Μέση μεταβολή %", "Ελάχιστη μεταβολή %", "Μέγιστη μεταβολή %"]:
            summary[col] = summary[col].round(2)
        st.dataframe(summary, use_container_width=True, hide_index=True)
    else:
        st.info("Δεν υπάρχουν συγκεντρωτικά στοιχεία για τα επιλεγμένα φίλτρα.")

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
            "🏬 Αλυσίδες Σούπερ Μάρκετ",
            "📥 Εισαγωγή Excel",
            "📊 Στατιστικά & Αναφορές",
            "🕘 Ιστορικό Εισαγωγών",
            "⚙️ Ρυθμίσεις"
        ] + (["👥 Διαχείριση Χρηστών"] if current_user["role"] == "admin" else []),
        label_visibility="collapsed"
    )

    st.divider()
    st.caption(f"Συνδεδεμένος: {current_user['username']} ({current_user['role']})")
    if st.button("🚪 Αποσύνδεση"):
        st.session_state.pop("auth_username", None)
        st.session_state.pop("auth_last_seen", None)
        st.rerun()
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
    st.caption("Δοκιμαστικός πίνακας με τις 16 στήλες του φύλλου 2026 — μόνο συνθετικά δεδομένα.")
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

    c1, c2 = st.columns(2)
    c1.metric("Σύνολο Προμηθευτών", len(suppliers))
    c2.metric("Αλλαγές", len(st.session_state.supplier_history))

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

        filtered = []

        for s in suppliers:
            searchable = " ".join([
                s["ΑΦΜ"],
                s["ΟΝΟΜΑΣΙΑ ΟΠΩΣ ΗΡΘΕ"],
                s["ΠΡΟΜΗΘΕΥΤΗΣ"]
            ]).lower()

            if search.lower() in searchable:
                filtered.append(s)

        columns = [
            "ID",
            "ΑΦΜ",
            "ΟΝΟΜΑΣΙΑ ΟΠΩΣ ΗΡΘΕ",
            "ΠΡΟΜΗΘΕΥΤΗΣ",
            "ΧΩΡΑ"
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
                supplier_id = next_supplier_id()

                suppliers.append({
                    "ID": supplier_id,
                    "ΑΦΜ": afm,
                    "ΟΝΟΜΑΣΙΑ ΟΠΩΣ ΗΡΘΕ": original_name,
                    "ΠΡΟΜΗΘΕΥΤΗΣ": official_name,
                    "ΧΩΡΑ": country
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
                "ΧΩΡΑ": new_country
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

if "category_mappings" not in st.session_state:
    st.session_state.category_mappings = {}


elif page == "🗂️ Μητρώο Κατηγοριών":
    st.title("🗂️ Μητρώο Κατηγοριών")
    st.caption("Επίσημος κατάλογος κατηγοριών για τον έλεγχο των DRAFT Excel.")
    st.metric("Σύνολο κατηγοριών", len(PRODUCT_CATEGORIES))
    category_search = st.text_input("Αναζήτηση κατηγορίας", placeholder="Πληκτρολογήστε όνομα κατηγορίας")
    shown_categories = [item for item in PRODUCT_CATEGORIES if normalize_category(category_search) in normalize_category(item)]
    st.dataframe(pd.DataFrame({"Κατηγορία προϊόντος": shown_categories}), hide_index=True, use_container_width=True)
    st.divider()
    st.subheader("Υποκατηγορίες και αντιστοιχίσεις αλυσίδων")
    st.caption("Κάθε αλυσίδα μπορεί να έχει διαφορετική ονομασία. Η αντιστοίχιση εγκρίνεται από εμάς και συνδέεται με μία επίσημη κατηγορία.")
    with st.form("new_category_mapping", clear_on_submit=True):
        chain = st.selectbox("Αλυσίδα σούπερ μάρκετ", SUPERMARKET_CHAINS)
        raw_name = st.text_input("Κατηγορία όπως τη δηλώνει το σούπερ μάρκετ", placeholder="π.χ. INSTANT COFFEE")
        official = st.selectbox("Επίσημη κατηγορία", PRODUCT_CATEGORIES, index=PRODUCT_CATEGORIES.index("ΚΑΦΕΣ ΣΥΣΚΕΥΑΣΜΕΝΟΣ"))
        subcategory = st.text_input("Υποκατηγορία", placeholder="π.χ. Στιγμιαίος καφές")
        submitted = st.form_submit_button("Προσθήκη αντιστοίχισης", type="primary")
    if submitted:
        if not raw_name.strip() or not subcategory.strip():
            st.error("Συμπλήρωσε την ονομασία της αλυσίδας και την υποκατηγορία.")
        elif mapping_key(chain, raw_name) in st.session_state.category_mappings:
            st.error("Η αντιστοίχιση υπάρχει ήδη για αυτή την αλυσίδα. Δεν αντικαταστάθηκε.")
        else:
            st.session_state.category_mappings[mapping_key(chain, raw_name)] = {
                "Κατηγορία": official,
                "Υποκατηγορία": " ".join(subcategory.split()),
            }
            st.success("Η αντιστοίχιση προστέθηκε στη δοκιμαστική συνεδρία.")
    mappings_rows = [
        {"Αλυσίδα": chain_name, "Κατηγορία αλυσίδας": raw,
         "Επίσημη κατηγορία": target["Κατηγορία"], "Υποκατηγορία": target["Υποκατηγορία"]}
        for (chain_name, raw), target in st.session_state.category_mappings.items()
    ]
    if mappings_rows:
        st.dataframe(pd.DataFrame(mappings_rows), hide_index=True, use_container_width=True)
    else:
        st.info("Δεν έχουν προστεθεί ακόμη αντιστοιχίσεις στη δοκιμαστική συνεδρία.")
    st.caption("DEMO: Οι αλλαγές χάνονται όταν λήξει η συνεδρία. Δεν αποθηκεύονται στο SharePoint.")


# ============================================================
# ΜΗΤΡΩΟ ΑΛΥΣΙΔΩΝ ΣΟΥΠΕΡ ΜΑΡΚΕΤ
# ============================================================

elif page == "🏬 Αλυσίδες Σούπερ Μάρκετ":
    st.title("🏬 Αλυσίδες Σούπερ Μάρκετ")
    st.caption("Επίσημος κατάλογος αλυσίδων για τον έλεγχο των DRAFT Excel.")
    st.metric("Σύνολο αλυσίδων", len(SUPERMARKET_CHAINS))
    chain_search = st.text_input("Αναζήτηση αλυσίδας", placeholder="Πληκτρολογήστε επωνυμία αλυσίδας")
    shown_chains = [item for item in SUPERMARKET_CHAINS if normalize_chain(chain_search) in normalize_chain(item)]
    st.dataframe(pd.DataFrame({"Αλυσίδα σούπερ μάρκετ": shown_chains}), hide_index=True, use_container_width=True)
    st.caption("Οι αλυσίδες είναι σταθερές στη δημόσια demo. Δεν γίνεται εγγραφή στο SharePoint.")


# ============================================================
# ΕΙΣΑΓΩΓΗ EXCEL
# ============================================================

elif page == "📥 Εισαγωγή Excel":
    st.title("📥 Εισαγωγή Excel")
    st.warning("ΔΗΜΟΣΙΑ DEMO: Μην ανεβάζετε πραγματικά υπηρεσιακά αρχεία, ΑΦΜ ή στοιχεία προμηθευτών. Δεν πραγματοποιείται αποθήκευση στο SharePoint.")
    kind = st.radio("Τύπος DRAFT", ["Ανατιμήσεις", "Υποτιμήσεις"], horizontal=True)
    st.caption("Οι αναμενόμενες επικεφαλίδες προέρχονται από τα δύο πρότυπα DRAFT.")
    with st.expander("Αναμενόμενες στήλες"):
        st.dataframe(pd.DataFrame({"Στήλη": DRAFT_HEADERS[kind]}), hide_index=True, use_container_width=True)
    st.subheader("Δοκιμή ελέγχων με συνθετικά δεδομένα")
    st.caption("Το παράδειγμα περιέχει σκόπιμα κενό ΑΦΜ, για να φανεί η αναφορά ελέγχου.")
    demo = synthetic_draft(kind)
    st.dataframe(demo, hide_index=True, use_container_width=True)
    if st.button("Έλεγχος δοκιμαστικού DRAFT", type="primary"):
        checked, report = validate_draft(demo, kind, st.session_state.category_mappings)
        st.metric("Εγγραφές", len(checked))
        if report.empty:
            st.success("Δεν βρέθηκαν προβλήματα.")
        else:
            st.error(f"Βρέθηκαν {len(report)} παρατηρήσεις. Δεν εγκρίνεται εισαγωγή.")
            st.dataframe(report, hide_index=True, use_container_width=True)
            st.download_button("Λήψη αναφοράς ελέγχου CSV", report.to_csv(index=False).encode("utf-8-sig"), "elegxos_draft.csv", "text/csv")
    st.info("Η φόρτωση πραγματικού DRAFT και η εγγραφή στο υπάρχον SharePoint Excel θα ενεργοποιηθούν μόνο σε εγκεκριμένη ιδιωτική εγκατάσταση, με έλεγχο αντιστοίχισης στηλών, δικαιώματα, αντίγραφο ασφαλείας και αποφυγή διπλοεγγραφών.")


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

    if current_user["role"] == "admin":
        st.subheader("🔌 Έλεγχος σύνδεσης Supabase (μόνο ανάγνωση)")
        if st.button("Έλεγχος PostgreSQL", key="db_smoke_test"):
            try:
                from db import check_schema
                tables = check_schema()
                st.success(f"Η σύνδεση πέτυχε. Βρέθηκαν {len(tables)} πίνακες στο schema mpa.")
                st.write(", ".join(tables) if tables else "Δεν βρέθηκαν πίνακες στο mpa.")
            except Exception:
                st.error("Η σύνδεση απέτυχε. Έλεγξε τα Streamlit Secrets, το SSL και τις ρυθμίσεις δικτύου του Supabase. Ο κωδικός δεν εμφανίζεται.")


    st.write("Εφαρμογή: Market Price Analytics")
    st.write("Τεχνολογία: Python / Streamlit")
    st.write("Έκδοση: Demo — Analytics & Supplier Registry v3")

    st.warning(
        "Η εφαρμογή είναι δημόσια δοκιμαστική. "
        "Δεν επιτρέπεται η καταχώριση "
        "πραγματικών υπηρεσιακών δεδομένων."
    )

elif page == "👥 Διαχείριση Χρηστών":
    admin_screen(current_user)
