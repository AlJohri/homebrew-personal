import sys
import argparse
from subprocess import run as original_run
from functools import partial

class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        """
        don't show error message if you just type `prog`
        """
        messages_to_mute = [
            "the following arguments are required: %s" % word for word in ('command',)
        ]
        if message not in messages_to_mute:
            sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)


# Copied from https://gist.github.com/sampsyo/471779
class AliasedSubParsersAction(argparse._SubParsersAction):

    class _AliasedPseudoAction(argparse.Action):
        def __init__(self, name, aliases, help):
            dest = name
            if aliases:
                dest += ' (%s)' % ','.join(aliases)
            sup = super(AliasedSubParsersAction._AliasedPseudoAction, self)
            sup.__init__(option_strings=[], dest=dest, help=help) 

    def add_parser(self, name, **kwargs):
        aliases = kwargs.pop('aliases', [])
        parser = super(AliasedSubParsersAction, self).add_parser(name, **kwargs)

        # Make the aliases work.
        for alias in aliases:
            self._name_parser_map[alias] = parser
        # Make the help text reflect them, first removing old help entry.
        if 'help' in kwargs:
            help = kwargs.pop('help')
            self._choices_actions.pop()
            pseudo_action = self._AliasedPseudoAction(name, aliases, help)
            self._choices_actions.append(pseudo_action)

        return parser

run = partial(original_run, shell=True)