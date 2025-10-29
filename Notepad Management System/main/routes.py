from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session
)
from utils.storage import (
    get_all_notes, new_note_id, add_note, find_note_by_id,
    update_note, delete_note_permanent, find_user_by_username, update_user
)
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os, random

main_bp = Blueprint("main", __name__, template_folder="../templates")

def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)
    return wrapper

@main_bp.route("/")
def index():
    if "user" in session:
        return redirect(url_for("main.home"))
    return redirect(url_for("auth.login"))

@main_bp.route("/home")
@login_required
def home():
    username = session["user"]
    sort_by = request.args.get("sort_by", "date_desc")

    notes = [n for n in get_all_notes() if n.get("owner") == username and n.get("status") == "active"]

    from datetime import datetime
    for n in notes:
        if n.get("created_at"):
            n["created_at_dt"] = datetime.fromisoformat(n["created_at"])
        else:
            n["created_at_dt"] = datetime.min
        if n.get("updated_at"):
            n["updated_at_dt"] = datetime.fromisoformat(n["updated_at"])
        else:
            n["updated_at_dt"] = n["created_at_dt"]

    if sort_by == "date_asc":
        notes.sort(key=lambda x: x["created_at_dt"])
    elif sort_by == "title_asc":
        notes.sort(key=lambda x: x["title"].lower())
    elif sort_by == "title_desc":
        notes.sort(key=lambda x: x["title"].lower(), reverse=True)
    elif sort_by == "updated_desc":
        notes.sort(key=lambda x: x["updated_at_dt"], reverse=True)
    else:
        notes.sort(key=lambda x: x["created_at_dt"], reverse=True)

    return render_template("home.html", notes=notes, sort_by=sort_by)


@main_bp.route("/note/new", methods=["GET", "POST"])
@login_required
def create_note():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        if not title:
            flash("Title is required.", "danger")
            return render_template("note_form.html", form=request.form)
        note = {
            "id": new_note_id(),
            "owner": session["user"],
            "title": title,
            "content": content,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": None
        }
        add_note(note)
        flash("Note created.", "success")
        return redirect(url_for("main.home"))
    return render_template("note_form.html")

@main_bp.route("/note/<int:note_id>/edit", methods=["GET", "POST"])
@login_required
def edit_note(note_id):
    note = find_note_by_id(note_id)
    if not note or note.get("owner") != session["user"]:
        flash("Note not found or access denied.", "danger")
        return redirect(url_for("main.home"))
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        if not title:
            flash("Title required.", "danger")
            return render_template("note_form.html", form=request.form, note=note)
        update_note(note_id, {"title": title, "content": content, "updated_at": datetime.utcnow().isoformat()})
        flash("Note updated.", "success")
        return redirect(url_for("main.home"))
    return render_template("note_form.html", note=note)

@main_bp.route("/note/<int:note_id>/archive", methods=["POST"])
@login_required
def archive_note(note_id):
    note = find_note_by_id(note_id)
    if not note or note.get("owner") != session["user"]:
        flash("Note not found or access denied.", "danger")
        return redirect(url_for("main.home"))
    update_note(note_id, {"status": "archived", "updated_at": datetime.utcnow().isoformat()})
    flash("Note moved to archive.", "info")
    return redirect(url_for("main.home"))

@main_bp.route("/archive")
@login_required
def archive_view():
    username = session["user"]
    notes = [n for n in get_all_notes() if n.get("owner") == username and n.get("status") == "archived"]
    return render_template("archive.html", notes=notes)

@main_bp.route("/note/<int:note_id>/restore", methods=["POST"])
@login_required
def restore_note(note_id):
    note = find_note_by_id(note_id)
    if not note or note.get("owner") != session["user"]:
        flash("Note not found or access denied.", "danger")
        return redirect(url_for("main.archive_view"))
    update_note(note_id, {"status": "active", "updated_at": datetime.utcnow().isoformat()})
    flash("Note restored.", "success")
    return redirect(url_for("main.archive_view"))

@main_bp.route("/note/<int:note_id>/delete", methods=["POST"])
@login_required
def permanent_delete(note_id):
    note = find_note_by_id(note_id)
    if not note or note.get("owner") != session["user"]:
        flash("Note not found or access denied.", "danger")
        return redirect(url_for("main.archive_view"))
    delete_note_permanent(note_id)
    flash("Note permanently deleted.", "danger")
    return redirect(url_for("main.archive_view"))


# -------------------------------
# PROFILE PAGE (with picture upload and OTP)
# -------------------------------
@main_bp.route("/profile", methods=["GET"])
@login_required
def profile():
    username = session["user"]
    user = find_user_by_username(username)
    return render_template("profile.html", user=user)


@main_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    username = session["user"]
    user = find_user_by_username(username)

    if request.method == "POST":
        action = request.form.get("action")

        # Upload profile picture
        if action == "upload_pic":
            file = request.files.get("profile_pic")
            if not file or file.filename == "":
                flash("No file selected.", "danger")
                return redirect(url_for("main.edit_profile"))
            
            allowed_extensions = {"png", "jpg", "jpeg", "gif"}
            if not ("." in file.filename and file.filename.rsplit(".", 1)[1].lower() in allowed_extensions):
                flash("Only image files are allowed (png, jpg, jpeg, gif).", "danger")
                return redirect(url_for("main.edit_profile"))

            filename = secure_filename(file.filename)
            upload_dir = os.path.join("static", "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            save_path = os.path.join(upload_dir, filename)
            file.save(save_path)

            update_user(username, {"profile_pic": filename})
            flash("Profile picture updated!", "success")
            return redirect(url_for("main.edit_profile"))

        # Request OTP
        elif action == "request_otp":
            otp = f"{random.randint(0,999999):06d}"
            session["profile_otp_for"] = username
            session["profile_otp_val"] = otp
            session["profile_otp_expiry"] = (datetime.now() + timedelta(minutes=3)).timestamp()
            flash(f"Profile OTP (demo): {otp} - expires in 3 minutes.", "info")
            # Use redirect to prevent form resubmission
            return redirect(url_for("main.edit_profile"))

        # Verify OTP
        elif action == "verify_otp":
            otp = request.form.get("otp", "").strip()
            expiry = session.get("profile_otp_expiry", 0)
            if datetime.now().timestamp() > expiry:
                flash("OTP expired.", "danger")
                return redirect(url_for("main.edit_profile"))
            if otp != session.get("profile_otp_val"):
                flash("Invalid OTP.", "danger")
                return redirect(url_for("main.edit_profile"))
            session["profile_otp_verified"] = True
            flash("OTP verified. You may update your profile now.", "success")
            return redirect(url_for("main.edit_profile"))

        # Update profile info
        elif action == "update_profile":
            if not session.get("profile_otp_verified"):
                flash("Please verify OTP before updating.", "danger")
                return redirect(url_for("main.edit_profile"))

            fn = request.form.get("first_name").strip()
            mn = request.form.get("middle_name").strip()
            ln = request.form.get("last_name").strip()
            dob = request.form.get("dob")
            contact = request.form.get("contact")
            address = request.form.get("address")
            email = request.form.get("email").strip()

            try:
                dob_dt = datetime.strptime(dob, "%Y-%m-%d").date()
                today = datetime.today().date()
                age = today.year - dob_dt.year - ((today.month, today.day) < (dob_dt.month, dob_dt.day))
            except Exception:
                age = user.get("age")

            update_fields = {
                "first_name": fn, "middle_name": mn, "last_name": ln,
                "dob": dob, "age": age, "contact": contact,
                "address": address, "email": email
            }
            update_user(username, update_fields)

            session.pop("profile_otp_for", None)
            session.pop("profile_otp_val", None)
            session.pop("profile_otp_expiry", None)
            session.pop("profile_otp_verified", None)

            flash("Profile updated successfully!", "success")
            return redirect(url_for("main.profile"))

    # Default (GET) - pass existing OTP expiry if available
    otp_expiry = session.get("profile_otp_expiry")
    return render_template("edit_profile.html", user=user, otp_expiry=otp_expiry)