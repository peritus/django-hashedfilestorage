from base64 import urlsafe_b64encode, urlsafe_b64decode
from hashlib import sha1
from os.path import exists, join
import os

from django.core.files.storage import Storage, FileSystemStorage

def _hash(data):
    # @see http://fi.am/entry/urlsafe-base64-encodingdecoding-in-two-lines/
    return urlsafe_b64encode(sha1(data).digest()).strip('=')

def generate_hashed_file_storage(storage_klass):
    '''
    Adds a thin layer to a django.core.files.storage.Storage subclass that
    rewrites filenames, so they depend (read: SHA1-hash) on the file's content

    This way, you can set a far future Expires http header to your
    upload-directory, so your visitors only need to download each file once(!).
    ( see http://stevesouders.com/hpws/rule-expires.php for details )
    '''
    old_save = storage_klass._save
    def _save(self, name, content):
        new_name = "/".join(name.split("/")[:-1]) + "/" + _hash(content.read()) + "." + name.split(".")[-1]

        if exists(self.path(new_name)):
	    # discard the uploaded file, make the storage backend move the
	    # existing file (guaranteed to be the same one) in-place
	    # (FileSystemStorage chokes on writing to existing files)
            content.temporary_file_path = lambda: self.path(new_name)

        return old_save(self, new_name, content)
    storage_klass._save = _save

    storage_klass.get_available_name = lambda _, overwrite_me: overwrite_me

    return storage_klass

HashedFileSystemStorage = generate_hashed_file_storage(FileSystemStorage)
