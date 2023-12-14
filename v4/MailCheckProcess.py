from MailChecker import MailChecker
from Firebase import FirebaseDB
from Hash import Hash
import time
import functools
from multiprocessing.dummy import Pool
import warnings

def on_snapshot(mail_checkers, doc_snapshot, changes, read_time):
    for change in changes:
        try:
            if change.type.name == 'MODIFIED':
                print(u'Documento modificado: {}'.format(change.document.id))
                print(u'Datos antiguos: {}'.format(change.old_index))
                print(u'Datos nuevos: {}'.format(change.document.to_dict()))
                doc_id = change.document.id
                if 'mail' in change.document.to_dict() and 'mailk' in change.document.to_dict():
                    mail_extract = change.document.to_dict()['mail']
                    password_extract = change.document.to_dict()['mailk']
                    access = change.document.to_dict()['access']
                    if ('subjects' in change.document.to_dict() and change.document.to_dict()['subjects'] and
                            access and mail_extract and password_extract):
                        mail = Hash.d_s_f(mail_extract)
                        password = Hash.d_s_f(password_extract)
                        new_subjects = change.document.to_dict()['subjects']
                        mail_checkers[doc_id] = (mail, password, new_subjects)

            if change.type.name == 'ADDED':
                print(u'Nuevo documento añadido: {}'.format(change.document.id))
                print(u'Datos del nuevo documento: {}'.format(change.document.to_dict()))
                doc_id = change.document.id
                if 'mail' in change.document.to_dict() and 'mailk' in change.document.to_dict():
                    mail_extract = change.document.to_dict()['mail']
                    password_extract = change.document.to_dict()['mailk']
                    access = change.document.to_dict()['access']
                    if ('subjects' in change.document.to_dict() and change.document.to_dict()['subjects'] and
                            access and mail_extract and password_extract):
                        mail = Hash.d_s_f(mail_extract)
                        password = Hash.d_s_f(password_extract)
                        new_subjects = change.document.to_dict()['subjects']
                        mail_checkers[doc_id] = (mail, password, new_subjects)

            if change.type.name == 'REMOVED':
                print(u'Documento eliminado: {}'.format(change.document.id))
                print(u'Datos del documento eliminado: {}'.format(change.document.to_dict()))
                doc_id = change.document.id
                mail_checkers = mail_checkers.pop(doc_id) if doc_id in mail_checkers.keys() else mail_checkers
        except Exception as e:
            print(f"The process for the change percieved was not possible, due to this exception: {e}")


def thread_mail(args):
    mail, key, subjects = args
    mc = MailChecker(mail, key)
    mc.check_mail(subjects)


def main_process():
    warnings.filterwarnings("ignore")
    firebase = FirebaseDB()
    db = firebase.get_db()
    collection = db.collection('db_acc')
    mail_checkers = {}
    processing = Pool(12)

    on_snapshot_arg = functools.partial(on_snapshot, mail_checkers)
    doc_watch = collection.on_snapshot(on_snapshot_arg)

    # Keep the app running
    while True:
        mail_elements = list(mail_checkers.values())
        processing.map(thread_mail, mail_elements)
        time.sleep(1)
        print('processing...')


main_process()
