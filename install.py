# installer savetoadditionalarchive
# Copyright 2026 Johanna Karen Roedenbeck
# Distributed under the terms of the GNU Public License (GPLv3)

from weecfg.extension import ExtensionInstaller
from weeutil.config import config_from_str

def loader():
    return AdditionalArchiveInstaller()

class AdditionalArchiveInstaller(ExtensionInstaller):
    def __init__(self):
        super(AdditionalArchiveInstaller, self).__init__(
            version="0.1",
            name='Additional save',
            description='save observation types to additional databases',
            author="Johanna Karen Roedenbeck",
            author_email="",
            archive_services='user.savetoadditionalarchive.AdditionalArchive',
            config=dict(),
            files=[('bin/user', ['bin/user/savetoadditionalarchive.py'])]
            )
