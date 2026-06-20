import streamlit as st
import pandas as pd
import re
from datetime import datetime
import sqlite3

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Attendance Portal", layout="wide")

# ---------------- BACKGROUND ----------------
st.markdown("""
<style>
.stApp{
background-color:#87CEEB;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DATABASE ----------------
conn = sqlite3.connect("attendance.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll TEXT,
    status TEXT,
    date TEXT
)
""")
conn.commit()

def insert_attendance(roll, status, date):
    c.execute("INSERT INTO attendance (roll, status, date) VALUES (?, ?, ?)",
              (roll, status, date))
    conn.commit()

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "master" not in st.session_state:
    st.session_state.master = None

if "teams" not in st.session_state:
    st.session_state.teams = None

# ---------------- FUNCTIONS ----------------
def extract_roll(text):
    text = str(text).upper()
    text = re.sub(r'[^A-Z0-9]', '', text)
    match = re.search(r'[0-9]{3}[A-Z0-9]{5,10}', text)
    return match.group() if match else None


def duration_minutes(duration):
    duration = str(duration).lower()

    h = re.search(r'(\d+)h', duration)
    m = re.search(r'(\d+)m', duration)
    s = re.search(r'(\d+)s', duration)

    h = int(h.group(1)) if h else 0
    m = int(m.group(1)) if m else 0
    s = int(s.group(1)) if s else 0

    return h * 60 + m + s / 60

# ---------------- LOGIN ----------------
st.image("oceanapps_logo.jpg", width=120)

st.title("OCEANAPPS TECHNOLOGIES")
st.subheader("Students Internship Attendance Portal")

username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    if username == "oceanapps" and password == "internships":
        st.session_state.logged_in = True
        st.success("Login Successful")
    else:
        st.error("Invalid Credentials")

# ---------------- MAIN APP ----------------
if st.session_state.logged_in:

    st.success("Welcome to Dashboard")

    menu = st.radio(
        "Menu",
        ["Upload Data", "Generate Attendance", "Overview"]
    )

    # ---------------- UPLOAD ----------------
    if menu == "Upload Data":

        master_file = st.file_uploader("Upload Master Roll List", type=["xlsx"])
        teams_file = st.file_uploader("Upload Teams Attendance", type=["xlsx"])

        if master_file:
            st.session_state.master = master_file

        if teams_file:
            st.session_state.teams = teams_file

    # ---------------- GENERATE ATTENDANCE ----------------
    if menu == "Generate Attendance":

        if st.button("Generate Attendance"):

            if st.session_state.master is None:
                st.error("Upload Master Roll List First")

            elif st.session_state.teams is None:
                st.error("Upload Teams File First")

            else:

                master_df = pd.read_excel(st.session_state.master)
                teams_df = pd.read_excel(st.session_state.teams)

                master_df.columns = master_df.columns.str.strip()
                teams_df.columns = teams_df.columns.str.strip()

                valid_rolls = []
                invalid_entries = []

                # ---------------- CLEAN TEAMS ----------------
                for _, row in teams_df.iterrows():

                    name = row.get("Name")

                    duration = None
                    for col in teams_df.columns:
                        if "duration" in col.lower():
                            duration = row[col]
                            break

                    if pd.isna(name) or duration is None:
                        continue

                    roll = extract_roll(name)

                    if roll is None:
                        invalid_entries.append([name, "Invalid / Name Only"])
                        continue

                    mins = duration_minutes(duration)

                    status = "P" if mins >= 15 else "A"

                    valid_rolls.append((roll, status))

                    insert_attendance(roll, status, str(datetime.today().date()))

                attendance_dict = dict(valid_rolls)

                # ---------------- MASTER MATCH ----------------
                today = str(datetime.today().date())
                master_df[today] = ""

                for idx, row in master_df.iterrows():

                    for col in master_df.columns[:-1]:

                        val = row[col]
                        roll = extract_roll(val)

                        if roll:
                            master_df.at[idx, today] = attendance_dict.get(roll, "A")
                            break

                df_final = master_df

                # ---------------- SUMMARY ----------------
                total = len(df_final)
                present = (df_final[today] == "P").sum()
                absent = (df_final[today] == "A").sum()

                st.subheader("Final Attendance (Master Order)")
                st.dataframe(df_final)

                st.success(f"Total Students: {total}")
                st.info(f"Present: {present}")
                st.error(f"Absent: {absent}")

                # ---------------- INVALID ENTRIES ----------------
                if len(invalid_entries) > 0:
                    st.subheader("Invalid Entries")
                    st.dataframe(pd.DataFrame(invalid_entries, columns=["Entry", "Reason"]))

                df_final.to_excel("attendance.xlsx", index=False)

                with open("attendance.xlsx", "rb") as f:
                    st.download_button("Download Attendance", f, "attendance.xlsx")

    # ---------------- OVERVIEW ----------------
    if menu == "Overview":

        conn = sqlite3.connect("attendance.db")
        df = pd.read_sql("SELECT * FROM attendance", conn)

        st.subheader("Database Records")
        st.dataframe(df)

        st.write("Total Records:", len(df))