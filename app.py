import streamlit as st
import sqlite3
from datetime import datetime

# DB setup
conn = sqlite3.connect('tracker.db', check_same_thread=False)
c = conn.cursor()

# Create tables
c.execute('''
CREATE TABLE IF NOT EXISTS components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    serial_number TEXT UNIQUE,
    current_machine TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS machines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component TEXT,
    serial_number TEXT,
    from_machine TEXT,
    to_machine TEXT,
    timestamp TEXT
)
''')

conn.commit()

# Default machines
default_machines = ['Machine A', 'Machine B', 'Machine C', 'Machine D', 'Machine E']
for machine in default_machines:
    c.execute("INSERT OR IGNORE INTO machines (name) VALUES (?)", (machine,))
conn.commit()

st.set_page_config(layout="wide")
st.title("🧩 Component Tracker v2")

menu = st.sidebar.radio(
    "View",
    ["Component Cards", "Machine View", "Move Component", "History Logs", "Add Machine", "Add Component"]
)

# Add new machine
if menu == "Add Machine":
    st.subheader("Add New Machine")
    new_machine = st.text_input("Machine Name")
    if st.button("Add Machine"):
        if new_machine:
            c.execute("INSERT OR IGNORE INTO machines (name) VALUES (?)", (new_machine,))
            conn.commit()
            st.success(f"Machine '{new_machine}' added successfully!")

# Add new component with serial number
elif menu == "Add Component":
    st.subheader("Add New Component")
    name = st.text_input("Component Name")
    serial = st.text_input("Serial Number")
    c.execute("SELECT name FROM machines")
    machines = [m[0] for m in c.fetchall()]
    machine = st.selectbox("Assign to Machine", machines)
    if st.button("Add Component"):
        if name and serial and machine:
            c.execute("INSERT OR IGNORE INTO components (name, serial_number, current_machine) VALUES (?, ?, ?)",
                      (name, serial, machine))
            conn.commit()
            st.success(f"Component '{name}' with Serial '{serial}' added to '{machine}'")

# View component cards
elif menu == "Component Cards":
    st.subheader("Component Cards")
    cols = st.columns(3)
    c.execute("SELECT name, serial_number, current_machine FROM components")
    for i, (name, serial, machine) in enumerate(c.fetchall()):
        with cols[i % 3]:
            with st.expander(f"🔧 {name} (S/N: {serial})"):
                st.markdown(f"**Current Machine:** {machine}")
                c.execute("SELECT from_machine, to_machine, timestamp FROM movements WHERE serial_number = ? ORDER BY id DESC", (serial,))
                history = c.fetchall()
                if history:
                    st.markdown("**Movement History:**")
                    for h in history:
                        st.markdown(f"- `{h[2]}`: {h[0]} ➝ {h[1]}")

# Machine view
elif menu == "Machine View":
    st.subheader("Machines and Their Components")
    c.execute("SELECT name FROM machines")
    machines = [m[0] for m in c.fetchall()]
    for machine in machines:
        with st.expander(f"🏭 {machine}"):
            c.execute("SELECT name, serial_number FROM components WHERE current_machine = ?", (machine,))
            comps = c.fetchall()
            if comps:
                st.markdown("**Components Here:**")
                for comp in comps:
                    st.markdown(f"- {comp[0]} (S/N: {comp[1]})")
            c.execute(
                "SELECT component, serial_number, from_machine, to_machine, timestamp FROM movements WHERE from_machine = ? OR to_machine = ? ORDER BY id DESC",
                (machine, machine)
            )
            moves = c.fetchall()
            if moves:
                st.markdown("**Movement Logs:**")
                for m in moves:
                    st.markdown(f"- `{m[4]}`: {m[0]} (S/N: {m[1]}) ➝ {m[3]}")

# Move components
elif menu == "Move Component":
    st.subheader("Move Component")
    c.execute("SELECT name, serial_number FROM components")
    comps = c.fetchall()
    comp = st.selectbox("Select Component", [f"{c[0]} (S/N: {c[1]})" for c in comps])
    serial = comp.split("S/N: ")[1].replace(")", "").strip()
    c.execute("SELECT name FROM machines")
    machines = [m[0] for m in c.fetchall()]
    to_machine = st.selectbox("Move To Machine", machines)
    if st.button("Move"):
        c.execute("SELECT current_machine FROM components WHERE serial_number = ?", (serial,))
        from_machine = c.fetchone()[0]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO movements (component, serial_number, from_machine, to_machine, timestamp) VALUES (?, ?, ?, ?, ?)",
                  (comp.split(" (S/N")[0], serial, from_machine, to_machine, timestamp))
        c.execute("UPDATE components SET current_machine = ? WHERE serial_number = ?", (to_machine, serial))
        conn.commit()
        st.success(f"{comp} moved from {from_machine} to {to_machine}")

# History Logs with delete option
elif menu == "History Logs":
    st.subheader("Movement History Logs")
    c.execute("SELECT component, serial_number, from_machine, to_machine, timestamp FROM movements ORDER BY id DESC")
    logs = c.fetchall()
    for log in logs:
        st.markdown(f"- `{log[4]}`: **{log[0]} (S/N: {log[1]})** from **{log[2]}** ➝ **{log[3]}**")

    st.warning("Danger Zone: Delete Logs")
    c.execute("SELECT DISTINCT serial_number FROM movements")
    serials = [s[0] for s in c.fetchall()]
    if serials:
        del_serial = st.selectbox("Delete logs for serial number:", serials)
        if st.button("Delete Selected History"):
            c.execute("DELETE FROM movements WHERE serial_number = ?", (del_serial,))
            conn.commit()
            st.success(f"Deleted history for serial number {del_serial}")

    if st.button("❗ Delete ALL Movement History"):
        c.execute("DELETE FROM movements")
        conn.commit()
        st.success("All movement history cleared.")

conn.close()
