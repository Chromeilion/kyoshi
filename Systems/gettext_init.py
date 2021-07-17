import os
import gettext
import daiquiri


class GettextInit:
    # Set up gettext
    def __init__(self, __file__):
        self.logging = daiquiri.getLogger(__name__)
        self.languages = os.environ["BOT_LANGUAGE"]
        self.full_dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.basename('locale'))
        self.domain = os.path.basename(__file__)[:-3:]

    def generate(self):
        try:
            self.logging.info(f"Searching for translation files for {self.domain} in language {self.languages}.")
            translator = gettext.translation(self.domain, self.full_dir_path, [self.languages])
            translator.install()
            _ = translator.gettext
            self.logging.info(f"Translation file found, now using {self.languages} for all "
                              f"communications from {self.domain}.")
            return _
        except FileNotFoundError:
            self.logging.info(f"No translation file found for {self.domain} in language {self.languages}, "
                              "no translation will be applied.")
            return lambda x: x
