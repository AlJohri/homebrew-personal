import argparse
import logging
import textwrap

from .utils import run, CustomArgumentParser, AliasedSubParsersAction

def make_get_cmd(subparsers, shared_parsers=[]):

    def get_cmd(args):
        run(f"aws ssm get-parameter --name {args.name} --with-decryption --query 'Parameter.Value' --output text")

    parser = subparsers.add_parser('get', parents=shared_parsers)
    parser.add_argument('name')
    parser.set_defaults(func=get_cmd)

def make_list_cmd(subparsers, shared_parsers=[]):

    def list_cmd(args):

        if args.json:
            query = 'Parameters[*].{Name:Name,Value:Value}'
            run(f"""
            aws ssm get-parameters-by-path \
                --path '{args.path}' --recursive --with-decryption \
                --query '{query}' --output json""")
        else:
            query = 'Parameters[*].{Name:Name}'
            run(f"""aws ssm get-parameters-by-path \
                    --path '{args.path}' --recursive --with-decryption \
                    --query '{query}' --output text""")

    parser = subparsers.add_parser('list', parents=shared_parsers, aliases=('ls',))
    parser.add_argument('--json', default=False, action='store_true')
    parser.add_argument('--path', default='/')

    parser.set_defaults(func=list_cmd)

def make_put_cmd(subparsers, shared_parsers=[]):

    def put_cmd(args):
        raise NotImplementedError("put not yet implemented")

    parser = subparsers.add_parser('put', parents=shared_parsers, aliases=('set',))
    parser.set_defaults(func=put_cmd)

def make_delete_cmd(subparsers, shared_parsers=[]):

    def delete_cmd(args):
        raise NotImplementedError("put not yet implemented")

    parser = subparsers.add_parser('delete', parents=shared_parsers, aliases=('rm',))
    parser.set_defaults(func=delete_cmd)

def make_help_cmd(subparsers, shared_parsers=[]):

    def help_cmd(args):
        import pdb; pdb.set_trace()
        parser.print_help()

    parser = subparsers.add_parser('help', parents=shared_parsers)
    parser.set_defaults(func=help_cmd)

def main():

    global_description = """
    examples:

    ssm list
    ssm list --json
    ssm list --path '/prod'
    ssm get /prod/sftp-to-s3/sftp-user-password
    """
    global_description = textwrap.dedent(global_description)

    formatter_class = lambda prog: argparse.RawDescriptionHelpFormatter(prog, max_help_position=32)

    parser = CustomArgumentParser(description=global_description, formatter_class=formatter_class)
    parser.register('action', 'parsers', AliasedSubParsersAction)

    shared_parser = argparse.ArgumentParser(add_help=False)
    shared_parser.add_argument('--verbose', default=False, action='store_true')

    subparsers = parser.add_subparsers(dest='command', parser_class=CustomArgumentParser)
    subparsers.required = True

    make_get_cmd(subparsers, [shared_parser])
    make_list_cmd(subparsers, [shared_parser])
    make_put_cmd(subparsers, [shared_parser])
    make_help_cmd(subparsers, [shared_parser])
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format=
            "[%(name)s | Thread: %(thread)d %(threadName)s | "
            "Process: %(process)d %(processName)s] %(asctime)s %(message)s")
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)

    args.func(args)

