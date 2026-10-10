"""Dataset of realistic benchmark tickets derived from real-world Azure DevOps workflows."""

from pydantic import BaseModel, Field


class EvalCase(BaseModel):
    """Evaluation test case specification."""

    ticket_id: int
    title: str
    description: str
    acceptance_criteria: list[str] = Field(default_factory=list)
    archetype: str  # localized_bug, vague_spec, api_contract, cross_cutting
    expected_clarification: bool  # True if ticket is deliberately underspecified
    expected_allowed_files: list[str] = Field(default_factory=list)
    expected_max_diff: int = 300
    pre_fix_branch: str = "main"


BENCHMARK_CASES: list[EvalCase] = [
    # --- Archetype A: Localized UI & Behavior Fixes ---
    EvalCase(
        ticket_id=4966,
        title="[IM-11517] App Header and Navigation Remain Fixed After Welcome Scrolls Away",
        description=(
            "As a user scrolling the main view, the app header and navigation bar "
            "should remain pinned to the top of the viewport once the welcome panel scrolls away."
        ),
        acceptance_criteria=[
            "Header stays sticky at top when scroll offset > 100px",
            "Navigation links remain clickable and visible during scroll",
            "No layout shift or overlapping content on mobile viewport",
        ],
        archetype="localized_bug",
        expected_clarification=False,
        expected_allowed_files=["src/components/Header/*", "src/styles/*"],
        expected_max_diff=45,
    ),
    EvalCase(
        ticket_id=4952,
        title="[IM-11424] Indicate Updated Solutions with 'New' Tag",
        description=(
            "Display a visual 'NEW' badge next to any solution card that was updated "
            "within the last 7 calendar days."
        ),
        acceptance_criteria=[
            "Badge rendered if updatedAt >= now - 7 days",
            "Badge color conforms to design system accent color",
            "Screen reader announcement includes 'Recently updated' status",
        ],
        archetype="localized_bug",
        expected_clarification=False,
        expected_allowed_files=["src/components/SolutionCard/*"],
        expected_max_diff=35,
    ),
    EvalCase(
        ticket_id=5001,
        title="[IM-12113] Benefits Widget - Progress Bar Correction",
        description=(
            "The progress bar in the benefits widget calculates percentage based on "
            "completed steps / total steps. Guard against division by zero when total is 0."
        ),
        acceptance_criteria=[
            "Guard against zero division; default to 0% progress",
            "Display integer percentage between 0 and 100",
            "Unit tests covering 0 total steps, partial, and 100% completion",
        ],
        archetype="localized_bug",
        expected_clarification=False,
        expected_allowed_files=["src/widgets/BenefitsWidget/*"],
        expected_max_diff=25,
    ),
    # --- Archetype B: Vague / Under-specified Specifications ---
    EvalCase(
        ticket_id=4969,
        title="[IM-11565] Update Login Error Message for Inactive Members",
        description=(
            "Update the login failure screen when a user account is inactive. "
            "It needs to show a better message."
        ),
        acceptance_criteria=[],
        archetype="vague_spec",
        expected_clarification=True,
        expected_allowed_files=["src/views/Login/*", "src/locales/*"],
        expected_max_diff=50,
    ),
    EvalCase(
        ticket_id=11619,
        title="not able to receive emails to a valid email id",
        description=(
            "Users report that sending emails from the chat button does not reach "
            "valid destination addresses."
        ),
        acceptance_criteria=[],
        archetype="vague_spec",
        expected_clarification=True,
        expected_allowed_files=["src/Services/Email/*", "src/Controllers/ChatController.cs"],
        expected_max_diff=80,
    ),
    EvalCase(
        ticket_id=10922,
        title="[IM-7445] Voicemails are not working in TEST",
        description="Voicemails are failing when tested in the test deployment environment.",
        acceptance_criteria=[],
        archetype="vague_spec",
        expected_clarification=True,
        expected_allowed_files=["src/Services/Telephony/*"],
        expected_max_diff=60,
    ),
    # --- Archetype C: API & Backend Contract Changes ---
    EvalCase(
        ticket_id=11595,
        title="when email is selected as valid contact getting 200 error with failed response",
        description=(
            "Selecting email contact validation returns HTTP 200 with an internal failure "
            "payload instead of HTTP 422 Unprocessable Entity with error details."
        ),
        acceptance_criteria=[
            "Return HTTP 422 with structured validation error when email format fails",
            "Return HTTP 200 with isValid: true when format is verified",
            "Consistent contract with OpenAPI specification",
        ],
        archetype="api_contract",
        expected_clarification=False,
        expected_allowed_files=["src/Controllers/ContactController.cs", "src/Models/Contact/*"],
        expected_max_diff=65,
    ),
    EvalCase(
        ticket_id=10923,
        title="[IM-7446] Deduplicate Multiple Clicks on Save in Activity Log",
        description=(
            "Rapid multiple clicks on the Save button create duplicate activity log "
            "entries for the same disposition."
        ),
        acceptance_criteria=[
            "Implement idempotency key or client button lock on save submission",
            "Backend rejects or deduplicates identical timestamps within 2000ms",
            "Activity log displays exactly 1 record per disposition action",
        ],
        archetype="api_contract",
        expected_clarification=False,
        expected_allowed_files=[
            "src/Services/ActivityLog/*",
            "src/Controllers/DispositionController.cs",
        ],
        expected_max_diff=55,
    ),
    EvalCase(
        ticket_id=10943,
        title="[IM-12704] Disable System Generated SMS for LA- Tier",
        description=(
            "Suppress automated background SMS job execution for all members enrolled "
            "in the LA- Tier cohort."
        ),
        acceptance_criteria=[
            "Check cohort code in notification worker before dispatching SMS",
            "Log skipped notification with reason 'Cohort suppression: LA- Tier'",
            "Ensure other cohort members still receive scheduled notifications",
        ],
        archetype="api_contract",
        expected_clarification=False,
        expected_allowed_files=["src/Jobs/SmsWorker/*", "src/Services/Notification/*"],
        expected_max_diff=45,
    ),
    # --- Archetype D: Cross-Cutting & Domain Rules ---
    EvalCase(
        ticket_id=11680,
        title="The need that is added from the CHI order after assessment is missing",
        description=(
            "When a CHI order is placed following an assessment with caregiver need ordered, "
            "the caregiver need fails to propagate into the Social Care Plan."
        ),
        acceptance_criteria=[
            "Assessment order completion triggers care plan item generation",
            "Caregiver need entity persisted with order linkage",
            "Social care plan view displays synchronized item",
        ],
        archetype="cross_cutting",
        expected_clarification=False,
        expected_allowed_files=[
            "src/Domain/CarePlan/*",
            "src/Services/Orders/*",
            "src/Controllers/AssessmentController.cs",
        ],
        expected_max_diff=110,
    ),
    EvalCase(
        ticket_id=11620,
        title="Referral created with blank primary coverage is missing from management filters",
        description=(
            "Referral search query filters omit records where PrimaryCoverageId is NULL "
            "due to an inner join on Coverage table."
        ),
        acceptance_criteria=[
            "Change inner join to left outer join in referral repository search query",
            "Referrals without primary coverage appear under 'All' filter view",
            "Regression test asserting retrieval of referrals with NULL coverage",
        ],
        archetype="cross_cutting",
        expected_clarification=False,
        expected_allowed_files=[
            "src/Repositories/ReferralRepository.cs",
            "src/Domain/Entities/Referral.cs",
        ],
        expected_max_diff=40,
    ),
    EvalCase(
        ticket_id=5011,
        title="[IM-12216] Replace Long/Short Term with Need Subcategory",
        description=(
            "Replace deprecated LongTerm / ShortTerm boolean flags with NeedSubcategory "
            "enum across solution models."
        ),
        acceptance_criteria=[
            "Add NeedSubcategory enum (Immediate, ShortTerm, LongTerm, Ongoing)",
            "Map legacy database columns during transition",
            "Update solution contract DTOs across API response models",
        ],
        archetype="cross_cutting",
        expected_clarification=False,
        expected_allowed_files=[
            "src/Domain/Enums/*",
            "src/Models/Solutions/*",
            "src/Services/Solutions/*",
        ],
        expected_max_diff=120,
    ),
]
