import streamlit as st

from firebase import FirebaseDB
from firebase_admin.auth import UserRecord
import time

#st.set_page_config(initial_sidebar_state="collapsed")
# Crear containers
# loginSect = st.container()
# signUpSect = st.container()
# mainLoggedSect = st.container()

def main():
    # Configuración inicial de la sesión
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if "page" not in st.session_state:
        st.session_state.page = "main"

    if "user" not in st.session_state:
        st.session_state.user = None

    # Lógica principal
    if not st.session_state["logged_in"]:
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"]{
                visibility: hidden;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        print("logged not")
    else:

        print("logged in")
        main_logged_page()

    if st.session_state.page == "main":
        main_page()
    elif st.session_state.page == "login":
        login()
    elif st.session_state.page == "signup":
        signup()

# Configuración de la página
# st.set_page_config(page_title="Authentication App")
def login_action(mail, password):
    user, cond = FirebaseDB().get_user(mail, password)
    if user is not None and cond == 0:
        container = st.empty()
        container.success("Login successful")
        time.sleep(2)
        container.empty()
        st.session_state["logged_in"] = True
        st.session_state.user = user
        st.session_state.page = "logged"
    else:
        st.error("Login failed")
        if cond == 1:
            st.error("User not found")
        elif cond == 2:
            st.error("Something went wrong")
        elif cond == -1:
            st.error("Wrong password")


def login():
    st.title("Login")
    st.write("Login to your account")
    mail = st.text_input("Email")
    password = st.text_input("Password", type="password")

    st.button("Access", on_click=lambda: login_action(mail, password))
    # Button to return to the main page
    st.button("Return to Main Page", on_click=lambda: st.session_state.update({"page": "main"}))


def signup_action(mail, password, name):
    user, cond = FirebaseDB().signup(mail, password, name)
    record: UserRecord = user
    if record is not None:
        st.session_state.page = "login"  # Redirect to login page after successful signup
        st.success("Sign up successful: New account with id: " + user.uid)
    else:
        st.error("Sign up failed")
        if cond == 1:
            st.error("Email already exists")
        if cond == 2:
            st.error("Username already exists")
        if cond == 3:
            st.error("Something went wrong")


def signup():
    st.title("Sign Up")
    st.write("Sign up to your account")
    mail = st.text_input("Email")
    password = st.text_input("Password", type="password")
    name = st.text_input("Name")
    st.button("New account", on_click=lambda: signup_action(mail, password, name))
    st.button("Return to Main Page", on_click=lambda: st.session_state.update({"page": "main"}))


def logout():
    st.session_state["logged_in"] = False
    st.session_state.user = None
    st.session_state.page = "main"


def main_logged_page():
    st.title("Main Page")
    st.write(f"Welcome back {st.session_state.user['nombre']}")

    if st.button("Log Out", on_click=logout):
        pass  # No es necesario hacer nada aquí, ya que la lógica está en la función logout

    st.sidebar.write(st.session_state.user['nombre'])


def main_page():
    st.title("Main Page")
    st.write("This is the main page")

    if st.button("Login", key="login_button", on_click= lambda:st.session_state.update(page = "login")):
        pass

    if st.button("Sign Up", key="signup_button", on_click= lambda: st.session_state.update(page = "signup")):
        pass


main()  # Llama a la función principal para iniciar la aplicación
