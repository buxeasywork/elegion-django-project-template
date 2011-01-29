from Crypto.Cipher import AES


def mysql_AES_key(key):
    key = key[:16]
    key = ''.join((
        key,
        chr(0)*(16-len(key))
    ))
    return key


def mysql_AES_encrypt(value, key):
    crypter = AES.new(mysql_AES_key(key), AES.MODE_ECB, '')
    pad = (16 - len(value) % 16) or 16
    value = ''.join((value,chr(pad)*pad))
    return crypter.encrypt(value)


def mysql_AES_decrypt(value, key):
    crypter = AES.new(mysql_AES_key(key), AES.MODE_ECB, '')
    value = crypter.decrypt(value)
    pad = ord(value[-1])
    return value[:-pad]

