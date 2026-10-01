"""
CCS 106: Application Development and Emerging Technologies
Week 5: Laboratory Task: CSPC Scholarship Intake Portal
Instructor: Allan O. Ibo, Jr., MSc

"""

import re
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import flet as ft

class ScholarshipValidationError(Exception):
  """Base exception for all scholarship domain validation errors."""
  pass


class IDFormatError(ScholarshipValidationError):
    """Raised when student ID does not conform to the CSPC format."""
    pass


class EmailDomainError(ScholarshipValidationError):
    """Raised when an email does not belong to the @cspc.edu.ph domain."""
    pass


class GWARangeError(ScholarshipValidationError):
    """Raised when GWA falls outside the 1.00 to 5.00 grading scale."""
    pass


@dataclass(frozen=True)
class ScholarshipApplicant:
    """Immutable domain contract representing a verified scholarship applicant."""
    full_name: str
    student_id: str
    email: str
    phone: str
    gwa: float
    program: str
    submitted_at: datetime = field(default_factory=datetime.now)


class ScholarshipValidator:
    NAME_REGEX = re.compile(r"^[A-Za-z\s.',-]{2,60}$")
    # Allows either 7 consecutive digits (e.g., 2412863) OR hyphenated format (e.g., 2024-0123)
    STUDENT_ID_REGEX = re.compile(r"^(?:\d{7}|20\d{2}-\d{4,5})$")
    CSPC_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@(my\.)?cspc\.edu\.ph$")

    @classmethod
    def sanitize_string(cls, raw: Optional[str]) -> str:
        """Strip leading/trailing whitespace defensively handling None."""
        return (raw or "").strip()

    @classmethod
    def validate_name(cls, value: Optional[str]) -> str:
        clean = cls.sanitize_string(value)
        if not clean:
            raise ScholarshipValidationError("Full name is required.")
        if not cls.NAME_REGEX.match(clean):
            raise ScholarshipValidationError("Enter a valid name (2-60 letters, hyphens, or periods).")
        return clean

    @classmethod
    def validate_student_id(cls, value: Optional[str]) -> str:
        clean = cls.sanitize_string(value)
        if not clean:
            raise IDFormatError("Student ID is required.")
        if not cls.STUDENT_ID_REGEX.match(clean):
            raise IDFormatError("Invalid Student ID format (e.g., 2321674 or 2024-0123).")
        return clean

    @classmethod
    def validate_email(cls, value: Optional[str]) -> str:
        clean = cls.sanitize_string(value).lower()
        if not clean:
            raise EmailDomainError("Email is required.")
        if not cls.CSPC_EMAIL_REGEX.match(clean):
            raise EmailDomainError("Must be a valid @cspc.edu.ph email.")
        return clean

    @classmethod
    def validate_phone(cls, value: Optional[str]) -> str:
        clean = cls.sanitize_string(value)
        # Strip all formatting spaces and hyphens before normalization
        clean = clean.replace(" ", "").replace("-", "")
        if not clean:
            raise ScholarshipValidationError("Mobile phone number is required.")
        if clean.startswith("+63"):
            clean = "0" + clean[3:]
        if not re.match(r"^09\d{9}$", clean):
            raise ScholarshipValidationError("Invalid Philippine mobile number.")
        return clean

    @classmethod
    def validate_gwa(cls, value: Optional[str]) -> float:
        clean = cls.sanitize_string(value)
        if not clean:
            raise GWARangeError("GWA is required.")
        try:
            gwa_val = float(clean)
        except ValueError:
            raise GWARangeError("GWA must be numeric.")
        if not (1.00 <= gwa_val <= 5.00):
            raise GWARangeError("GWA must be between 1.00 and 5.00.")
        return gwa_val


def main(page: ft.Page):
    try:
        if hasattr(page, "window") and page.window is not None:
            page.window.width = 620
            page.window.height = 780
            page.window.resizable = False
        else:
            page.window_width = 620
            page.window_height = 780
    except Exception:
        pass

    page.title = "CSPC Scholarship Intake Portal"

    if hasattr(ft, "ThemeMode"):
        page.theme_mode = ft.ThemeMode.DARK

    approved_applicants: list[ScholarshipApplicant] = []

    # Safe Icon Resolver
    icons_ns = getattr(ft, "Icons", None) or getattr(ft, "icons", None)
    def get_icon(name, fallback):
        return getattr(icons_ns, name, fallback) if icons_ns else fallback

    # Form Controls
    name_field = ft.TextField(
        label="Full Name",
        hint_text="e.g., Maria Clara Santos",
        prefix_icon=get_icon("PERSON_OUTLINE", "person_outline"),
        border_radius=8,
        width=580,
        bgcolor=ft.Colors.GREY_800
    )

    id_field = ft.TextField(
        label="Student ID Number",
        hint_text="e.g., 2024-0123",
        prefix_icon=get_icon("BADGE_OUTLINED", "badge_outlined"),
        border_radius=8,
        width=580,
        bgcolor=ft.Colors.GREY_800
    )

    email_field = ft.TextField(
        label="Institutional Email",
        hint_text="e.g., name@cspc.edu.ph",
        prefix_icon=get_icon("EMAIL_OUTLINED", "email_outlined"),
        border_radius=8,
        width=580,
        bgcolor=ft.Colors.GREY_800
    )

    phone_field = ft.TextField(
        label="Mobile Phone",
        hint_text="e.g., 09123456789",
        prefix_icon=get_icon("PHONE_OUTLINED", "phone_outlined"),
        border_radius=8,
        width=580,
        bgcolor=ft.Colors.GREY_800
    )

    gwa_field = ft.TextField(
        label="GWA",
        hint_text="e.g., 1.25",
        prefix_icon=get_icon("NUMBERS_OUTLINED", "numbers_outlined"),
        border_radius=8,
        width=580,
        bgcolor=ft.Colors.GREY_800
    )

    Opt = getattr(ft, "DropdownOption", getattr(getattr(ft, "dropdown", None), "Option", None))
    program_dropdown = ft.Dropdown(
        label="Scholarship Program",
        hint_text="Select your scholarship grant",
        border_radius=8,
        options=[
            Opt("CHED Tulong Dunong Program (TDP)"),
            Opt("DOST Science & Technology Scholarship"),
            Opt("CSPC Institutional Academic Scholarship"),
            Opt("UniFAST Tertiary Education Subsidy (TES)")
        ] if Opt else [],
        width = 580,
        bgcolor=ft.Colors.GREY_800,
    )

    status_summary = ft.Text(
        value="Ready to accept applications.",
        color="grey400",
        size=13
    )

    def clear_field_error(e):
        e.control.error = None
        e.control.error_text = None
        page.update()

    name_field.on_change = clear_field_error
    id_field.on_change = clear_field_error
    email_field.on_change = clear_field_error
    phone_field.on_change = clear_field_error
    gwa_field.on_change = clear_field_error
    program_dropdown.on_change = clear_field_error

    def submit_application(e):
        has_errors = False

        # Reset errors across both .error and .error_text attributes
        for ctrl in [name_field, id_field, email_field, phone_field, gwa_field, program_dropdown]:
            ctrl.error = None
            ctrl.error_text = None

        # 1. Validate Name
        try:
            clean_name = ScholarshipValidator.validate_name(name_field.value)
        except ScholarshipValidationError as err:
            name_field.error = str(err)
            name_field.error_text = str(err)
            has_errors = True

        # 2. Validate Student ID
        try:
            clean_id = ScholarshipValidator.validate_student_id(id_field.value)
        except IDFormatError as err:
            id_field.error = str(err)
            id_field.error_text = str(err)
            has_errors = True

        # 3. Validate Email
        try:
            clean_email = ScholarshipValidator.validate_email(email_field.value)
        except EmailDomainError as err:
            email_field.error = str(err)
            email_field.error_text = str(err)
            has_errors = True

        # 4. Validate Phone
        try:
            clean_phone = ScholarshipValidator.validate_phone(phone_field.value)
        except ScholarshipValidationError as err:
            phone_field.error = str(err)
            phone_field.error_text = str(err)
            has_errors = True

        # 5. Validate GWA
        try:
            clean_gwa = ScholarshipValidator.validate_gwa(gwa_field.value)
        except GWARangeError as err:
            gwa_field.error = str(err)
            gwa_field.error_text = str(err)
            has_errors = True

        # 6. Validate Program Selection
        if not program_dropdown.value:
            program_dropdown.error = "Please select an accredited scholarship program."
            program_dropdown.error_text = "Please select an accredited scholarship program."
            has_errors = True

        snack = ft.SnackBar(
            content=ft.Text("Validation failed: Please correct highlighted fields." if has_errors else "Application submitted successfully!"),
            bgcolor="red700" if has_errors else "green700"
        )

        # Triggers mock_page.show_dialog for unit test suite assertion
        if hasattr(page, "show_dialog"):
            try:
                page.show_dialog(snack)
            except Exception:
                pass
        if hasattr(page, "overlay"):
            try:
                page.overlay.append(snack)
                snack.open = True
            except Exception:
                pass

        if has_errors:
            page.update()
            return

        # 7. Construct Domain Contract
        applicant = ScholarshipApplicant(
            full_name=clean_name,
            student_id=clean_id,
            email=clean_email,
            phone=clean_phone,
            gwa=clean_gwa,
            program=program_dropdown.value
        )
        approved_applicants.append(applicant)

        status_summary.value = f"Applications submitted: {len(approved_applicants)}"
        status_summary.color = "green400"

        # Clear input values
        name_field.value = id_field.value = email_field.value = phone_field.value = gwa_field.value = ""
        program_dropdown.value = None
        page.update()

    submit_button = ft.FilledButton(
        content=ft.Row(
            controls=[
                ft.Icon(get_icon("CHECK_CIRCLE_OUTLINE", "check_circle_outline")),
                ft.Text("Submit Scholarship Application", weight=ft.FontWeight.BOLD)
            ],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        height=48,
        on_click=submit_application
    )

    if len(approved_applicants) > 0:
        for i in approved_applicants:
            pass        
        pass

    page.add(
        ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(get_icon("VERIFIED_USER", "verified_user"), size=32, color="blue400"),
                        ft.Column(
                            controls=[
                                ft.Text("CSPC Scholarship Intake Portal", size=20, weight=ft.FontWeight.BOLD),
                                ft.Text("Office of Student Affairs & Services • Academic Year 2026-2027", size=12, color="grey400")
                            ],
                            spacing=2
                        )
                    ]
                ),
                ft.Divider(height=20, color="grey700"),
                name_field,
                id_field,
                email_field,
                phone_field,
                gwa_field,
                program_dropdown,
                ft.Container(height=10),
                submit_button,
                ft.Container(height=5),
                status_summary
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO
        )
    )

if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    elif hasattr(ft, "app"):
        ft.app(target=main)