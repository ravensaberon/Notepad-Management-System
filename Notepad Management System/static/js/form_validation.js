function showError(input, message) {
  const errorEl = input.parentElement.querySelector(".error");
  if (!errorEl) return;
  errorEl.textContent = message;
  input.classList.toggle("invalid", !!message);
}

function clearErrors(form) {
  form.querySelectorAll(".error").forEach(e => (e.textContent = ""));
  form.querySelectorAll(".invalid").forEach(i => i.classList.remove("invalid"));
}

function computeAge(input) {
  if (!input.value) return;
  const dob = new Date(input.value);
  const today = new Date();
  let age = today.getFullYear() - dob.getFullYear();
  const m = today.getMonth() - dob.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) age--;

  const ageField = document.querySelector('input[name="age"]');
  ageField.value = age > 0 ? age : "";

  if (age < 8 || age > 80) {
    showError(input, "Age must be between 8 and 80.");
    ageField.value = "";
  } else {
    showError(input, "");
  }
}

function validateRegister(form, singleField = null) {
  let valid = true;

  // Patterns
  const namePattern = /^[A-Za-z\s]{2,50}$/;
  const usernamePattern = /^[A-Za-z0-9_]{3,20}$/; // only letters, numbers, underscores
  const emailPattern = /^[a-z0-9._%+-]+@(gmail|yahoo|icloud|hotmail)\.[a-z]{2,}$/;
  const contactPattern = /^(?:\+639|09)\d{9}$/; // PH number pattern

  const fields = {
    first_name: "First name",
    last_name: "Last name",
    municipality: "Municipality",
    dob: "Birthday",
    email: "Email",
    contact: "Contact",
    username: "Username",
    password: "Password",
    confirm_password: "Confirm password"
  };

  const inputs = singleField ? [singleField] : form.querySelectorAll("input, select");

  inputs.forEach(input => {
    const name = input.name;
    const value = input.value.trim();
    showError(input, "");

    // Required check
    if (fields[name] && !value) {
      showError(input, `${fields[name]} is required.`);
      valid = false;
    }

    // Name check
    if (["first_name", "middle_name", "last_name"].includes(name) && value && !namePattern.test(value)) {
      showError(input, "Only letters and spaces (2–50 chars).");
      valid = false;
    }

    // Username validation
    if (name === "username" && value && !usernamePattern.test(value)) {
      showError(input, "Only letters, numbers, and underscores (3–20 chars).");
      valid = false;
    }

    // Email validation
    if (name === "email" && value && !emailPattern.test(value)) {
      showError(input, "Use a valid Gmail/Yahoo/iCloud/Hotmail email (lowercase only).");
      valid = false;
    }

    // Contact validation (PH format + 11 digits)
    if (name === "contact" && value) {
  const digitsOnly = value.replace(/\D/g, ""); // remove non-digits
  const startsWithValidPrefix = /^(\+639|09)/.test(value);

  // Only run validation after full number is entered
  if (digitsOnly.length === 11) {
    if (!startsWithValidPrefix) {
      showError(input, "Use valid PH number: must start with +639 or 09.");
      valid = false;
    } 
    // All digits the same (e.g., 00000000000)
    else if (/^(\d)\1{10}$/.test(digitsOnly)) {
      showError(input, "Invalid contact number — repeated digits are not allowed.");
      valid = false;
    } 
    // Contains any sequence of 6+ identical digits (like 111111 or 000000)
    else if (/(\d)\1{5,}/.test(digitsOnly)) {
      showError(input, "Invalid contact number — too many repeated digits.");
      valid = false;
    } 
    // Disallow numbers with mostly zeros (like +639000000000)
    else if (/^(\+?639|09)0{8}$/.test(value)) {
      showError(input, "Invalid contact number — zeros are not allowed.");
      valid = false;
    } 
    else {
      showError(input, ""); // ✅ Valid
    }
  } 
  else if (digitsOnly.length > 0 && digitsOnly.length < 11) {
    // Don't show errors while typing incomplete numbers
    showError(input, "");
  } 
  else if (digitsOnly.length === 0) {
    // Required field check
    showError(input, "Contact is required.");
    valid = false;
  }
}

    // Password
    if (name === "password" && value.length < 6) {
      showError(input, "At least 6 characters.");
      valid = false;
    }

    // Confirm password
    if (name === "confirm_password" && value !== form.password.value) {
      showError(input, "Passwords do not match.");
      valid = false;
    }
  });

  // Age check (only if DOB has value)
  if (form.dob.value) {
    const age = parseInt(form.age.value);
    if (isNaN(age) || age < 8 || age > 80) {
      showError(form.dob, "Age must be between 8 and 80.");
      valid = false;
    }
  }

  return valid;
}

// Live inline validation
document.addEventListener("input", e => {
  if (!e.target.form || e.target.form.id !== "registerForm") return;
  validateRegister(e.target.form, e.target);
});

// Final submission check
document.addEventListener("submit", e => {
  if (e.target.id === "registerForm" && !validateRegister(e.target)) {
    e.preventDefault();
  }
});
