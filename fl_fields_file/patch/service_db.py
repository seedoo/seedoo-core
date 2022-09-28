# Copyright 2020-2022 Flosslab S.r.l.
# Copyright 2017-2019 MuK IT GmbH
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
import os
import shutil
import tempfile
import zipfile

from odoo.addons.fl_fields_file.fields import file

from odoo.service import db
from odoo.tools import osutil

_logger = logging.getLogger(__name__)

def monkey_patch(cls):
    def decorate(func):
        name = func.__name__
        func.super = getattr(cls, name, None)
        setattr(cls, name, func)
        return func
    return decorate

@monkey_patch(db)
@db.check_db_management_enabled
def exp_duplicate_database(db_original_name, db_name):
    res = exp_duplicate_database.super(db_original_name, db_name)
    from_files = file.get_store_path(db_original_name)
    to_files = file.get_store_path(db_name)
    if os.path.exists(from_files) and not os.path.exists(to_files):
        shutil.copytree(from_files, to_files)
    return res

@monkey_patch(db)
@db.check_db_management_enabled
def exp_drop(db_name):
    res = exp_drop.super(db_name)
    files = file.get_store_path(db_name)
    if os.path.exists(files):
        shutil.rmtree(files)
    return res

@monkey_patch(db)
@db.check_db_management_enabled
def dump_db(db_name, stream, backup_format="zip"):
    if backup_format == "zip":
        res = dump_db.super(db_name, False, backup_format)
        with osutil.tempdir() as dump_dir:
            with zipfile.ZipFile(res, "r") as zip:
                zip.extractall(dump_dir)
                files = file.get_store_path(db_name)
                if os.path.exists(files):
                    shutil.copytree(files, os.path.join(dump_dir, "files"))
            if stream:
                osutil.zip_dir(
                    dump_dir,
                    stream,
                    include_dir=False,
                    fnct_sort=lambda file_name: file_name != "dump.sql",
                )
            else:
                t = tempfile.TemporaryFile()
                osutil.zip_dir(
                    dump_dir,
                    t,
                    include_dir=False,
                    fnct_sort=lambda file_name: file_name != "dump.sql",
                )
                t.seek(0)
                return t
    else:
        return dump_db.super(db_name, stream, backup_format)

@monkey_patch(db)
@db.check_db_management_enabled
def restore_db(db, dump_file, copy=False):
    res = restore_db.super(db, dump_file, copy)
    with osutil.tempdir() as dump_dir:
        if zipfile.is_zipfile(dump_file):
            with zipfile.ZipFile(dump_file, "r") as zip:
                files = [m for m in zip.namelist() if m.startswith("files/")]
                if files:
                    zip.extractall(dump_dir, files)
                    files_path = os.path.join(dump_dir, "files")
                    shutil.move(files_path, file.get_store_path(db))
    return res

@monkey_patch(db)
@db.check_db_management_enabled
def exp_rename(old_name, new_name):
    res = exp_rename.super(old_name, new_name)
    from_files = file.get_store_path(old_name)
    to_files = file.get_store_path(new_name)
    if os.path.exists(from_files) and not os.path.exists(to_files):
        shutil.copytree(from_files, to_files)
    return res
