# import smtplib
# import ssl
# from email.message import EmailMessage

# def send_email_on_inquiry(data):
#     # SMTP server configuration
#     smtp_host = "10.25.36.110"
#     smtp_port = 25  # no SSL, but we can use STARTTLS
#     timeout = 30

#     from_addr = "it.announcement@changan.com.pk"
#     recipients = data.get("recipients", [])
#     subject = data.get("subject", "")
#     message_body = data.get("message", "")

#     # Build the email
#     msg = EmailMessage()
#     msg["From"] = from_addr
#     msg["To"] = ", ".join(recipients)
#     msg["Subject"] = subject
#     msg.set_content(message_body, subtype="html")  # because mailtype = html

#     # SSL context similar to your PHP config (allow self-signed)
#     context = ssl.create_default_context()
#     context.check_hostname = False
#     context.verify_mode = ssl.CERT_NONE

#     try:
#         with smtplib.SMTP(smtp_host, smtp_port, timeout=timeout) as server:
#             server.ehlo()

#             # enable TLS (like smtp_crypto => tls)
#             server.starttls(context=context)

#             # No login() used because your PHP config doesn’t show authentication
#             server.send_message(msg)

#         print("✅ Email sent successfully")

#     except Exception as e:
#         print(f"❌ Error sending email: {e}")



# data = {
#     "subject": "Test Email",
#     "message": "<h3>Hello, this is a test email!</h3>",
#     "recipients": ["example1@domain.com", "example2@domain.com"]
# }

# send_email_on_inquiry(data)

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- Configuration ---
smtp_server = "smtp.office365.com"
port = 587  # STARTTLS port

sender_email = "customer.experience@changan.com.pk"
password = "F/877606196884us"  # or use an app password
receiver_email = "azmat.ali@changan.com.pk"

# --- Email Content ---
subject = "TESTING EMAIL"
body = """
Dear Team,

TESTING EMAIL (UAT)

Best regards,
IT Department
Changan Pakistan
"""

# --- Create Email ---
msg = MIMEMultipart()
msg["From"] = sender_email
msg["To"] = receiver_email
msg["Subject"] = subject
msg.attach(MIMEText(body, "plain"))

# --- Send Email ---
try:
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls()  # 🔒 Enable encryption
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        print("✅ Email sent successfully!")

except Exception as e:
    print(f"❌ Error sending email: {e}")




# import imaplib
# import email
# from email.header import decode_header

# # --- Configuration ---
# imap_server = "outlook.office365.com"
# # email_user = "customer.experience@changan.com.pk"
# # password = "your_password_here"  # ⚠️ Use app password if MFA is enabled

# # --- Connect to the server ---
# mail = imaplib.IMAP4_SSL(imap_server, 443)

# # --- Login ---
# mail.login(sender_email, password)

# # --- Select INBOX ---
# mail.select("inbox")

# # --- Search for all emails ---
# status, messages = mail.search(None, 'FROM "raza.khan@changan.com.pk')


# # --- Convert messages to list of email IDs ---
# email_ids = messages[0].split()

# print(f"📬 Total emails: {len(email_ids)}")

# # --- Fetch the latest 5 emails ---
# for i in email_ids[-5:]:
#     status, msg_data = mail.fetch(i, "(RFC822)")
#     msg = email.message_from_bytes(msg_data[0][1])

#     # Decode email subject
#     subject, encoding = decode_header(msg["Subject"])[0]
#     if isinstance(subject, bytes):
#         subject = subject.decode(encoding if encoding else "utf-8")

#     from_ = msg.get("From")
#     print(f"📨 From: {from_}")
#     print(f"📌 Subject: {subject}")
#     print("-" * 40)

# # --- Close connection ---
# mail.logout()
