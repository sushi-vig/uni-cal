import streamlit as st
from streamlit_calendar import calendar
import datetime
import pandas as pd
from ics import Calendar, Event
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="🌸 My Schedule 🌸",
    page_icon=" M",
    layout="wide",
    initial_sidebar_state="auto"
)

# --- Enhanced Pastel Theme (via Custom CSS) ---
st.markdown("""
    <style>
        /* Main background color */
        .stApp {
            background-color: #F0F8FF; /* Alice Blue */
        }

        /* Main content area styling */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            padding-left: 5rem;
            padding-right: 5rem;
            background-color: #FFFFFF;
            border-radius: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }

        /* Title styling */
        h1 {
            color: #4682B4; /* Steel Blue */
            text-align: center;
            font-weight: bold;
        }

        /* Subheader styling */
        h2, h3 {
            color: #5F9EA0; /* Cadet Blue */
        }
        
        /* Button styling */
        .stButton>button {
            background-color: #B0E0E6; /* Powder Blue */
            color: #36454F;
            border: 2px solid #4682B4;
            border-radius: 10px;
            padding: 10px 20px;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #4682B4;
            color: white;
            border-color: #B0E0E6;
        }
        
        /* Styling for the calendar component */
        .fc-toolbar-title {
            color: #4682B4 !important;
        }
        .fc-daygrid-day-number {
             color: #36454F !important;
        }
        .fc-col-header-cell-cushion {
            color: #4682B4 !important;
            font-weight: bold;
        }

    </style>
""", unsafe_allow_html=True)

# --- Data Persistence ---
BOOKINGS_FILE = "bookings.csv"

def load_bookings():
    """Loads bookings from the CSV file. If the file doesn't exist, creates it."""
    if not os.path.exists(BOOKINGS_FILE):
        df = pd.DataFrame(columns=["start", "end", "title", "email", "phone", "notes"])
        df.to_csv(BOOKINGS_FILE, index=False)
    return pd.read_csv(BOOKINGS_FILE)

def save_booking(date, time, name, email, phone, notes):
    """Saves a new booking to the CSV file."""
    start_dt = datetime.datetime.combine(date, datetime.datetime.strptime(time, "%H:%M").time())
    end_dt = start_dt + datetime.timedelta(minutes=30) # Assuming 30-min slots
    
    new_booking = pd.DataFrame([{
        "start": start_dt.isoformat(),
        "end": end_dt.isoformat(),
        "title": f"Meeting with {name}",
        "email": email,
        "phone": phone,
        "notes": notes
    }])
    new_booking.to_csv(BOOKINGS_FILE, mode='a', header=False, index=False)

# --- Load existing bookings ---
bookings_df = load_bookings()

# --- Initialize Session State ---
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = None
if 'selected_time' not in st.session_state:
    st.session_state.selected_time = None
if 'view' not in st.session_state:
    st.session_state.view = 'calendar'

# --- Sidebar for Import/Export ---
with st.sidebar:
    st.header("🗓️ Calendar Tools")
    st.write("Manage your schedule across different platforms.")
    
    st.subheader("Import Schedule")
    st.info("This feature is coming soon! It will allow you to sync your live availability.")
    st.button("Import from Google Calendar", disabled=True)
    st.button("Import from Outlook Calendar", disabled=True)
    
    st.subheader("Export Schedule")
    
    # Create the .ics file content
    cal = Calendar()
    if not bookings_df.empty:
      for index, row in bookings_df.iterrows():
          event = Event()
          event.name = row['title']
          event.begin = row['start']
          event.end = row['end']
          event.description = row['notes']
          cal.events.add(event)

    st.download_button(
        label="Export Schedule (.ics)",
        data=str(cal),
        file_name="my_schedule.ics",
        mime="text/calendar",
    )

# --- Get View from URL Query Parameter ---
view_mode = st.query_params.get('view')

# --- Header ---
st.title("Schedule a Meeting with Me 🌸")
if view_mode == 'friends':
    st.markdown("<p style='text-align: center; color: #696969;'>Showing full 24/7 availability for friends & family.</p>", unsafe_allow_html=True)
else:
    st.markdown("<p style='text-align: center; color: #696969;'>Showing professional availability (Weekdays, 10 AM - 4 PM).</p>", unsafe_allow_html=True)
st.markdown("---")

# --- Main Layout ---
col1, col2 = st.columns([1.2, 1])

with col1:
    st.subheader("1. Select a Date")
    
    # Convert bookings to the format required by the calendar component
    calendar_events = []
    if not bookings_df.empty:
        for index, row in bookings_df.iterrows():
            calendar_events.append({
                "title": row["title"],
                "start": row["start"],
                "end": row["end"],
                "color": "#4682B4" # Steel Blue for booked events
            })

    calendar_options = {
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
        "initialView": "dayGridMonth",
        "selectable": True,
        "events": calendar_events,
    }
    
    selected_calendar_date = calendar(events=calendar_events, options=calendar_options, key="calendar")

    if selected_calendar_date and selected_calendar_date.get("dateClick"):
        clicked_date_str = selected_calendar_date["dateClick"]["date"].split("T")[0]
        st.session_state.selected_date = datetime.datetime.strptime(clicked_date_str, "%Y-%m-%d").date()
        st.session_state.selected_time = None
        st.session_state.view = 'calendar'

with col2:
    if not st.session_state.selected_date:
        st.info("Please select a date from the calendar to see available times.")
    else:
        st.subheader(f"2. Select a Time for {st.session_state.selected_date.strftime('%A, %B %d')}")
        
        # --- Generate time slots based on view mode ---
        is_weekday = st.session_state.selected_date.weekday() < 5  # Monday=0, Sunday=6

        if view_mode == 'friends':
            all_times = [(datetime.datetime.min + datetime.timedelta(minutes=30 * i)).strftime('%H:%M') for i in range(48)]
        else: # Professional view
            if is_weekday:
                all_times = [
                    "10:00", "10:30", "11:00", "11:30",
                    "12:00", "12:30", "13:00", "13:30",
                    "14:00", "14:30", "15:00", "15:30",
                ]
            else:
                all_times = []
        
        # --- Filter out booked times ---
        booked_times_for_date = []
        if not bookings_df.empty:
            booked_starts = pd.to_datetime(bookings_df['start'])
            booked_times_for_date = [
                dt.strftime('%H:%M') for dt in booked_starts
                if dt.date() == st.session_state.selected_date
            ]
        
        available_times = [t for t in all_times if t not in booked_times_for_date]
        
        if not available_times:
            if view_mode != 'friends' and not is_weekday:
                st.warning("Bookings are only available on weekdays for this professional link.")
            else:
                st.warning("Sorry, there are no available slots on this day.")
        else:
            time_cols = st.columns(4)
            for i, time in enumerate(available_times):
                if time_cols[i % 4].button(time, key=f"time_{time}"):
                    st.session_state.selected_time = time
                    st.session_state.view = 'form'
                    st.rerun()

# --- Booking Form or Confirmation ---
if st.session_state.view == 'form' and st.session_state.selected_date and st.session_state.selected_time:
    st.markdown("---")
    st.subheader("3. Enter Your Details to Book")
    
    with st.form("booking_form"):
        st.write(f"You are booking the **{st.session_state.selected_time}** slot on **{st.session_state.selected_date.strftime('%A, %B %d')}**.")
        name = st.text_input("Your Name *")
        email = st.text_input("Your Email *")
        phone = st.text_input("Phone Number (Optional)")
        notes = st.text_area("Message / Reason for meeting *")
        
        submitted = st.form_submit_button("Confirm Booking")
        
        if submitted:
            if not name or not email or not notes:
                st.error("Please fill in all required fields (*).")
            else:
                save_booking(st.session_state.selected_date, st.session_state.selected_time, name, email, phone, notes)
                st.session_state.view = 'confirmation'
                st.rerun()

elif st.session_state.view == 'confirmation':
    st.balloons()
    st.success("🌸 **Thank you! Your meeting has been scheduled.**")
    st.markdown("You can now export the schedule from the sidebar and import it into your personal calendar.")
    
    if st.button("Schedule Another Meeting"):
        st.session_state.selected_date = None
        st.session_state.selected_time = None
        st.session_state.view = 'calendar'
        st.rerun()
