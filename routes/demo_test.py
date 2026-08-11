import json
import csv
import io
import os

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    current_app
)

from azure.storage.blob import BlobServiceClient


# ============================================================
# BLUEPRINT
# ============================================================

demotest_bp = Blueprint(
    "demo_test",
    __name__,
    url_prefix="/test"
)


# ============================================================
# AZURE SETTINGS
# ============================================================

CONTAINER_NAME = os.getenv(
    "AZURE_DATA_CONTAINER",
    "ode"
)

CONFIG_PREFIX = "config/"
DATA_PREFIX = "data/"


# ============================================================
# AZURE CLIENT
# ============================================================

def get_blob_service_client():

    connection_string = os.getenv(
        "AZURE_STORAGE_CONNECTION_STRING"
    )

    if not connection_string:
        raise RuntimeError(
            "AZURE_STORAGE_CONNECTION_STRING is not configured."
        )

    return BlobServiceClient.from_connection_string(
        connection_string
    )


def get_container_client():

    service = get_blob_service_client()

    return service.get_container_client(
        CONTAINER_NAME
    )


# ============================================================
# READ JSON FROM AZURE
# ============================================================

def load_json_file(filename):

    container = get_container_client()

    blob_name = f"{CONFIG_PREFIX}{filename}"

    try:

        blob_client = container.get_blob_client(
            blob_name
        )

        data = blob_client.download_blob().readall()

        return json.loads(
            data.decode("utf-8-sig")
        )

    except Exception as e:

        current_app.logger.exception(
            f"Failed to load config file: {blob_name}"
        )

        raise RuntimeError(
            f"Unable to load {filename}"
        ) from e


# ============================================================
# LOAD CONFIGURATION
# ============================================================

def load_categories():

    data = load_json_file(
        "categories.json"
    )

    return data.get(
        "Categories",
        []
    )


def load_subcategories():

    data = load_json_file(
        "subcategories.json"
    )

    return data.get(
        "SubCategories",
        []
    )


def load_subjects():

    data = load_json_file(
        "subjects.json"
    )

    return data.get(
        "Subjects",
        []
    )


# ============================================================
# NEW - LOAD CONTENT TYPES
# ============================================================

def load_contenttypes():

    data = load_json_file(
        "contenttype.json"
    )

    return data.get(
        "Contenttype",
        []
    )


# ============================================================
# FIND ONE CATEGORY
# ============================================================

def get_category(category_id):

    categories = load_categories()

    for category in categories:

        if category.get("CategoryId") == category_id:
            return category

    return None


# ============================================================
# FIND ONE SUBCATEGORY
# ============================================================

def get_subcategory(subcategory_id):

    subcategories = load_subcategories()

    for subcategory in subcategories:

        if (
            subcategory.get("SubCategoryId")
            == subcategory_id
        ):
            return subcategory

    return None


# ============================================================
# FIND SUBJECTS
# ============================================================

def get_subjects(subcategory_id):

    subjects = load_subjects()

    return [
        subject
        for subject in subjects
        if subject.get("SubCategoryId")
        == subcategory_id
    ]


# ============================================================
# FIND ONE SUBJECT
# ============================================================

def get_subject(
    subcategory_id,
    subject_id
):

    subjects = get_subjects(
        subcategory_id
    )

    for subject in subjects:

        if subject.get("SubjectId") == subject_id:
            return subject

    return None


# ============================================================
# NEW - FIND CONTENT TYPES FOR SUBJECT
# ============================================================

def get_contenttypes(subject_id):

    contenttypes = load_contenttypes()

    return [
        contenttype
        for contenttype in contenttypes
        if contenttype.get("SubjectId")
        == subject_id
    ]


# ============================================================
# NEW - FIND ONE CONTENT TYPE
# ============================================================

def get_contenttype(
    subject_id,
    contenttype_id
):

    contenttypes = get_contenttypes(
        subject_id
    )

    for contenttype in contenttypes:

        if (
            contenttype.get("ContenttypeId")
            == contenttype_id
        ):
            return contenttype

    return None


# ============================================================
# LIST CSV SETS FROM AZURE
# ============================================================

def get_sets(
    category_id,
    subcategory_id,
    subject_id,
    contenttype_id
):

    container = get_container_client()

    prefix = (
        f"{DATA_PREFIX}"
        f"{category_id}/"
        f"{subcategory_id}/"
        f"{subject_id}/"
        f"{contenttype_id}/"
    )

    sets = []

    try:

        blobs = container.list_blobs(
            name_starts_with=prefix
        )

        for blob in blobs:

            blob_name = blob.name

            # Ignore folders
            if blob_name.endswith("/"):
                continue

            # Only CSV files
            if not blob_name.lower().endswith(".csv"):
                continue

            filename = os.path.basename(
                blob_name
            )

            set_name = os.path.splitext(
                filename
            )[0]

            sets.append({
                "name": set_name,
                "filename": filename,
                "blob_name": blob_name
            })

        # Natural sorting
        sets.sort(
            key=lambda x: (
                x["name"].lower()
            )
        )

        return sets

    except Exception as e:

        current_app.logger.exception(
            f"Unable to list sets from {prefix}"
        )

        raise RuntimeError(
            "Unable to load test sets."
        ) from e


# ============================================================
# LOAD QUESTIONS FROM CSV
# ============================================================

def load_questions(
    category_id,
    subcategory_id,
    subject_id,
    contenttype_id,
    set_name
):

    container = get_container_client()

    # Protect against path traversal
    if (
        "/" in set_name
        or "\\" in set_name
        or ".." in set_name
    ):
        abort(400)

    # Protect content type path too
    if (
        "/" in contenttype_id
        or "\\" in contenttype_id
        or ".." in contenttype_id
    ):
        abort(400)

    blob_name = (
        f"{DATA_PREFIX}"
        f"{category_id}/"
        f"{subcategory_id}/"
        f"{subject_id}/"
        f"{contenttype_id}/"
        f"{set_name}.csv"
    )

    try:

        blob_client = container.get_blob_client(
            blob_name
        )

        raw_data = (
            blob_client
            .download_blob()
            .readall()
        )

        text = raw_data.decode(
            "utf-8-sig"
        )

        reader = csv.DictReader(
            io.StringIO(text)
        )

        questions = []

        for row in reader:

            questions.append(
                dict(row)
            )

        return questions

    except Exception as e:

        current_app.logger.exception(
            f"Unable to load CSV: {blob_name}"
        )

        raise RuntimeError(
            f"Unable to load test file {set_name}.csv"
        ) from e


# ============================================================
# CATEGORY PAGE
# ============================================================

@demotest_bp.route(
    "/category/<category_id>"
)
def subcategories(category_id):

    category = get_category(
        category_id
    )

    if not category:
        abort(404)

    subcategories_data = [
        item
        for item in load_subcategories()
        if item.get("CategoryId")
        == category_id
    ]

    return render_template(
        "test_subcategories.html",
        category=category,
        subcategories=subcategories_data
    )


# ============================================================
# SUBJECT PAGE
# ============================================================

@demotest_bp.route(
    "/category/<category_id>/<subcategory_id>"
)
def subjects(
    category_id,
    subcategory_id
):

    category = get_category(
        category_id
    )

    subcategory = get_subcategory(
        subcategory_id
    )

    if not category or not subcategory:
        abort(404)

    # Make sure subcategory belongs
    # to selected category
    if (
        subcategory.get("CategoryId")
        != category_id
    ):
        abort(404)

    subjects_data = get_subjects(
        subcategory_id
    )

    return render_template(
        "test_subjects.html",
        category=category,
        subcategory=subcategory,
        subjects=subjects_data
    )


# ============================================================
# NEW - CONTENT TYPE PAGE
# ============================================================

@demotest_bp.route(
    "/category/<category_id>/<subcategory_id>/<subject_id>"
)
def contenttypes(
    category_id,
    subcategory_id,
    subject_id
):

    category = get_category(
        category_id
    )

    subcategory = get_subcategory(
        subcategory_id
    )

    subject = get_subject(
        subcategory_id,
        subject_id
    )

    if (
        not category
        or not subcategory
        or not subject
    ):
        abort(404)

    # Verify category relationship
    if (
        subcategory.get("CategoryId")
        != category_id
    ):
        abort(404)

    # Get content types for subject
    contenttypes_data = get_contenttypes(
        subject_id
    )

    return render_template(
        "test_contenttypes.html",
        category=category,
        subcategory=subcategory,
        subject=subject,
        contenttypes=contenttypes_data
    )


# ============================================================
# SET PAGE
# ============================================================

@demotest_bp.route(
    "/category/<category_id>/<subcategory_id>/<subject_id>/<contenttype_id>"
)
def sets(
    category_id,
    subcategory_id,
    subject_id,
    contenttype_id
):

    category = get_category(
        category_id
    )

    subcategory = get_subcategory(
        subcategory_id
    )

    subject = get_subject(
        subcategory_id,
        subject_id
    )

    contenttype = get_contenttype(
        subject_id,
        contenttype_id
    )

    if (
        not category
        or not subcategory
        or not subject
        or not contenttype
    ):
        abort(404)

    # Verify category relationship
    if (
        subcategory.get("CategoryId")
        != category_id
    ):
        abort(404)

    # Get CSV sets
    sets_data = get_sets(
        category_id,
        subcategory_id,
        subject_id,
        contenttype_id
    )

    return render_template(
        "test_sets.html",
        category=category,
        subcategory=subcategory,
        subject=subject,
        contenttype=contenttype,
        sets=sets_data
    )


# ============================================================
# TEST PAGE
# ============================================================

@demotest_bp.route(
    "/category/<category_id>/<subcategory_id>/<subject_id>/<contenttype_id>/<set_name>",
    methods=["GET", "POST"]
)
def test_page(
    category_id,
    subcategory_id,
    subject_id,
    contenttype_id,
    set_name
):

    category = get_category(
        category_id
    )

    subcategory = get_subcategory(
        subcategory_id
    )

    subject = get_subject(
        subcategory_id,
        subject_id
    )

    contenttype = get_contenttype(
        subject_id,
        contenttype_id
    )

    if (
        not category
        or not subcategory
        or not subject
        or not contenttype
    ):
        abort(404)

    # Verify relationships
    if (
        subcategory.get("CategoryId")
        != category_id
    ):
        abort(404)

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    if request.method == "GET":

        language = request.args.get(
            "language",
            "english"
        ).lower()

        if language not in [
            "english",
            "hindi"
        ]:
            language = "english"

        questions = load_questions(
            category_id,
            subcategory_id,
            subject_id,
            contenttype_id,
            set_name
        )

        return render_template(
            "demotest.html",
            category=category,
            subcategory=subcategory,
            subject=subject,
            contenttype=contenttype,
            set_name=set_name,
            language=language,
            questions=questions
        )

    # --------------------------------------------------------
    # POST - CHECK ANSWERS
    # --------------------------------------------------------

    language = request.form.get(
        "language",
        "english"
    )

    questions = load_questions(
        category_id,
        subcategory_id,
        subject_id,
        contenttype_id,
        set_name
    )

    score = 0
    attempted = 0

    results = []

    for index, question in enumerate(
        questions
    ):

        field_name = (
            f"question_{index}"
        )

        user_answer = request.form.get(
            field_name
        )

        correct_answer = str(
            question.get("answer", "")
        ).strip()

        if user_answer:
            attempted += 1

        is_correct = (
            user_answer == correct_answer
        )

        if is_correct:
            score += 1

        results.append({
            "question": question,
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct
        })

    total = len(questions)

    percentage = (
        round(
            (score / total) * 100,
            2
        )
        if total > 0
        else 0
    )

    return render_template(
        "test_result.html",
        category=category,
        subcategory=subcategory,
        subject=subject,
        contenttype=contenttype,
        set_name=set_name,
        language=language,
        score=score,
        attempted=attempted,
        total=total,
        percentage=percentage,
        results=results
    )
