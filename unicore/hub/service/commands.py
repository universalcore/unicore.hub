from pyramid.paster import bootstrap

import click

from unicore.hub.service.models import App
from unicore.hub.service.utils import make_password


@click.group()
@click.argument('ini_file_path',
                type=click.Path(exists=True, dir_okay=False))
@click.pass_context
def in_app_env(ctx, ini_file_path):
    env = bootstrap(ini_file_path)
    ctx.obj = {'env': env}


@in_app_env.command()
@click.option('--group', multiple=True,
              type=click.Choice(App.all_groups),
              help='a permission group to add')
@click.argument('title')
@click.pass_context
def create_app(ctx, group, title):
    session = ctx.obj['env']['request'].db

    app = App()
    session.add(app)
    app.title = title
    app.groups = group

    password = make_password(bit_length=15)
    app.password = password

    session.commit()
    click.echo('')
    click.echo(
        "App '%s' has been created and assigned to %r" % (title, group))
    click.echo("App identifier is '%s'" % app.uuid)
    click.echo("App password is '%s'" % password)
    click.echo('')
