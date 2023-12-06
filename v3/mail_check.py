from mail2 import MailChecker
from firebase import FirebaseDB
import hash
import time
import functools
from multiprocessing.dummy import Pool


def on_snapshot(mail_checkers, doc_snapshot, changes, read_time):
    for change in changes:
        if change.type.name == 'MODIFIED':
            print(u'Documento modificado: {}'.format(change.document.id))
            print(u'Datos antiguos: {}'.format(change.old_index))
            print(u'Datos nuevos: {}'.format(change.document.to_dict()))
            doc_id = change.document.id
            mail = hash.d_s_f(change.document.to_dict()['mail'])
            password = hash.d_s_f(change.document.to_dict()['mailk'])
            if ('subjects' in change.document.to_dict() and change.document.to_dict()['subjects'] and
                    change.document.to_dict()['access']):
                new_subjects = change.document.to_dict()['subjects']
                mail_checkers[doc_id] = (mail, password, new_subjects)

        if change.type.name == 'ADDED':
            print(u'Nuevo documento añadido: {}'.format(change.document.id))
            print(u'Datos del nuevo documento: {}'.format(change.document.to_dict()))
            doc_id = change.document.id
            mail = hash.d_s_f(change.document.to_dict()['mail'])
            password = hash.d_s_f(change.document.to_dict()['mailk'])
            if ('subjects' in change.document.to_dict() and change.document.to_dict()['subjects'] and
                    change.document.to_dict()['access']):
                new_subjects = change.document.to_dict()['subjects']
                mail_checkers[doc_id] = (mail, password, new_subjects)

        if change.type.name == 'REMOVED':
            print(u'Documento eliminado: {}'.format(change.document.id))
            print(u'Datos del documento eliminado: {}'.format(change.document.to_dict()))
            doc_id = change.document.id
            mail_checkers.pop(doc_id)


def thread_mail(args):
    mail, key, subjects = args
    mc = MailChecker(mail, key)
    mc.check_mail(subjects)


def main():
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


main()

