import click

from gorunn.helpers import load_available_projects
# Validator function for the click callbacks to return avail apps
class AppValidator:
    def __init__(self):
        self.available_projects = load_available_projects()

    def validate_apps(self, app=None, include_services=False):
        if include_services:
            # Append additional services to the available projects list
            self.available_projects.extend(["proxy", "mysql", "opensearch", "postgresql", "chroma", "redis"])

        if app:
            if app != "all" and app not in self.available_projects:
                raise click.BadParameter(f"Choose from {', '.join(self.available_projects)}.")
            return app
        else:
            return self.available_projects

    def validate_app_callback(self, ctx, param, value):
        try:
            self.validate_apps(app=value, include_services=True)
            return value
        except click.BadParameter as e:
            raise e
        except Exception as e:
            raise click.BadParameter(str(e))