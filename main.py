import datetime
import streamlit as st
import google.generativeai as genai
import sqlite3

# ==============================
# 🛠️ UI CONFIGURATION
# ==============================
# Set page configuration must be the first Streamlit command
st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Apply custom CSS for better aesthetics (e.g., button style)
st.markdown(
    """
    <style>
    /* Change primary color for buttons */
    .stButton>button {
        background-color: #4CAF50; /* Green */
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 24px;
        border: none;
        transition: background-color 0.3s;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    /* Customize the form submit button color (Blue) */
    div.stForm button {
        background-color: #008CBA !important; 
    }
    div.stForm button:hover {
        background-color: #007bb5 !important;
    }
    /* Style for the main app title */
    .main-title {
        font-size: 2.5em;
        color: #008CBA;
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==============================
# 📌 DATABASE SETUP (SQLite)
# ==============================

# Create/connect to SQLite database
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

# Create users table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT
    )
""")
conn.commit()

# ==============================
# 📌 SESSION STATES
# ==============================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "show_signup" not in st.session_state:
    st.session_state.show_signup = False


# ==============================
# 🆕 SIGN-UP PAGE
# ==============================

def signup_page():
    # Use a container for centering and background
    with st.container(border=True):
        st.markdown("<h1 style='text-align: center; color: #4CAF50;'>🆕 Create New Account</h1>", unsafe_allow_html=True)
        
        with st.form("signup_form"):
            new_user = st.text_input("Choose Username", help="Must be unique.")
            new_pass = st.text_input("Choose Password", type="password")

            submit_btn = st.form_submit_button("Create Account")

            if submit_btn:
                if new_user == "" or new_pass == "":
                    st.error("Username and password cannot be empty.")
                else:
                    cursor.execute("SELECT * FROM users WHERE username=?", (new_user,))
                    if cursor.fetchone():
                        st.error("Username already exists!")
                    else:
                        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                                       (new_user, new_pass))
                        conn.commit()

                        st.success("Account created successfully! Please login.")
                        st.session_state.show_signup = False
                        st.rerun()
        
        if st.button("Back to Login", key="signup_back_btn"):
            st.session_state.show_signup = False
            st.rerun()


# ==============================
# 🔐 LOGIN PAGE
# ==============================

def login_page():
    # Use a container for centering and background
    with st.container(border=True):
        st.markdown("<h1 style='text-align: center; color: #008CBA;'>🔐 AI Travel Planner Login</h1>", unsafe_allow_html=True)

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        col1, col2 = st.columns(2)

        with col1:
            login_btn = st.button("Login", use_container_width=True)

        with col2:
            signup_btn = st.button("Create New Account", use_container_width=True)

        if login_btn:
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                           (username, password))
            record = cursor.fetchone()

            if record:
                st.session_state.logged_in = True
                st.session_state.username = username # Store username
                st.success("Login successful! Redirecting...")
                st.balloons()
                st.rerun()
            else:
                st.error("Invalid username or password.")

        if signup_btn:
            st.session_state.show_signup = True
            st.rerun()


# ==============================
# 🌍 TRAVEL PLANNER APP
# ==============================

def travel_planner_app():

    st.markdown("<h1 class='main-title'>AI Travel Planner 🌍✈️🚗🚂🚆</h1>", unsafe_allow_html=True)
    st.info(f"Welcome back, **{st.session_state.username.title()}**! Plan your next adventure.")

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    with st.expander("Plan Your Trip Details", expanded=True):
        with st.form("travel_form"):
            
            # Use columns for better layout of input fields
            col_a, col_b = st.columns(2)
            with col_a:
                starting_point = st.text_input("📍 Starting Point (City or Landmark)", placeholder="Enter Starting Point")
                starting_date = st.date_input("📅 Starting Date", min_value=datetime.date.today())
                currency = st.selectbox("💰 Currency", ["INR", "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CNY"])
            
            with col_b:
                destinations = st.text_input("🗺️ Destination(s) (comma-separated)", placeholder="Enter destinations")
                ending_date = st.date_input("🏁 Ending Date", min_value=starting_date)
                budget = st.number_input("💵 Budget (Total Estimate)", min_value=5000, help=f"Enter budget in {currency}")
            
            trip_type = st.radio("✨ Trip Style", 
                                 ["Adventure", "Cultural", "Family", "Solo", "Budget", "Luxury"], 
                                 horizontal=True)

            st.markdown("---")
            submit_btn = st.form_submit_button("Get Travel Plan", use_container_width=True)

    if submit_btn:
        if not starting_point or not destinations:
            st.error("Please enter both a Starting Point and at least one Destination.")
        elif starting_date > ending_date:
            st.error("The ending date cannot be before the starting date.")
        else:
            st.subheader("Your Personalized Travel Plan:")
            output_area = st.empty()

            # 🛑 The AI Prompt is kept exactly as requested 🛑
            prompt = f"""
            Create a well-structured travel itinerary.

            Trip Details:
            Starting Point: {starting_point}
            Destinations: {destinations}
            From: {starting_date}
            To: {ending_date}
            Budget: {budget} {currency}
            Travel Style: {trip_type}

            Provide:
            - Transport options and booking links
            - Hotel recommendations
            - Daily attractions
            - Weather & travel advisories

            Keep it practical and easy to read.
            """

            try:
                model = genai.GenerativeModel("gemini-2.0-flash")
                response = model.generate_content(prompt, stream=True)

                final_text = ""

                with st.spinner("Generating your itinerary... this might take a moment."):
                    for chunk in response:
                        if chunk.text:
                            final_text += chunk.text
                            # Use markdown to render the AI's structured output
                            output_area.markdown(final_text, unsafe_allow_html=True) 

                st.success("Your travel plan is ready! Enjoy your trip! ✨")

            except Exception as e:
                st.error(f"An error occurred during AI generation: {e}")

    st.markdown("---")
    
    # 📌 FIX FOR BUTTON UI: Use a wider column ratio [3, 2, 3] and disable container width 
    # to prevent the button text from wrapping vertically.
    logout_col = st.columns([3, 2, 3])[1]
    with logout_col:
        if st.button("Logout", use_container_width=False):
            st.session_state.logged_in = False
            if 'username' in st.session_state:
                del st.session_state.username
            st.rerun()


# ==============================
# 🚦 PAGE ROUTING LOGIC
# ==============================

if st.session_state.logged_in:
    travel_planner_app()

else:
    if st.session_state.show_signup:
        signup_page()
    else:

        login_page()
