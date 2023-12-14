import hashlib
import base64


class Hash:
    @staticmethod
    def h_dm5(text):
        # Codifica el texto en formato UTF-8 antes de hacer el hashing
        encoded_text = text.encode('utf-8')

        # Crea un objeto hash MD5
        md5_hash = hashlib.md5()

        # Actualiza el hash con el texto codificado
        md5_hash.update(encoded_text)

        # Obtiene el resultado del hashing en formato hexadecimal
        hashed_result = md5_hash.hexdigest()

        return hashed_result

    # funcion para codifcar texto en base64
    @staticmethod
    def e_s_f(text):
        # Codifica el texto en formato UTF-8 y luego realiza la codificación Base64
        encoded_bytes = base64.b64encode(text.encode('utf-8'))
        encoded_text = encoded_bytes.decode('utf-8')
        return encoded_text

    # funcion para decodifcar texto en base64
    @staticmethod
    def d_s_f(encoded_text):
        # Decodifica la cadena Base64 de nuevo al texto original en formato UTF-8
        decoded_bytes = base64.b64decode(encoded_text)
        decoded_text = decoded_bytes.decode('utf-8')
        return decoded_text
