from pyramid.paster import bootstrap

import click
import colander

from unicore.hub.service.models import App
from unicore.hub.service.schema import App as AppSchema


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
@click.option('--url', default=None,
              help='the app\'s url, if it has one')
@click.argument('title')
@click.pass_context
def create_app(ctx, group, url, title):
    session = ctx.obj['env']['request'].db

    app = App()
    session.add(app)

    try:
        data = AppSchema().deserialize({
            'title': title,
            'url': url,
            'groups': group})
        for key, value in data.iteritems():
            setattr(app, key, value)
    except colander.Invalid as e:
        first_error = e.children[0]
        raise click.BadParameter(
            '\n'.join(first_error.messages()),
            param_hint=first_error.node.name)

    session.commit()
    click.echo('')
    click.echo(
        "App '%s' has been created and assigned to %r" % (title, group))
    click.echo("App identifier is '%s'" % app.uuid)
    click.echo("App key is '%s'" % app.key)
    click.echo('')
