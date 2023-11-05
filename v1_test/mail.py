import time
import os
import email
import imaplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataExtractor import DataExtractor
from firebase import FirebaseDB


class MailChecker:
    def __init__(self, email, password, imap_server, smtp_server):
        self.email_address = email
        self.password = password
        self.imap_server = imap_server
        self.smtp_server = smtp_server
        self.attachment_save_path = "C:\\Users\\gapas\\PycharmProjects\\streamlit"  # Update the path here

    def check_mail(self, subject_filters):
        while True:
            # Connect to the IMAP server
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_address, self.password)
            mail.select('inbox')

            for subject_filter in subject_filters:
                _, message_nums = mail.search(None, f'(UNSEEN SUBJECT "{subject_filter}")')
                for num in message_nums[0].split():
                    _, msg_data = mail.fetch(num, '(RFC822)')
                    raw_email = msg_data[0][1]
                    email_message = email.message_from_bytes(raw_email)

                    # Extract information from the email
                    subject = email_message['Subject']
                    sender = email.utils.parseaddr(email_message['From'])[1]
                    attachments = []
                    content = ""

                    if email_message.is_multipart():
                        for part in email_message.walk():
                            if part.get_content_type().startswith('multipart/'):
                                continue
                            elif part.get_content_type().startswith('text/'):
                                # Get the text content of the email
                                content = part.get_payload(decode=True).decode()
                            else:
                                # Extract attachments
                                attachments.append(part)

                    # Process the extracted information as needed
                    print("Subject:", subject)
                    print("Sender:", sender)
                    if attachments:
                        print("Attachments:")
                        for attachment in attachments:
                            filename = attachment.get_filename()

                            # Save the attachment to the specified path
                            if filename:
                                download_path = os.path.join(self.attachment_save_path, filename)
                                with open(download_path, "wb") as file:
                                    file.write(attachment.get_payload(decode=True))
                                print("- Saved Attachment:", download_path)

                                # Send an email to notify the sender about the saved file
                                notification_subject = f"Attachment '{filename}' is saved"
                                notification_body = f"The attachment '{filename}' is saved in the specified path."
                                self.send_email(sender, notification_subject, notification_body)

                    print("Content:", content)

            mail.logout()
            time.sleep(1)

    def send_email(self, recipient, subject, message):
        # Create a multipart message
        email_message = MIMEMultipart()
        email_message['From'] = self.email_address
        email_message['To'] = recipient
        email_message['Subject'] = subject

        # Attach the message to the email
        email_message.attach(MIMEText(message, "plain"))

        # Connect to the SMTP server and send the email
        with smtplib.SMTP(self.smtp_server) as smtp:
            smtp.starttls()
            smtp.login(self.email_address, self.password)
            smtp.send_message(email_message)

    def save_data(self, file, mail, subject):
        # file = "uploaded_pdf.pdf"
        file_db = file
        # mail = "testmail"
        # subject = "test"
        mail_db = mail
        subject_db = subject
        # Create an instance of the FirebaseDB class
        firebase_db = FirebaseDB()
        path = "db_coord/" + mail_db + "/" + subject_db
        # Extract data from the Firebase database
        df_firebase = firebase_db.extract_data(path)
        tables_list = []

        for entry in df_firebase:
            x1 = entry['Left']
            x2 = entry['Final width']
            y1 = entry['Top']
            y2 = entry['Final height']
            page = entry['page']
            print(f"x1: {x1}, x2: {x2}, y1: {y1}, y2: {y2}, page: {page}")

            # Create an instance of the DataExtractor class
            data_extractor = DataExtractor(file, page, y1, x1, x2, y2)

            # Extract tables using the DataExtractor class
            tables = data_extractor.extract_tables()
            for table in tables:
                tables_list.append(table)

            print(tables)
            print()

        firebase_db.guardar_dataframe(tables_list, "db_collection", f"{mail_db}/{subject_db}", file_db)


#mail_checker = MailChecker("example6@gmail.com", "example_pass", "imap.gmail.com", "smtp.gmail.com")

#subject_filters = ["test", "content", "mailer"]  # Update with desired subject filters
#mail_checker.check_mail(subject_filters)

# Send an email
# mail_checker.send_email("recipient@example.com", "Hello", "This is the message body.")

