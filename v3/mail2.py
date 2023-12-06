import pandas as pd
from exchangelib import Credentials, Account, Message, FileAttachment, Configuration, DELEGATE
import os
import time
from datetime import date
import email
import imaplib
from firebase import FirebaseDB
from dataExtractor import DataExtractor
import re

class MailChecker:
    def __init__(self, mail, password):
        self.email_address = mail
        self.password = password
        self.attachment_save_path = "C:\\Users\\gapas\\PycharmProjects\\streamlit"
        self.subjects = []

    def check_mail_outlook(self, subject_filters):
        while True:
            messages_to_mark_as_read = []
            credentials = Credentials(self.email_address, self.password)
            config = Configuration(server='outlook.office365.com', credentials=credentials)
            account = Account(primary_smtp_address=self.email_address, config=config,
                              autodiscover=False, access_type=DELEGATE)
            print(f"Mail connection to {self.email_address} is now")
            for subject_filter in subject_filters:
                print(f"Inbox check to {self.email_address} for {subject_filter} is now")
                for message in account.inbox.filter(subject=subject_filter, is_read=False):
                    subject = message.subject
                    sender = message.sender.email_address

                    attachments = []
                    content = ""

                    for attachment in message.attachments:
                        if isinstance(attachment, FileAttachment):
                            attachments.append(attachment)

                    # Procesar la información extraída según sea necesario
                    print("Subject:", subject)
                    print("Sender:", sender)
                    if attachments:
                        print("Attachments:")
                        for attachment in attachments:
                            filename = attachment.name
                            attachment_path = os.path.join(self.attachment_save_path, filename)

                            # Llamar a la función save_data para procesar el archivo adjunto
                            self.save_data(filename, self.email_address, subject_filter)
                    messages_to_mark_as_read.append(message)
                for message in messages_to_mark_as_read:
                    message.is_read = True
                    message.save()
            account.protocol.close()
            #time.sleep(1)
            return 0

    def check_mail_gmail(self, subject_filters, imap_server):
        while True:
            # Connect to the IMAP server
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(self.email_address, self.password)
            mail.select('inbox')
            print(f"Mail connection to {self.email_address} is now")
            for subject_filter in subject_filters:
                print(f"Inbox check to {self.email_address} for {subject_filter} is now")
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
                                self.save_data(filename, self.email_address, subject_filter)
            mail.logout()
            #time.sleep(5)
            return 0

    def check_mail(self, subject_filters, imap_server='imap.gmail.com'):
        self.subjects += subject_filters
        if '@gmail' in self.email_address:
            self.check_mail_gmail(subject_filters, imap_server)
        elif '@hotmail' in self.email_address or '@outlook' in self.email_address:
            self.check_mail_outlook(subject_filters)
        else:
            raise ValueError("Unsupported email provider")

    def get_subjects(self):
        return self.subjects

    @staticmethod
    def save_data(file, mail_d, subject):
        # file = "uploaded_pdf.pdf"
        file_db = file
        # mail = "testmail"
        # subject = "test"
        mail_db = mail_d
        subject_db = subject
        main_table_name = 'general'
        # Create an instance of the FirebaseDB class
        firebase_db = FirebaseDB()
        path = "db_coord/" + mail_db + "/" + subject_db
        # Extract data from the Firebase database
        df_firebase_text = firebase_db.extract_data(path, 'text', 'coord')
        df_firebase_tables = firebase_db.extract_data(path, 'tables', 'coord')
        tables_list = []
        general_table = {}

        for entry in df_firebase_text:
            x1 = entry['Left']
            x2 = entry['Final width']
            y1 = entry['Top']
            y2 = entry['Final height']
            page = entry['page']
            title = entry['Title']
            print(f"x1: {x1}, x2: {x2}, y1: {y1}, y2: {y2}, page: {page}, title: {title}")

            # Create an instance of the DataExtractor class
            data_extractor = DataExtractor(file_db, page, y1, x1, x2, y2)

            string = data_extractor.get_text(title, 0)
            general_table = data_extractor.compile_fields(general_table, title, string)
            general_table['Fecha extracción'] = date.today().strftime("%d/%m/%Y")

        tables_list.append((main_table_name, pd.DataFrame([general_table])))

        for entry in df_firebase_tables:
            x1 = entry['Left']
            x2 = entry['Final width']
            y1 = entry['Top']
            y2 = entry['Final height']
            page = entry['page']
            title = entry['Title']
            print(f"x1: {x1}, x2: {x2}, y1: {y1}, y2: {y2}, page: {page}, title: {title}")

            # Create an instance of the DataExtractor class
            data_extractor = DataExtractor(file, page, y1, x1, x2, y2)

            # Extract tables using the DataExtractor class
            tables, title_value = data_extractor.clean_unnamed_columns(title)
            for table in tables:
                table['Campo'] = general_table['Campo']
                table['Fecha extracción'] = general_table['Fecha extracción']
                table['Pozo'] = general_table['Pozo']
                tables_list.append((title_value, table))

            print(tables)
            print()

        firebase_db.guardar_dataframe(tables_list, "db_collection", f"{mail_db}/{subject_db}")

# Crear una instancia de MailChecker para Gmail
#mail_checker_gmail = MailChecker("mariel.78.86@gmail.com", "iizw wckp uvcs sbij")

# Filtrar correos con asuntos específicos y procesarlos
#mail_checker_gmail.check_mail(["Artificial_Lift", "Agua"], 'imap.gmail.com')

# Crear una instancia de MailChecker para Outlook
#mail_checker_outlook = MailChecker("mariel.78.86@hotmail.com", "PES2206Madrid")

# Filtrar correos con asuntos específicos y procesarlos
#mail_checker_outlook.check_mail(["asunto3", "asunto4"])

#MailChecker.save_data('uploaded_pdf2.1.pdf', 'mariel.78.86@gmail.com', 'Artificial_Lift')
