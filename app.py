
import streamlit as st
import sqlite3
from datetime import datetime

# DB setup
conn = sqlite3.connect('tracker.db', check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
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
    from_machine TEXT,
    to_machine TEXT,
    timestamp TEXT
)
''')

conn.commit()

# Initial components
default_components = ['Compressor', 'Suction Pump', 'Vacuum Pump', 'HMI', 'Filter']
for comp in default_components:
    c.execute("INSERT OR IGNORE INTO components (name, current_machine) VALUES (?, ?)", (comp, 'Machine A'))

# Initial machines
default_machines = ['Machine A', 'Machine B', 'Machine C', 'Machine D', 'Machine E']
for machine in default_machines:
    c.execute("INSERT OR IGNORE INTO machines (name) VALUES (?)", (machine,))

conn.commit()

st.set_page_config(layout="wide")
st.title("🧩 Component Tracker")

menu = st.sidebar.radio("View", ["Component Cards", "Machine View", "Move Component", "History Logs"])

if menu == "Component Cards":
    st.subheader("Component Status")
    cols = st.columns(3)
    c.execute("SELECT name, current_machine FROM components")
    for i, (name, machine) in enumerate(c.fetchall()):
        with cols[i % 3]:
            with st.expander(f"🔧 {name}"):
                st.markdown(f"**Current Machine:** {machine}")
                c.execute("SELECT from_machine, to_machine, timestamp FROM movements WHERE component = ? ORDER BY id DESC", (name,))
                history = c.fetchall()
                if history:
                    st.markdown("**Movement History:**")
                    for h in history:
                        st.markdown(f"- `{h[2]}`: {h[0]} ➝ {h[1]}")

elif menu == "Machine View":
    st.subheader("Machines and Their Components")
    c.execute("SELECT name FROM machines")
    machines = [m[0] for m in c.fetchall()]
    for machine in machines:
        with st.expander(f"🏭 {machine}"):
            c.execute("SELECT name FROM components WHERE current_machine = ?", (machine,))
            comps = c.fetchall()
            if comps:
                st.markdown("**Components Currently Here:**")
                for comp in comps:
                    st.markdown(f"- {comp[0]}")
            c.execute("SELECT component, from_machine, to_machine, timestamp FROM movements WHERE from_machine = ? OR to_machine = ? ORDER BY id DESC", (machine, machine))
            moves = c.fetchall()
            if moves:
                st.markdown("**Movement Logs:**")
                for m in moves:
                    st.markdown(f"- `{m[3]}`: {m[0]} ➝ {m[2]} (from {m[1]})")

elif menu == "Move Component":
    st.subheader("Move a Component")
    c.execute("SELECT name FROM components")
    component_list = [c[0] for c in c.fetchall()]
    c.execute("SELECT name FROM machines")
    machine_list = [m[0] for m in c.fetchall()]
    comp = st.selectbox("Select Component", component_list)
    to_machine = st.selectbox("Move To Machine", machine_list)
    if st.button("Move"):
        c.execute("SELECT current_machine FROM components WHERE name = ?", (comp,))
        from_machine = c.fetchone()[0]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO movements (component, from_machine, to_machine, timestamp) VALUES (?, ?, ?, ?)",
                  (comp, from_machine, to_machine, timestamp))
        c.execute("UPDATE components SET current_machine = ? WHERE name = ?", (to_machine, comp))
        conn.commit()
        st.success(f"{comp} moved from {from_machine} to {to_machine}")

elif menu == "History Logs":
    st.subheader("Movement History Log")
    c.execute("SELECT component, from_machine, to_machine, timestamp FROM movements ORDER BY id DESC")
    logs = c.fetchall()
    for log in logs:
        st.markdown(f"- `{log[3]}`: **{log[0]}** moved from **{log[1]}** to **{log[2]}**")

conn.close()
