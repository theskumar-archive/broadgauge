import functools
import web

from ..template import render_template
from ..models import User, Organization
from ..flash import flash
from .. import account
from .. import forms

urls = (
    "/admin", "admin",
    "/admin/orgs", "admin_orgs",
    "/admin/people", "admin_people",
)


def has_admins():
    """Returns True if there is at least one admin defined.
    """
    admins = User.findall(is_admin=True)
    return bool(admins)


def admin_required(f):
    def is_current_user_admin():
        user = account.get_current_user()
        if not user:
            return False

        if user.is_admin():
            return True

        # Bootstrap Mode
        # when there are no admins defined, consider everyone an admin.
        if user and not User.findall(is_admin=True):
            return True

    @functools.wraps(f)
    def g(*a, **kw):
        if is_current_user_admin():
            return f(*a, **kw)
        else:
            return render_template("permission_denied.html")
    return g


class admin:
    @admin_required
    def GET(self):
        admins = User.findall(is_admin=True)
        return render_template("admin/index.html", admins=admins)

    @admin_required
    def POST(self):
        i = web.input(action=None)
        if i.action == "add-admin" and 'email' in i:
            user = User.find(email=i.email)
            if user:
                user.update(is_admin=True)
                flash('Succefully marked {} as admin'.format(i.email))
                raise web.seeother("/admin")
            else:
                admins = User.findall(is_admin=True)
                return render_template("admin/index.html",  # noqa
                        admins=admins,
                        error_add_admin="Not a valid user.")
        else:
            return self.GET()


class admin_orgs:
    @admin_required
    def GET(self):
        form = forms.AdminAddOrgForm()
        return render_template("admin/orgs.html", form=form)

    @admin_required
    def POST(self):
        i = web.input()
        form = forms.AdminAddOrgForm(i)
        if not form.validate():
            return render_template("admin/orgs.html", form=form)
        org = Organization.new(name=i.name, city=i.city)
        flash("Successfully created new organizaton.")
        raise web.seeother("/orgs/{}".format(org.id))


class admin_people:
    @admin_required
    def GET(self):
        people = User.findall(order='id desc')
        form = forms.AdminAddPersonForm()
        return render_template("admin/people.html", form=form, people=people)

    @admin_required
    def POST(self):
        i = web.input()
        form = forms.AdminAddPersonForm(i)
        if not form.validate():
            people = User.findall(order='id desc')
            return render_template("admin/people.html", form=form, people=people)
        else:
            User.new(name=i.name, email=i.email, phone=i.phone, city=i.city, is_trainer=form.trainer.data)
            flash("Created new user successfully.")
            raise web.seeother("/admin/people")
