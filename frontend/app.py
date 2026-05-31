import time

import streamlit as st

from services.api import ApiClient

st.set_page_config(page_title="Medical AI Assistant", page_icon="+", layout="wide")


def init_state() -> None:
    defaults = {
        "token": None,
        "thread_id": None,
        "model": None,
        "memory_depth": 12,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def api() -> ApiClient:
    return ApiClient(st.session_state.token)


def auth_screen() -> None:
    st.title("Medical AI Assistant")
    login_tab, register_tab = st.tabs(["Login", "Register"])
    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
        if submitted:
            try:
                token = ApiClient().login(email, password)["access_token"]
                st.session_state.token = token
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    with register_tab:
        with st.form("register_form"):
            full_name = st.text_input("Full name")
            email = st.text_input("Registration email")
            password = st.text_input("Registration password", type="password")
            submitted = st.form_submit_button("Create account")
        if submitted:
            try:
                client = ApiClient()
                client.register(email, password, full_name)
                token = client.login(email, password)["access_token"]
                st.session_state.token = token
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def sidebar() -> None:
    client = api()
    with st.sidebar:
        st.title("Threads")
        if st.button("New Thread", use_container_width=True):
            thread = client.create_thread("New conversation")
            st.session_state.thread_id = thread["id"]
            st.rerun()

        search = st.text_input("Search Threads")
        try:
            threads = client.threads(search or None)
        except Exception as exc:
            st.error(str(exc))
            threads = []

        for thread in threads:
            selected = thread["id"] == st.session_state.thread_id
            label = thread["title"][:42]
            if st.button(label, key=f"thread-{thread['id']}", type="primary" if selected else "secondary", use_container_width=True):
                st.session_state.thread_id = thread["id"]
                st.rerun()

        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state.token = None
            st.session_state.thread_id = None
            st.rerun()


def chat_panel() -> None:
    client = api()
    st.subheader("Chat")
    messages = []
    if st.session_state.thread_id:
        try:
            detail = client.get_thread(st.session_state.thread_id)
            messages = detail.get("messages", [])
            title = st.text_input("Thread name", value=detail["title"], key=f"title-{detail['id']}")
            if title != detail["title"]:
                client.rename_thread(detail["id"], title)
        except Exception as exc:
            st.error(str(exc))

    for message in messages:
        with st.chat_message("assistant" if message["role"] == "assistant" else "user"):
            st.write(message["content"])

    prompt = st.chat_input("Ask about symptoms, medications, nutrition, documents, or care planning")
    if prompt:
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"):
            stream_box = st.empty()
            try:
                response = client.chat(prompt, st.session_state.thread_id, st.session_state.model)
                st.session_state.thread_id = response["thread_id"]
                rendered = ""
                for token in response["response"].split(" "):
                    rendered += token + " "
                    stream_box.write(rendered)
                    time.sleep(0.01)
                with st.expander("Retrieved sources"):
                    st.json(response["retrieved_sources"])
                with st.expander("Extracted health information"):
                    st.json(response["extracted_health_information"])
            except Exception as exc:
                st.error(str(exc))
        st.rerun()


def health_dashboard() -> None:
    client = api()
    st.subheader("Health Dashboard")
    try:
        profile = client.health_profile()
    except Exception as exc:
        st.error(str(exc))
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Age", profile.get("age") or "Unknown")
    col2.metric("Gender", profile.get("gender") or "Unknown")
    col3.metric("Weight kg", profile.get("weight_kg") or "Unknown")
    col4.metric("Height cm", profile.get("height_cm") or "Unknown")

    sections = [
        ("Conditions", profile.get("conditions", [])),
        ("Symptoms", profile.get("symptoms", [])),
        ("Medications", profile.get("medications", [])),
        ("Allergies", profile.get("allergies", [])),
    ]
    cols = st.columns(4)
    for col, (title, values) in zip(cols, sections, strict=True):
        with col:
            st.markdown(f"**{title}**")
            if values:
                for item in values:
                    st.write(item["name"])
            else:
                st.caption("None recorded")

    with st.form("profile_form"):
        st.markdown("**Profile Details**")
        age = st.number_input("Age", min_value=0, max_value=130, value=int(profile["age"] or 0))
        gender = st.text_input("Gender", value=profile.get("gender") or "")
        weight = st.number_input("Weight kg", min_value=0.0, max_value=500.0, value=float(profile["weight_kg"] or 0.0))
        height = st.number_input("Height cm", min_value=0.0, max_value=260.0, value=float(profile["height_cm"] or 0.0))
        nutrition = st.text_input("Nutrition preferences", value=", ".join(profile.get("nutrition_preferences", [])))
        lifestyle = st.text_input("Lifestyle factors", value=", ".join(profile.get("lifestyle_factors", [])))
        if st.form_submit_button("Save Profile"):
            payload = {
                "age": age or None,
                "gender": gender or None,
                "weight_kg": weight or None,
                "height_cm": height or None,
                "nutrition_preferences": [item.strip() for item in nutrition.split(",") if item.strip()],
                "lifestyle_factors": [item.strip() for item in lifestyle.split(",") if item.strip()],
            }
            try:
                client.update_health_profile(payload)
                st.success("Saved")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def knowledge_dashboard() -> None:
    client = api()
    st.subheader("Knowledge Dashboard")
    upload = st.file_uploader("Upload PDF, DOCX, or TXT", type=["pdf", "docx", "txt"])
    if upload and st.button("Index Document"):
        try:
            result = client.upload_document(upload)
            st.success(f"Document queued: {result['document_id']}")
        except Exception as exc:
            st.error(str(exc))

    try:
        docs = client.documents()
    except Exception as exc:
        st.error(str(exc))
        docs = []

    if docs:
        st.dataframe(
            [
                {
                    "Filename": doc["filename"],
                    "Status": doc["status"],
                    "SHA256": doc["sha256"][:12],
                    "Uploaded": doc["uploaded_at"],
                    "Chunks": doc.get("document_metadata", {}).get("chunk_count", 0),
                }
                for doc in docs
            ],
            use_container_width=True,
        )
    else:
        st.info("No uploaded documents yet.")

    st.markdown("**Indexed Sources**")
    st.dataframe(
        [
            {"Source": "Disease Symptom Dataset", "Collection": "medical_knowledge"},
            {"Source": "Disease Precaution Dataset", "Collection": "medical_knowledge"},
            {"Source": "Medication Dataset", "Collection": "medical_knowledge"},
            {"Source": "Drug Interaction Dataset", "Collection": "medical_knowledge"},
            {"Source": "Nutrition Dataset", "Collection": "medical_knowledge"},
            {"Source": "Healthcare FAQ Dataset", "Collection": "medical_knowledge"},
            {"Source": "Clinical Guidelines Dataset", "Collection": "medical_knowledge"},
            {"Source": "WHO Guidelines", "Collection": "medical_knowledge"},
            {"Source": "CDC Guidelines", "Collection": "medical_knowledge"},
        ],
        use_container_width=True,
    )


def settings_panel() -> None:
    st.subheader("Settings")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Model Settings**")
        st.session_state.model = st.text_input("Model override", value=st.session_state.model or "")
        st.slider("Response creativity", 0.0, 1.0, 0.2, disabled=True)
    with col2:
        st.markdown("**Memory Settings**")
        st.session_state.memory_depth = st.slider("Visible thread memory", 4, 30, st.session_state.memory_depth)
        st.toggle("Universal memory", value=True, disabled=True)
        st.toggle("Thread summarization", value=True, disabled=True)


def main() -> None:
    init_state()
    if not st.session_state.token:
        auth_screen()
        return
    sidebar()
    tab_chat, tab_health, tab_knowledge, tab_settings = st.tabs(["Chat", "Health Dashboard", "Knowledge Dashboard", "Settings"])
    with tab_chat:
        chat_panel()
    with tab_health:
        health_dashboard()
    with tab_knowledge:
        knowledge_dashboard()
    with tab_settings:
        settings_panel()


if __name__ == "__main__":
    main()
