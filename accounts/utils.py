import hashlib

def hash_document(file):
    sha256 = hashlib.sha256()
    for chunk in file.chunks():
        sha256.update(chunk)
    file.seek(0)  # reset file pointer after reading
    return sha256.hexdigest()