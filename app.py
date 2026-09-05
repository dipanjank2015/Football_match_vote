import streamlit as st
import base64

from database import (
    initialize_database,
    reset_admin_password,
    get_session,
    Settings,
    Player,
    Admin,
    hash_value,
    verify_value
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Football Attendance",
    page_icon="⚽",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==========================================
# FOOTBALL GROUND BACKGROUND
# ==========================================

with open("football_ground.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

st.markdown(
    f"""
    <style>

    .stApp {{
        background-image:
            linear-gradient(
                rgba(0, 30, 10, 0.72),
                rgba(0, 30, 10, 0.72)
            ),
            url("data:image/jpeg;base64,{image_data}");

        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }}

    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# DATABASE INIT
# ============================================================

initialize_database()

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        padding-top: 1rem;
    }

    .block-container {
        max-width: 900px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .hero {
        text-align: center;
        padding: 25px 15px;
        border-radius: 20px;
        background: linear-gradient(
            135deg,
            #111827,
            #1f2937
        );
        color: white;
        margin-bottom: 25px;
    }

    .hero h1 {
        font-size: 32px;
        margin-bottom: 5px;
    }

    .hero p {
        margin: 5px;
        opacity: 0.85;
    }

    .info-card {
        background: #f8fafc;
        padding: 18px;
        border-radius: 15px;
        margin-bottom: 20px;
        border: 1px solid #e5e7eb;
    }

    .player-card {
        background: white;
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 10px;
        border: 1px solid #e5e7eb;
    }

    .going {
        color: #15803d;
        font-weight: 700;
    }

    .not-going {
        color: #6b7280;
        font-weight: 700;
    }

    .admin-header {
        text-align: center;
        padding: 20px;
        margin-bottom: 20px;
    }

    .small-text {
        font-size: 13px;
        color: #6b7280;
    }

     [data-testid="stAppViewContainer"] {
        background-image: url("images/football.jpg");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SESSION STATE
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "home"

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False


# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def get_settings():

    db = get_session()

    try:
        return db.query(Settings).first()

    finally:
        db.close()


def get_active_players():

    db = get_session()

    try:

        return (
            db.query(Player)
            .filter_by(active=True)
            .order_by(Player.id)
            .all()
        )

    finally:

        db.close()


def get_all_players():

    db = get_session()

    try:

        return (
            db.query(Player)
            .order_by(Player.id)
            .all()
        )

    finally:

        db.close()


# ============================================================
# PUBLIC PAGE
# ============================================================

def public_page():

    settings = get_settings()
    players = get_active_players()

    st.markdown(
        f"""
        <div class="hero">
            <h1>⚽ {settings.match_title}</h1>
            <p>Football Attendance</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # MATCH INFORMATION
    # --------------------------------------------------------

    st.markdown(
        f"""
        <div class="info-card">

        <b>📅 Date:</b>
        {settings.match_date or "Not set"}

        <br><br>

        <b>📍 Venue:</b>
        {settings.venue or "Not set"}

        <br><br>

        <b>⏰ Time:</b>
        {settings.match_time or "Not set"}

        <br><br>

        <b>💰 Fees:</b>
        {settings.fees or "Not set"}

        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # ATTENDANCE SUMMARY
    # --------------------------------------------------------

    going_count = sum(
        1 for p in players if p.going
    )

    total_count = len(players)

    st.metric(
        "Players Going",
        f"{going_count} / {total_count}"
    )

    st.divider()

    st.subheader("👥 Player Attendance")

    if not players:

        st.warning("No active players available.")

        return

    # --------------------------------------------------------
    # PLAYER SELECT
    # --------------------------------------------------------

    player_names = [
        p.name for p in players
    ]

    selected_name = st.selectbox(
        "Select your name",
        player_names,
        key="selected_player"
    )

    selected_player = next(
        (
            p for p in players
            if p.name == selected_name
        ),
        None
    )

    # --------------------------------------------------------
    # PIN
    # --------------------------------------------------------

    pin = st.text_input(
        "🔐 Enter your PIN",
        type="password",
        max_chars=20,
        key="player_pin"
    )

    # --------------------------------------------------------
    # ACTION
    # --------------------------------------------------------

    if st.button(
        "⚽ Submit Attendance",
        use_container_width=True,
        type="primary"
    ):

        if not pin:

            st.error("Please enter your PIN.")

            return

        db = get_session()

        try:

            player = db.query(Player).filter_by(
                id=selected_player.id
            ).first()

            if not player:

                st.error("Player not found.")

                return

            # ------------------------------------------------
            # PIN VERIFY
            # ------------------------------------------------

            if not verify_value(
                pin,
                player.pin_hash
            ):

                st.error("❌ Incorrect PIN.")

                return

            # ------------------------------------------------
            # TOGGLE ATTENDANCE
            # ------------------------------------------------

            player.going = not player.going

            db.commit()

            if player.going:

                st.success(
                    f"✅ {player.name} marked as GOING!"
                )

            else:

                st.info(
                    f"ℹ️ {player.name} marked as NOT GOING."
                )

            st.rerun()

        finally:

            db.close()

    st.divider()

    # --------------------------------------------------------
    # CURRENT STATUS
    # --------------------------------------------------------

    st.subheader("📋 Current Attendance")

    db = get_session()

    try:

        players = (
            db.query(Player)
            .filter_by(active=True)
            .order_by(Player.id)
            .all()
        )

        for player in players:

            status = (
                "🟢 GOING"
                if player.going
                else
                "⚪ NOT GOING"
            )

            css_class = (
                "going"
                if player.going
                else
                "not-going"
            )

            st.markdown(
                f"""
                <div class="player-card">
                    <b>{player.name}</b>
                    <span class="{css_class}"
                    style="float:right;">
                        {status}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )

    finally:

        db.close()

    st.divider()

    if st.button(
        "🔐 Admin Panel",
        use_container_width=True
    ):

        st.session_state.page = "admin_login"

        st.rerun()


# ============================================================
# ADMIN LOGIN
# ============================================================

def admin_login_page():

    st.markdown(
        """
        <div class="admin-header">

        <h1>🔐 Admin Login</h1>

        <p>
        Football Attendance Management
        </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    username = st.text_input(
        "Username"
    )

    password = st.text_input(
        "Password",
        type="password"
    )

    col1, col2 = st.columns(2)

    with col1:

        login = st.button(
            "Login",
            use_container_width=True,
            type="primary"
        )

    with col2:

        back = st.button(
            "← Back",
            use_container_width=True
        )

    if back:

        st.session_state.page = "home"

        st.rerun()

    if login:

        if not username or not password:

            st.error(
                "Please enter username and password."
            )

            return

        db = get_session()

        try:

            admin = db.query(Admin).filter_by(
                username=username
            ).first()

            if admin and verify_value(
                password,
                admin.password_hash
            ):

                st.session_state.admin_logged_in = True

                st.session_state.page = "admin"

                st.success("Login successful!")

                st.rerun()

            else:

                st.error(
                    "❌ Invalid username or password."
                )

        finally:

            db.close()


# ============================================================
# ADMIN DASHBOARD
# ============================================================

def admin_page():

    if not st.session_state.admin_logged_in:

        st.session_state.page = "admin_login"

        st.rerun()

    st.markdown(
        """
        <div class="admin-header">

        <h1>⚙️ Admin Panel</h1>

        <p>
        Manage players, match information and votes
        </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    # ========================================================
    # TOP BUTTONS
    # ========================================================

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🏠 Public Page",
            use_container_width=True
        ):

            st.session_state.page = "home"

            st.rerun()

    with col2:

        if st.button(
            "🚪 Logout",
            use_container_width=True
        ):

            st.session_state.admin_logged_in = False

            st.session_state.page = "home"

            st.rerun()

    st.divider()

    # ========================================================
    # MATCH SETTINGS
    # ========================================================

    st.subheader("⚽ Match Settings")

    settings = get_settings()

    with st.form("match_settings_form"):

        title = st.text_input(
            "Match Title",
            value=settings.match_title or ""
        )

        date = st.text_input(
            "Match Date",
            value=settings.match_date or ""
        )

        venue = st.text_input(
            "Venue",
            value=settings.venue or ""
        )

        match_time = st.text_input(
            "Match Time",
            value=settings.match_time or ""
        )

        fees = st.text_input(
            "Fees",
            value=settings.fees or ""
        )

        submitted = st.form_submit_button(
            "💾 Save Match Settings",
            use_container_width=True
        )

        if submitted:

            db = get_session()

            try:

                db_settings = db.query(
                    Settings
                ).first()

                db_settings.match_title = title
                db_settings.match_date = date
                db_settings.venue = venue
                db_settings.match_time = match_time
                db_settings.fees = fees

                db.commit()

                st.success(
                    "✅ Match settings updated."
                )

                st.rerun()

            finally:

                db.close()

    st.divider()

    # ========================================================
    # ATTENDANCE SUMMARY
    # ========================================================

    all_players = get_all_players()

    active_players = [
        p for p in all_players
        if p.active
    ]

    going_players = [
        p for p in active_players
        if p.going
    ]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total",
        len(active_players)
    )

    col2.metric(
        "Going",
        len(going_players)
    )

    col3.metric(
        "Not Going",
        len(active_players) - len(going_players)
    )

    st.divider()

    # ========================================================
    # ADD PLAYER
    # ========================================================

    st.subheader("➕ Add New Player")

    with st.form("add_player_form"):

        new_name = st.text_input(
            "Player Name"
        )

        new_pin = st.text_input(
            "Player PIN",
            type="password",
            max_chars=20
        )

        add = st.form_submit_button(
            "Add Player",
            use_container_width=True
        )

        if add:

            if not new_name.strip():

                st.error(
                    "Player name is required."
                )

            elif not new_pin:

                st.error(
                    "Player PIN is required."
                )

            else:

                db = get_session()

                try:

                    existing = db.query(
                        Player
                    ).filter_by(
                        name=new_name.strip()
                    ).first()

                    if existing:

                        st.error(
                            "A player with this name already exists."
                        )

                    else:

                        player = Player(
                            name=new_name.strip(),
                            pin_hash=hash_value(new_pin),
                            going=False,
                            active=True
                        )

                        db.add(player)

                        db.commit()

                        st.success(
                            f"✅ {new_name} added successfully."
                        )

                        st.rerun()

                finally:

                    db.close()

    st.divider()

    # ========================================================
    # PLAYER MANAGEMENT
    # ========================================================

    st.subheader("👥 Manage Players")

    all_players = get_all_players()

    for player in all_players:

        with st.expander(
            f"{'🟢' if player.active else '⚫'} {player.name}"
        ):

            status = (
                "GOING"
                if player.going
                else
                "NOT GOING"
            )

            st.write(
                f"Attendance: **{status}**"
            )

            st.write(
                f"Status: **{'Active' if player.active else 'Hidden'}**"
            )

            # ------------------------------------------------
            # EDIT NAME
            # ------------------------------------------------

            with st.form(
                f"edit_name_{player.id}"
            ):

                edited_name = st.text_input(
                    "Player Name",
                    value=player.name
                )

                update_name = st.form_submit_button(
                    "✏️ Update Name",
                    use_container_width=True
                )

                if update_name:

                    if not edited_name.strip():

                        st.error(
                            "Name cannot be empty."
                        )

                    else:

                        db = get_session()

                        try:

                            db_player = db.query(
                                Player
                            ).filter_by(
                                id=player.id
                            ).first()

                            db_player.name = edited_name.strip()

                            db.commit()

                            st.success(
                                "Player name updated."
                            )

                            st.rerun()

                        finally:

                            db.close()

            # ------------------------------------------------
            # CHANGE PIN
            # ------------------------------------------------

            with st.form(
                f"change_pin_{player.id}"
            ):

                new_pin = st.text_input(
                    "New PIN",
                    type="password",
                    max_chars=20
                )

                change_pin = st.form_submit_button(
                    "🔑 Change PIN",
                    use_container_width=True
                )

                if change_pin:

                    if not new_pin:

                        st.error(
                            "Please enter a new PIN."
                        )

                    else:

                        db = get_session()

                        try:

                            db_player = db.query(
                                Player
                            ).filter_by(
                                id=player.id
                            ).first()

                            db_player.pin_hash = hash_value(
                                new_pin
                            )

                            db.commit()

                            st.success(
                                "✅ PIN changed successfully."
                            )

                            st.info(
                                "The old PIN can no longer be used."
                            )

                        finally:

                            db.close()

            # ------------------------------------------------
            # ACTION BUTTONS
            # ------------------------------------------------

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "👁️ Hide" if player.active
                    else "👁️ Show",
                    key=f"toggle_{player.id}",
                    use_container_width=True
                ):

                    db = get_session()

                    try:

                        db_player = db.query(
                            Player
                        ).filter_by(
                            id=player.id
                        ).first()

                        db_player.active = not db_player.active

                        db.commit()

                        st.rerun()

                    finally:

                        db.close()

            with col2:

                if st.button(
                    "🔄 Reset Vote",
                    key=f"reset_{player.id}",
                    use_container_width=True
                ):

                    db = get_session()

                    try:

                        db_player = db.query(
                            Player
                        ).filter_by(
                            id=player.id
                        ).first()

                        db_player.going = False

                        db.commit()

                        st.success(
                            "Vote reset."
                        )

                        st.rerun()

                    finally:

                        db.close()

            # ------------------------------------------------
            # DELETE
            # ------------------------------------------------

            if st.button(
                "🗑️ Delete Player",
                key=f"delete_{player.id}",
                use_container_width=True
            ):

                db = get_session()

                try:

                    db_player = db.query(
                        Player
                    ).filter_by(
                        id=player.id
                    ).first()

                    db.delete(db_player)

                    db.commit()

                    st.success(
                        f"{player.name} deleted."
                    )

                    st.rerun()

                finally:

                    db.close()

    st.divider()

    # ========================================================
    # RESET ALL VOTES
    # ========================================================

    st.subheader("🔄 Reset Attendance")

    if st.button(
        "⚠️ Reset ALL Votes",
        use_container_width=True
    ):

        db = get_session()

        try:

            players = db.query(Player).all()

            for player in players:

                player.going = False

            db.commit()

            st.success(
                "✅ All attendance votes have been reset."
            )

            st.rerun()

        finally:

            db.close()

    st.divider()

   


# ============================================================
# ROUTING
# ============================================================

if st.session_state.page == "home":

    public_page()

elif st.session_state.page == "admin_login":

    admin_login_page()

elif st.session_state.page == "admin":

    admin_page()


     # ========================================================
        # CHANGE ADMIN PASSWORD
        # ========================================================
    
        
    with st.expander("🔐 Change Admin Password"):
    
        with st.form("admin_password_form"):
    
            current_password = st.text_input(
                "Current Password",
                type="password"
            )
    
            new_password = st.text_input(
                "New Password",
                type="password"
            )
    
            confirm_password = st.text_input(
                "Confirm New Password",
                type="password"
            )
    
            change_password = st.form_submit_button(
                "Change Admin Password",
                use_container_width=True
            )
    
            if change_password:
    
                if not current_password:
                    st.error("❌ Please enter your current password.")
    
                elif not new_password:
                    st.error("❌ New password cannot be empty.")
    
                elif new_password != confirm_password:
                    st.error("❌ New passwords do not match.")
    
                else:
    
                    db = get_session()
    
                    try:
                        admin = db.query(Admin).filter(
                            Admin.username == "admin"
                        ).first()
    
                        if admin is None:
                            st.error("❌ Admin account not found.")
    
                        elif not verify_value(
                            current_password,
                            admin.password_hash
                        ):
                            st.error("❌ Current password is incorrect.")
    
                        else:
    
                            admin.password_hash = hash_value(
                                new_password
                            )
    
                            db.commit()
    
                            st.success(
                                "✅ Admin password changed successfully!"
                            )
    
                            st.info(
                                "Please logout and login again."
    
                            )
    
                    except Exception as e:
    
                        db.rollback()
    
                        st.error(
                            f"❌ Password change failed: {e}"
                        )
    
                    finally:
                        db.close()
    
    
               
    
               