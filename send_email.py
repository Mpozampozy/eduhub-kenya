import streamlit as st
import smtplib
from email.mime.text import MIMEText

def send_email(to_address, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = st.secrets["email"]["address"]
    msg["To"] = to_address

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(st.secrets["email"]["address"], st.secrets["email"]["app_password"])
        server.send_message(msg)
