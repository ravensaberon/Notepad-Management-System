from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session, current_app
)
from utils.storage import (
    find_user_by_username, add_user, hash_password, verify_password, update_user
)
from datetime import datetime, timedelta
import random

auth_bp = Blueprint("auth", __name__, url_prefix="/auth", template_folder="../templates")

def calculate_age(dob_str):
    dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
    today = datetime.today().date()
    years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return years


# ===================== REGISTER =====================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data = request.form
        username = data.get("username").strip()
        email = data.get("email").strip()
        password = data.get("password")
        confirm = data.get("confirm_password")
        first = data.get("first_name").strip()
        middle = data.get("middle_name", "").strip()
        last = data.get("last_name").strip()
        dob = data.get("dob")
        age = data.get("age")
        contact = data.get("contact")
        province = data.get("province", "").strip()
        municipality = data.get("municipality", "").strip()
        barangay = data.get("barangay", "").strip()
        street = data.get("street", "").strip()
        zipcode = data.get("zipcode", "").strip()
        address = f"{street}, Brgy. {barangay}, {municipality}, {province}, {zipcode}".strip()

        # server-side validation
        if not (first and last and dob and username and email and password and confirm and contact):
            flash("Please fill required fields.", "danger")
            return render_template("register.html", form=data)
        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("register.html", form=data)
        if find_user_by_username(username):
            flash("Username already exists. Choose another.", "danger")
            return render_template("register.html", form=data)

        age = calculate_age(dob)
        user = {
            "username": username,
            "email": email,
            "password_hash": hash_password(password),
            "first_name": first,
            "middle_name": middle,
            "last_name": last,
            "dob": dob,
            "age": age,
            "contact": contact,
            "address": address,
            "created_at": datetime.utcnow().isoformat()
        }
        add_user(user)
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("register.html")


# ===================== LOGIN =====================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("username", "").strip()
        password = request.form.get("password") or ""

        # Try to find user by username
        user = find_user_by_username(identifier)

        # If not found, try finding by email
        if not user:
            from utils.storage import find_user_by_email
            user = find_user_by_email(identifier)

        if not user or not verify_password(user["password_hash"], password):
            attempts = session.get("login_attempts", 0) + 1
            session["login_attempts"] = attempts
            flash("Invalid username/email or password.", "danger")
            return render_template("login.html")

        # Success
        session.clear()
        session["user"] = user["username"]
        flash("Logged in.", "success")
        return redirect(url_for("main.home"))

    return render_template("login.html")


# ===================== LOGOUT =====================
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("auth.login"))


# ===================== FORGOT PASSWORD (ONE PAGE OTP) =====================
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    from datetime import datetime, timedelta
    import time
    action = request.form.get("action")
    otp_stage = False
    otp_expiry = None

    # Step 1: Request OTP
    if action == "request_otp":
        username = request.form.get("username", "").strip()
        user = find_user_by_username(username)
        if not user:
            flash("Username not found.", "danger")
            return render_template("forgot_password.html", otp_stage=False)

        # generate 6-digit OTP
        otp = f"{random.randint(0, 999999):06d}"

        # store in session
        session["otp_for"] = username
        session["otp_value"] = otp
        session["otp_expiry"] = (datetime.utcnow() + timedelta(minutes=3)).timestamp()
        
        otp_stage = True
        otp_expiry = session["otp_expiry"]
        flash(f"OTP (for demo): {otp} — expires in 3 minutes.", "info")

        # Pass expiry timestamp to HTML for countdown
        return render_template("forgot_password.html", otp_stage=otp_stage, otp_expiry=otp_expiry)

    # Step 2: Verify OTP
    elif action == "verify_otp":
        otp_stage = True
        otp = request.form.get("otp", "").strip()

        if "otp_value" not in session:
            flash("No OTP found. Please request a new one.", "danger")
            return render_template("forgot_password.html", otp_stage=False)

        expiry_ts = session.get("otp_expiry", 0)
        otp_expiry = expiry_ts  # ensure countdown still works

        now_ts = datetime.utcnow().timestamp()
        if now_ts > expiry_ts:
            flash("OTP expired. Please request a new one.", "danger")
            session.pop("otp_value", None)
            session.pop("otp_expiry", None)
            session.pop("otp_for", None)
            return render_template("forgot_password.html", otp_stage=False)

        if otp != session.get("otp_value"):
            flash("Invalid OTP. Please try again.", "danger")
            return render_template("forgot_password.html", otp_stage=True, otp_expiry=otp_expiry)

        # OTP is correct
        session["otp_verified"] = True
        return redirect(url_for("auth.reset_password"))

    # Default page (no OTP yet)
    return render_template("forgot_password.html", otp_stage=False, otp_expiry=otp_expiry)


# ===================== RESET PASSWORD =====================
@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if not session.get("otp_verified") or not session.get("otp_for"):
        flash("Unauthorized or session expired. Start forgot password again.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        pwd = request.form.get("password")
        confirm = request.form.get("confirm_password")
        if not pwd or pwd != confirm:
            flash("Passwords do not match or are empty.", "danger")
            return render_template("reset_password.html")

        username = session.get("otp_for")
        success = update_user(username, {"password_hash": hash_password(pwd)})

        # Clear OTP-related session data
        session.pop("otp_for", None)
        session.pop("otp_value", None)
        session.pop("otp_expiry", None)
        session.pop("otp_verified", None)

        flash("Password updated successfully. Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html")
