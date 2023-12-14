import pandas as pd
from exchangelib import Credentials, Account, FileAttachment, Configuration, DELEGATE
import os
from datetime import date
import email
import imaplib
from Firebase import FirebaseDB
from DataExtractor import DataExtractor
import tempfile


class MailChecker:
    def __init__(self, mail, password):
        self.email_address = mail
        self.password = password
        self.firebase = None
        #self.attachment_save_path = "C:\\Users\\gapas\\PycharmProjects\\streamlit"

    def check_mail(self, subject_filters, imap_server='imap.gmail.com'):
        if '@gmail' in self.email_address:
            self.check_mail_gmail(subject_filters, imap_server)
        elif '@hotmail' in self.email_address or '@outlook' in self.email_address:
            self.check_mail_outlook(subject_filters)
        else:
            raise ValueError("Unsupported email provider")

    def check_mail_outlook(self, subject_filters):
        while True:
            messages_to_mark_as_read = []
            credentials = Credentials(self.email_address, self.password)
            config = Configuration(server='outlook.office365.com', credentials=credentials)
            account = Account(primary_smtp_address=self.email_address, config=config,
                              autodiscover=False, access_type=DELEGATE)
            print(f"Mail connection to {self.email_address} is now")
            for id_doc, subject_filter in subject_filters.items():
                print(f"Inbox check to {self.email_address} for {subject_filter} and documents: {id_doc} is now")
                for message in account.inbox.filter(subject=subject_filter, is_read=False):
                    if subject_filter in message.subject:
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
                                if isinstance(attachment, FileAttachment):
                                    filename = attachment.name
                                    attachment_content = attachment.content  # Obtener el contenido del adjunto

                                    # Guardar el archivo adjunto temporalmente
                                    temp_dir = tempfile.mkdtemp()
                                    temp_file_path = os.path.join(temp_dir, filename)
                                    with open(temp_file_path, 'wb') as temp_file:
                                        temp_file.write(attachment_content)

                                    # Llamar a la función save_data para procesar el archivo adjunto
                                    self.save_data(temp_file_path, self.email_address, subject_filter, id_doc)

                                    # Eliminar el archivo temporal después de usarlo
                                    os.remove(temp_file_path)
                                    os.rmdir(temp_dir)
                        messages_to_mark_as_read.append(message)
                for message in messages_to_mark_as_read:
                    message.is_read = True
                    message.save()
            account.protocol.close()
            # time.sleep(1)
            return 0

    def check_mail_gmail(self, subject_filters, imap_server):
        while True:
            # Connect to the IMAP server
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(self.email_address, self.password)
            mail.select('inbox')
            print(f"Mail connection to {self.email_address} is now")
            for id_doc, subject_filter in subject_filters.items():
                print(f"Inbox check to {self.email_address} for {subject_filter} and document {id_doc} is now")
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
                                # Get the text content of the email, handling decoding errors
                                content = part.get_payload(decode=True).decode(errors='replace')
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
                            attachment_content = attachment.get_payload(decode=True)

                            # Guardar el archivo adjunto temporalmente
                            temp_dir = tempfile.mkdtemp()
                            temp_file_path = os.path.join(temp_dir, filename)
                            with open(temp_file_path, 'wb') as temp_file:
                                temp_file.write(attachment_content)

                            # Save the attachment to the specified path
                            if filename:
                                self.save_data(temp_file_path, self.email_address, subject_filter, id_doc)

                            # Eliminar el archivo temporal después de usarlo
                            os.remove(temp_file_path)
                            os.rmdir(temp_dir)
            mail.logout()
            # time.sleep(5)
            return 0

    @staticmethod
    def save_data(file, mail_d, subject, doc_type):
        # file = "uploaded_pdf.pdf"
        file_db = file
        # mail = "testmail"
        # subject = "test"
        mail_db = mail_d
        subject_db = subject
        main_table_name = 'general'
        # Create an instance of the FirebaseDB class
        firebase_db = FirebaseDB()
        path = "db_coord/" + mail_db + "/" + doc_type
        field_text = subject_db + "/text"
        field_tables = subject_db + "/tables"
        # Extract data from the Firebase database
        df_firebase_text = firebase_db.extract_data(path, field_text, 'coord')
        df_firebase_tables = firebase_db.extract_data(path, field_tables, 'coord')
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
                table['Fecha extracción'] = general_table['Fecha extracción']
                table['Pozo'] = general_table['Pozo']
                tables_list.append((title_value, table))

            print(tables)
            print()

        firebase_db.save_dataframe(tables_list, "db_collection", f"{mail_db}/{doc_type}%{subject_db}")
