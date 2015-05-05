from __future__ import unicode_literals
from devpi_common.request import new_requests_session
from devpi_server.views import TriggerError, server_version
from devpi_server.config import render_string
import json
import py


def devpiserver_indexconfig_defaults():
    return {"uploadtrigger_jenkins": None}


def devpiserver_trigger(log, application_url, stage, projectname, version):
    jenkinsurl = stage.ixconfig.get("uploadtrigger_jenkins")
    if not jenkinsurl:
        return
    jenkinsurl = jenkinsurl.format(pkgname=projectname, pkgversion=version)

    source = render_string(
        "devpibootstrap.py",
        INDEXURL=application_url + "/" + stage.name,
        VIRTUALENVTARURL= (application_url +
            "/root/pypi/+f/f61/cdd983d2c4e6a/"
            "virtualenv-1.11.6.tar.gz"
            ),
        TESTSPEC=projectname,
        DEVPI_INSTALL_INDEX = application_url + "/" + stage.name + "/+simple/"
    )
    inputfile = py.io.BytesIO(source.encode("ascii"))
    session = new_requests_session(agent=("server", server_version))
    try:
        r = session.post(jenkinsurl, data={
                        "Submit": "Build",
                        "name": "jobscript.py",
                        "json": json.dumps(
                    {"parameter": {"name": "jobscript.py", "file": "file0"}}),
            },
                files={"file0": ("file0", inputfile)})
    except session.Errors:
        raise TriggerError("%s: failed to connect to jenkins at %s",
                           projectname, jenkinsurl)

    if 200 <= r.status_code < 300:
        log.info("successfully triggered jenkins: %s", jenkinsurl)
    else:
        log.error("%s: failed to trigger jenkins at %s", r.status_code,
                  jenkinsurl)
        log.debug(r.content)
        raise TriggerError("%s: failed to trigger jenkins at %s",
                           projectname, jenkinsurl)
