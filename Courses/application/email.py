import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# def send_email(sender_email, sender_password, recipient_email, subject, body, smtp_server="smtp.gmail.com", smtp_port=587, attachment_path=None):
#     """
#     Sends an email with the specified details.

#     Args:
#         sender_email (str): The sender's email address.
#         sender_password (str): The sender's email password.
#         recipient_email (str): The recipient's email address.
#         subject (str): The subject of the email.
#         body (str): The body of the email.
#         smtp_server (str): The SMTP server address (default: 'smtp.gmail.com').
#         smtp_port (int): The SMTP server port (default: 587).
#         attachment_path (str): The path to the file to attach (default: None).

#     Returns:
#         None
#     """
#     try:
#         # Set up the MIME structure
#         msg = MIMEMultipart()
#         msg['From'] = sender_email
#         msg['To'] = recipient_email
#         msg['Subject'] = subject

#         # Attach the body
#         msg.attach(MIMEText(body, 'plain'))

#         # Handle attachments
#         if attachment_path:
#             try:
#                 with open(attachment_path, "rb") as attachment:
#                     part = MIMEBase('application', 'octet-stream')
#                     part.set_payload(attachment.read())
#                 encoders.encode_base64(part)
#                 part.add_header('Content-Disposition', f'attachment; filename={attachment_path.split("/")[-1]}')
#                 msg.attach(part)
#             except FileNotFoundError:
#                 print(f"Attachment file not found: {attachment_path}")
#                 return

#         # Set up the SMTP server
#         with smtplib.SMTP(smtp_server, smtp_port) as server:
#             server.starttls()  # Upgrade to a secure connection
#             server.login(sender_email, sender_password)
#             server.sendmail(sender_email, recipient_email, msg.as_string())

#         print("Email sent successfully!")

#     except smtplib.SMTPException as e:
#         print(f"Failed to send email: {e}")
#     except Exception as e:
#         print(f"An error occurred: {e}")


def send_email(sender_email, sender_password, recipient_email, subject, body, attachment_path=None):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        print(f"Email sent successfully to {recipient_email}")
    except Exception as e:
        print(f"Failed to send email to {recipient_email}: {e}")


